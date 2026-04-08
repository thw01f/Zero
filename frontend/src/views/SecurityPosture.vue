<template>
  <div class="space-y-4">
    <div class="ft-card-title" style="font-size:11px;letter-spacing:0.12em">SECURITY POSTURE</div>

    <div v-if="!report.data" class="ft-card ft-card-body text-center py-12">
      <div class="text-sm mb-1" style="color:#8a96b0">No scan loaded</div>
      <div class="text-xs" style="color:#4a5568">Load a scan to see security posture</div>
    </div>

    <template v-else>
      <!-- Score gauge + OWASP -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="ft-card">
          <div class="ft-card-header"><span class="ft-card-title">Security Score</span></div>
          <div class="ft-card-body">
            <apexchart
              type="radialBar"
              height="220"
              :options="gaugeOpts"
              :series="[securityScore]"
            />
            <div class="text-center text-xs" style="color:#8a96b0">
              {{ report.criticalIssues.length }} critical &mdash;
              {{ secrets.length }} secrets &mdash;
              {{ securityIssues.length }} security findings
            </div>
          </div>
        </div>

        <div class="ft-card">
          <div class="ft-card-header"><span class="ft-card-title">CWE Distribution</span></div>
          <div class="ft-card-body">
            <apexchart
              v-if="cweSeries.length"
              type="bar"
              height="220"
              :options="cweOpts"
              :series="[{ name: 'Count', data: cweCounts }]"
            />
            <div v-else class="text-center py-8 text-xs" style="color:#4a5568">No CWE data</div>
          </div>
        </div>
      </div>

      <!-- OWASP Top 10 -->
      <div class="ft-card">
        <div class="ft-card-header"><span class="ft-card-title">OWASP Top 10 Coverage</span></div>
        <div style="overflow-x:auto">
          <table class="ft-table">
            <thead>
              <tr>
                <th>Category</th>
                <th>Findings</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in owaspRows" :key="row.cat">
                <td style="color:#dde3ef">{{ row.cat }}</td>
                <td>
                  <span :style="{ color: row.count > 0 ? '#f25555' : '#3ecf8e' }">{{ row.count }}</span>
                </td>
                <td>
                  <span class="status-dot" :class="row.count > 0 ? 'status-critical' : 'status-ok'"></span>
                  <span class="ml-2 text-xs" :style="{ color: row.count > 0 ? '#f25555' : '#3ecf8e' }">
                    {{ row.count > 0 ? 'Findings' : 'Clean' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Secrets -->
      <div class="ft-card">
        <div class="ft-card-header">
          <span class="ft-card-title">Secrets Found</span>
          <span class="ft-tag" :style="{ color: secrets.length ? '#f25555' : '#3ecf8e' }">{{ secrets.length }}</span>
        </div>
        <div v-if="!secrets.length" class="ft-card-body text-xs" style="color:#4a5568">No secrets detected</div>
        <div v-else style="overflow-x:auto">
          <table class="ft-table">
            <thead>
              <tr>
                <th>Severity</th>
                <th>File:Line</th>
                <th>Message</th>
                <th>Tool</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in secrets" :key="s.id">
                <td><span class="sev sev-critical">critical</span></td>
                <td class="font-mono text-xs" style="color:#8a96b0">{{ s.file_path }}:{{ s.line_start }}</td>
                <td style="max-width:300px" class="truncate">{{ s.message }}</td>
                <td style="font-size:11px;color:#4a5568">{{ s.tool }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
<script setup lang="ts">
// TODO: implement logic
</script>
