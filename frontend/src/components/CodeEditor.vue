
<template>
  <div class="code-editor-wrap">
    <div class="editor-header">
      <span class="editor-lang">{{ lang }}</span>
      <button class="copy-btn" @click="doCopy">{{ copied ? '✓ Copied' : 'Copy' }}</button>
    </div>
    <textarea
      v-model="localVal"
      :placeholder="placeholder"
      class="ft-textarea code-input"
      :rows="rows"
      spellcheck="false"
      autocorrect="off"
      autocapitalize="off"
      @keydown.tab.prevent="insertTab"
    />
  </div>
</template>
<script setup lang="ts">
import { ref, watch } from 'vue'
import { useClipboard } from '../composables/useClipboard'

const props = defineProps<{
  modelValue: string
  lang?: string
  placeholder?: string
  rows?: number
}>()

const emit = defineEmits<{ 'update:modelValue': [string] }>()
const localVal = ref(props.modelValue)
const { copy, copied } = useClipboard()

watch(() => props.modelValue, v => { localVal.value = v })
watch(localVal, v => emit('update:modelValue', v))

function doCopy() { copy(localVal.value) }
function insertTab(e: KeyboardEvent) {
  const el = e.target as HTMLTextAreaElement
  const start = el.selectionStart
  localVal.value = localVal.value.slice(0, start) + '  ' + localVal.value.slice(el.selectionEnd)
}
</script>
