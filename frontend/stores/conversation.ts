import { defineStore } from 'pinia'

const MAX_MESSAGE_LENGTH = 2000

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ProjectSummary {
  name: string
  description?: string
  game_type: string
  complexity: string
  core_mechanics?: string[]
  suggested_agents?: string[]
}

export const useConversationStore = defineStore('conversation', () => {
  const messages = ref<ChatMessage[]>([])
  const projectSummary = ref<ProjectSummary | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const sessionId = ref<string | null>(null)

  const { post } = useApi()

  function validateMessage(content: string): string {
    const trimmed = content.trim()
    if (!trimmed) {
      throw new Error('消息不能为空')
    }
    if (trimmed.length > MAX_MESSAGE_LENGTH) {
      throw new Error(`消息不能超过 ${MAX_MESSAGE_LENGTH} 个字符`)
    }
    return trimmed
  }

  async function send(content: string) {
    const validated = validateMessage(content)
    messages.value.push({ role: 'user', content: validated })
    loading.value = true
    error.value = null

    try {
      // 调用 MasterChatAgent (LLM) API
      const res = await post<{
        session_id: string
        response: string
        state: string
        project_summary: ProjectSummary | null
      }>('/agents/chat', {
        message: validated,
        session_id: sessionId.value,
      })

      // 保存 session_id
      if (res.session_id) {
        sessionId.value = res.session_id
      }

      // 添加回复
      messages.value.push({ role: 'assistant', content: res.response })

      // 如果确认了项目概要
      if (res.project_summary) {
        projectSummary.value = res.project_summary
      }
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : '请求失败'
      error.value = message
      messages.value.push({
        role: 'assistant',
        content: `错误：${message}`,
      })
    } finally {
      loading.value = false
    }
  }

  function clear() {
    messages.value = []
    projectSummary.value = null
    error.value = null
    sessionId.value = null
  }

  return {
    messages,
    projectSummary,
    loading,
    error,
    sessionId,
    send,
    clear,
  }
})
