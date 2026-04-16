<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div class="ft-card-title" style="font-size:11px;letter-spacing:0.12em">ISSUE TRACKER</div>
      <div class="flex items-center gap-2">
        <span class="ft-tag">{{ filtered.length }} of {{ report.issues.length }}</span>
        <button class="ft-btn ft-btn-secondary" @click="exportCsv">Export CSV</button>
      </div>
    </div>

    <!-- No data -->
    <div v-if="!report.data" class="ft-card ft-card-body text-center py-12">
      <div class="text-sm mb-1" style="color:#8a96b0">No scan loaded</div>
      <div class="text-xs" style="color:#4a5568">Load a scan to see issues</div>
    </div>

    <template v-else>
      <!-- Filter bar -->
      <div class="ft-card ft-card-body">
        <div class="flex flex-wrap gap-2">
          <input
            v-model="search"
            placeholder="Search issues..."
            class="ft-input"
            style="width:200px"
            @input="page = 0"
          />
          <select v-model="filterSev" class="ft-input ft-select" style="width:130px" @change="page = 0">
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="major">Major</option>
            <option value="minor">Minor</option>
            <option value="info">Info</option>
          </select>
          <select v-model="filterCat" class="ft-input ft-select" style="width:140px" @change="page = 0">
            <option value="">All Categories</option>
            <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
          </select>
          <select v-model="sortBy" class="ft-input ft-select" style="width:140px">
            <option value="severity">Sort: Severity</option>
            <option value="file">Sort: File</option>
            <option value="tool">Sort: Tool</option>
          </select>
        </div>
      </div>

      <!-- Table -->
      <div class="ft-card" style="overflow:hidden">
        <div style="overflow-x:auto">
          <table class="ft-table">
            <thead>
              <tr>
                <th class="sortable" @click="sortBy = 'severity'">Severity</th>
                <th>Category</th>
                <th class="sortable" @click="sortBy = 'file'">File:Line</th>
                <th>Rule</th>
                <th>Message</th>
                <th>OWASP</th>
                <th>CWE</th>
                <th class="sortable" @click="sortBy = 'tool'">Tool</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <template v-for="issue in paginated" :key="issue.id">
                <tr @click="toggleExpand(issue.id)" class="cursor-pointer">
                  <td>
                    <span class="sev" :class="'sev-' + issue.severity">{{ issue.severity }}</span>
                  </td>
                  <td>
                    <span class="cat-badge" :class="'cat-' + issue.category">{{ issue.category }}</span>
                  </td>
                  <td class="font-mono text-xs" style="color:#8a96b0;white-space:nowrap">
                    {{ truncatePath(issue.file_path) }}:{{ issue.line_start }}
                  </td>
                  <td style="color:#4a9ff5;font-size:11px;white-space:nowrap">{{ issue.rule_id }}</td>
                  <td style="max-width:280px" class="truncate">{{ issue.message }}</td>
                  <td style="font-size:11px;color:#8a96b0;white-space:nowrap">{{ issue.owasp_category || '—' }}</td>
                  <td style="font-size:11px;color:#8a96b0">{{ issue.cwe_id || '—' }}</td>
                  <td style="font-size:11px;color:#4a5568">{{ issue.tool }}</td>
                  <td>
                    <span style="color:#4a5568;font-size:10px">{{ expanded.has(issue.id) ? '▲' : '▼' }}</span>
                  </td>
                </tr>
                <tr v-if="expanded.has(issue.id)" style="background:#0f1526">
                  <td colspan="9" class="px-3 py-3">
                    <div v-if="issue.llm_explanation" class="mb-2">
                      <div class="ft-card-title mb-1">AI Explanation</div>
                      <p class="text-sm leading-relaxed" style="color:#dde3ef">{{ issue.llm_explanation }}</p>
                    </div>
                    <div class="flex flex-wrap gap-3 text-xs" style="color:#8a96b0">
                      <span v-if="issue.owasp_category">OWASP: <span style="color:#dde3ef">{{ issue.owasp_category }}</span></span>
                      <span v-if="issue.cwe_id">CWE: <span style="color:#dde3ef">{{ issue.cwe_id }}</span></span>
                      <span v-if="issue.file_path">File: <span class="font-mono" style="color:#dde3ef">{{ issue.file_path }}</span></span>
                    </div>
                  </td>
                </tr>
              </template>
<script setup lang="ts">
// TODO: implement logic
</script>
