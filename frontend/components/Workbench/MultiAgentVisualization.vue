<template>
  <div class="flex flex-col h-full">
    <!-- Header -->
    <div class="h-12 flex items-center justify-between px-4 border-b" :class="isDark ? 'border-border-secondary bg-bg-secondary' : 'border-border bg-bg-primary'">
      <div class="flex items-center gap-2">
        <div class="w-5 h-5 rounded bg-accent flex items-center justify-center">
          <svg class="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
        </div>
        <span class="font-medium" :class="isDark ? 'text-text-primary' : 'text-text-primary'">Agent 协作网络</span>
      </div>
      <div class="flex items-center gap-3">
        <span class="text-xs flex items-center gap-1.5" :class="isDark ? 'text-brand-base' : 'text-brand-base'">
          <span class="relative flex h-2 w-2">
            <span class="absolute inline-flex h-full w full rounded-full bg-green-500 opacity-75 animate-ping"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
          </span>
          {{ isConnecting ? '已连接' : '未连接' }}
        </span>
        <button @click="toggleTheme" class="p-1.5 rounded transition-colors" :class="isDark ? 'hover:bg-bg-secondary' : 'hover:bg-bg-secondary'" title="切换主题">
          <span class="text-lg">☀️</span>
        </button>
      </div>
    </div>

    <!-- Main visualization area -->
    <div ref="vizContainer" class="flex-1 relative">
      <!-- SVG connection lines (simple, no effects) -->
      <svg ref="svgElement" class="absolute inset-0 w-full h-full pointer-events-none">
        <g v-if="connections.length > 0">
          <path
            v-for="conn in connections"
            :key="conn.id"
            :d="getConnectionPath(conn)"
            :stroke="conn.color"
            stroke-width="2"
            fill="none"
            :opacity="conn.highlight ? 0.8 : 0.3"
          />
        </g>
      </svg>

      <!-- Agent nodes -->
      <div class="absolute inset-0">
        <div
          v-for="agent in agents"
          :key="agent.id"
          ref="agentNodes"
          class="absolute transition-all duration-200"
          :style="getNodePosition(agent)"
          @mouseenter="hoveredAgent = agent.id"
          @mouseleave="hoveredAgent = null"
        >
          <!-- Node card -->
          <div
            class="relative p-3 rounded-lg border transition-all duration-200 cursor-pointer"
            :class="[
              agent.status === 'running' ? 'border-green-500 bg-bg-secondary' :
                agent.status === 'error' ? 'border-red-500 bg-bg-secondary' :
                agent.status === 'done' ? 'border-brand-base bg-bg-secondary' :
                'border-border bg-bg-secondary',
              hoveredAgent === agent.id ? 'ring-2 ring-brand-base ring-offset-1' : '',
            ]"
          >
            <!-- Status indicator -->
            <div
              class="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold"
              :class="[
                agent.status === 'running' ? 'bg-green-500 text-white' :
                  agent.status === 'error' ? 'bg-red-500 text-white' :
                  agent.status === 'waiting' ? 'bg-yellow-500 text-white' :
                  'bg-brand-base text-white',
              ]"
            >
              {{ getStatusIcon(agent.status) }}
            </div>

            <!-- Agent icon (simple colored circle) -->
            <div
              class="w-8 h-8 rounded-full flex items-center justify-center text-sm mb-1.5"
              :class="agent.status === 'running' ? 'bg-brand-base/20 text-brand-base' : 'bg-bg-tertiary text-text-secondary'"
            >
              {{ agent.icon }}
            </div>

            <!-- Name -->
            <div class="text-sm font-medium truncate" :class="isDark ? 'text-text-primary' : 'text-text-primary'">{{ agent.name }}</div>

            <!-- Task -->
            <div class="text-xs mt-0.5 truncate" :class="isDark ? 'text-text-secondary' : 'text-text-secondary'">{{ agent.currentTask || '待命' }}</div>

            <!-- Progress bar -->
            <div v-if="agent.progress !== undefined && agent.progress > 0" class="mt-1.5">
              <div class="flex items-center justify-between text-xs mb-1">
                <span :class="isDark ? 'text-text-secondary' : 'text-text-secondary'">进度</span>
                <span :class="agent.status === 'done' ? 'text-green-500' : 'text-brand-base'">{{ agent.progress }}%</span>
              </div>
              <div class="h-1 bg-bg-tertiary rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-300"
                  :class="agent.status === 'done' ? 'bg-green-500' : 'bg-brand-base'"
                  :style="`width: ${Math.min(agent.progress, 100)}%`"
                ></div>
              </div>
            </div>

            <!-- Agent level/rank -->
            <div v-if="agent.level" class="mt-1 text-xs" :class="isDark ? 'text-text-tertiary' : 'text-text-tertiary'">{{ agent.level }}</div>
          </div>

          <!-- Tooltip on hover -->
          <div
            v-if="hoveredAgent === agent.id"
            class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2.5 py-1.5 rounded bg-bg-secondary border border-border text-xs shadow"
          >
            <div class="font-medium text-text-primary">{{ agent.name }}</div>
            <div class="text-text-secondary">任务: {{ agent.currentTask || '空闲' }}</div>
            <div class="text-text-secondary">耗时: {{ formatDuration(agent.elapsedTime || 0) }}</div>
          </div>
        </div>
      </div>

      <!-- Stats overlay -->
      <div class="absolute top-2 right-2 flex flex-col gap-1.5 p-2 rounded bg-bg-secondary border border-border">
        <div class="flex items-center gap-1 text-xs" :class="isDark ? 'text-text-secondary' : 'text-text-secondary'">
          <span>总任务:</span>
          <span class="font-medium text-brand-base">{{ totalTasks }}</span>
        </div>
        <div class="flex items-center gap-1 text-xs" :class="isDark ? 'text-text-secondary' : 'text-text-secondary'">
          <span>平均耗时:</span>
          <span class="font-medium text-brand-base">{{ avgDuration }}</span>
        </div>
        <div class="flex items-center gap-1 text-xs" :class="isDark ? 'text-text-secondary' : 'text-text-secondary'">
          <span>通信次数:</span>
          <span class="font-medium text-brand-base">{{ totalCommunications }}</span>
        </div>
      </div>
    </div>

    <!-- Timeline log -->
    <div v-if="logEvents.length > 0" class="h-24 border-t overflow-y-auto p-2" :class="isDark ? 'border-bg-secondary' : 'border-border'">
      <div class="text-xs font-medium mb-1" :class="isDark ? 'text-text-secondary' : 'text-text-secondary'">事件日志</div>
      <div
        v-for="log in logEvents"
        :key="log.id"
        class="flex items-center gap-1.5 px-1.5 py-0.5 rounded text-xs"
        :class="log.type === 'success' ? 'text-green-600 bg-green-50' :
          log.type === 'error' ? 'text-red-600 bg-red-50' :
          log.type === 'info' ? (isDark ? 'text-text-secondary bg-bg-secondary' : 'text-text-secondary bg-bg-primary') :
          'text-brand-base bg-brand-bg'"
      >
        <span :class="isDark ? 'text-text-tertiary' : 'text-text-tertiary'">{{ log.time }}</span>
        <span class="truncate">{{ log.message }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useTheme } from '~/composables/useTheme'

interface Agent {
  id: string
  name: string
  icon: string
  status: 'idle' | 'running' | 'waiting' | 'done' | 'error'
  currentTask?: string
  progress?: number
  parentId?: string | null
  x: number
  y: number
  level?: string
  elapsedTime?: number
  inputTokens?: number
  outputTokens?: number
}

interface Connection {
  id: string
  from: string
  to: string
  color: string
  active: boolean
  highlight: boolean
}

interface LogEvent {
  id: number
  time: string
  message: string
  type: 'success' | 'error' | 'info' | 'action'
}

const props = defineProps<{
  agents?: Agent[]
  connections?: Connection[]
  theme?: 'light' | 'dark'
}>()

const emit = defineEmits<{
  (e: 'node-click', agentId: string): void
}>()

// State
const vizContainer = ref<HTMLElement>()
const svgElement = ref<SVGElement>()
const agentNodes = ref<(HTMLElement | null)[]>([])
const hoveredAgent = ref<string | null>(null)
const isConnecting = ref(true)
const { isDark } = useTheme()

// Agent display data (with layout positions)
const agents = computed(() => {
  if (props.agents) return props.agents
  // Demo data (simple icons)
  return [
    { id: 'master', name: 'Master', icon: 'M', status: 'running', x: 50, y: 30, level: 'Orchestrator', currentTask: '协调任务分派' },
    { id: 'planner', name: 'Planner', icon: 'P', status: 'waiting', x: 20, y: 60, parentId: 'master', level: 'L2', currentTask: '任务规划中...' },
    { id: 'architect', name: 'Architect', icon: 'A', status: 'running', x: 50, y: 60, parentId: 'master', level: 'L2', currentTask: '系统设计', progress: 65 },
    { id: 'programmer', name: 'Programmer', icon: 'C', status: 'done', x: 80, y: 60, parentId: 'master', level: 'L2', currentTask: '代码实现', progress: 100 },
    { id: 'tester', name: 'QA', icon: 'T', status: 'idle', x: 35, y: 85, parentId: 'architect', level: 'L3', currentTask: null },
    { id: 'documenter', name: 'Doc', icon: 'D', status: 'idle', x: 65, y: 85, parentId: 'architect', level: 'L3', currentTask: null },
  ] as Agent[]
})

const connections = computed(() => {
  if (props.connections) return props.connections
  // Auto-generate connections from parent relationships
  const parentAgents = agents.value.filter(a => a.parentId)
  return parentAgents.map((agent, i) => ({
    id: `conn-${agent.parentId}-${agent.id}`,
    from: agent.parentId!,
    to: agent.id,
    color: i % 2 === 0 ? 'oklch(0.65 0.18 250)' : 'oklch(0.70 0.15 270)',
    active: agent.status === 'running',
    highlight: hoveredAgent.value === agent.id || hoveredAgent.value === agent.parentId,
  }))
})

const logEvents = ref<LogEvent[]>([
  { id: 1, time: '10:30:01', message: 'Master 启动工作流', type: 'info' },
  { id: 2, time: '10:30:05', message: 'Planner 开始任务分解', type: 'info' },
  { id: 3, time: '10:30:12', message: 'Architect 完成架构设计', type: 'success' },
  { id: 4, time: '10:30:45', message: 'Programmer 提交代码', type: 'success' },
  { id: 5, time: '10:31:02', message: 'QA 运行测试套件', type: 'info' },
])

// Stats
const totalTasks = computed(() => agents.value.filter(a => a.currentTask).length)
const avgDuration = computed(() => {
  const running = agents.value.filter(a => a.elapsedTime)
  if (running.length === 0) return '--'
  const total = running.reduce((s, a) => s + (a.elapsedTime || 0), 0)
  return formatDuration(Math.round(total / running.length))
})
const totalCommunications = computed(() => connections.value.filter(c => c.active).length)

// Methods
function getNodePosition(agent: Agent): { left: string; top: string } {
  return { left: `${agent.x}%`, top: `${agent.y}%` }
}

function getConnectionPath(conn: Connection): string {
  const fromAgent = agents.value.find(a => a.id === conn.from)
  const toAgent = agents.value.find(a => a.id === conn.to)
  if (!fromAgent || !toAgent) return ''

  const container = vizContainer.value
  if (!container) return ''

  const rect = container.getBoundingClientRect()
  const fromX = (fromAgent.x / 100) * rect.width + 50
  const fromY = (fromAgent.y / 100) * rect.height + 50
  const toX = (toAgent.x / 100) * rect.width + 50
  const toY = (toAgent.y / 100) * rect.height + 50

  // Simple curved path
  const midX = (fromX + toX) / 2
  const midY = (fromY + toY) / 2

  return `M ${fromX} ${fromY} Q ${midX} ${midY} ${toX} ${toY}`
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

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}m ${secs}s`
}

// Watch for agent updates
watch(() => props.agents, (newAgents) => {
  if (newAgents) {
    logEvents.value.push({
      id: Date.now(),
      time: new Date().toLocaleTimeString('zh-CN', { hour12: false }),
      message: `收到 ${newAgents.length} 个 Agent 状态更新`,
      type: 'info',
    })
  }
}, { deep: true })

// Keep log events trimmed
watch(logEvents, (logs) => {
  if (logs.length > 20) {
    logEvents.value = logs.slice(logs.length - 20)
  }
}, { deep: true })
</script>
