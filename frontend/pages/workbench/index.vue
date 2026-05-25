<template>
  <div class="h-full flex flex-col" :class="isDark ? 'dark' : ''">
    <!-- 头部 -->
    <div class="h-14 flex items-center justify-between px-4 border-b transition-colors duration-200" :class="isDark ? 'bg-[#121212] border-[#2D2D2D]' : 'bg-[#F8F9FB] border-[#E5E7EB]'">
      <div class="flex items-center gap-4">
        <h1 class="text-lg font-medium" :class="isDark ? 'text-white' : 'text-[#1A1D23]'">工作台</h1>
        <span v-if="workbenchStore.sessionId" class="text-xs px-2 py-1 rounded" :class="isDark ? 'bg-[#2D2D2D] text-[#9CA3AF]' : 'bg-gray-100 text-[#6B7280]'">
          Session: {{ workbenchStore.sessionId }}
        </span>
      </div>
      <div class="flex items-center gap-2">
        <div class="flex items-center gap-2 px-3 py-1 rounded-lg" :class="isDark ? 'bg-[#2D2D2D]' : 'bg-gray-100'">
          <span class="relative flex h-2 w-2">
            <span v-if="ws.status.value === 'open'" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2" :class="wsStatusColor"></span>
          </span>
          <span class="text-xs" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">{{ wsStatusText }}</span>
        </div>
        <button
          @click="router.push('/')"
          class="px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 text-white"
          :class="isDark ? 'bg-[#60A5FA] hover:bg-[#93C5FD]' : 'bg-[#4A80F0] hover:bg-[#6B9AF5]'"
        >
          + 新建项目
        </button>
        <!-- 主题切换按钮 -->
        <button
          @click="toggleTheme"
          class="w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-200"
          :class="isDark ? 'bg-[#2D2D2D] text-yellow-400 hover:bg-[#3D3D3D]' : 'bg-gray-100 text-[#6B7280] hover:bg-gray-200'"
          :title="isDark ? '切换到浅色主题' : '切换到深色主题'"
        >
          <span v-if="isDark" class="text-sm">☀️</span>
          <span v-else class="text-sm">🌙</span>
        </button>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="flex-1 flex overflow-hidden">
      <!-- 加载中 -->
      <div v-if="loading" class="flex-1 flex items-center justify-center" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">
        <span class="animate-spin text-2xl">↻</span>
        <span class="ml-2">加载项目...</span>
      </div>

      <!-- 有项目时 -->
      <div v-else-if="currentProject" class="flex-1 grid grid-cols-3 gap-4 p-4" :class="isDark ? 'bg-[#121212]' : 'bg-[#F8F9FB]'">
        <div class="col-span-2 rounded-2xl border overflow-hidden shadow-sm" :class="isDark ? 'bg-[#1E1E1E] border-[#2D2D2D]' : 'bg-white border-[#E5E7EB]'">
          <ChatPanel :agent-id="workbenchStore.activeAgentId" :agent-name="workbenchStore.activeAgent?.name || 'Master'" />
        </div>
        <div class="space-y-4 overflow-y-auto scrollbar-thin">
          <ComponentPanel />
          <div class="rounded-2xl border p-4 shadow-sm" :class="isDark ? 'bg-[#1E1E1E] border-[#2D2D2D]' : 'bg-white border-[#E5E7EB]'">
            <h3 class="text-sm font-medium mb-3" :class="isDark ? 'text-[#F9FAFB]' : 'text-[#1A1D23]'">📋 项目信息</h3>
            <div class="space-y-2 text-xs">
              <div class="flex justify-between">
                <span :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">名称</span>
                <span :class="isDark ? 'text-[#F9FAFB]' : 'text-[#1A1D23]'">{{ currentProject.name }}</span>
              </div>
              <div class="flex justify-between">
                <span :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">ID</span>
                <span :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">#{{ currentProject.id }}</span>
              </div>
              <div class="flex justify-between">
                <span :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">Agent 状态</span>
                <span :class="isDark ? 'text-[#60A5FA]' : 'text-[#4A80F0]'">{{ workbenchStore.agentStats.running }}/{{ workbenchStore.agentStats.total }}</span>
              </div>
              <div class="flex justify-between">
                <span :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">WebSocket</span>
                <span class="text-xs" :class="ws.status.value === 'open' ? 'text-green-500' : (isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]')">{{ ws.status.value }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 无项目时 -->
      <div v-else class="flex-1 flex flex-col items-center justify-center" :class="isDark ? 'bg-[#121212] text-[#9CA3AF]' : 'bg-[#F8F9FB] text-[#6B7280]'">
        <span class="text-6xl mb-4">🎮</span>
        <h2 class="text-xl font-medium mb-2" :class="isDark ? 'text-[#F9FAFB]' : 'text-[#1A1D23]'">欢迎使用 Agent Studio</h2>
        <p class="text-sm mb-6">去首页创建一个项目</p>
        <button
          @click="router.push('/')"
          class="px-6 py-3 rounded-xl text-sm font-medium transition-all duration-200 text-white shadow-sm"
          :class="isDark ? 'bg-[#60A5FA] hover:bg-[#93C5FD]' : 'bg-[#4A80F0] hover:bg-[#6B9AF5]'"
        >
          开始需求沟通
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useProjectStore } from '~/stores/project'
import { useWorkbenchStore } from '~/stores/workbench'
import { useProjectWebSocket } from '~/composables/useWebSocket'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const workbenchStore = useWorkbenchStore()

const loading = ref(true)
const currentProject = computed(() => projectStore.current)
const { isDark, toggleTheme } = useTheme()

// WebSocket 连接
const projectId = computed(() => {
  const id = route.params.id
  return id ? Number(id) : null
})

const ws = projectId.value ? useProjectWebSocket(projectId.value) : { status: ref<'closed'>('closed') }

const wsStatusColor = computed(() => {
  switch (ws.status.value) {
    case 'open': return 'bg-green-500'
    case 'connecting': return 'bg-yellow-500'
    case 'error': return 'bg-red-500'
    default: return 'bg-gray-600'
  }
})

const wsStatusText = computed(() => {
  switch (ws.status.value) {
    case 'open': return '已连接'
    case 'connecting': return '连接中...'
    case 'error': return '连接错误'
    default: return '未连接'
  }
})

// 初始化
onMounted(async () => {
  // 从 URL 获取 session
  if (route.query.session) {
    workbenchStore.setSessionId(route.query.session as string)
  }

  // 初始化 Agent
  if (workbenchStore.agents.length === 0) {
    workbenchStore.initDefaultAgents()
  }

  // 获取项目
  if (projectId.value) {
    try {
      await projectStore.fetchOne(projectId.value)
    } catch (e) {
      console.error('获取项目失败:', e)
    }
  }

  loading.value = false
})

</script>
