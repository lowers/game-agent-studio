<template>
  <div class="agent-coordination-board">
    <!-- Agent 依赖关系图 -->
    <div class="dependency-diagram">
      <svg class="dependency-svg" viewBox="0 0 400 80">
        <!-- Master Agent -->
        <circle cx="40" cy="40" r="20" :fill="isDark ? '#1E1E1E' : '#F3F4F6'" opacity="0.5" />
        <text x="40" y="44" text-anchor="middle" :fill="isDark ? '#F9FAFB' : '#1A1D23'" font-size="10">主</text>

        <!-- 连接线 -->
        <line x1="60" y1="40" x2="120" y2="40" :stroke="isDark ? '#60A5FA' : '#4A80F0'" stroke-width="1" opacity="0.3" />

        <!-- Agent 节点 -->
        <circle
          v-for="(agent, index) in agents"
          :key="agent.role"
          :cx="150 + index * 70"
          cy="40"
          r="18"
          :fill="getAgentColor(agent)"
          :opacity="agent.status === 'idle' ? 0.3 : 0.8"
          :class="{ 'agent-pulse': agent.status === 'running' }"
        />
        <text
          v-for="(agent, index) in agents"
          :key="'label-' + agent.role"
          :x="150 + index * 70"
          y="44"
          text-anchor="middle"
          :fill="isDark ? '#F9FAFB' : '#1A1D23'"
          font-size="9"
        >
          {{ agent.name.slice(0, 2) }}
        </text>

        <!-- 阻塞连线 -->
        <line
          v-if="blockedAgent"
          :x1="blockedAgent.x" :y1="blockedAgent.y"
          :x2="blockedAgent.blockedX" :y2="blockedAgent.blockedY"
          stroke="#EF4444" stroke-width="2" stroke-dasharray="4"
        />
      </svg>
    </div>

    <!-- Agent 卡片列表 -->
    <div class="agent-cards">
      <div
        v-for="agent in agents"
        :key="agent.role"
        :class="[
          'agent-card',
          `agent-card--${agent.status}`,
          { 'agent-card--active': agent.status === 'running' }
        ]"
      >
        <!-- 头部 -->
        <div class="agent-card__header">
          <div class="agent-card__title">
            <span :class="['status-dot', `status-dot--${agent.status}`]" />
            <span class="agent-name">{{ agent.name }}</span>
          </div>
          <span :class="['status-badge', `status-badge--${agent.status}`]">
            {{ getStatusLabel(agent.status) }}
          </span>
        </div>

        <!-- 当前任务 -->
        <div v-if="agent.task" class="agent-card__task">
          <span class="task-label">任务</span>
          <span class="task-content">{{ agent.task }}</span>
        </div>

        <!-- 进度条 -->
        <div v-if="agent.status === 'running' || agent.progress > 0" class="agent-card__progress">
          <div class="progress-bar">
            <div
              class="progress-bar__fill"
              :style="{ width: `${agent.progress}%` }"
            />
          </div>
          <span class="progress-label">{{ agent.progress }}%</span>
        </div>

        <!-- 输出预览 -->
        <div v-if="agent.output_preview" class="agent-card__output">
          <div class="output-header">
            <span>输出</span>
            <span class="output-live" v-if="agent.status === 'running'">● LIVE</span>
          </div>
          <div class="output-content">{{ agent.output_preview }}</div>
        </div>

        <!-- 阻塞信息 -->
        <div v-if="agent.blocked_by" class="agent-card__blocked">
          <span class="blocked-icon">⏸</span>
          <span>等待 {{ getAgentName(agent.blocked_by) }} 完成</span>
        </div>

        <!-- 错误信息 -->
        <div v-if="agent.error_message" class="agent-card__error">
          <span class="error-icon">⚠</span>
          <span>{{ agent.error_message }}</span>
        </div>
      </div>
    </div>

    <!-- 实时日志流 -->
    <div class="activity-log">
      <div class="log-header">
        <span>实时日志</span>
        <span class="log-count">{{ logs.length }} 条</span>
      </div>
      <div class="log-content">
        <div v-for="(log, index) in recentLogs" :key="index" :class="['log-item', `log-item--${log.type}`]">
          <span class="log-time">{{ formatTime(log.timestamp) }}</span>
          <span class="log-agent">{{ log.agent }}</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AgentState, AgentRole } from '~/types'

interface Props {
  agents: AgentState[]
  logs?: Array<{
    timestamp: string
    type: 'info' | 'warning' | 'error' | 'success'
    agent: string
    message: string
  }>
}

const props = withDefaults(defineProps<Props>(), {
  logs: () => []
})

const { isDark } = useTheme()

// 获取最近10条日志
const recentLogs = computed(() => props.logs.slice(-10).reverse())

// 获取 Agent 颜色
const getAgentColor = (agent: AgentState): string => {
  const colors: Record<AgentRole, string> = {
    planner: isDark.value ? '#60A5FA' : '#4A80F0',
    architect: isDark.value ? '#818CF8' : '#6366F1',
    programmer: isDark.value ? '#34D399' : '#10B981',
    qa: isDark.value ? '#FBBF24' : '#D97706'
  }
  return colors[agent.role] || (isDark.value ? '#9CA3AF' : '#6B7280')
}

// 获取状态标签
const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    idle: '空闲',
    running: '运行中',
    blocked: '已阻塞',
    done: '完成',
    error: '错误'
  }
  return labels[status] || status
}

// 获取 Agent 中文名
const getAgentName = (role: AgentRole | null): string => {
  if (!role) return ''
  const names: Record<AgentRole, string> = {
    planner: '策划',
    architect: '架构',
    programmer: '程序',
    qa: 'QA'
  }
  return names[role] || role
}

// 计算阻塞位置
const blockedAgent = computed(() => {
  const blocked = props.agents.find(a => a.blocked_by)
  if (!blocked) return null

  const blockerIndex = props.agents.findIndex(a => a.role === blocked.blocked_by)
  if (blockerIndex === -1) return null

  return {
    x: 150 + blockerIndex * 70,
    y: 40,
    blockedX: 150 + props.agents.indexOf(blocked) * 70,
    blockedY: 40
  }
})

// 格式化时间
const formatTime = (timestamp: string): string => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}
</script>

<style scoped>
.agent-coordination-board {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
}

/* 依赖关系图 */
.dependency-diagram {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 0.5rem;
  padding: 0.5rem;
  overflow: hidden;
}

.dependency-svg {
  width: 100%;
  height: 80px;
}

/* Agent 卡片 */
.agent-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
}

.agent-card {
  background: var(--bg-secondary);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.5rem;
  padding: 0.75rem;
  transition: all 0.3s ease;
}

.agent-card--active {
  border-color: var(--brand-base);
  box-shadow: 0 0 15px rgba(74, 128, 240, 0.15);
}

.agent-card--error {
  border-color: #EF4444;
}

.agent-card--blocked {
  border-color: #FBBF24;
  opacity: 0.85;
}

.agent-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.agent-card__title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.agent-name {
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--text-primary);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot--idle { background: var(--text-muted); }
.status-dot--running { background: var(--brand-base); animation: pulse 1.5s infinite; }
.status-dot--blocked { background: #FBBF24; }
.status-dot--done { background: #34D399; }
.status-dot--error { background: #EF4444; }

.status-badge {
  font-size: 0.625rem;
  padding: 0.125rem 0.375rem;
  border-radius: 9999px;
  font-weight: 500;
}

.status-badge--idle { background: rgba(255, 255, 255, 0.1); color: var(--text-muted); }
.status-badge--running { background: rgba(74, 128, 240, 0.15); color: var(--brand-base); }
.status-badge--blocked { background: rgba(251, 191, 36, 0.15); color: #FBBF24; }
.status-badge--done { background: rgba(52, 211, 153, 0.15); color: #34D399; }
.status-badge--error { background: rgba(239, 68, 68, 0.15); color: #EF4444; }

.agent-card__task {
  margin-bottom: 0.5rem;
}

.task-label {
  font-size: 0.625rem;
  color: var(--text-muted);
}

.task-content {
  display: block;
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-top: 0.25rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 进度条 */
.progress-bar {
  flex: 1;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.progress-bar__fill {
  height: 100%;
  background: linear-gradient(90deg, var(--brand-base), var(--brand-hover));
  transition: width 0.3s ease;
}

.progress-label {
  font-size: 0.625rem;
  font-weight: 500;
  color: var(--brand-base);
}

/* 输出预览 */
.agent-card__output {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 0.25rem;
  padding: 0.5rem;
  margin-top: 0.5rem;
}

.output-header {
  display: flex;
  justify-content: space-between;
  font-size: 0.625rem;
  color: var(--text-muted);
  margin-bottom: 0.25rem;
}

.output-live {
  color: #EF4444;
  animation: blink 1s infinite;
}

.output-content {
  font-size: 0.625rem;
  color: var(--text-secondary);
  max-height: 60px;
  overflow: hidden;
  white-space: pre-wrap;
  word-break: break-all;
}

/* 阻塞信息 */
.agent-card__blocked {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: #FBBF24;
  margin-top: 0.5rem;
}

.blocked-icon {
  font-size: 0.875rem;
}

/* 错误信息 */
.agent-card__error {
  display: flex;
  align-items: flex-start;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: #EF4444;
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 0.25rem;
}

.error-icon {
  font-size: 0.875rem;
}

/* 活动日志 */
.activity-log {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 0.5rem;
  padding: 0.75rem;
}

.log-header {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.log-count {
  font-weight: 500;
}

.log-content {
  max-height: 150px;
  overflow-y: auto;
}

.log-item {
  display: flex;
  gap: 0.5rem;
  font-size: 0.6875rem;
  padding: 0.25rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.log-time {
  color: var(--text-muted);
  font-weight: 500;
}

.log-agent {
  color: var(--brand-base);
  min-width: 40px;
}

.log-message {
  color: var(--text-secondary);
  flex: 1;
}

.log-item--error .log-message { color: #EF4444; }
.log-item--success .log-message { color: #34D399; }
.log-item--warning .log-message { color: #FBBF24; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
</style>
