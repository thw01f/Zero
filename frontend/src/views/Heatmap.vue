<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div class="ft-card-title" style="font-size:11px;letter-spacing:0.12em">FILE HEATMAP</div>
      <div class="flex gap-2">
        <button
          v-for="m in ['debt', 'severity', 'churn']"
          :key="m"
          class="ft-btn capitalize"
          :class="colorMode === m ? 'ft-btn-primary' : 'ft-btn-secondary'"
          @click="colorMode = m"
        >{{ m }}</button>
      </div>
    </div>

    <div v-if="!report.data" class="ft-card ft-card-body text-center py-12">
      <div class="text-sm mb-1" style="color:#8a96b0">No scan loaded</div>
      <div class="text-xs" style="color:#4a5568">Load a scan to see the file heatmap</div>
    </div>

    <template v-else>
      <div class="ft-card" style="overflow:hidden;height:500px">
        <div ref="container" style="width:100%;height:100%"></div>
      </div>

      <!-- Selected module panel -->
      <div v-if="selected" class="ft-card">
        <div class="ft-card-header">
          <span class="ft-card-title font-mono">{{ selected.path }}</span>
          <span class="font-bold text-lg" :class="'grade-' + (selected.grade ?? 'F')">{{ selected.grade ?? '—' }}</span>
        </div>
        <div class="ft-card-body">
          <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div>
              <div class="metric-label">Debt Score</div>
              <div class="metric-value text-lg" :style="{ color: debtColor(selected.debt_score) }">{{ selected.debt_score ?? '—' }}</div>
            </div>
            <div>
              <div class="metric-label">LOC</div>
              <div class="metric-value text-lg">{{ selected.loc ?? '—' }}</div>
            </div>
            <div>
              <div class="metric-label">Critical</div>
              <div class="metric-value text-lg" style="color:#f25555">{{ selected.issue_count_critical ?? 0 }}</div>
            </div>
            <div>
              <div class="metric-label">Major</div>
              <div class="metric-value text-lg" style="color:#f26d21">{{ selected.issue_count_major ?? 0 }}</div>
            </div>
            <div>
              <div class="metric-label">Churn</div>
              <div class="metric-value text-lg">{{ selected.churn_count ?? '—' }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Legend -->
      <div class="ft-card ft-card-body">
        <div class="flex items-center gap-3">
          <span class="text-xs" style="color:#8a96b0">Low</span>
          <div style="height:8px;width:160px;border-radius:4px;background:linear-gradient(to right,#3ecf8e,#f5a623,#f25555)"></div>
          <span class="text-xs" style="color:#8a96b0">High</span>
          <span class="ft-tag ml-4">Size = LOC</span>
        </div>
      </div>
    </template>
<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { useReportStore } from '../stores/report'

const report = useReportStore()
const container = ref<HTMLElement | null>(null)
const selected = ref<any>(null)
const colorMode = ref('debt')

function debtColor(score: number) {
  if (score >= 70) return '#f25555'
  if (score >= 40) return '#f5a623'
  return '#3ecf8e'
}

const colorScale = d3.scaleSequential(
  d3.interpolateRgbBasis(['#3ecf8e', '#f5a623', '#f25555'])
).domain([0, 100])

function getVal(m: any): number {
  if (colorMode.value === 'debt') return m.debt_score ?? 0
  if (colorMode.value === 'churn') return Math.min(100, (m.churn_count ?? 0) * 5)
  return Math.min(100, (m.issue_count_critical ?? 0) * 10 + (m.issue_count_major ?? 0) * 5 + (m.issue_count_minor ?? 0))
}

function draw() {
  if (!container.value || !report.modules.length) return
  d3.select(container.value).selectAll('*').remove()
  const rect = container.value.getBoundingClientRect()
  const width = rect.width || 800
  const height = rect.height || 500

  const data = {
    name: 'root',
    children: report.modules.map((m: any) => ({ ...m, value: Math.max(m.loc ?? 1, 1) })),
  }

  const hierarchy = d3.hierarchy(data).sum((d: any) => d.value).sort((a, b) => (b.value || 0) - (a.value || 0))
  const root = d3.treemap<any>().size([width, height]).padding(2)(hierarchy)

  const svg = d3.select(container.value)
    .append('svg')
    .attr('width', width)
    .attr('height', height)

  const cell = svg.selectAll('g')
    .data(root.leaves())
    .enter()
    .append('g')
    .attr('transform', (d: any) => `translate(${d.x0},${d.y0})`)
    .style('cursor', 'pointer')
    .on('click', (_: any, d: any) => { selected.value = d.data })

  cell.append('rect')
    .attr('width', (d: any) => Math.max(0, d.x1 - d.x0))
    .attr('height', (d: any) => Math.max(0, d.y1 - d.y0))
    .attr('fill', (d: any) => colorScale(getVal(d.data)))
    .attr('stroke', '#0a0e1a')
    .attr('stroke-width', 1)
    .attr('rx', 2)
    .attr('opacity', 0.85)

  cell.append('text')
    .attr('x', 4)
    .attr('y', 14)
    .style('font-size', '10px')
    .style('font-family', 'Inter, sans-serif')
    .style('fill', 'rgba(0,0,0,0.8)')
    .style('font-weight', '600')
    .style('pointer-events', 'none')
    .text((d: any) => {
      const w = d.x1 - d.x0
      const name = (d.data.path || '').split('/').pop() || ''
      return w > 50 ? name.slice(0, Math.floor(w / 7)) : ''
    })
}

watch(() => report.modules, () => nextTick(draw), { deep: true })
watch(colorMode, () => nextTick(draw))
onMounted(() => nextTick(draw))
</script>