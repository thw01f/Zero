<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as d3 from 'd3'
import { useReportStore } from '../stores/report'
import AppIcon from '../components/AppIcon.vue'

const report  = useReportStore()
const svgEl   = ref<SVGSVGElement | null>(null)
const loading = ref(false)
const error   = ref('')
const colorMode = ref<'severity' | 'language' | 'debt'>('severity')
const searchQ   = ref('')
const selected  = ref<any>(null)
const hoveredId = ref<string | null>(null)

const nodes = ref<any[]>([])
const edges = ref<any[]>([])
const stats = ref<any>({})

let simulation: d3.Simulation<any, any> | null = null
let svgSel: d3.Selection<SVGSVGElement, unknown, null, undefined> | null = null
let zoomBehavior: d3.ZoomBehavior<SVGSVGElement, unknown> | null = null

const SEV_COLOR: Record<string, string> = {
  critical: '#ef4444', major: '#f97316', minor: '#eab308', info: '#60a5fa', clean: '#22c55e',
}
const LANG_COLOR: Record<string, string> = {
  python: '#3b82f6', javascript: '#f59e0b', typescript: '#8b5cf6',
  java: '#ef4444', go: '#06b6d4', rust: '#f97316',
  ruby: '#ec4899', php: '#a855f7', csharp: '#2563eb', shell: '#6b7280',
  terraform: '#5c4ee5', yaml: '#0ea5e9', unknown: '#9ca3af',
}

function nodeColor(n: any): string {
  if (colorMode.value === 'severity') return SEV_COLOR[n.severity] ?? '#9ca3af'
  if (colorMode.value === 'language') return LANG_COLOR[n.language ?? 'unknown'] ?? '#9ca3af'
  // debt — gradient green→red
  const t = Math.min((n.debt_score ?? 0) / 10, 1)
  return d3.interpolateRdYlGn(1 - t)
}

function nodeRadius(n: any): number {
  const base = 5
  const bonus = Math.sqrt(n.issue_count ?? 0) * 2
  return Math.min(base + bonus, 22)
}

async function loadGraph() {
  const jobId = report.currentJob?.id
  if (!jobId) { error.value = 'No active scan — run a scan first'; return }
  loading.value = true; error.value = ''
  try {
    const r = await fetch(`/api/graph/${jobId}`)
    if (!r.ok) throw new Error('Graph data not available')
    const d = await r.json()
    nodes.value = d.nodes ?? []
    edges.value = d.edges ?? []
    stats.value = d.stats  ?? {}
    await nextTick()
    renderGraph()
  } catch (e: any) {
    error.value = e.message ?? 'Failed to load graph'
  } finally {
    loading.value = false
  }
}

function renderGraph() {
  if (!svgEl.value || !nodes.value.length) return
  const el   = svgEl.value
  const W    = el.clientWidth  || 900
  const H    = el.clientHeight || 600

  d3.select(el).selectAll('*').remove()

  svgSel = d3.select(el)
  const defs = svgSel.append('defs')

  // Glow filter
  const glow = defs.append('filter').attr('id', 'glow').attr('x', '-50%').attr('y', '-50%').attr('width', '200%').attr('height', '200%')
  glow.append('feGaussianBlur').attr('stdDeviation', '3').attr('result', 'blur')
  const feMerge = glow.append('feMerge')
  feMerge.append('feMergeNode').attr('in', 'blur')
  feMerge.append('feMergeNode').attr('in', 'SourceGraphic')

  const g = svgSel.append('g').attr('class', 'graph-group')

  zoomBehavior = d3.zoom<SVGSVGElement, unknown>()
    .scaleExtent([0.1, 6])
    .on('zoom', (event) => { g.attr('transform', event.transform) })
  svgSel.call(zoomBehavior).on('dblclick.zoom', null)

  const filtered = searchQ.value
    ? nodes.value.filter(n => n.id.toLowerCase().includes(searchQ.value.toLowerCase()))
    : nodes.value
  const filteredIds = new Set(filtered.map((n: any) => n.id))
  const filteredEdges = edges.value.filter((e: any) => filteredIds.has(e.source) && filteredIds.has(e.target))

  const nodesCopy = filtered.map(n => ({ ...n }))
  const edgesCopy = filteredEdges.map(e => ({ ...e }))

  simulation = d3.forceSimulation(nodesCopy)
    .force('link',    d3.forceLink(edgesCopy).id((d: any) => d.id).distance(80).strength(0.4))
    .force('charge',  d3.forceManyBody().strength(-180).distanceMax(300))
    .force('center',  d3.forceCenter(W / 2, H / 2))
    .force('collide', d3.forceCollide().radius((d: any) => nodeRadius(d) + 6))
    .force('x',       d3.forceX(W / 2).strength(0.04))
    .force('y',       d3.forceY(H / 2).strength(0.04))

  // Edges
  const link = g.append('g').attr('class', 'links')
    .selectAll('line')
    .data(edgesCopy)
    .join('line')
    .attr('stroke', 'var(--gc-border)')
    .attr('stroke-width', 1)
    .attr('stroke-opacity', 0.5)

  // Node groups
  const node = g.append('g').attr('class', 'nodes')
    .selectAll('g.node-g')
    .data(nodesCopy)
    .join('g')
    .attr('class', 'node-g')
    .style('cursor', 'pointer')
    .call(d3.drag<SVGGElement, any>()
      .on('start', (event, d) => {
        if (!event.active) simulation!.alphaTarget(0.3).restart()
        d.fx = d.x; d.fy = d.y
      })
      .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y })
      .on('end',  (event, d) => {
        if (!event.active) simulation!.alphaTarget(0)
        d.fx = null; d.fy = null
      })
    )

  node.append('circle')
    .attr('r',    (d: any) => nodeRadius(d))
    .attr('fill', (d: any) => nodeColor(d))
    .attr('fill-opacity', 0.9)
    .attr('stroke', '#fff')
    .attr('stroke-width', 1.5)

  // File name labels (only for selected/hovered, done via JS)
  node.append('text')
    .attr('dy', (d: any) => nodeRadius(d) + 10)
    .attr('text-anchor', 'middle')
    .attr('fill', 'var(--gc-text-2)')
    .attr('font-size', '10px')
    .attr('pointer-events', 'none')
    .attr('class', 'node-label')
    .text((d: any) => d.label)
    .style('display', (d: any) => (d.issue_count > 0 || nodeRadius(d) > 12) ? 'block' : 'none')

  node.on('click', (_event: any, d: any) => {
    selected.value = d
  })
  .on('mouseenter', (_event: any, d: any) => {
    hoveredId.value = d.id
    d3.select(_event.currentTarget).select('circle')
      .attr('stroke', nodeColor(d))
      .attr('stroke-width', 3)
      .attr('filter', 'url(#glow)')
  })
  .on('mouseleave', (_event: any, d: any) => {
    hoveredId.value = null
    d3.select(_event.currentTarget).select('circle')
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5)
      .attr('filter', null)
  })

  simulation.on('tick', () => {
    link
      .attr('x1', (d: any) => d.source.x)
      .attr('y1', (d: any) => d.source.y)
      .attr('x2', (d: any) => d.target.x)
      .attr('y2', (d: any) => d.target.y)
    node.attr('transform', (d: any) => `translate(${d.x},${d.y})`)
  })
}

function resetZoom() {
  if (svgSel && zoomBehavior) {
    svgSel.transition().duration(400).call(zoomBehavior.transform, d3.zoomIdentity)
  }
}

const legendItems = computed(() => {
  if (colorMode.value === 'severity') return [
    { label: 'Critical', color: SEV_COLOR.critical },
    { label: 'Major',    color: SEV_COLOR.major    },
    { label: 'Minor',    color: SEV_COLOR.minor    },
    { label: 'Info',     color: SEV_COLOR.info     },
    { label: 'Clean',    color: SEV_COLOR.clean    },
  ]
  if (colorMode.value === 'language') return Object.entries(LANG_COLOR)
    .filter(([k]) => k !== 'unknown')
    .map(([k, v]) => ({ label: k, color: v }))
  return [
    { label: 'Low debt',  color: '#22c55e' },
    { label: 'Med debt',  color: '#eab308' },
    { label: 'High debt', color: '#ef4444' },
  ]
})

watch(colorMode, () => renderGraph())
watch(searchQ, () => { if (simulation) { simulation.stop(); renderGraph() } })

onMounted(() => {
  loadGraph()
  window.addEventListener('resize', renderGraph)
})
onBeforeUnmount(() => {
  simulation?.stop()
  window.removeEventListener('resize', renderGraph)
})
</script>

<template>
  <div class="cg-root">
    <!-- Header bar -->
    <div class="cg-header">
      <div class="cg-title">
        <AppIcon name="graph" :size="18" style="color:var(--gc-primary)"/>
        <span>Code Graph</span>
        <span class="cg-badge">Obsidian-style</span>
      </div>

      <div class="cg-controls">
        <div class="cg-search-wrap">
          <AppIcon name="search" :size="14" style="color:var(--gc-text-3);position:absolute;left:9px;top:9px;"/>
          <input v-model="searchQ" class="cg-search" placeholder="Filter files…" />
        </div>

        <div class="cg-control-item">
          <label class="cg-label">Color</label>
          <select v-model="colorMode" class="gc-select gc-select-sm" style="width:110px;">
            <option value="severity">Severity</option>
            <option value="language">Language</option>
            <option value="debt">Debt Score</option>
          </select>
        </div>

        <button class="gc-btn gc-btn-ghost gc-btn-sm" @click="resetZoom">
          <AppIcon name="cpu" :size="13" /> Reset View
        </button>
        <button class="gc-btn gc-btn-primary gc-btn-sm" @click="loadGraph" :disabled="loading">
          <AppIcon name="update" :size="13" /> {{ loading ? 'Loading…' : 'Refresh' }}
        </button>
      </div>
    </div>

    <!-- Stats ribbon -->
    <div class="cg-stats" v-if="stats.total_files">
      <div class="cg-stat"><span class="cg-stat-val">{{ stats.total_files }}</span><span class="cg-stat-lbl">files</span></div>
      <div class="cg-stat-sep">·</div>
      <div class="cg-stat"><span class="cg-stat-val">{{ stats.total_edges }}</span><span class="cg-stat-lbl">edges</span></div>
      <div class="cg-stat-sep">·</div>
      <div class="cg-stat sev-crit"><span class="cg-stat-val">{{ stats.critical_files }}</span><span class="cg-stat-lbl">critical</span></div>
      <div class="cg-stat-sep">·</div>
      <div class="cg-stat sev-ok"><span class="cg-stat-val">{{ stats.clean_files }}</span><span class="cg-stat-lbl">clean</span></div>

      <div class="cg-legend">
        <span v-for="item in legendItems.slice(0, 6)" :key="item.label" class="cg-leg-item">
          <span class="cg-leg-dot" :style="{background: item.color}"></span>
          {{ item.label }}
        </span>
      </div>
    </div>

    <!-- Canvas + side panel -->
    <div class="cg-body">
      <!-- Loading / error state -->
      <div v-if="loading" class="cg-overlay">
        <div class="cg-spinner"></div>
        <div style="margin-top:12px;color:var(--gc-text-2);">Building graph…</div>
      </div>
      <div v-else-if="error" class="cg-overlay">
        <AppIcon name="warning" :size="32" style="color:var(--gc-warning)"/>
        <div style="margin-top:12px;color:var(--gc-text-2);">{{ error }}</div>
        <button class="gc-btn gc-btn-primary gc-btn-sm" style="margin-top:12px;" @click="loadGraph">Retry</button>
      </div>

      <svg ref="svgEl" class="cg-svg" />

      <!-- Detail side panel -->
      <transition name="panel-slide">
        <div v-if="selected" class="cg-panel">
          <div class="cg-panel-hdr">
            <div class="cg-panel-name" :title="selected.id">{{ selected.label }}</div>
            <button class="gc-icon-btn" style="width:26px;height:26px;font-size:13px;" @click="selected=null">✕</button>
          </div>
          <div class="cg-panel-path">{{ selected.id }}</div>

          <div class="cg-panel-metrics">
            <div class="cg-metric">
              <div class="cg-metric-val" :class="`chip chip-${selected.severity}`">{{ selected.severity }}</div>
              <div class="cg-metric-lbl">Max Severity</div>
            </div>
            <div class="cg-metric">
              <div class="cg-metric-val">{{ selected.issue_count }}</div>
              <div class="cg-metric-lbl">Issues</div>
            </div>
            <div class="cg-metric">
              <div class="cg-metric-val">{{ selected.grade }}</div>
              <div class="cg-metric-lbl">Grade</div>
            </div>
            <div class="cg-metric">
              <div class="cg-metric-val">{{ selected.loc }}</div>
              <div class="cg-metric-lbl">LOC</div>
            </div>
          </div>

          <div v-if="selected.top_issues?.length" class="cg-issues-list">
            <div class="cg-issues-ttl">Top Issues</div>
            <div v-for="(iss, i) in selected.top_issues" :key="i" class="cg-iss-row">
              <span :class="`chip chip-${iss.severity}`" style="font-size:10px;padding:1px 5px;">{{ iss.severity }}</span>
              <div class="cg-iss-body">
                <div class="cg-iss-msg">{{ iss.message }}</div>
                <div class="cg-iss-meta">line {{ iss.line }} · {{ iss.rule_id }}
                  <span v-if="iss.cwe" style="opacity:.7"> · {{ iss.cwe }}</span>
                </div>
              </div>
            </div>
          </div>

          <router-link :to="`/issues?file=${encodeURIComponent(selected.id)}`"
            class="gc-btn gc-btn-primary gc-btn-sm" style="margin-top:12px;display:inline-flex;align-items:center;gap:6px;">
            <AppIcon name="bug" :size="13" /> View All Issues
          </router-link>
        </div>
      </transition>
    </div>
  </div>
</template>

<style scoped>
.cg-root { display: flex; flex-direction: column; height: calc(100vh - 64px - 48px); min-height: 500px; }

.cg-header {
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
  padding: 12px 16px; border-bottom: 1px solid var(--gc-border);
  background: var(--gc-surface);
}
.cg-title { display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 600; color: var(--gc-text); }
.cg-badge { font-size: 10px; padding: 2px 7px; border-radius: 10px; background: var(--gc-primary-light); color: var(--gc-primary); font-weight: 500; }
.cg-controls { display: flex; align-items: center; gap: 8px; margin-left: auto; flex-wrap: wrap; }
.cg-search-wrap { position: relative; }
.cg-search { padding: 6px 10px 6px 30px; border: 1px solid var(--gc-border); border-radius: 6px; background: var(--gc-surface-2); color: var(--gc-text); font-size: 13px; width: 160px; }
.cg-search:focus { outline: none; border-color: var(--gc-primary); }
.cg-control-item { display: flex; align-items: center; gap: 6px; }
.cg-label { font-size: 12px; color: var(--gc-text-3); white-space: nowrap; }

.cg-stats {
  display: flex; align-items: center; gap: 8px; padding: 8px 16px;
  background: var(--gc-surface-2); border-bottom: 1px solid var(--gc-border);
  font-size: 12px; flex-wrap: wrap;
}
.cg-stat { display: flex; align-items: center; gap: 4px; }
.cg-stat-val { font-weight: 600; color: var(--gc-text); }
.cg-stat-lbl { color: var(--gc-text-3); }
.cg-stat.sev-crit .cg-stat-val { color: #ef4444; }
.cg-stat.sev-ok   .cg-stat-val { color: #22c55e; }
.cg-stat-sep { color: var(--gc-divider); }
.cg-legend { display: flex; align-items: center; gap: 10px; margin-left: auto; flex-wrap: wrap; }
.cg-leg-item { display: flex; align-items: center; gap: 5px; font-size: 11px; color: var(--gc-text-2); }
.cg-leg-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }

.cg-body { flex: 1; position: relative; overflow: hidden; display: flex; background: var(--gc-bg); }
.cg-svg { flex: 1; width: 100%; height: 100%; cursor: grab; }
.cg-svg:active { cursor: grabbing; }

.cg-overlay {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center; z-index: 10;
  background: var(--gc-bg);
}
.cg-spinner {
  width: 36px; height: 36px; border: 3px solid var(--gc-border);
  border-top-color: var(--gc-primary); border-radius: 50%; animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Side panel */
.cg-panel {
  width: 300px; flex-shrink: 0; border-left: 1px solid var(--gc-border);
  background: var(--gc-surface); padding: 16px; overflow-y: auto;
}
.cg-panel-hdr { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; }
.cg-panel-name { font-size: 14px; font-weight: 600; color: var(--gc-text); word-break: break-all; }
.cg-panel-path { font-size: 11px; color: var(--gc-text-3); margin-top: 4px; word-break: break-all; }
.cg-panel-metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 14px; }
.cg-metric { background: var(--gc-surface-2); border-radius: 8px; padding: 10px; text-align: center; }
.cg-metric-val { font-size: 16px; font-weight: 600; color: var(--gc-text); }
.cg-metric-lbl { font-size: 11px; color: var(--gc-text-3); margin-top: 2px; }

.cg-issues-list { margin-top: 14px; }
.cg-issues-ttl  { font-size: 12px; font-weight: 600; color: var(--gc-text-2); text-transform: uppercase; letter-spacing: .5px; margin-bottom: 8px; }
.cg-iss-row { display: flex; gap: 8px; align-items: flex-start; padding: 6px 0; border-bottom: 1px solid var(--gc-divider); }
.cg-iss-body { flex: 1; min-width: 0; }
.cg-iss-msg  { font-size: 12px; color: var(--gc-text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cg-iss-meta { font-size: 11px; color: var(--gc-text-3); margin-top: 2px; }

.panel-slide-enter-active, .panel-slide-leave-active { transition: transform .2s, opacity .2s; }
.panel-slide-enter-from, .panel-slide-leave-to { transform: translateX(30px); opacity: 0; }

/* Chip styles (also in style.css but scoped here too) */
.chip { display: inline-block; padding: 2px 7px; border-radius: 4px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .3px; }
.chip-critical { background: #fef2f2; color: #dc2626; }
.chip-major    { background: #fff7ed; color: #ea580c; }
.chip-minor    { background: #fefce8; color: #ca8a04; }
.chip-info     { background: #eff6ff; color: #2563eb; }
.chip-clean    { background: #f0fdf4; color: #16a34a; }
[data-theme="dark"] .chip-critical { background: #450a0a; color: #fca5a5; }
[data-theme="dark"] .chip-major    { background: #431407; color: #fdba74; }
[data-theme="dark"] .chip-minor    { background: #422006; color: #fde047; }
[data-theme="dark"] .chip-info     { background: #172554; color: #93c5fd; }
[data-theme="dark"] .chip-clean    { background: #052e16; color: #86efac; }
</style>
