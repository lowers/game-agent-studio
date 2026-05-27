<template>
  <div class="flex-1 flex flex-col min-h-0 transition-colors duration-300" :class="isDark ? 'bg-[#111827]' : 'bg-[#F9FAFB]'">

    <!-- 顶部导航栏 -->
    <nav class="flex items-center justify-between px-6 py-3 border-b" :class="isDark ? 'border-[#374151]' : 'border-[#E5E7EB]'">
      <div class="flex items-center gap-2">
        <div class="w-8 h-8 rounded-lg bg-accent-bg flex items-center justify-center">
          <svg class="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
          </svg>
        </div>
        <span class="font-semibold" :class="isDark ? 'text-white' : 'text-[#1A1D23]'">Game Agent Studio</span>
      </div>
      <div class="flex items-center gap-3">
        <template v-if="isAuthenticated">
          <NuxtLink
            to="/settings"
            class="p-2 rounded-lg transition-colors duration-200"
            :class="isDark ? 'hover:bg-[#374151] text-[#9CA3AF]' : 'hover:bg-[#F3F4F6] text-[#6B7280]'"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </NuxtLink>
          <button
            @click="handleLogout"
            class="px-3 py-1.5 rounded-lg text-sm transition-colors duration-200"
            :class="isDark
              ? 'bg-[#374151] text-[#D1D5DB] hover:bg-[#4B5563]'
              : 'bg-[#F3F4F6] text-[#374151] hover:bg-[#E5E7EB]'"
          >
            登出
          </button>
        </template>
        <template v-else>
          <NuxtLink
            to="/login"
            class="px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-200"
            :class="isDark
              ? 'bg-[#4A80F0] text-white hover:bg-[#6B9AF5]'
              : 'bg-[#4A80F0] text-white hover:bg-[#6B9AF5]'"
          >
            登录
          </NuxtLink>
        </template>
      </div>
    </nav>

    <!-- 聊天消息区 -->
    <div ref="chatContainer" class="flex-1 overflow-y-auto">
      <div class="max-w-3xl mx-auto px-5 py-6 space-y-6">

        <!-- 空状态 -->
        <div v-if="conversation.messages.length === 0" class="pt-16 text-center">
          <div class="w-12 h-12 rounded-full bg-accent-bg flex items-center justify-center mx-auto mb-4">
            <svg class="w-6 h-6 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
            </svg>
          </div>
          <h1 class="text-4xl font-bold mb-2" :class="isDark ? 'text-white' : 'text-[#1A1D23]'">
            告诉我你想做什么游戏
          </h1>
          <p class="text-sm mb-8" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">
            我来帮你分析需求，确认后自动开发
          </p>

          <div class="flex flex-wrap justify-center gap-3">
            <button
              v-for="s in suggestions"
              :key="s"
              class="px-5 py-2.5 text-sm rounded-full transition-all duration-200"
              :class="isDark
                ? 'bg-[#1F2937] text-[#D1D5DB] border border-[#374151] hover:border-[#4A80F0] hover:text-[#4A80F0]'
                : 'bg-[#4A80F0] text-white hover:bg-[#6B9AF5]'"
              @click="selectAndSend(s)"
            >
              {{ s }}
            </button>
          </div>
        </div>

        <!-- 消息列表（使用共享组件） -->
        <ChatBubble
          v-for="(msg, i) in conversation.messages"
          :key="i"
          :role="msg.role"
          :content="msg.content"
        />

        <!-- 思考指示器（共享组件） -->
        <ChatThinkingIndicator v-if="conversation.loading" />

        <!-- 项目概要卡片（共享组件） -->
        <div v-if="conversation.projectSummary" class="!mt-8">
          <ChatProjectSummary
            :summary="{
              name: conversation.projectSummary.name,
              game_type: conversation.projectSummary.game_type,
              complexity: conversation.projectSummary.complexity,
              suggested_agents: conversation.projectSummary.suggested_agents,
            }"
            @confirm="confirmDevelop" :disabled="confirming"
            @modify="modifySummary"
          />
        </div>

      </div>
    </div>

    <!-- 底部输入栏 -->
    <ChatInputBar
      v-model="input"
      :loading="conversation.loading"
      :placeholder="conversation.projectSummary ? '继续提出修改...' : '输入你的游戏需求...'"
      @send="handleSend"
    />

  </div>
</template>

<script setup lang="ts">
import { useConversationStore } from '~/stores/conversation'
import { useProjectStore } from '~/stores/project'
import { useRouter } from 'vue-router'

const conversation = useConversationStore()
const projectStore = useProjectStore()
const router = useRouter()
const input = ref('')
const chatContainer = ref<HTMLElement>()
const inputRef = ref<HTMLInputElement>()
const confirming = ref(false)
const { isDark } = useTheme()
const { isAuthenticated, logout } = useAuth()

function handleLogout() {
  logout()
}

const suggestions = ['做一个贪吃蛇', '一个平台跳跃游戏', '一个迷宫挑战']

function selectAndSend(s: string) {
  input.value = s
  nextTick(() => handleSend())
}

async function handleSend() {
  const text = input.value.trim()
  if (!text) return
  input.value = ''
  await conversation.send(text)
  nextTick(() => {
    chatContainer.value?.scrollTo({ top: chatContainer.value.scrollHeight, behavior: 'smooth' })
  })
}

async function confirmDevelop() {
  if (!conversation.projectSummary) return
  if (confirming.value) return
  confirming.value = true
  const summary = conversation.projectSummary
  const sid = conversation.sessionId
  const name = summary.name
  const description = summary.description || `${summary.game_type}游戏`
  try {
    const p = await projectStore.create(name, description)
    conversation.clear()
    router.push(`/workbench/${p.id}?session=${sid}&autoStartWorkflow=true`)
  } catch (e) {
    console.error('Create project failed:', e)
  } finally {
    confirming.value = false
  }
}

function modifySummary() {
  conversation.projectSummary = null
  input.value = '我来修改一下需求...'
  nextTick(() => inputRef.value?.focus?.())
}

onMounted(() => {
  nextTick(() => inputRef.value?.focus?.())
})
</script>
