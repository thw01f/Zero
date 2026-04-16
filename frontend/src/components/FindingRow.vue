
<template>
  <tr class="finding-row" @click="expanded = !expanded" :class="{expanded}">
    <td class="line-col">{{ finding.line ?? '—' }}</td>
    <td><SeverityPill :sev="finding.severity" /></td>
    <td class="rule-col"><code>{{ finding.rule }}</code></td>
    <td class="msg-col">{{ finding.message }}</td>
    <td><span class="tool-badge">{{ finding.tool ?? 'llm' }}</span></td>
    <td><CweTag :cwe="finding.cwe" /></td>
    <td class="chevron-col">{{ expanded ? '▲' : '▼' }}</td>
  </tr>
  <tr v-if="expanded && finding.explanation" class="explanation-row">
    <td colspan="7" class="explanation-cell">
      <p>{{ finding.explanation }}</p>
      <code v-if="finding.owasp" class="owasp-tag">{{ finding.owasp }}</code>
    </td>
  </tr>
</template>
<script setup lang="ts">
import { ref } from 'vue'
import SeverityPill from './SeverityPill.vue'
import CweTag from './CweTag.vue'
const props = defineProps<{ finding: Record<string,any> }>()
const expanded = ref(false)
</script>
