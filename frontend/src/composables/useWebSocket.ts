import { ref, onUnmounted } from 'vue'

export function useWebSocket() {
  let ws: WebSocket | null = null
  const connected = ref(false)

  function connect(jobId: string, onMessage: (msg: any) => void) {
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const host = window.location.host
    ws = new WebSocket(`${proto}://${host}/api/ws/${jobId}`)
    ws.onopen = () => { connected.value = true }
    ws.onmessage = (e) => {
      try { onMessage(JSON.parse(e.data)) } catch {}
    }
    ws.onclose = () => { connected.value = false }
    ws.onerror = () => { connected.value = false }
  }

  function disconnect() {
    ws?.close()
    ws = null
    connected.value = false
  }

  onUnmounted(disconnect)
  return { connect, disconnect, connected }
}
