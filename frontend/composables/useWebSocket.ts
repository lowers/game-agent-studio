import type { WorkbenchMessage } from '~/types'

export type WebSocketStatus = 'connecting' | 'open' | 'closed' | 'error'

export interface WebSocketMessage {
  type: string
  data?: Record<string, unknown>
}

/**
 * WebSocket Composable
 * 支持项目模式 (projectId) 和聊天模式 (sessionId)
 */
export function useWebSocket(options: { projectId?: number; sessionId?: string }) {
  const config = useRuntimeConfig()
  const wsBase = config.public.wsBase as string

  const messages = ref<WebSocketMessage[]>([])
  const status = ref<WebSocketStatus>('connecting')
  const lastMessage = ref<WebSocketMessage | null>(null)

  let socket: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let isUnmounted = false
  let messageHandlers: Map<string, ((data: any) => void)[]> = new Map()

  // 计算 WebSocket URL
  const wsUrl = computed(() => {
    if (options.projectId) {
      return `${wsBase}/${options.projectId}`
    } else if (options.sessionId) {
      return `${wsBase}/chat/${options.sessionId}`
    }
    return `${wsBase}/chat`
  })

  function connect() {
    if (isUnmounted) return
    if (socket?.readyState === WebSocket.OPEN) return

    status.value = 'connecting'

    try {
      socket = new WebSocket(wsUrl.value)
    } catch (e) {
      console.error('WebSocket connection error:', e)
      status.value = 'error'
      return
    }

    socket.onopen = () => {
      if (isUnmounted) {
        socket?.close()
        return
      }
      status.value = 'open'

      // 发送订阅消息
      if (options.projectId) {
        socket?.send(JSON.stringify({ type: 'subscribe', data: { project_id: options.projectId } }))
      } else if (options.sessionId) {
        socket?.send(JSON.stringify({ type: 'subscribe', data: { session_id: options.sessionId } }))
      }
    }

    socket.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data) as WebSocketMessage
        messages.value.push(data)
        lastMessage.value = data

        // 触发对应的处理器
        const handlers = messageHandlers.get(data.type)
        if (handlers) {
          handlers.forEach(handler => handler(data.data))
        }
      } catch (e) {
        console.warn('Failed to parse WebSocket message:', e)
      }
    }

    socket.onclose = () => {
      if (isUnmounted) return
      status.value = 'closed'
      scheduleReconnect()
    }

    socket.onerror = () => {
      if (isUnmounted) return
      status.value = 'error'
      socket?.close()
    }
  }

  function scheduleReconnect() {
    if (isUnmounted) return
    if (reconnectTimer) clearTimeout(reconnectTimer)
    reconnectTimer = setTimeout(connect, 3000)
  }

  function send(data: unknown) {
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(data))
      return true
    }
    return false
  }

  function onMessage(type: string, handler: (data: any) => void) {
    if (!messageHandlers.has(type)) {
      messageHandlers.set(type, [])
    }
    messageHandlers.get(type)!.push(handler)
  }

  function offMessage(type: string, handler?: (data: any) => void) {
    if (!handler) {
      messageHandlers.delete(type)
    } else {
      const handlers = messageHandlers.get(type)
      if (handlers) {
        const idx = handlers.indexOf(handler)
        if (idx >= 0) handlers.splice(idx, 1)
      }
    }
  }

  function disconnect() {
    isUnmounted = true
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (socket) {
      socket.onclose = null
      socket.close()
      socket = null
    }
    status.value = 'closed'
    messageHandlers.clear()
  }

  onMounted(connect)
  onUnmounted(disconnect)

  return {
    messages,
    lastMessage,
    status,
    send,
    disconnect,
    onMessage,
    offMessage,
    reconnect: connect,
  }
}

/**
 * 专门用于聊天的 WebSocket
 */
export function useChatWebSocket(sessionId: string) {
  return useWebSocket({ sessionId })
}

/**
 * 专门用于项目的 WebSocket
 */
export function useProjectWebSocket(projectId: number) {
  return useWebSocket({ projectId })
}
