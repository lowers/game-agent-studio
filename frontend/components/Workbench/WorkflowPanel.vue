<template>
  <div class="flex flex-col h-full" :class="isDark ? 'dark' : ''">
    <!-- 头部 -->
    <div class="h-14 flex items-center justify-between px-4 border-b transition-colors duration-200" :class="isDark ? 'border-[#2D2D2D]' : 'border-[#E5E7EB]'">
      <div>
        <div class="font-medium" :class="isDark ? 'text-white' : 'text-[#1A1D23]'">多专家并行工作流</div>
        <div class="text-xs" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">Project #{{ projectId }} · {{ workflowId ? `wf-${workflowId}` : '未启动' }}</div>
      </div>
      <div class="flex items-center gap-3">
        <span v-if="wsStatus === 'open'" class="flex items-center gap-1 text-xs" :class="isDark ? 'text-[#60A5FA]' : 'text-[#4A80F0]'">
          <span class="relative flex h-2 w-2">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
          </span>
          已连接
        </span>
        <span v-else class="flex items-center gap-1 text-xs" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">
          <span class="relative inline-flex rounded-full h-2 w-2 bg-gray-500"></span>
          WebSocket: {{ wsStatus }}
        </span>
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

    <!-- 控制面板 -->
    <div class="flex gap-2 px-4 py-3 border-b transition-colors duration-200" :class="isDark ? 'border-[#2D2D2D]' : 'border-[#E5E7EB]'">
      <button
        @click="startWorkflow"
        :disabled="workflowStarted || isRunning || isWaiting"
        class="px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 text-white shadow-sm"
        :class="(workflowStarted || isRunning || isWaiting)
          ? (isDark ? 'bg-[#2D2D2D] text-[#9CA3AF] cursor-not-allowed' : 'bg-gray-100 text-gray-400 cursor-not-allowed')
          : (isDark ? 'bg-[#60A5FA] hover:bg-[#93C5FD]' : 'bg-[#4A80F0] hover:bg-[#6B9AF5]')"
      >
        {{ workflowStarted ? '运行中...' : '▶ 启动' }}
      </button>
      <button
        @click="pauseWorkflow"
        :disabled="!isRunning"
        class="px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-200"
        :class="!isRunning
          ? (isDark ? 'bg-[#2D2D2D] text-[#9CA3AF] cursor-not-allowed' : 'bg-gray-100 text-gray-400 cursor-not-allowed')
          : (isDark ? 'bg-[#1E1E1E] hover:bg-[#2D2D2D] text-[#D1D5DB]' : 'bg-white hover:bg-gray-100 text-[#6B7280]')"
      >
        ⏸ 暂停
      </button>
      <button
        @click="resumeWorkflow"
        :disabled="!isWaiting"
        class="px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-200"
        :class="!isWaiting
          ? (isDark ? 'bg-[#2D2D2D] text-[#9CA3AF] cursor-not-allowed' : 'bg-gray-100 text-gray-400 cursor-not-allowed')
          : (isDark ? 'bg-[#1E1E1E] hover:bg-[#2D2D2D] text-[#D1D5DB]' : 'bg-white hover:bg-gray-100 text-[#6B7280]')"
      >
        ▶ 恢复
      </button>
      <button
        @click="cancelWorkflow"
        :disabled="!isRunning && !isWaiting"
        class="px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 text-white shadow-sm"
        :class="(!isRunning && !isWaiting)
          ? (isDark ? 'bg-[#2D2D2D] text-[#9CA3AF] cursor-not-allowed' : 'bg-gray-100 text-gray-400 cursor-not-allowed')
          : 'bg-red-500 hover:bg-red-600'"
      >
        ✕ 取消
      </button>
      <button
        @click="showLogs = !showLogs"
        class="px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 ml-auto"
        :class="isDark ? 'bg-[#1E1E1E] hover:bg-[#2D2D2D] text-[#D1D5DB]' : 'bg-white hover:bg-gray-100 text-[#6B7280]'"
      >
        📋 日志
      </button>
    </div>

    <!-- 确认面板 -->
    <div v-if="isWaiting" class="mx-4 mt-4 p-3 rounded-lg border transition-all duration-200" :class="isDark ? 'bg-[#1E1E1E] border-[#2D2D2D]' : 'bg-white border-[#E5E7EB]'">
      <div class="flex items-center gap-3 mb-3">
        <span class="text-xl">⚠️</span>
        <div>
          <div class="text-sm font-medium" :class="isDark ? 'text-white' : 'text-[#1A1D23]'">等待用户确认</div>
          <div class="text-xs" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">{{ waitingMessage }}</div>
        </div>
      </div>
      <button
        @click="resumeWorkflow"
        class="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 text-white shadow-sm"
        :class="isDark ? 'bg-[#60A5FA] hover:bg-[#93C5FD]' : 'bg-[#4A80F0] hover:bg-[#6B9AF5]'"
      >
        继续
      </button>
    </div>

    <!-- 状态摘要 -->
    <div class="flex gap-3 px-4 py-3">
      <div
        v-for="st in statusSummary"
        :key="st.status"
        class="flex-1 text-center p-3 rounded-lg border transition-all duration-200 shadow-sm"
        :class="isDark ? 'bg-[#1E1E1E] border-[#2D2D2D]' : 'bg-white border-[#E5E7EB]'"
      >
        <div class="text-xl font-bold" :style="{ color: st.color }">{{ st.count }}</div>
        <div class="text-xs mt-1" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">{{ st.label }}</div>
      </div>
    </div>

    <!-- DAG 执行轮次 -->
    <div class="flex-1 overflow-y-auto px-4 py-3 scrollbar-thin">
      <div class="text-xs font-medium mb-3" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">🔄 并行执行轮次</div>
      
      <div v-for="(round, roundIdx) in executionRounds" :key="roundIdx" class="flex flex-wrap gap-3 mb-3 p-3 rounded-lg border transition-all duration-200" :class="currentRound === roundIdx && (isRunning || isWaiting) ? (isDark ? 'bg-[#1E1E1E] border-[#4A80F0]' : 'bg-white border-[#4A80F0]') : (isDark ? 'bg-[#121212] border-[#2D2D2D]' : 'bg-[#F8F9FB] border-[#E5E7EB]')">
        <div class="w-full text-xs mb-2" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">Round {{ roundIdx }}</div>
        
        <div
          v-for="expertId in round"
          :key="expertId"
          class="relative p-3 rounded-lg border transition-all duration-200 shadow-sm"
          :class="getExpertCardClass(expertId)"
          :style="getExpertGlowStyle(expertId)"
        >
          <!-- 状态徽章 -->
          <div
            class="absolute -top-2 -right-2 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold"
            :class="getStatusBadgeClass(getExpertStatus(expertId))"
          >
            {{ getStatusIcon(getExpertStatus(expertId)) }}
          </div>

          <!-- 专家图标 -->
          <div
            class="w-10 h-10 rounded-lg flex items-center justify-center text-lg mb-2"
            :class="getExpertStatus(expertId) === 'running' ? 'animate-spin-slow' : ''"
          >
            {{ getExpertIcon(expertId) }}
          </div>

          <!-- 名称 -->
          <div class="text-sm font-medium truncate" :class="isDark ? 'text-[#F9FAFB]' : 'text-[#1A1D23]'">{{ getExpertName(expertId) }}</div>

          <!-- 任务 -->
          <div class="text-xs mt-0.5 truncate" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">{{ getExpertTask(expertId) || '待命' }}</div>

          <!-- 进度条 -->
          <div v-if="getExpertProgress(expertId) !== undefined && getExpertProgress(expertId) > 0" class="mt-2">
            <div class="flex items-center justify-between text-xs mb-1">
              <span :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">进度</span>
              <span :class="getExpertStatus(expertId) === 'done' ? 'text-green-500' : (isDark ? 'text-[#60A5FA]' : 'text-[#4A80F0]')">{{ getExpertProgress(expertId) }}%</span>
            </div>
            <div class="h-1.5 rounded-full overflow-hidden" :class="isDark ? 'bg-[#2D2D2D]' : 'bg-gray-200'">
              <div
                class="h-full rounded-full transition-all duration-300"
                :class="getExpertStatus(expertId) === 'done' ? 'bg-green-500' : (isDark ? 'bg-[#60A5FA]' : 'bg-[#4A80F0]')"
                :style="`width: ${Math.min(getExpertProgress(expertId), 100)}%`"
              ></div>
            </div>
          </div>

          <!-- 专家等级 -->
          <div v-if="getExpertLevel(expertId)" class="mt-1.5 text-xs" :class="getLevelColor(getExpertLevel(expertId))">
            {{ getExpertLevel(expertId) }}
          </div>
        </div>
      </div>
    </div>

    <!-- 日志 -->
    <div v-if="showLogs" class="h-32 border-t overflow-y-auto p-2 scrollbar-thin transition-colors duration-200" :class="isDark ? 'border-[#2D2D2D]' : 'border-[#E5E7EB]'">
      <div class="text-xs font-medium mb-1" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">📜 执行日志</div>
      <div
        v-for="(log, i) in timelineLogs"
        :key="i"
        class="flex items-center gap-2 px-2 py-1 rounded-lg text-xs transition-all duration-150"
        :class="log.type === 'success' ? (isDark ? 'text-green-400 bg-green-900/10' : 'text-green-600 bg-green-50') :
          log.type === 'error' ? (isDark ? 'text-red-400 bg-red-900/10' : 'text-red-600 bg-red-50') :
          log.type === 'info' ? (isDark ? 'text-[#D1D5DB] bg-[#1E1E1E]' : 'text-[#6B7280] bg-white') :
          (isDark ? 'text-[#60A5FA] bg-[#4A80F0]/10' : 'text-[#4A80F0] bg-[#4A80F0]/10')"
      >
        <span class="whitespace-nowrap" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">{{ log.time }}</span>
        <span>{{ log.message }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useTheme } from '~/composables/useTheme'

interface ExpertData {
  name: string
  icon: string
  desc: string
}

interface StatusConfig {
  color: string
  text: string
  badge: string
}

interface LogEvent {
  id: number
  time: string
  message: string
  type: 'success' | 'error' | 'info' | 'action'
}

const props = defineProps<{
  projectId: number
}>()

const emit = defineEmits<{
  (e: 'workflow-started', workflowId: string): void
  (e: 'workflow-paused'): void
  (e: 'workflow-resumed'): void
  (e: 'workflow-cancelled'): void
}>()

// 状态
const workflowStarted = ref(false)
const workflowId = ref<string | null>(null)
const currentRound = ref(0)
const totalRounds = ref(0)
const executionRounds = ref<string[][]>([])
const expertStatus = ref<Record<string, string>>({ })
const expertResults = ref<Record<string, any>>({ })
const timelineLogs = ref<LogEvent[]>([])
const showLogs = ref(false)
const waitingMessage = ref('')
const { isDark, toggleTheme } = useTheme()

// WebSocket 状态
const wsStatus = ref<'open' | 'connecting' | 'error' | 'closed'>('closed')

// 计算属性
const isRunning = computed(() => Object.values(expertStatus.value).some(s => s === 'running'))
const isWaiting = computed(() => Object.values(expertStatus.value).some(s => s === 'waiting'))

const statusSummary = computed(() => {
  const counts: Record<string, number> = {}
  for (const s of Object.values(expertStatus.value)) {
    counts[s] = (counts[s] ?? 0) + 1
  }
  return [
    { status: 'running', label: '运行中', count: counts.running ?? 0, color: '#10B981' },
    { status: 'done', label: '已完成', count: counts.done ?? 0, color: '#4A80F0' },
    { status: 'waiting', label: '等待确认', count: counts.waiting ?? 0, color: '#F59E0B' },
    { status: 'idle', label: '未启动', count: counts.idle ?? 0, color: '#6B7280' },
  ]
})

// 专家数据
const EXPERT_DATA: Record<string, ExpertData> = {
  planner: { name: '策划师', icon: '📋', desc: '需求分析、任务规划' },
  architect: { name: '架构师', icon: '🏗️', desc: '技术选型、系统架构' },
  programmer: { name: '程序员', icon: '💻', desc: '代码生成、功能实现' },
  qa: { name: '测试工程师', icon: '🔍', desc: '测试设计、质量评估' },
  security: { name: '安全专家', icon: '🛡️', desc: '安全审计、漏洞扫描' },
  devops: { name: '运维专家', icon: '⚙️', desc: '部署配置、CI/CD' },
}

const STATUS_CONFIG: Record<string, StatusConfig> = {
  idle: { color: '#6B7280', text: '未启动', badge: 'bg-gray-500 text-white' },
  running: { color: '#10B981', text: '运行中', badge: 'bg-green-500 text-white' },
  waiting: { color: '#F59E0B', text: '等待确认', badge: 'bg-yellow-500 text-white' },
  done: { color: '#4A80F0', text: '已完成', badge: 'bg-[#4A80F0] text-white' },
  error: { color: '#EF4444', text: '出错', badge: 'bg-red-500 text-white' },
  blocked: { color: '#6E7681', text: '已阻塞', badge: 'bg-gray-500 text-white' },
}

// 方法
function getExpertName(expertId: string): string {
  return EXPERT_DATA[expertId]?.name ?? expertId
}

function getExpertIcon(expertId: string): string {
  return EXPERT_DATA[expertId]?.icon ?? '🤖'
}

function getExpertStatus(expertId: string): string {
  return expertStatus.value[expertId] ?? 'idle'
}

function getExpertTask(expertId: string): string | undefined {
  return expertResults.value[expertId]?.currentTask
}

function getExpertProgress(expertId: string): number {
  return expertResults.value[expertId]?.progress ?? 0
}

function getExpertLevel(expertId: string): string {
  return expertResults.value[expertId]?.level ?? ''
}

function getStatusIcon(status: string): string {
  switch (status) {
    case 'running': return '▶'
    case 'waiting': return '⏳'
    case 'done': return '✓'
    case 'error': return '✗'
    default: return '○'
  }
}

function getStatusBadgeClass(status: string): string {
  return STATUS_CONFIG[status]?.badge ?? 'bg-gray-500 text-white'
}

function getExpertCardClass(expertId: string): string {
  const status = getExpertStatus(expertId)
  const base = 'border transition-all duration-200'
  
  if (status === 'running') {
    return `${base} ${isDark.value ? 'border-[#4A80F0] bg-[#1E1E1E]/90' : 'border-[#4A80F0] bg-white/90'}`
  } else if (status === 'done') {
    return `${base} ${isDark.value ? 'border-green-500 bg-[#1E1E1E]/90' : 'border-green-500 bg-white/90'}`
  } else if (status === 'error') {
    return `${base} ${isDark.value ? 'border-red-500 bg-[#1E1E1E]/90' : 'border-red-500 bg-white/90'}`
  } else if (status === 'waiting') {
    return `${base} ${isDark.value ? 'border-yellow-500 bg-[#1E1E1E]/90' : 'border-yellow-500 bg-white/90'}`
  } else {
    return `${base} ${isDark.value ? 'border-[#2D2D2D] bg-[#1E1E1E]/50' : 'border-[#E5E7EB] bg-white/50'}`
  }
}

function getExpertGlowStyle(expertId: string): string {
  const status = getExpertStatus(expertId)
  if (status === 'running') {
    return isDark.value
      ? 'box-shadow: 0 0 30px rgba(74, 128, 240, 0.3), 0 0 60px rgba(74, 128, 240, 0.15);'
      : 'box-shadow: 0 0 30px rgba(74, 128, 240, 0.15), 0 0 60px rgba(74, 128, 240, 0.05);'
  }
  if (status === 'error') {
    return isDark.value
      ? 'box-shadow: 0 0 30px rgba(239, 68, 68, 0.3);'
      : 'box-shadow: 0 0 30px rgba(239, 68, 68, 0.2);'
  }
  return ''
}

function getLevelColor(level: string): string {
  const colors: Record<string, string> = {
    'Orchestrator': 'text-yellow-400',
    'L2': 'text-blue-400',
    'L3': 'text-purple-400',
  }
  return colors[level] || 'text-gray-400'
}

// 工作流控制
async function startWorkflow() {
  if (workflowStarted.value) return
  
  try {
    // 调用 API 创建工作流
    const result = await $fetch<Record<string, any>>('/api/workflows', {
      method: 'POST',
      body: {
        project_id: props.projectId,
        experts: ['planner', 'architect', 'programmer', 'qa', 'security', 'devops'],
        mode: 'confirm',
        auto_start: true,
      }
    })
    
    workflowId.value = result.workflow_id
    workflowStarted.value = true
    currentRound.value = 0
    totalRounds.value = result.total_rounds
    executionRounds.value = result.execution_rounds
    
    // 初始化专家状态
    for (const expertId of result.execution_rounds.flat()) {
      expertStatus.value[expertId] = 'idle'
    }
    
    addLog('success', `工作流已创建: ${result.workflow_id}`)
    emit('workflow-started', result.workflow_id)
  } catch (e) {
    addLog('error', `创建工作流失败: ${(e as Error).message}`)
  }
}

async function pauseWorkflow() {
  if (!isRunning.value || !workflowId.value) return
  
  try {
    await $fetch(`/api/workflows/${workflowId.value}/pause`, { method: 'POST' })
    addLog('info', '工作流已暂停')
    emit('workflow-paused')
  } catch (e) {
    addLog('error', `暂停工作流失败: ${(e as Error).message}`)
  }
}

async function resumeWorkflow() {
  if (!isWaiting.value || !workflowId.value) return
  
  try {
    await $fetch(`/api/workflows/${workflowId.value}/resume`, { method: 'POST' })
    addLog('info', '用户确认后继续')
    emit('workflow-resumed')
  } catch (e) {
    addLog('error', `恢复工作流失败: ${(e as Error).message}`)
  }
}

async function cancelWorkflow() {
  if (!workflowId.value) return
  
  try {
    await $fetch(`/api/workflows/${workflowId.value}`, { method: 'DELETE' })
    addLog('error', '用户取消工作流')
    emit('workflow-cancelled')
    resetWorkflow()
  } catch (e) {
    addLog('error', `取消工作流失败: ${(e as Error).message}`)
  }
}

function resetWorkflow() {
  workflowStarted.value = false
  workflowId.value = null
  currentRound.value = 0
  totalRounds.value = 0
  executionRounds.value = []
  expertStatus.value = {}
  expertResults.value = {}
  timelineLogs.value = []
  showLogs.value = false
}

function addLog(type: 'success' | 'error' | 'info' | 'action', message: string) {
  timelineLogs.value.unshift({
    id: Date.now(),
    time: new Date().toLocaleTimeString('zh-CN', { hour12: false }),
    message,
    type,
  })
  
  // 限制日志数量
  if (timelineLogs.value.length > 50) {
    timelineLogs.value = timelineLogs.value.slice(0, 50)
  }
}

// 初始化
onMounted(() => {
  // 模拟 WebSocket 连接
  setTimeout(() => {
    wsStatus.value = 'open'
  }, 1000)
  
  // 模拟日志
  addLog('info', '工作流系统已启动')
  addLog('info', '等待用户创建工作流...')
})

onUnmounted(() => {
  // 清理资源
})
</script>