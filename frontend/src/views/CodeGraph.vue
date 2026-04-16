<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as d3 from 'd3'
import { useReportStore } from '../stores/report'
import { useScanStore } from '../stores/scan'
import AppIcon from '../components/AppIcon.vue'

const report = useReportStore()
const scan   = useScanStore()
const svgEl  = ref<SVGSVGElement | null>(null)

const loading    = ref(false)
const error      = ref('')
const colorMode  = ref<'severity' | 'language' | 'debt'>('severity')
const searchQ    = ref('')
const selected   = ref<any>(null)
const showDirs   = ref(false)
const viewMode   = ref<'file' | 'entity'>('file')

const nodes = ref<any[]>([])
const edges = ref<any[]>([])
const stats = ref<any>({})
const truncated = ref(false)
const totalRaw  = ref(0)

// Entity view
const entityNodes = ref<any[]>([])
const entityEdges = ref<any[]>([])
const entityStats = ref<any>({})

let simulation: d3.Simulation<any, any> | null = null
let svgSel: d3.Selection<SVGSVGElement, unknown, null, undefined> | null = null
let zoomBehavior: d3.ZoomBehavior<SVGSVGElement, unknown> | null = null
let hullUpdateFn: (() => void) | null = null

const SEV_COLOR: Record<string, string> = {
  critical: '#ef4444', major: '#f97316', minor: '#eab308', info: '#60a5fa', clean: '#22c55e',
}
const LANG_COLOR: Record<string, string> = {
  python: '#3b82f6', javascript: '#f59e0b', typescript: '#8b5cf6',
  java: '#ef4444', go: '#06b6d4', rust: '#f97316', ruby: '#ec4899',
  php: '#a855f7', csharp: '#2563eb', shell: '#6b7280', c: '#a3a3a3',
  cpp: '#7c3aed', terraform: '#5c4ee5', yaml: '#0ea5e9', unknown: '#9ca3af',
}
const DIR_PALETTE = [
  '#3b82f6','#8b5cf6','#06b6d4','#f59e0b','#ec4899',
  '#22c55e','#f97316','#ef4444','#6366f1','#14b8a6',
]

function nodeColor(n: any): string {
  if (colorMode.value === 'severity') return SEV_COLOR[n.severity] ?? '#9ca3af'
  if (colorMode.value === 'language') return LANG_COLOR[n.language ?? 'unknown'] ?? '#9ca3af'
  const t = Math.min((n.debt_score ?? 0) / 10, 1)
  return d3.interpolateRdYlGn(1 - t)
}

function nodeRadius(n: any): number {
  return Math.min(5 + Math.sqrt(n.issue_count ?? 0) * 2.2, 24)
}

// ── Data loading ──────────────────────────────────────────────────────────────
async function loadGraph() {
  if (viewMode.value === 'entity') { await loadEntityGraph(); return }
  const jobId = report.data?.job_id || scan.jobId
  if (!jobId) { error.value = 'No active scan — run a scan first'; return }
  loading.value = true; error.value = ''
  try {
    const r = await fetch(`/api/graph/${jobId}`)
    if (!r.ok) throw new Error(r.status === 404 ? 'No graph data for this scan' : `HTTP ${r.status}`)
    const d = await r.json()
    nodes.value     = d.nodes     ?? []
    edges.value     = d.edges     ?? []
    stats.value     = d.stats     ?? {}
    truncated.value = d.truncated ?? false
    totalRaw.value  = d.total_raw ?? 0
    await nextTick()
    renderGraph()
  } catch (e: any) {
    error.value = e.message ?? 'Failed to load graph'
  } finally {
    loading.value = false
  }
}

async function loadEntityGraph() {
  const jobId = report.data?.job_id || scan.jobId
  if (!jobId) { error.value = 'No active scan'; return }
  loading.value = true; error.value = ''
  try {
    const r = await fetch(`/api/graph/${jobId}/entities`)
    if (!r.ok) throw new Error(r.status === 404 ? 'No entity data — re-scan to generate AST graph' : `HTTP ${r.status}`)
    const d = await r.json()
    entityNodes.value = d.nodes ?? []
    entityEdges.value = d.edges ?? []
    entityStats.value = d.stats ?? {}
    await nextTick()
    renderEntityGraph()
  } catch (e: any) {
    error.value = e.message ?? 'Failed to load entity graph'
  } finally {
    loading.value = false
  }
}

const ENTITY_COLOR: Record<string, string> = {
  function: '#3b82f6', method: '#8b5cf6', class: '#f59e0b',
}

function entityNodeColor(n: any): string {
  const sevC = SEV_COLOR[n.severity]
  if (sevC && n.severity !== 'clean') return sevC
  return ENTITY_COLOR[n.entity_type] ?? '#9ca3af'
}

function entityRadius(n: any): number {
  if (n.entity_type === 'class')    return Math.min(10 + Math.sqrt(n.issue_count ?? 0) * 2.5, 28)
  if (n.entity_type === 'method')   return Math.min(4  + Math.sqrt(n.issue_count ?? 0) * 1.8, 16)
  return Math.min(6 + Math.sqrt(n.issue_count ?? 0) * 2, 20)
}

function renderEntityGraph() {
  if (!svgEl.value) return
  simulation?.stop()
  hullUpdateFn = null
  selected.value = null

  const el = svgEl.value
  const W  = el.clientWidth  || 960
  const H  = el.clientHeight || 640

  d3.select(el).selectAll('*').remove()
  svgSel = d3.select(el)

  const defs = svgSel.append('defs')
  const glow = defs.append('filter').attr('id', 'glow')
    .attr('x', '-40%').attr('y', '-40%').attr('width', '180%').attr('height', '180%')
  glow.append('feGaussianBlur').attr('stdDeviation', '3').attr('result', 'blur')
  const fm = glow.append('feMerge')
  fm.append('feMergeNode').attr('in', 'blur')
  fm.append('feMergeNode').attr('in', 'SourceGraphic')

  // Arrow marker for call edges
  defs.append('marker').attr('id', 'arrow-call').attr('viewBox', '0 -3 6 6')
    .attr('refX', 6).attr('refY', 0).attr('markerWidth', 5).attr('markerHeight', 5)
    .attr('orient', 'auto')
    .append('path').attr('d', 'M0,-3L6,0L0,3').attr('fill', '#6366f1').attr('fill-opacity', .6)

  const g = svgSel.append('g').attr('class', 'graph-root')

  zoomBehavior = d3.zoom<SVGSVGElement, unknown>()
    .scaleExtent([0.05, 10])
    .on('zoom', ev => g.attr('transform', ev.transform))
  svgSel.call(zoomBehavior).on('dblclick.zoom', null)

  const q = searchQ.value.toLowerCase()
  const fn = q
    ? entityNodes.value.filter(n => n.label.toLowerCase().includes(q) || n.file_path.toLowerCase().includes(q))
    : entityNodes.value
  const fnIds = new Set(fn.map((n: any) => n.id))
  const fe = entityEdges.value.filter((e: any) => fnIds.has(e.source) && fnIds.has(e.target))

  const nc = fn.map((n: any) => ({ ...n }))
  const ec = fe.map((e: any) => ({ ...e }))

  if (!nc.length) {
    g.append('text').attr('x', W/2).attr('y', H/2)
      .attr('text-anchor', 'middle').attr('fill', '#6b7280').attr('font-size', 14)
      .text(q ? 'No entities match search' : 'No entity data')
    return
  }

  const linkLayer = g.append('g').attr('class', 'links')
  const link = linkLayer.selectAll('line').data(ec).join('line')
    .attr('stroke',         (d: any) => d.type === 'calls' ? '#6366f1' : '#22c55e')
    .attr('stroke-width',   (d: any) => d.type === 'contains' ? 2 : 1)
    .attr('stroke-opacity', (d: any) => d.type === 'contains' ? 0.5 : 0.4)
    .attr('stroke-dasharray', (d: any) => d.type === 'calls' ? '4,3' : null)
    .attr('marker-end', (d: any) => d.type === 'calls' ? 'url(#arrow-call)' : null)

  const nodeLayer = g.append('g').attr('class', 'nodes')
  const node = nodeLayer.selectAll<SVGGElement, any>('g.node-g')
    .data(nc).join('g')
    .attr('class', 'node-g')
    .style('cursor', 'pointer')
    .call(d3.drag<SVGGElement, any>()
      .on('start', (ev, d) => { if (!ev.active) simulation!.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y })
      .on('drag',  (ev, d) => { d.fx = ev.x; d.fy = ev.y })
      .on('end',   (ev, d) => { if (!ev.active) simulation!.alphaTarget(0); d.fx = null; d.fy = null })
    )

  // Class nodes: rounded rect; function: circle; method: diamond
  node.each(function(d: any) {
    const sel = d3.select(this)
    const r = entityRadius(d)
    const col = entityNodeColor(d)
    const brighter = d3.color(col)?.brighter(0.5)?.toString() ?? '#fff'
    if (d.entity_type === 'class') {
      sel.append('rect')
        .attr('x', -r).attr('y', -r * 0.65)
        .attr('width', r * 2).attr('height', r * 1.3)
        .attr('rx', 3)
        .attr('fill', col).attr('fill-opacity', 0.85)
        .attr('stroke', brighter).attr('stroke-width', 1.5)
    } else if (d.entity_type === 'method') {
      const s = r * 0.9
      sel.append('polygon')
        .attr('points', `0,${-s} ${s},0 0,${s} ${-s},0`)
        .attr('fill', col).attr('fill-opacity', 0.85)
        .attr('stroke', brighter).attr('stroke-width', 1.5)
    } else {
      sel.append('circle')
        .attr('r', r)
        .attr('fill', col).attr('fill-opacity', 0.85)
        .attr('stroke', brighter).attr('stroke-width', 1.5)
    }
  })

  node.append('text')
    .attr('dy', (d: any) => entityRadius(d) + 10)
    .attr('text-anchor', 'middle')
    .attr('fill', '#8a96b0').attr('font-size', '9px')
    .attr('pointer-events', 'none')
    .text((d: any) => d.label)
    .style('display', (d: any) => entityRadius(d) > 8 ? 'block' : 'none')

  node
    .on('click', (_ev, d) => { selected.value = d })
    .on('mouseenter', (ev) => {
      d3.select(ev.currentTarget).select('circle,rect,polygon')
        .attr('stroke', '#fff').attr('stroke-width', 2.5).attr('filter', 'url(#glow)')
    })
    .on('mouseleave', (ev, d) => {
      const col = d3.color(entityNodeColor(d))?.brighter(0.5)?.toString() ?? '#fff'
      d3.select(ev.currentTarget).select('circle,rect,polygon')
        .attr('stroke', col).attr('stroke-width', 1.5).attr('filter', null)
    })

  simulation = d3.forceSimulation(nc)
    .force('link',    d3.forceLink(ec).id((d: any) => d.id).distance(60).strength(0.5))
    .force('charge',  d3.forceManyBody().strength(-180).distanceMax(300))
    .force('center',  d3.forceCenter(W / 2, H / 2))
    .force('collide', d3.forceCollide().radius((d: any) => entityRadius(d) + 6).iterations(2))
    .velocityDecay(0.45).alphaDecay(0.025)

  simulation.on('tick', () => {
    link
      .attr('x1', (d: any) => d.source.x).attr('y1', (d: any) => d.source.y)
      .attr('x2', (d: any) => d.target.x).attr('y2', (d: any) => d.target.y)
    node.attr('transform', (d: any) => `translate(${d.x ?? 0},${d.y ?? 0})`)
  })

  setTimeout(() => fitGraph(), 1800)
}

// ── Rendering ─────────────────────────────────────────────────────────────────
function renderGraph() {
  if (!svgEl.value) return
  simulation?.stop()
  hullUpdateFn = null

  const el = svgEl.value
  const W  = el.clientWidth  || 960
  const H  = el.clientHeight || 640

  d3.select(el).selectAll('*').remove()
  svgSel = d3.select(el)

  // defs
  const defs = svgSel.append('defs')
  const glow = defs.append('filter').attr('id', 'glow')
    .attr('x', '-40%').attr('y', '-40%').attr('width', '180%').attr('height', '180%')
  glow.append('feGaussianBlur').attr('stdDeviation', '4').attr('result', 'blur')
  const fm = glow.append('feMerge')
  fm.append('feMergeNode').attr('in', 'blur')
  fm.append('feMergeNode').attr('in', 'SourceGraphic')

  defs.append('marker').attr('id', 'arrow').attr('viewBox', '0 -4 8 8')
    .attr('refX', 8).attr('refY', 0).attr('markerWidth', 6).attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path').attr('d', 'M0,-4L8,0L0,4').attr('fill', '#334155').attr('fill-opacity', .5)

  const g = svgSel.append('g').attr('class', 'graph-root')

  zoomBehavior = d3.zoom<SVGSVGElement, unknown>()
    .scaleExtent([0.05, 8])
    .on('zoom', ev => g.attr('transform', ev.transform))
  svgSel.call(zoomBehavior).on('dblclick.zoom', null)

  // Filter nodes
  const q = searchQ.value.toLowerCase()
  const filteredNodes = q
    ? nodes.value.filter(n => n.id.toLowerCase().includes(q) || n.label.toLowerCase().includes(q))
    : nodes.value
  const filteredIds = new Set(filteredNodes.map((n: any) => n.id))
  const filteredEdges = edges.value.filter((e: any) =>
    filteredIds.has(e.source) && filteredIds.has(e.target))

  if (!filteredNodes.length) {
    g.append('text').attr('x', W/2).attr('y', H/2)
      .attr('text-anchor', 'middle').attr('fill', '#6b7280').attr('font-size', 14)
      .text(q ? 'No files match search' : 'No data to display')
    return
  }

  const nc = filteredNodes.map((n: any) => ({ ...n }))
  const ec = filteredEdges.map((e: any) => ({ ...e }))

  // Directory colour map
  const dirs = [...new Set(nc.map((n: any) => n.dir).filter(Boolean))] as string[]
  const dirColor = new Map(dirs.map((d, i) => [d, DIR_PALETTE[i % DIR_PALETTE.length]]))

  // ── Hulls (directory regions) ──────────────────────────────────────────────
  const hullLayer = g.append('g').attr('class', 'hulls')

  function updateHulls() {
    hullLayer.selectAll('path.hull').remove()
    hullLayer.selectAll('text.hull-label').remove()
    dirs.forEach(dir => {
      const pts = nc.filter((n: any) => n.dir === dir && n.x != null)
        .map((n: any): [number, number] => [n.x!, n.y!])
      if (pts.length < 2) return
      const col = dirColor.get(dir) ?? '#6b7280'

      if (pts.length === 2) {
        // Draw a line instead of hull
        hullLayer.append('line')
          .attr('class', 'hull')
          .attr('x1', pts[0][0]).attr('y1', pts[0][1])
          .attr('x2', pts[1][0]).attr('y2', pts[1][1])
          .attr('stroke', col).attr('stroke-opacity', 0.2).attr('stroke-width', 2)
        return
      }

      const hull = d3.polygonHull(pts)
      if (!hull || hull.length < 3) return

      const cx = d3.mean(hull, p => p[0])!
      const cy = d3.mean(hull, p => p[1])!
      const expanded = hull.map(([x, y]): [number, number] => {
        const dx = x - cx, dy = y - cy
        const len = Math.sqrt(dx*dx + dy*dy) || 1
        return [x + dx/len * 22, y + dy/len * 22]
      })

      // Smooth path using catmull-rom
      const closed = [...expanded, expanded[0], expanded[1]]
      const line = d3.line<[number,number]>().x(p => p[0]).y(p => p[1])
        .curve(d3.curveCatmullRomClosed.alpha(0.5))

      hullLayer.append('path')
        .attr('class', 'hull')
        .attr('d', line(expanded)!)
        .attr('fill', col)
        .attr('fill-opacity', showDirs.value ? 0.12 : 0.06)
        .attr('stroke', col)
        .attr('stroke-opacity', 0.3)
        .attr('stroke-width', 1.5)

      // Dir label at centroid
      if (showDirs.value) {
        const shortLabel = dir.split('/').slice(-1)[0] || dir
        hullLayer.append('text')
          .attr('class', 'hull-label')
          .attr('x', cx).attr('y', cy)
          .attr('text-anchor', 'middle')
          .attr('fill', col)
          .attr('fill-opacity', 0.6)
          .attr('font-size', '10px')
          .attr('pointer-events', 'none')
          .text(shortLabel)
      }
    })
  }

  hullUpdateFn = updateHulls

  // ── Edges ──────────────────────────────────────────────────────────────────
  const linkLayer = g.append('g').attr('class', 'links')
  const link = linkLayer.selectAll('line').data(ec).join('line')
    .attr('stroke', (d: any) => d.type === 'cross-dir' ? '#4a5568' : (d.type === 'lang-cluster' ? '#7c3aed' : '#1e2d47'))
    .attr('stroke-width', (d: any) => d.type === 'cross-dir' ? 1.5 : 1)
    .attr('stroke-opacity', (d: any) => d.type === 'cross-dir' ? 0.6 : 0.35)
    .attr('stroke-dasharray', (d: any) => d.type === 'cross-dir' ? '3,3' : null)

  // ── Nodes ──────────────────────────────────────────────────────────────────
  const nodeLayer = g.append('g').attr('class', 'nodes')
  const node = nodeLayer.selectAll<SVGGElement, any>('g.node-g')
    .data(nc).join('g')
    .attr('class', 'node-g')
    .style('cursor', 'pointer')
    .call(d3.drag<SVGGElement, any>()
      .on('start', (ev, d) => { if (!ev.active) simulation!.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y })
      .on('drag',  (ev, d) => { d.fx = ev.x; d.fy = ev.y })
      .on('end',   (ev, d) => { if (!ev.active) simulation!.alphaTarget(0); d.fx = null; d.fy = null })
    )

  node.append('circle')
    .attr('r',            (d: any) => nodeRadius(d))
    .attr('fill',         (d: any) => nodeColor(d))
    .attr('fill-opacity', 0.88)
    .attr('stroke',       (d: any) => d3.color(nodeColor(d))?.brighter(0.6)?.toString() ?? '#fff')
    .attr('stroke-width', 1.5)

  node.append('text')
    .attr('dy', (d: any) => nodeRadius(d) + 11)
    .attr('text-anchor', 'middle')
    .attr('fill', '#8a96b0')
    .attr('font-size', '10px')
    .attr('pointer-events', 'none')
    .text((d: any) => d.label)
    .style('display', (d: any) => (nodeRadius(d) > 11 || d.issue_count > 0) ? 'block' : 'none')

  node
    .on('click', (_ev, d) => { selected.value = d })
    .on('mouseenter', (ev, d) => {
      d3.select(ev.currentTarget).select('circle')
        .attr('stroke', '#fff')
        .attr('stroke-width', 3)
        .attr('filter', 'url(#glow)')
    })
    .on('mouseleave', (ev, d) => {
      d3.select(ev.currentTarget).select('circle')
        .attr('stroke', d3.color(nodeColor(d))?.brighter(0.6)?.toString() ?? '#fff')
        .attr('stroke-width', 1.5)
        .attr('filter', null)
    })

  // ── Simulation ─────────────────────────────────────────────────────────────
  simulation = d3.forceSimulation(nc)
    .force('link',    d3.forceLink(ec).id((d: any) => d.id).distance(75).strength(0.3))
    .force('charge',  d3.forceManyBody().strength(-220).distanceMax(350))
    .force('center',  d3.forceCenter(W / 2, H / 2))
    .force('collide', d3.forceCollide().radius((d: any) => nodeRadius(d) + 8).iterations(2))
    .force('x',       d3.forceX(W / 2).strength(0.03))
    .force('y',       d3.forceY(H / 2).strength(0.03))
    .velocityDecay(0.4)
    .alphaDecay(0.025)

  let tickCount = 0
  simulation.on('tick', () => {
    tickCount++
    link
      .attr('x1', (d: any) => d.source.x)
      .attr('y1', (d: any) => d.source.y)
      .attr('x2', (d: any) => d.target.x)
      .attr('y2', (d: any) => d.target.y)
    node.attr('transform', (d: any) => `translate(${d.x ?? 0},${d.y ?? 0})`)
    // Update hulls every 3 ticks for performance
    if (tickCount % 3 === 0) updateHulls()
  })

  simulation.on('end', () => updateHulls())

  // Auto-fit after stabilisation
  setTimeout(() => fitGraph(), 1800)
}

function fitGraph() {
  if (!svgSel || !zoomBehavior || !svgEl.value) return
  const el = svgEl.value
  const grp = (el.querySelector('.graph-root') as SVGGElement | null)
  if (!grp) return
  const bbox = grp.getBBox()
  if (!bbox.width || !bbox.height) return
  const W = el.clientWidth, H = el.clientHeight
  const scale = Math.min(0.9, Math.min(W / (bbox.width + 60), H / (bbox.height + 60)))
  const tx = W/2 - scale * (bbox.x + bbox.width/2)
  const ty = H/2 - scale * (bbox.y + bbox.height/2)
  svgSel.transition().duration(600)
    .call(zoomBehavior.transform, d3.zoomIdentity.translate(tx, ty).scale(scale))
}

function resetZoom() { fitGraph() }

// ── Legend ────────────────────────────────────────────────────────────────────
const legendItems = computed(() => {
  if (colorMode.value === 'severity') return Object.entries(SEV_COLOR).map(([k, v]) => ({ label: k, color: v }))
  if (colorMode.value === 'language') return Object.entries(LANG_COLOR)
    .filter(([k]) => k !== 'unknown').map(([k, v]) => ({ label: k, color: v }))
  return [
    { label: 'Low debt',  color: '#22c55e' },
    { label: 'Med debt',  color: '#eab308' },
    { label: 'High debt', color: '#ef4444' },
  ]
})

watch(colorMode,  () => { if (viewMode.value === 'file') renderGraph() })
watch(searchQ,    () => { simulation?.stop(); viewMode.value === 'entity' ? renderEntityGraph() : renderGraph() })
watch(showDirs,   () => { if (hullUpdateFn) hullUpdateFn(); else renderGraph() })
watch(viewMode,   () => loadGraph())

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
    <!-- Header -->
    <div class="cg-header">
      <div class="cg-title">
        <AppIcon name="graph" :size="18" style="color:var(--gc-primary)" />
        <span>Code Graph</span>
        <span class="cg-badge" v-if="viewMode === 'file'">{{ stats.total_files ?? 0 }} files · {{ stats.total_edges ?? 0 }} edges</span>
        <span class="cg-badge" v-if="viewMode === 'entity'">{{ entityStats.total_entities ?? 0 }} entities · {{ entityStats.total_edges ?? 0 }} edges</span>
        <span v-if="truncated" class="cg-badge" style="background:#451407;color:#fdba74;">
          top {{ stats.total_files }} / {{ totalRaw }} shown
        </span>
      </div>

      <div class="cg-controls">
        <!-- View mode toggle -->
        <div class="cg-view-toggle">
          <button class="cg-vt-btn" :class="{ active: viewMode === 'file' }" @click="viewMode = 'file'">
            Files
          </button>
          <button class="cg-vt-btn" :class="{ active: viewMode === 'entity' }" @click="viewMode = 'entity'">
            Entities
          </button>
        </div>

        <div class="cg-search-wrap">
          <AppIcon name="search" :size="13" class="cg-search-icon" />
          <input v-model="searchQ" class="cg-search" :placeholder="viewMode === 'entity' ? 'Filter entities…' : 'Filter files…'" />
        </div>

        <template v-if="viewMode === 'file'">
          <label class="cg-toggle">
            <input type="checkbox" v-model="showDirs" />
            <span>Dir labels</span>
          </label>

          <div class="cg-control-item">
            <label class="cg-label">Color</label>
            <select v-model="colorMode" class="gc-select gc-select-sm" style="width:115px;">
              <option value="severity">Severity</option>
              <option value="language">Language</option>
              <option value="debt">Debt Score</option>
            </select>
          </div>
        </template>

        <button class="gc-btn gc-btn-ghost gc-btn-sm" @click="resetZoom">Fit</button>
        <button class="gc-btn gc-btn-primary gc-btn-sm" @click="loadGraph" :disabled="loading">
          {{ loading ? 'Loading…' : 'Refresh' }}
        </button>
      </div>
    </div>

    <!-- Stats ribbon — file view -->
    <div class="cg-stats" v-if="viewMode === 'file' && stats.total_files">
      <div class="cg-stat sev-crit">
        <span class="cg-stat-val">{{ stats.critical_files }}</span>
        <span class="cg-stat-lbl">critical</span>
      </div>
      <div class="cg-stat-sep">·</div>
      <div class="cg-stat" style="color:#f97316">
        <span class="cg-stat-val">{{ stats.major_files }}</span>
        <span class="cg-stat-lbl">major</span>
      </div>
      <div class="cg-stat-sep">·</div>
      <div class="cg-stat sev-ok">
        <span class="cg-stat-val">{{ stats.clean_files }}</span>
        <span class="cg-stat-lbl">clean</span>
      </div>
      <div class="cg-stat-sep">·</div>
      <div class="cg-stat">
        <span class="cg-stat-val">{{ stats.total_dirs }}</span>
        <span class="cg-stat-lbl">dirs</span>
      </div>
      <div class="cg-legend">
        <span v-for="item in legendItems.slice(0, 8)" :key="item.label" class="cg-leg-item">
          <span class="cg-leg-dot" :style="{ background: item.color }"></span>
          {{ item.label }}
        </span>
      </div>
    </div>

    <!-- Stats ribbon — entity view -->
    <div class="cg-stats" v-if="viewMode === 'entity' && entityStats.total_entities">
      <div class="cg-stat" style="color:#f59e0b">
        <span class="cg-stat-val">{{ entityStats.classes }}</span>
        <span class="cg-stat-lbl">classes</span>
      </div>
      <div class="cg-stat-sep">·</div>
      <div class="cg-stat" style="color:#3b82f6">
        <span class="cg-stat-val">{{ entityStats.functions }}</span>
        <span class="cg-stat-lbl">functions</span>
      </div>
      <div class="cg-stat-sep">·</div>
      <div class="cg-stat" style="color:#8b5cf6">
        <span class="cg-stat-val">{{ entityStats.methods }}</span>
        <span class="cg-stat-lbl">methods</span>
      </div>
      <div class="cg-stat-sep">·</div>
      <div class="cg-stat sev-crit">
        <span class="cg-stat-val">{{ entityStats.critical }}</span>
        <span class="cg-stat-lbl">critical entities</span>
      </div>
      <div class="cg-stat-sep">·</div>
      <div class="cg-stat">
        <span class="cg-stat-val">{{ entityStats.total_edges }}</span>
        <span class="cg-stat-lbl">edges</span>
      </div>
      <div class="cg-legend">
        <span class="cg-leg-item"><span class="cg-leg-dot" style="background:#f59e0b;border-radius:2px"></span>class</span>
        <span class="cg-leg-item"><span class="cg-leg-dot" style="background:#3b82f6"></span>function</span>
        <span class="cg-leg-item"><span class="cg-leg-dot" style="background:#8b5cf6;clip-path:polygon(50% 0,100% 50%,50% 100%,0 50%)"></span>method</span>
        <span class="cg-leg-item"><span style="display:inline-block;width:16px;height:2px;background:#6366f1;border-top:1px dashed #6366f1;vertical-align:middle"></span>calls</span>
        <span class="cg-leg-item"><span style="display:inline-block;width:16px;height:2px;background:#22c55e;vertical-align:middle"></span>contains</span>
      </div>
    </div>

    <!-- Canvas + panel -->
    <div class="cg-body">
      <div v-if="loading" class="cg-overlay">
        <div class="cg-spinner"></div>
        <div class="cg-overlay-text">Building graph…</div>
      </div>
      <div v-else-if="error" class="cg-overlay">
        <AppIcon name="warning" :size="32" style="color:var(--gc-warning)" />
        <div class="cg-overlay-text">{{ error }}</div>
        <button class="gc-btn gc-btn-primary gc-btn-sm" style="margin-top:12px;" @click="loadGraph">Retry</button>
      </div>

      <svg ref="svgEl" class="cg-svg" />

      <!-- Detail panel -->
      <transition name="panel-slide">
        <div v-if="selected" class="cg-panel">
          <div class="cg-panel-hdr">
            <div class="cg-panel-name" :title="selected.id">{{ selected.label }}</div>
            <button class="gc-icon-btn" style="width:26px;height:26px;font-size:14px;" @click="selected = null">✕</button>
          </div>
          <div class="cg-panel-path">{{ selected.id }}</div>

          <!-- File node metrics -->
          <div v-if="viewMode === 'file'" class="cg-panel-metrics">
            <div class="cg-metric">
              <div class="cg-metric-val" :class="`chip chip-${selected.severity}`">{{ selected.severity }}</div>
              <div class="cg-metric-lbl">Severity</div>
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
              <div class="cg-metric-val">{{ selected.loc ?? 0 }}</div>
              <div class="cg-metric-lbl">LOC</div>
            </div>
            <div class="cg-metric">
              <div class="cg-metric-val">{{ selected.debt_score }}</div>
              <div class="cg-metric-lbl">Debt</div>
            </div>
            <div class="cg-metric">
              <div class="cg-metric-val cg-lang-badge">{{ selected.language }}</div>
              <div class="cg-metric-lbl">Language</div>
            </div>
          </div>

          <!-- Entity node metrics -->
          <div v-if="viewMode === 'entity'" class="cg-panel-metrics">
            <div class="cg-metric">
              <div class="cg-metric-val" :class="`chip chip-${selected.severity}`">{{ selected.severity }}</div>
              <div class="cg-metric-lbl">Severity</div>
            </div>
            <div class="cg-metric">
              <div class="cg-metric-val" style="text-transform:capitalize">{{ selected.entity_type }}</div>
              <div class="cg-metric-lbl">Type</div>
            </div>
            <div class="cg-metric">
              <div class="cg-metric-val">{{ selected.issue_count }}</div>
              <div class="cg-metric-lbl">Issues</div>
            </div>
            <div class="cg-metric">
              <div class="cg-metric-val">{{ selected.loc ?? 0 }}</div>
              <div class="cg-metric-lbl">LOC</div>
            </div>
            <div class="cg-metric" v-if="selected.line_start">
              <div class="cg-metric-val">{{ selected.line_start }}–{{ selected.line_end }}</div>
              <div class="cg-metric-lbl">Lines</div>
            </div>
            <div class="cg-metric" v-if="selected.parent_name">
              <div class="cg-metric-val cg-lang-badge" style="font-size:10px">{{ selected.parent_name }}</div>
              <div class="cg-metric-lbl">Parent</div>
            </div>
          </div>

          <!-- Entity file path & issues -->
          <div v-if="viewMode === 'entity' && selected.file_path" class="cg-panel-path" style="margin-top:6px">
            {{ selected.file_path }}
          </div>
          <div v-if="viewMode === 'entity' && selected.issues?.length" class="cg-issues-list">
            <div class="cg-issues-ttl">Issues in this entity</div>
            <div v-for="(iss, i) in selected.issues" :key="i" class="cg-iss-row">
              <span :class="`chip chip-${iss.severity}`" style="font-size:10px;padding:1px 5px;flex-shrink:0;">{{ iss.severity }}</span>
              <div class="cg-iss-body">
                <div class="cg-iss-msg">{{ iss.message }}</div>
                <div class="cg-iss-meta">line {{ iss.line }} · {{ iss.rule_id }}</div>
              </div>
            </div>
          </div>

          <div v-if="selected.top_issues?.length" class="cg-issues-list">
            <div class="cg-issues-ttl">Top Issues</div>
            <div v-for="(iss, i) in selected.top_issues" :key="i" class="cg-iss-row">
              <span :class="`chip chip-${iss.severity}`" style="font-size:10px;padding:1px 5px;flex-shrink:0;">
                {{ iss.severity }}
              </span>
              <div class="cg-iss-body">
                <div class="cg-iss-msg">{{ iss.message }}</div>
                <div class="cg-iss-meta">
                  line {{ iss.line }} · {{ iss.rule_id }}
                  <span v-if="iss.cwe" style="opacity:.65"> · CWE-{{ iss.cwe }}</span>
                </div>
              </div>
            </div>
          </div>

          <router-link
            :to="`/issues?file=${encodeURIComponent(selected.id)}`"
            class="gc-btn gc-btn-primary gc-btn-sm"
            style="margin-top:14px;display:inline-flex;align-items:center;gap:6px;">
            <AppIcon name="bug" :size="13" /> View All Issues
          </router-link>
        </div>
      </transition>
    </div>
  </div>
</template>

<style scoped>
.cg-root {
  display: flex; flex-direction: column;
  height: calc(100vh - 64px - 48px); min-height: 500px;
  background: var(--gc-bg);
}

/* Header */
.cg-header {
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
  padding: 10px 16px; border-bottom: 1px solid var(--gc-border);
  background: var(--gc-surface); flex-shrink: 0;
}
.cg-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 14px; font-weight: 600; color: var(--gc-text);
}
.cg-badge {
  font-size: 10px; padding: 2px 7px; border-radius: 10px;
  background: var(--gc-primary-light); color: var(--gc-primary); font-weight: 500;
}
.cg-controls { display: flex; align-items: center; gap: 8px; margin-left: auto; flex-wrap: wrap; }
.cg-view-toggle {
  display: flex; border: 1px solid var(--gc-border); border-radius: 6px; overflow: hidden;
}
.cg-vt-btn {
  padding: 4px 12px; font-size: 11px; font-weight: 600; cursor: pointer;
  background: transparent; border: none; color: var(--gc-text-3); transition: all 0.15s;
}
.cg-vt-btn.active { background: var(--gc-primary-light); color: var(--gc-primary); }
.cg-vt-btn:not(.active):hover { color: var(--gc-text); background: var(--gc-surface-2); }
.cg-search-wrap { position: relative; }
.cg-search-icon { position: absolute; left: 9px; top: 50%; transform: translateY(-50%); color: var(--gc-text-3); }
.cg-search {
  padding: 6px 10px 6px 28px; border: 1px solid var(--gc-border);
  border-radius: 6px; background: var(--gc-surface-2); color: var(--gc-text);
  font-size: 12px; width: 150px;
}
.cg-search:focus { outline: none; border-color: var(--gc-primary); }
.cg-control-item { display: flex; align-items: center; gap: 6px; }
.cg-label { font-size: 11px; color: var(--gc-text-3); white-space: nowrap; }
.cg-toggle {
  display: flex; align-items: center; gap: 5px;
  font-size: 11px; color: var(--gc-text-2); cursor: pointer;
}
.cg-toggle input { accent-color: var(--gc-primary); }

/* Stats ribbon */
.cg-stats {
  display: flex; align-items: center; gap: 8px; padding: 6px 16px;
  background: var(--gc-surface-2); border-bottom: 1px solid var(--gc-border);
  font-size: 12px; flex-wrap: wrap; flex-shrink: 0;
}
.cg-stat { display: flex; align-items: center; gap: 4px; }
.cg-stat-val { font-weight: 600; color: var(--gc-text); }
.cg-stat-lbl { color: var(--gc-text-3); }
.cg-stat.sev-crit .cg-stat-val { color: #ef4444; }
.cg-stat.sev-ok   .cg-stat-val { color: #22c55e; }
.cg-stat-sep { color: var(--gc-divider); }
.cg-legend { display: flex; align-items: center; gap: 10px; margin-left: auto; flex-wrap: wrap; }
.cg-leg-item { display: flex; align-items: center; gap: 4px; font-size: 11px; color: var(--gc-text-2); }
.cg-leg-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

/* Body */
.cg-body { flex: 1; position: relative; overflow: hidden; display: flex; }
.cg-svg { flex: 1; width: 100%; height: 100%; cursor: grab; background: var(--gc-bg); }
.cg-svg:active { cursor: grabbing; }

/* Overlay */
.cg-overlay {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center; z-index: 20; background: var(--gc-bg);
}
.cg-overlay-text { margin-top: 12px; color: var(--gc-text-2); font-size: 13px; }
.cg-spinner {
  width: 36px; height: 36px; border: 3px solid var(--gc-border);
  border-top-color: var(--gc-primary); border-radius: 50%; animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Detail panel */
.cg-panel {
  width: 300px; flex-shrink: 0; border-left: 1px solid var(--gc-border);
  background: var(--gc-surface); padding: 16px; overflow-y: auto;
}
.cg-panel-hdr { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; }
.cg-panel-name { font-size: 14px; font-weight: 600; color: var(--gc-text); word-break: break-all; }
.cg-panel-path { font-size: 11px; color: var(--gc-text-3); margin-top: 4px; word-break: break-all; line-height: 1.4; }
.cg-panel-metrics { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6px; margin-top: 14px; }
.cg-metric { background: var(--gc-surface-2); border-radius: 8px; padding: 8px; text-align: center; }
.cg-metric-val { font-size: 14px; font-weight: 600; color: var(--gc-text); }
.cg-metric-lbl { font-size: 10px; color: var(--gc-text-3); margin-top: 2px; }
.cg-lang-badge { font-size: 11px; text-transform: lowercase; }

.cg-issues-list { margin-top: 14px; }
.cg-issues-ttl { font-size: 11px; font-weight: 600; color: var(--gc-text-3); text-transform: uppercase; letter-spacing: .5px; margin-bottom: 8px; }
.cg-iss-row { display: flex; gap: 7px; align-items: flex-start; padding: 6px 0; border-bottom: 1px solid var(--gc-divider); }
.cg-iss-body { flex: 1; min-width: 0; }
.cg-iss-msg { font-size: 12px; color: var(--gc-text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cg-iss-meta { font-size: 10px; color: var(--gc-text-3); margin-top: 2px; }

/* Transitions */
.panel-slide-enter-active, .panel-slide-leave-active { transition: transform .2s, opacity .2s; }
.panel-slide-enter-from, .panel-slide-leave-to { transform: translateX(30px); opacity: 0; }

/* Chips */
.chip { display: inline-block; padding: 2px 7px; border-radius: 4px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .3px; }
.chip-critical { background: #450a0a; color: #fca5a5; }
.chip-major    { background: #431407; color: #fdba74; }
.chip-minor    { background: #422006; color: #fde047; }
.chip-info     { background: #172554; color: #93c5fd; }
.chip-clean    { background: #052e16; color: #86efac; }
</style>
