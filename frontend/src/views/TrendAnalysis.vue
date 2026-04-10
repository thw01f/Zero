<template>
  <div class="space-y-4">
    <div class="ft-card-title" style="font-size:11px;letter-spacing:0.12em">TREND ANALYSIS</div>

    <div v-if="!report.data" class="ft-card ft-card-body text-center py-12">
      <div class="text-sm mb-1" style="color:#8a96b0">No scan loaded</div>
      <div class="text-xs" style="color:#4a5568">Load a scan to see trend data</div>
    </div>

    <template v-else>
      <!-- Info banner -->
      <div class="ft-card ft-card-body" style="border-left:2px solid #4a9ff5">
        <div class="text-xs" style="color:#8a96b0">
          Trend tracking requires multiple scans of the same project. Showing current scan snapshot below.
          Register a project with auto-rescan to track changes over time.
        </div>
      </div>

      <!-- Current snapshot bar chart -->
      <div class="ft-card">
        <div class="ft-card-header"><span class="ft-card-title">Issue Severity Distribution — Current Scan</span></div>
        <div class="ft-card-body">
          <apexchart
            type="bar"
            height="240"
            :options="sevOpts"
            :series="sevSeries"
          />
        </div>
      </div>

      <!-- Category breakdown -->
      <div class="ft-card">
        <div class="ft-card-header"><span class="ft-card-title">Issues by Category</span></div>
        <div class="ft-card-body">
          <apexchart
            v-if="catSeries.length"
            type="bar"
            height="200"
            :options="catOpts"
            :series="[{ name: 'Issues', data: catCounts }]"
          />
          <div v-else class="text-center py-8 text-xs" style="color:#4a5568">No category data</div>
        </div>
      </div>

      <!-- Debt message -->
      <div class="ft-card">
        <div class="ft-card-header"><span class="ft-card-title">Debt Score Summary</span></div>
        <div class="ft-card-body">
          <div class="flex items-center gap-4">
            <div class="text-5xl font-bold" :class="'grade-' + (report.data.overall_grade ?? 'F')">
              {{ report.data.overall_grade ?? '?' }}
            </div>
            <div>
              <div class="text-2xl font-bold" style="color:#dde3ef">{{ report.data.overall_debt_score ?? '—' }}</div>
              <div class="text-xs" style="color:#8a96b0">Debt Score / 100</div>
              <div class="text-xs mt-1" style="color:#4a5568">
                {{ debtMessage }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
<script setup lang="ts">
// TODO: implement logic
</script>
