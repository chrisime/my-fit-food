import { ref, onMounted, onUnmounted } from 'vue'

export function useWebSocket() {
  const connected = ref(false)
  let ws: WebSocket | null = null
  const handlers = new Map<string, (data: any) => void>()

  function connect() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    ws = new WebSocket(`${protocol}//${location.host}/api/ws`)

    ws.onopen = () => (connected.value = true)
    ws.onclose = () => {
      connected.value = false
      setTimeout(connect, 3000)
    }
    ws.onmessage = (msg) => {
      try {
        const { event, data } = JSON.parse(msg.data)
        const handler = handlers.get(event)
        if (handler) handler(data)
      } catch {
        /* ignore */
      }
    }
  }

  function on(event: string, cb: (data: any) => void) {
    handlers.set(event, cb)
  }

  function off(event: string) {
    handlers.delete(event)
  }

  onMounted(connect)
  onUnmounted(() => ws?.close())

  return { connected, on, off }
}
