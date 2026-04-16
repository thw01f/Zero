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
// TODO: implement logic
</script>
