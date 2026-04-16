<template>
  <div class="space-y-2">
    <form @submit.prevent="submit">
      <input
        v-model="repoUrl"
        type="text"
        placeholder="https://github.com/owner/repo"
        class="ft-input mb-2"
      />
      <div class="flex gap-1.5">
        <select v-model="language" class="ft-input ft-select flex-1">
          <option value="auto">Auto</option>
          <option value="python">Python</option>
          <option value="javascript">JavaScript</option>
          <option value="typescript">TypeScript</option>
          <option value="java">Java</option>
          <option value="go">Go</option>
          <option value="ruby">Ruby</option>
        </select>
        <button
          type="submit"
          :disabled="loading || !repoUrl"
          class="ft-btn ft-btn-primary"
        >{{ loading ? '...' : 'Scan' }}</button>
      </div>
    </form>

    <div v-if="error" class="text-xs" style="color:#f25555">{{ error }}</div>

    <div v-if="scan.status !== 'idle'" class="space-y-1 pt-1">
      <div class="flex items-center gap-2">
        <span
          class="status-dot"
          :class="{
            'status-running': scan.status === 'running' || scan.status === 'queued',
            'status-ok': scan.status === 'complete',
            'status-critical': scan.status === 'failed',
          }"
        ></span>
        <span class="text-xs" style="color:#8a96b0">
          {{ statusLabel }}
        </span>
      </div>
      <div v-if="scan.status === 'running' || scan.status === 'queued'" class="ft-progress">
        <div class="ft-progress-bar" :style="{ width: scan.progress + '%' }"></div>
      </div>
      <div v-if="scan.currentStage" class="text-xs" style="color:#4a5568">{{ scan.currentStage }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useScanStore } from '../stores/scan'
import { useReportStore } from '../stores/report'
import { useWebSocket } from '../composables/useWebSocket'

const scan = useScanStore()
const report = useReportStore()
const { connect } = useWebSocket()

const repoUrl = ref('')
const language = ref('auto')
const loading = ref(false)
const error = ref('')

const statusLabel = computed(() => {
  const map: Record<string, string> = {
    idle: 'Idle',
    queued: 'Queued',
    running: `Running — ${scan.progress}%`,
    complete: 'Complete',
    failed: 'Failed',
  }
  return map[scan.status] ?? scan.status
})

async function submit() {
  if (!repoUrl.value) return
  loading.value = true
  error.value = ''
  try {
    await scan.submitScan(repoUrl.value, language.value)
    connect(scan.jobId!, (msg) => {
      scan.handleWsMessage(msg)
      if (msg.event === 'complete' && scan.jobId) {
        setTimeout(() => report.fetchReport(scan.jobId!), 500)
      }
    })
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    loading.value = false
  }
}
</script>
