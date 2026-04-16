<template>
  <div class="flex flex-col space-y-4" style="height:calc(100vh - 80px)">
    <div class="ft-card-title" style="font-size:11px;letter-spacing:0.12em">AI ASSISTANT</div>

    <div v-if="!scan.jobId" class="ft-card ft-card-body text-center py-12 flex-1">
      <div class="mb-3" style="color:#4a5568">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" class="mx-auto">
          <path d="M12 2a10 10 0 110 20A10 10 0 0112 2zM8 12h8M12 8v8"/>
        </svg>
      </div>
      <div class="text-sm mb-1" style="color:#8a96b0">No scan loaded</div>
      <div class="text-xs" style="color:#4a5568">Run a scan first to enable AI chat</div>
    </div>

    <template v-else>
      <!-- Messages area -->
      <div
        ref="messagesEl"
        class="ft-card ft-card-body flex-1 overflow-y-auto space-y-3"
        style="min-height:0"
      >
        <!-- Empty state with suggestions -->
        <div v-if="!messages.length" class="space-y-3">
          <div class="text-center py-4">
            <div class="text-sm mb-4" style="color:#8a96b0">Ask anything about your scan results</div>
            <div class="flex flex-wrap gap-2 justify-center">
              <button
                v-for="q in suggestions"
                :key="q"
                class="ft-btn ft-btn-secondary"
                style="font-size:11px"
                @click="sendQuestion(q)"
              >{{ q }}</button>
            </div>
          </div>
        </div>

        <!-- Chat messages -->
        <div
          v-for="(msg, i) in messages"
          :key="i"
          class="flex"
          :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
        >
          <div
            class="max-w-xl rounded px-4 py-3 text-sm"
            :style="msgStyle(msg.role)"
          >
            <pre class="whitespace-pre-wrap font-sans text-sm leading-relaxed">{{ msg.content }}</pre>
          </div>
        </div>

        <!-- Loading indicator -->
        <div v-if="loading" class="flex justify-start">
          <div class="rounded px-4 py-3" style="background:#141d30;border:1px solid #1e2d47">
            <div class="flex items-center gap-2">
              <span class="status-dot status-running"></span>
              <span class="text-xs" style="color:#8a96b0">Thinking...</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Suggestions when chat has messages -->
      <div v-if="messages.length && !loading" class="flex flex-wrap gap-2">
        <button
          v-for="q in suggestions"
          :key="q"
          class="ft-btn ft-btn-ghost"
          style="font-size:11px"
          @click="sendQuestion(q)"
        >{{ q }}</button>
      </div>

      <!-- Input -->
      <div class="flex gap-2">
        <input
          v-model="input"
          @keyup.enter="send"
          placeholder="Ask about your codebase security, issues, or recommendations..."
          class="ft-input flex-1"
        />
        <button
          class="ft-btn ft-btn-primary"
          :disabled="loading || !input.trim()"
          @click="send"
        >Send</button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import axios from 'axios'
import { useScanStore } from '../stores/scan'

const scan = useScanStore()
const messages = ref<{ role: string; content: string }[]>([])
const input = ref('')
const loading = ref(false)
const messagesEl = ref<HTMLElement | null>(null)

const suggestions = [
  'What are the top 3 critical fixes?',
  'Is this project safe to deploy?',
  'Summarize all injection risks',
  'Which files need immediate attention?',
]

function msgStyle(role: string) {
  if (role === 'user') {
    return {
      background: '#f26d21',
      color: '#fff',
      borderRadius: '12px 12px 2px 12px',
    }
  }
  return {
    background: '#141d30',
    border: '1px solid #1e2d47',
    color: '#dde3ef',
    borderRadius: '2px 12px 12px 12px',
  }
}

async function scrollToBottom() {
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}

async function send() {
  if (!input.value.trim() || !scan.jobId) return
  await sendQuestion(input.value.trim())
  input.value = ''
}

async function sendQuestion(q: string) {
  if (!scan.jobId) return
  messages.value.push({ role: 'user', content: q })
  input.value = ''
  loading.value = true
  await scrollToBottom()
  try {
    const { data } = await axios.post(`/api/chat/${scan.jobId}`, { message: q })
    messages.value.push({ role: 'assistant', content: data.response })
  } catch (e: any) {
    messages.value.push({ role: 'assistant', content: 'Error: ' + (e.response?.data?.detail || e.message || 'unknown') })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}
</script>
