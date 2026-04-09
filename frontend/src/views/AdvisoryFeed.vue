<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div class="ft-card-title" style="font-size:11px;letter-spacing:0.12em">ADVISORY FEED</div>
      <div class="flex items-center gap-2">
        <span class="ft-tag">{{ advisories.length }} advisories</span>
        <span v-if="autoRefresh" class="status-dot status-running" title="Auto-refresh active"></span>
        <button class="ft-btn ft-btn-secondary" @click="load">Refresh</button>
      </div>
    </div>

    <!-- Filters -->
    <div class="ft-card ft-card-body">
      <div class="flex flex-wrap gap-3 items-center">
        <label class="flex items-center gap-2 text-xs cursor-pointer" style="color:#8a96b0">
          <input type="checkbox" v-model="unreadOnly" @change="load" class="rounded" style="accent-color:#f26d21" />
          Unread only
        </label>
        <label class="flex items-center gap-2 text-xs cursor-pointer" style="color:#8a96b0">
          <input type="checkbox" v-model="autoRefresh" class="rounded" style="accent-color:#f26d21" />
          Auto-refresh 30s
        </label>
        <button class="ft-btn ft-btn-ghost" @click="markAll">Mark all read</button>
      </div>
    </div>

    <div v-if="loading" class="ft-card ft-card-body text-center py-8">
      <div class="flex items-center justify-center gap-2">
        <span class="status-dot status-running"></span>
        <span class="text-xs" style="color:#8a96b0">Loading advisories...</span>
      </div>
    </div>

    <div v-else-if="!advisories.length" class="ft-card ft-card-body text-center py-12">
      <div class="text-sm mb-1" style="color:#8a96b0">No advisories found</div>
      <div class="text-xs" style="color:#4a5568">Advisory data is pulled from OSV, GitHub, and NVD</div>
    </div>

    <div v-else class="ft-card" style="overflow:hidden">
      <div style="overflow-x:auto">
        <table class="ft-table">
          <thead>
            <tr>
              <th>Source</th>
              <th>Advisory ID</th>
              <th>Package</th>
              <th>Severity</th>
              <th>CVSS</th>
              <th>Title</th>
              <th>Published</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="adv in advisories"
              :key="adv.id ?? adv.advisory_id"
              :style="{ opacity: adv.is_read ? 0.6 : 1 }"
            >
              <td>
                <span class="ft-tag" style="text-transform:uppercase">{{ adv.source }}</span>
              </td>
              <td>
                <a
                  v-if="adv.advisory_url"
                  :href="adv.advisory_url"
                  target="_blank"
                  class="font-mono text-xs"
                  style="color:#4a9ff5;text-decoration:none"
                >{{ adv.advisory_id }}</a>
                <span v-else class="font-mono text-xs" style="color:#8a96b0">{{ adv.advisory_id }}</span>
              </td>
              <td style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#dde3ef">
                {{ adv.package_name || '—' }}
              </td>
              <td>
                <span class="sev" :class="'sev-' + adv.severity">{{ adv.severity }}</span>
              </td>
              <td style="color:#8a96b0;font-size:11px">{{ adv.cvss_score ?? '—' }}</td>
              <td style="max-width:280px" class="truncate">{{ adv.title }}</td>
              <td style="font-size:11px;color:#4a5568;white-space:nowrap">{{ formatDate(adv.published_at) }}</td>
              <td>
                <button
                  v-if="!adv.is_read"
                  class="ft-btn ft-btn-ghost"
                  style="font-size:10px;padding:2px 6px"
                  @click="mark(adv.id)"
                >Read</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
// TODO: implement logic
</script>
