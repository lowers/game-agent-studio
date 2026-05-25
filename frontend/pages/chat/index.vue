<template>
  <div class="flex-1 flex flex-col min-h-0 transition-colors duration-300" :class="isDark ? 'bg-bg-primary' : 'bg-bg-primary'">

    <!-- 聊天消息区 -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto">
      <div class="max-w-3xl mx-auto px-5 py-6 space-y-6">

        <!-- 空状态 -->
        <div v-if="messages.length === 0" class="pt-16 text-center">
          <div class="w-16 h-16 rounded-full bg-brand-bg flex items-center justify-center mx-auto mb-4">
            <svg class="w-8 h-8 text-brand-base" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.259 1.035a3.375 3.375 0 002.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 00-2.455 2.456L21.75 6l-1.036-.259a3.375 3.375 0 002.455-2.456zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 00-2.455 2.456L21.75 6l-1.036-.259a3.375 3.375 0 002.455-2.456z" />
            </svg>
          </div>
          <h1 class="text-2xl font-semibold mb-2" :class="isDark ? 'text-text-primary' : 'text-text-primary'">
            告诉我你想做什么游戏
          </h1>
          <p class="text-sm mb-8" :class="isDark ? 'text-text-secondary' : 'text-text-secondary'">
            我来帮你分析需求，确认后自动开发
          </p>

          <div class="flex flex-wrap justify-center gap-3">
            <button
              v-for="(suggestion, idx) in suggestions"
              :key="idx"
              :disabled="suggestion.selected"
              class="px-5 py-2.5 text-sm rounded-xl transition-all duration-200 border"
              :class="suggestion.selected
                ? 'bg-bg-secondary text-text-secondary cursor-not-allowed border-border'
                : isDark
                  ? 'bg-bg-secondary text-text-primary border-border hover:border-brand-base hover:text-brand-base'
                  : 'bg-brand-base text-white hover:bg-brand-hover'"
              @click="selectSuggestion(suggestion)"
            >
              {{ suggestion.text }}
            </button>
          </div>
        </div>

        <!-- 消息列表（共享组件） -->
        <ChatBubble
          v-for="msg in messages"
          :key="msg.id"
          :role="msg.role"
          :content="msg.content"
          :streaming="msg.streaming"
        />

        <!-- 思考指示器（共享组件） -->
        <ChatThinkingIndicator v-if="thinking" />

        <!-- 项目概要卡片（共享组件） -->
        <div v-if="projectSummary" class="!mt-8">
          <ChatProjectSummary
            :summary="projectSummary"
            @confirm="confirmDevelop()"
            @modify="modifySummary()"
          />
        </div>

      </div>
    </div>

    <!-- 底部输入栏 -->
    <ChatInputBar
      v-model="inputMessage"
      :loading="thinking"
      :placeholder="thinking ? 'AI 正在思考...' : '输入你的游戏需求...'"
      @send="sendMessage()"
    />

  </div>
</template>

<script setup lang="ts">
interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  streaming?: boolean
  isError?: boolean
  time: string
}

const config = useRuntimeConfig()
const messages = ref<Message[]>([])
const inputMessage = ref('')
const thinking = ref(false)
const projectSummary = ref<any>(null)
const sessionId = ref<string | null>(null)
const messagesContainer = ref<HTMLElement>()
const { isDark } = useTheme()

const suggestions = ref([
  { text: '做一个贪吃蛇', selected: false },
  { text: '一个平台跳跃游戏', selected: false },
  { text: '一个迷宫挑战', selected: false },
])

function scrollToBottom() {
  nextTick(() => {
    messagesContainer.value?.scrollTo({ top: messagesContainer.value.scrollHeight, behavior: 'smooth' })
  })
}

function selectSuggestion(suggestion: { text: string; selected: boolean }) {
  suggestion.selected = true
  inputMessage.value = suggestion.text
  sendMessage()
}

async function sendMessage() {
  if (!inputMessage.value.trim() || thinking.value) return

  const text = inputMessage.value.trim()
  inputMessage.value = ''

  const userMsg: Message = {
    id: Date.now().toString(),
    role: 'user',
    content: text,
    time: '刚刚'
  }
  messages.value.push(userMsg)
  scrollToBottom()

  thinking.value = true

  try {
    const response = await $fetch(`${config.public.apiBase}/agents/chat`, {
      method: 'POST',
      body: {
        message: text,
        session_id: sessionId.value
      }
    }) as any

    if (response.session_id) {
      sessionId.value = response.session_id
    }

    const assistantMsg: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      streaming: true,
      time: '刚刚'
    }
    messages.value.push(assistantMsg)
    scrollToBottom()

    const content = response.response || ''
    for (let i = 0; i < content.length; i++) {
      await new Promise(r => setTimeout(r, 15))
      const msg = messages.value.find(m => m.id === assistantMsg.id)
      if (msg) {
        msg.content += content[i]
        scrollToBottom()
      }
    }

    const msg = messages.value.find(m => m.id === assistantMsg.id)
    if (msg) msg.streaming = false

    if (response.project_summary) {
      projectSummary.value = response.project_summary
    }
  } catch (e: any) {
    console.error('Chat error:', e)
    messages.value.push({
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '哎呀，生成失败了，请稍后重试',
      isError: true,
      time: '刚刚'
    })
    scrollToBottom()
  }

  thinking.value = false
}

function confirmDevelop() {
  navigateTo(`/workbench?session=${sessionId.value}`)
}

function modifySummary() {
  projectSummary.value = null
  messages.value.push({
    id: Date.now().toString(),
    role: 'user',
    content: '我来修改一下需求...',
    time: '刚刚'
  })
}
</script>
