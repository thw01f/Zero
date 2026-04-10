<template>
  <div class="space-y-4">
    <div class="ft-card-title" style="font-size:11px;letter-spacing:0.12em">GIT INTELLIGENCE</div>

    <div v-if="!report.data" class="ft-card ft-card-body text-center py-12">
      <div class="text-sm mb-1" style="color:#8a96b0">No scan loaded</div>
      <div class="text-xs" style="color:#4a5568">Load a scan to see git intelligence</div>
    </div>

    <template v-else>
      <!-- Top churned files chart -->
      <div class="ft-card">
        <div class="ft-card-header"><span class="ft-card-title">Top 10 Churned Files</span></div>
        <div class="ft-card-body">
          <apexchart
            v-if="top10.length"
            type="bar"
            height="260"
            :options="churnOpts"
            :series="churnSeries"
          />
          <div v-else class="text-center py-8 text-xs" style="color:#4a5568">No churn data available</div>
        </div>
      </div>

      <!-- Module table -->
      <div class="ft-card">
        <div class="ft-card-header">
          <span class="ft-card-title">Module Analysis</span>
          <span class="ft-tag">{{ sortedModules.length }} modules</span>
        </div>
        <div style="overflow-x:auto">
          <table class="ft-table">
            <thead>
              <tr>
                <th class="sortable" @click="sortField = 'path'">Module Path</th>
                <th class="sortable" @click="sortField = 'loc'">LOC</th>
                <th class="sortable" @click="sortField = 'churn_count'">Churn</th>
                <th class="sortable" @click="sortField = 'debt_score'">Debt Score</th>
                <th>Grade</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in sortedModules" :key="m.id ?? m.path">
                <td class="font-mono text-xs" style="color:#8a96b0">{{ m.path }}</td>
                <td style="color:#dde3ef">{{ m.loc ?? '—' }}</td>
                <td :style="{ color: (m.churn_count ?? 0) > 20 ? '#f25555' : '#dde3ef' }">
                  {{ m.churn_count ?? '—' }}
                </td>
                <td>
                  <div class="flex items-center gap-2">
                    <div class="ft-progress" style="width:60px">
                      <div
                        class="ft-progress-bar"
                        :style="{
                          width: (m.debt_score ?? 0) + '%',
                          background: debtColor(m.debt_score),
                        }"
                      ></div>
                    </div>
                    <span style="color:#dde3ef">{{ m.debt_score ?? '—' }}</span>
                  </div>
                </td>
                <td>
                  <span class="font-bold text-sm" :class="'grade-' + (m.grade ?? 'F')">{{ m.grade ?? '—' }}</span>
                </td>
              </tr>
              <tr v-if="!sortedModules.length">
                <td colspan="5" class="text-center py-8" style="color:#4a5568">No module data</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
<script setup lang="ts">
// TODO: implement logic
</script>
