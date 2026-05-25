<script setup lang="ts">
import { useProjectStore } from '@/stores/project'
import { useTaskStore } from '@/stores/task'
import { useWorkbenchStore } from '@/stores/workbench'
import { useWebSocket } from '@/composables/useWebSocket'
import type { WebSocketMessage } from '@/composables/useWebSocket'
import WikiPanel from '@/components/Workbench/WikiPanel.vue'

type AgentStatus = 'idle' | 'running' | 'done' | 'error'

interface Agent {
  name: string
  role: string
  status: AgentStatus
  task: string
}

const route = useRoute()
const config = useRuntimeConfig()
const project = useProjectStore()
const tasks = useTaskStore()

const chatInput = ref('')
const previewUrl = ref('')
const runningWorkflow = ref(false)
const hasError = ref(false)
const errorMessage = ref('')
const showWikiPanel = ref(false)

const agents = ref<Agent[]>([
  { name: '策划', role: 'planner', status: 'idle', task: '' },
  { name: '架构', role: 'architect', status: 'idle', task: '' },
  { name: '程序', role: 'programmer', status: 'idle', task: '' },
  { name: 'QA', role: 'qa', status: 'idle', task: '' },
  { name: '安全', role: 'security', status: 'idle', task: '' },
  { name: '运维', role: 'devops', status: 'idle', task: '' },
])

const fileTree = ref([
  { name: 'src/', children: [
    { name: 'index.html', path: '/src/index.html' },
    { name: 'game.js', path: '/src/game.js' },
    { name: 'style.css', path: '/src/style.css' },
  ]},
  { name: 'assets/', children: [
    { name: 'sprites/', children: [] },
  ]},
])

const projectId = Number(route.params.id)

// 新版 WebSocket（传入对象格式）
const ws = useWebSocket({ projectId })

// 初始化 workbench store
const workbenchStore = useWorkbenchStore()

onMounted(async () => {
  // 初始化 workbench store
  if (workbenchStore.agents.length === 0) {
    workbenchStore.initDefaultAgents()
  }
  if (route.query.session) {
    workbenchStore.setSessionId(route.query.session as string)
  }

  try {
    await Promise.all([
      project.fetchOne(projectId),
      tasks.fetchByProject(projectId),
    ])
    hasError.value = false

    // 🔴 项目创建后自动跳转工作台：如果 URL 带有 autoStartWorkflow=true，自动触发工作流
    if (route.query.autoStartWorkflow === 'true') {
      await handleRunAgents()
      // 清除 URL 参数避免重复触发
      await navigateTo(`/workbench/${projectId}`, { replace: true })
    }
  } catch (e) {
    hasError.value = true
    errorMessage.value = e instanceof Error ? e.message : '加载失败'
  }
})

function handleAgentMessage(msg: WebSocketMessage) {
  if (!msg.data) return

  if (msg.type === 'agent_status') {
    const data = msg.data as { agent: string; status: AgentStatus; task?: string }
    const agent = agents.value.find(a => a.role === data.agent)
    if (agent) {
      agent.status = data.status
      agent.task = data.task || ''
    }
  }

  // 🔴 前端任务：AgentTree 与 WebSocket 实时同步
  if (msg.type === 'agent_tree_update') {
    const data = msg.data as { nodes: any[], root_ids: string[] }
    if (data.nodes && data.nodes.length > 0) {
      // 将后端 Agent 树数据同步到 workbench store
      workbenchStore.updateFromWebSocket(data)
    }
  }

  if (msg.type === 'task_updated' || msg.type === 'task_created') {
    tasks.fetchByProject(projectId)
  }
  if (msg.type === 'project_updated') {
    project.fetchOne(projectId)
    // 设置预览 URL
    const data = msg.data as { preview_url?: string; files?: string[] }
    if (data.preview_url) {
      previewUrl.value = `${config.public.apiBase.replace('/api', '')}${data.preview_url}`
    }
  }
  // 🔴 新增：处理项目创建事件（来自其他标签页的跳转）
  if (msg.type === 'project_created') {
    const data = msg.data as { auto_start_workflow?: boolean }
    if (data.auto_start_workflow) {
      // 自动启动工作流
      handleRunAgents()
    }
  }
  if (msg.type === 'workflow_completed') {
    runningWorkflow.value = false
    tasks.fetchByProject(projectId)
  }
  // 🔴 新增：处理文件/浏览器变更实时推送
  if (msg.type === 'file_change') {
    const data = msg.data as { path: string; action: string; description?: string }
    workbenchStore.addFileChange({
      type: 'file',
      action: data.action as 'modify' | 'add' | 'delete',
      path: data.path,
      description: data.description,
    })
  }
  if (msg.type === 'browser_change') {
    const data = msg.data as { url: string; action: string; description?: string }
    workbenchStore.addBrowserChange({
      type: 'browser',
      action: data.action as 'modify' | 'add' | 'delete',
      path: data.url,
      description: data.description,
    })
  }
}

// Visual agents data for MultiAgentVisualization component
const visualAgents = computed(() => {
  const icons: Record<string, string> = {
    planner: '📋', architect: '🏗️', programmer: '💻', qa: '🔍', security: '🔒', devops: '🚀',
    '策划': '📋', '架构': '🏗️', '程序': '💻', 'QA': '🔍', '安全': '🔒', '运维': '🚀',
  }
  const levels: Record<string, string> = {
    planner: 'L2', architect: 'L2', programmer: 'L2', qa: 'L3', security: 'L3', devops: 'L4',
    '策划': 'L2', '架构': 'L2', '程序': 'L2', 'QA': 'L3', '安全': 'L3', '运维': 'L4',
  }
  return agents.value.map(a => ({
    id: a.role,
    name: a.name,
    icon: icons[a.role] || '🤖',
    status: a.status,
    currentTask: a.task || undefined,
    x: (a.role === 'planner' || a.role === '策划' || a.role === '策划师') ? 20 :
         a.role === 'architect' || a.role === '架构' ? 50 :
         a.role === 'programmer' || a.role === '程序' ? 80 : 65,
    y: a.status === 'done' ? 85 : 60,
    level: levels[a.role] || 'L1',
    parentId: a.role !== 'planner' && a.role !== '策划' && a.role !== '策划师' ? 'master' : undefined,
  }))
})

// WebSocket listener
watch(() => ws.messages.value.length, () => {
  const last = ws.messages.value[ws.messages.value.length - 1]
  if (last) {
    handleAgentMessage(last)
  }
})

const statusCycle: TaskStatus[] = ['todo', 'in_progress', 'review', 'done']

type TaskStatus = 'todo' | 'in_progress' | 'review' | 'done'

function cycleTaskStatus(task: { id: number; status: TaskStatus }) {
  const idx = statusCycle.indexOf(task.status)
  const next = statusCycle[(idx + 1) % statusCycle.length]
  tasks.update(task.id, { status: next })
}

async function handleRunAgents() {
  // 防重复点击
  if (runningWorkflow.value) return
  if (!project.current) return

  runningWorkflow.value = true
  agents.value.forEach(a => { a.status = 'idle'; a.task = '' })

  try {
    // 🔴 迁移到新版 /workflows API
    // Step 1: 创建工作流配置
    const workflowResult = await $fetch<{ workflow_id: string; execution_rounds: string[][] }>(
      `${config.public.apiBase}/workflows`,
      {
        method: 'POST',
        body: {
          project_id: projectId,
          experts: ['planner', 'architect', 'programmer', 'qa'],
          mode: 'confirm', // 需要用户确认
          auto_start: true, // 自动启动
        },
      }
    )

    // Step 2: 如果 auto_start=false，手动触发启动
    if (!(workflowResult as any).auto_started) {
      await $fetch(
        `${config.public.apiBase}/workflows/${workflowResult.workflow_id}/start`,
        { method: 'POST' }
      )
    }

    // Step 3: 监听 WebSocket 事件获取进度
    // 已在 ws 监听器中处理 agent_status 事件

  } catch (e) {
    runningWorkflow.value = false
    errorMessage.value = e instanceof Error ? e.message : 'Agent 执行失败'
    console.error('启动工作流失败:', e)
  }
}

async function handleBuild() {
  try {
    await $fetch(`${config.public.apiBase}/projects/${projectId}/builds`, {
      method: 'POST',
      body: { platform: 'web' },
    })
  } catch (e) {
    errorMessage.value = e instanceof Error ? e.message : '构建失败'
  }
}

function handleFileSelect(node: { path?: string; name: string }) {
  // File selection handled here
}

function handleChat() {
  const text = chatInput.value.trim()
  if (!text) return
  chatInput.value = ''
  ws.send({ type: 'chat', data: { content: text } })
}

function clearError() {
  hasError.value = false
  errorMessage.value = ''
}
</script>

<template>
  <div class="h-[calc(100vh-57px)] flex flex-col relative">
  <!-- Wiki Panel Overlay -->
  <div v-if="showWikiPanel" class="absolute right-0 top-0 bottom-0 w-80 z-40">
    <WikiPanel />
  </div>
  <div v-else></div>
    <div v-if="hasError" class="absolute inset-0 bg-bg/90 flex items-center justify-center z-50">
      <div class="bg-card border border-red-500/30 rounded-card p-6 max-w-md text-center">
        <div class="text-red-400 text-2xl mb-3">⚠</div>
        <h3 class="text-text-primary font-medium mb-2">加载错误</h3>
        <p class="text-text-muted text-sm mb-4">{{ errorMessage }}</p>
        <RetroButton variant="primary" @click="clearError">重试</RetroButton>
      </div>
    </div>

    <div class="border-b border-brand-dim/20 px-6 py-2 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <NuxtLink to="/admin" class="text-text-muted hover:text-brand-base text-xs transition-colors">← 管理</NuxtLink>
        <h2 class="font-medium text-sm text-text-primary">{{ project.current?.name || '加载中...' }}</h2>
        <span :class="['status-badge', `status-badge--${project.current?.status || 'draft'}`]">
          {{ project.current?.status }}
        </span>
        <span class="text-xs text-amber-600 font-medium">{{ project.current?.complexity }}</span>
      </div>
      <div class="flex items-center gap-2">
      <RetroButton @click="handleRunAgents">运行 Agent</RetroButton>
      <RetroButton variant="primary" @click="handleBuild">构建</RetroButton>
      <RetroButton variant="ghost" @click="showWikiPanel = !showWikiPanel" class="text-amber-600">
        📖 Wiki
      </RetroButton>
      <div class="flex items-center gap-1.5 text-xs text-text-muted ml-2">
          <div :class="['w-1.5 h-1.5 rounded-full', ws.status.value === 'open' ? 'bg-brand-base' : 'bg-red-500']" />
          {{ ws.status.value === 'open' ? 'WS' : '断开' }}
        </div>
      </div>
    </div>

    <div class="flex-1 grid grid-cols-3 grid-rows-2 gap-3 p-4 min-h-0 overflow-hidden">
      <!-- Multi-Agent Real-Time Visualization -->
      <BentoCard title="AGENT COORDINATION NETWORK" class="row-span-2 overflow-y-auto">
        <MultiAgentVisualization
          :agents="visualAgents"
          theme="dark"
          class="h-full"
        />
      </BentoCard>

      <BentoCard title="GAME PREVIEW" :col-span="2">
        <div class="h-full flex items-center justify-center text-text-muted text-sm">
          <iframe
            v-if="previewUrl"
            :src="previewUrl"
            class="w-full h-full border-0 rounded"
          />
          <div v-else class="text-center">
            <div class="text-3xl mb-2 opacity-20">▶</div>
            <p class="text-xs">构建完成后预览将在此显示</p>
          </div>
        </div>
      </BentoCard>

      <BentoCard title="FILES & TASKS" :col-span="2" class="overflow-hidden">
        <div class="grid grid-cols-2 gap-4 h-full min-h-0">
          <div class="overflow-y-auto">
            <div class="text-xs text-brand-base font-medium mb-2">文件树</div>
            <FileTree :tree="fileTree" @select="handleFileSelect" />
          </div>
          <div class="overflow-y-auto">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs text-brand-base font-medium">任务</span>
              <span class="text-xs text-text-muted">{{ tasks.tasks.length }}</span>
            </div>
            <div class="space-y-1">
              <div
                v-for="task in tasks.tasks"
                :key="task.id"
                class="flex items-center gap-2 px-2 py-1.5 rounded bg-bg/50 hover:bg-card-hover transition-colors cursor-pointer text-xs"
                @click="cycleTaskStatus(task)"
              >
                <div
                  :class="[
                    'w-1.5 h-1.5 rounded-full flex-shrink-0',
                    task.status === 'done' ? 'bg-green-500' :
                    task.status === 'in_progress' ? 'bg-brand-base agent-pulse' :
                    task.status === 'review' ? 'bg-amber-500' :
                    'bg-text-muted',
                  ]"
                />
                <span class="flex-1 truncate text-text-primary">{{ task.name }}</span>
                <span class="text-text-muted text-xs px-1.5 py-0.5 rounded bg-bg/80 font-medium">
                  {{ task.assigned_agent || '-' }}
                </span>
              </div>
              <div v-if="tasks.tasks.length === 0" class="text-center text-text-muted/40 text-xs py-6">
                暂无任务
              </div>
            </div>
          </div>
        </div>
      </BentoCard>
    </div>

    <div class="border-t border-brand-dim/20 px-4 py-3 flex gap-2">
      <input
        v-model="chatInput"
        class="flex-1 bg-card border border-brand-dim/30 rounded-card px-4 py-2 text-sm text-text-primary placeholder-text-muted/40 outline-none transition-glow"
        placeholder="输入指令或反馈..."
        @keyup.enter="handleChat"
      />
      <RetroButton variant="primary" @click="handleChat">发送</RetroButton>
    </div>
  </div>
</template>
