<template>
  <div class="task-timeline">
    <!-- 头部时间轴 -->
    <div class="timeline-header">
      <div class="task-name-col">任务</div>
      <div class="timeline-axis">
        <div
          v-for="tick in timeTicks"
          :key="tick"
          class="time-tick"
          :style="{ left: tick + '%' }"
        >
          {{ formatTick(tick) }}
        </div>
      </div>
    </div>

    <!-- 任务行 -->
    <div class="timeline-body">
      <div
        v-for="task in tasksWithPosition"
        :key="task.id"
        class="task-row"
      >
        <div class="task-name-col">
          <div class="task-name" :title="task.name">
            <span class="task-status-dot" :class="'status-' + task.status"></span>
            {{ task.name }}
          </div>
          <div class="task-agent" v-if="task.assigned_agent">
            {{ getAgentLabel(task.assigned_agent) }}
          </div>
        </div>
        <div class="timeline-track">
          <!-- 任务条 -->
          <div
            class="task-bar"
            :class="'status-' + task.status"
            :style="{
              left: task.start_offset + '%',
              width: task.duration + '%'
            }"
            :title="getTaskTooltip(task)"
          >
            <span class="task-bar-label">{{ (task as any).progress ?? 0 }}%</span>
          </div>
          <!-- 依赖连线 -->
          <svg
            v-if="task.dependencies && task.dependencies.length > 0"
            class="dependency-lines"
          >
            <defs>
              <marker
                id="arrowhead"
                markerWidth="10"
                markerHeight="7"
                refX="9"
                refY="3.5"
                orient="auto"
              >
                <polygon points="0 0, 10 3.5, 0 7" fill="#6366f1" />
              </marker>
            </defs>
            <line
              v-for="dep in getDependencyLines(task)"
              :key="dep.id"
              :x1="dep.x1 + '%'"
              :y1="dep.y1"
              :x2="dep.x2 + '%'"
              :y2="dep.y2"
              class="dependency-line"
            />
          </svg>
        </div>
      </div>
    </div>

    <!-- 图例 -->
    <div class="timeline-legend">
      <div class="legend-item" v-for="s in statusLegend" :key="s.status">
        <span class="legend-dot" :class="'status-' + s.status"></span>
        {{ s.label }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Task, AgentRole } from '~/types'

interface Props {
  tasks: Task[]
  startTime?: Date
  endTime?: Date
}

const props = withDefaults(defineProps<Props>(), {
  startTime: () => new Date(),
  endTime: () => new Date(Date.now() + 3600000) // 默认1小时后
})

// 状态图例
const statusLegend = [
  { status: 'todo', label: '待处理' },
  { status: 'in_progress', label: '进行中' },
  { status: 'review', label: '审核中' },
  { status: 'done', label: '已完成' }
]

// Agent 标签
const agentLabels: Record<AgentRole, string> = {
  planner: '策划',
  architect: '架构',
  programmer: '程序',
  qa: 'QA'
}

const getAgentLabel = (role: string) => agentLabels[role as AgentRole] || role

// 时间刻度
const timeTicks = computed(() => {
  const ticks: number[] = []
  for (let i = 0; i <= 100; i += 25) {
    ticks.push(i)
  }
  return ticks
})

const formatTick = (tick: number) => {
  const ms = props.startTime.getTime() +
    (props.endTime.getTime() - props.startTime.getTime()) * tick / 100
  const date = new Date(ms)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

// 任务位置计算
const tasksWithPosition = computed(() => {
  const totalMs = props.endTime.getTime() - props.startTime.getTime()

  return props.tasks.map((task, index) => {
    // 模拟任务的开始时间和持续时间
    const baseOffset = (index * 15) // 每个任务间隔 15%
    const duration = task.status === 'done' ? 20 : 15 // 已完成的任务显示更长

    return {
      ...task,
      start_offset: Math.min(baseOffset, 90),
      duration: duration,
      rowY: index * 48 + 24 // 用于依赖连线计算
    }
  })
})

// 依赖连线
const getDependencyLines = (task: any) => {
  if (!task.dependencies || task.dependencies.length === 0) return []

  const lines: any[] = []
  const taskIndex = props.tasks.findIndex(t => t.id === task.id)

  task.dependencies.forEach((depId: number) => {
    const depIndex = props.tasks.findIndex(t => t.id === depId)
    if (depIndex >= 0) {
      const depTask = tasksWithPosition.value[depIndex]
      lines.push({
        id: `${depId}-${task.id}`,
        x1: depTask.start_offset + depTask.duration,
        y1: depIndex * 48 + 24,
        x2: task.start_offset,
        y2: taskIndex * 48 + 24
      })
    }
  })

  return lines
}

const getTaskTooltip = (task: Task) => {
  return `${task.name}\n状态: ${statusLegend.find(s => s.status === task.status)?.label}\n优先级: ${task.priority}`
}
</script>

<style scoped>
.task-timeline {
  background: var(--bg-secondary, #1a1a2e);
  border-radius: 12px;
  padding: 16px;
  font-family: 'JetBrains Mono', monospace;
}

.timeline-header {
  display: flex;
  border-bottom: 1px solid rgba(99, 102, 241, 0.2);
  padding-bottom: 8px;
  margin-bottom: 8px;
}

.task-name-col {
  width: 200px;
  flex-shrink: 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

.timeline-axis {
  flex: 1;
  position: relative;
  height: 20px;
}

.time-tick {
  position: absolute;
  transform: translateX(-50%);
  font-size: 10px;
  color: rgba(255, 255, 255, 0.4);
}

.timeline-body {
  min-height: 200px;
}

.task-row {
  display: flex;
  align-items: center;
  height: 48px;
  border-bottom: 1px solid rgba(99, 102, 241, 0.1);
}

.task-row:last-child {
  border-bottom: none;
}

.task-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.9);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.task-status-dot.status-todo { background: #64748b; }
.task-status-dot.status-in_progress { background: #3b82f6; animation: pulse 2s infinite; }
.task-status-dot.status-review { background: #f59e0b; }
.task-status-dot.status-done { background: #10b981; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.task-agent {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 2px;
}

.timeline-track {
  flex: 1;
  position: relative;
  height: 32px;
  background: rgba(99, 102, 241, 0.05);
  border-radius: 4px;
}

.task-bar {
  position: absolute;
  top: 4px;
  height: 24px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.task-bar:hover {
  transform: scaleY(1.1);
  filter: brightness(1.2);
}

.task-bar.status-todo {
  background: linear-gradient(90deg, #475569, #64748b);
}

.task-bar.status-in_progress {
  background: linear-gradient(90deg, #1d4ed8, #3b82f6);
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.task-bar.status-review {
  background: linear-gradient(90deg, #d97706, #f59e0b);
}

.task-bar.status-done {
  background: linear-gradient(90deg, #059669, #10b981);
}

.task-bar-label {
  font-size: 10px;
  color: white;
  font-weight: 500;
}

.dependency-lines {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.dependency-line {
  stroke: #6366f1;
  stroke-width: 2;
  stroke-dasharray: 4 2;
  fill: none;
  marker-end: url(#arrowhead);
  opacity: 0.6;
}

.timeline-legend {
  display: flex;
  gap: 16px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(99, 102, 241, 0.2);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.6);
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 3px;
}

.legend-dot.status-todo { background: #64748b; }
.legend-dot.status-in_progress { background: #3b82f6; }
.legend-dot.status-review { background: #f59e0b; }
.legend-dot.status-done { background: #10b981; }
</style>
