<template>
  <div class="flex flex-col h-full">
    <!-- 头部 -->
    <div class="h-14 flex items-center justify-between px-4 border-b" :class="isDark ? 'border-bg-secondary bg-bg-secondary' : 'border-border bg-bg-primary'">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-full flex items-center justify-center bg-brand-base">
          <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
        </div>
        <div>
          <div class="text-sm font-medium" :class="isDark ? 'text-text-primary' : 'text-text-primary'">{{ currentAgentName }}</div>
          <div class="text-xs" :class="isDark ? 'text-text-secondary' : 'text-text-secondary'">{{ agentStatus }}</div>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <span v-if="streaming" class="flex items-center gap-1 text-xs" :class="isDark ? 'text-brand-base' : 'text-brand-base'">
          <span class="animate-pulse">●</span> 思考中
        </span>
      </div>
    </div>

    <!-- 消息列表 -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-4">
      <!-- 欢迎消息 -->
      <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full" :class="isDark ? 'text-text-secondary' : 'text-text-secondary'">
        <div class="w-16 h-16 rounded-full bg-brand-bg flex items-center justify-center mb-4">
          <svg class="w-8 h-8 text-brand-base" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </div>
        <p class="text-sm">开始与 {{ currentAgentName }} 对话</p>
      </div>

      <!-- 消息 -->
      <div
        v-for="(msg, idx) in messages"
        :key="idx"
        class="flex gap-3"
        :class="msg.role === 'user' ? 'flex-row-reverse' : ''"
      >
        <!-- 头像 -->
        <div class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm shadow-sm"
          :class="msg.role === 'user' ? 'bg-brand-base text-white' : 'bg-bg-tertiary'"
        >
          <svg v-if="msg.role === 'user'" class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          <svg v-else class="w-4 h-4 text-brand-base" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        </div>

        <!-- 消息内容 -->
        <div class="flex-1 max-w-[80%]" :class="msg.role === 'user' ? 'text-right' : ''">
          <div
            class="inline-block px-4 py-2 rounded-xl text-sm whitespace-pre-wrap leading-relaxed"
            :class="msg.role === 'user'
              ? 'bg-brand-base text-white rounded-tr-md'
              : (isDark ? 'bg-bg-secondary text-text-primary rounded-tl-md' : 'bg-bg-primary text-text-primary rounded-tl-md')"
          >
            {{ msg.content }}
            <span v-if="msg.streaming" class="typing-cursor"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入框 -->
    <div class="p-4 border-t" :class="isDark ? 'border-bg-secondary' : 'border-border'">
      <div class="flex gap-3">
        <input
          v-model="inputMessage"
          type="text"
          placeholder="输入消息..."
          class="flex-1 rounded-xl px-4 py-3 text-sm transition-all duration-200 focus:outline-none focus:ring-2"
          :class="isDark
            ? 'bg-bg-secondary border border-border text-text-primary placeholder-text-secondary focus:border-brand-base focus:ring-brand-bg'
            : 'bg-bg-primary border border-border text-text-primary placeholder-text-secondary focus:border-brand-base focus:ring-brand-bg'"
          @keyup.enter="sendMessage()"
        />
        <button
          @click="sendMessage()"
          :disabled="!inputMessage.trim() || sending"
          class="px-5 py-3 rounded-xl text-sm font-medium transition-all duration-200 flex items-center gap-2 text-white shadow-sm"
          :class="(inputMessage.trim() && !sending)
            ? 'bg-brand-base hover:bg-brand-hover active:scale-95'
            : (isDark ? 'bg-bg-secondary text-text-secondary cursor-not-allowed' : 'bg-bg-tertiary text-text-secondary cursor-not-allowed')"
        >
          <span>发送</span>
          <span v-if="sending" class="animate-spin">↻</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useTheme } from '~/composables/useTheme'

interface Message {
  role: 'user' | 'assistant'
  content: string
  streaming?: boolean
}

const props = defineProps<{
  agentId: string
  agentName: string
}>()

const messagesContainer = ref<HTMLElement>()
const messages = ref<Message[]>([])
const inputMessage = ref('')
const sending = ref(false)
const streaming = ref(false)
const { isDark } = useTheme()

const currentAgentName = computed(() => props.agentName || 'Master')
const currentAgentIcon = computed(() => {
  // Simple initials instead of emoji
  const initials: Record<string, string> = {
    'Master': 'M', 'Planner': 'P', 'Architect': 'A',
    'Programmer': 'C', 'QA': 'T'
  }
  return initials[currentAgentName.value] || 'A'
})

const agentStatus = computed(() => '在线')

async function sendMessage() {
  if (!inputMessage.value.trim() || sending.value) return

  const text = inputMessage.value.trim()
  inputMessage.value = ''

  // 添加用户消息
  messages.value.push({ role: 'user', content: text })
  scrollToBottom()

  sending.value = true
  streaming.value = true

  try {
    // 调用 API
    const response = await $fetch('/api/agents/chat', {
      method: 'POST',
      body: { message: text, mode: 'continue' }
    }) as any

    // 添加助手消息（流式效果模拟）
    messages.value.push({ role: 'assistant', content: '', streaming: true })

    // 模拟打字机效果
    const content = response.response || ''
    for (let i = 0; i < content.length; i++) {
      await new Promise(r => setTimeout(r, 20))
      messages.value[messages.value.length - 1].content += content[i]
      scrollToBottom()
    }

    messages.value[messages.value.length - 1].streaming = false
  } catch (e) {
    messages.value.push({ role: 'assistant', content: '抱歉，发生了错误。' })
  }

  sending.value = false
  streaming.value = false
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}
</script>
