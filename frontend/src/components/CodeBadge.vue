<template>
  <code :class="['code-badge', variant]">{{ text }}</code>
</template>
<script setup lang="ts">
defineProps<{ text: string; variant?: 'default'|'rule'|'cwe'|'owasp' }>()
</script>
<style scoped>
.code-badge { padding:1px 6px; border-radius:3px; font-family:'JetBrains Mono',monospace; font-size:12px; }
.default { background:#1e2d45; color:#d4dde8; border:1px solid #2a3f60; }
.rule    { background:#1a2540; color:#4a9ff5; border:1px solid #2a3f60; }
.cwe     { background:#1f2a1f; color:#3ecf8e; border:1px solid #2a4a2a; }
.owasp   { background:#2a1f1f; color:#f26d21; border:1px solid #4a2a1f; }
</style>
