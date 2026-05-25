/**
 * 工作台 UI 状态管理 — Composition API 风格
 */
import { defineStore } from 'pinia'

export interface AgentNode {
  id: string
  name: string
  role: string
  status: 'idle' | 'running' | 'waiting' | 'done' | 'error' | 'blocked'
  task: string
  progress: number
  parentId: string | null
  output?: string
}

export interface ComponentChange {
  type: 'browser' | 'file' | 'progress'
  action: 'add' | 'modify' | 'delete'
  path: string
  description?: string
}

export interface WorkflowInfo {
  workflowId: string | null
  status: 'idle' | 'running' | 'paused' | 'waiting' | 'completed' | 'error'
  currentRound: number
  totalRounds: number
  executionRounds: string[][]
  expertStatus: Record<string, string>
  expertResults: Record<string, { progress: number; output: string }>
}

export const useWorkbenchStore = defineStore('workbench', () => {
  // ====== State ======
  const agents = ref<AgentNode[]>([
    { id: 'master', name: 'Master', role: 'master', status: 'idle', task: '', progress: 0, parentId: null },
    { id: 'planner', name: 'Planner', role: 'planner', status: 'idle', task: '', progress: 0, parentId: 'master' },
    { id: 'architect', name: 'Architect', role: 'architect', status: 'idle', task: '', progress: 0, parentId: 'master' },
    { id: 'programmer', name: 'Programmer', role: 'programmer', status: 'idle', task: '', progress: 0, parentId: 'master' },
    { id: 'qa', name: 'QA', role: 'qa', status: 'idle', task: '', progress: 0, parentId: 'master' },
    { id: 'security', name: 'Security', role: 'security', status: 'idle', task: '', progress: 0, parentId: 'master' },
    { id: 'devops', name: 'DevOps', role: 'devops', status: 'idle', task: '', progress: 0, parentId: 'master' },
  ])
  const activeAgentId = ref('master')
  const sessionId = ref<string | null>(null)
  const componentPanel = ref({
    browser: false,
    files: true,
    progress: false,
  })
  const fileChanges = ref<ComponentChange[]>([])
  const browserChanges = ref<ComponentChange[]>([])
  const overallProgress = ref(0)
  const sidebarExpanded = ref(true)
  const panelMode = ref<'chat' | 'workflow'>('chat')
  const workflow = ref<WorkflowInfo>({
    workflowId: null,
    status: 'idle',
    currentRound: 0,
    totalRounds: 0,
    executionRounds: [],
    expertStatus: {},
    expertResults: {},
  })

  // ====== Getters ======
  const getChildren = computed(() => (parentId: string) =>
    agents.value.filter(a => a.parentId === parentId)
  )
  const rootAgents = computed(() =>
    agents.value.filter(a => a.parentId === null)
  )
  const activeAgent = computed(() =>
    agents.value.find(a => a.id === activeAgentId.value)
  )
  const agentStats = computed(() => {
    const stats = { total: agents.value.length, running: 0, done: 0, waiting: 0, idle: 0, error: 0 }
    agents.value.forEach(a => {
      if (a.status in stats) {
        (stats as any)[a.status]++
      }
    })
    return stats
  })
  const isWorkflowRunning = computed(() => workflow.value.status === 'running')
  const isWorkflowWaiting = computed(() => workflow.value.status === 'waiting')

  // ====== Actions ======
  function initDefaultAgents() {
    agents.value = [
      { id: 'master', name: 'Master', role: 'master', status: 'idle', task: '', progress: 0, parentId: null },
      { id: 'planner', name: 'Planner', role: 'planner', status: 'idle', task: '', progress: 0, parentId: 'master' },
      { id: 'architect', name: 'Architect', role: 'architect', status: 'idle', task: '', progress: 0, parentId: 'master' },
      { id: 'programmer', name: 'Programmer', role: 'programmer', status: 'idle', task: '', progress: 0, parentId: 'master' },
      { id: 'qa', name: 'QA', role: 'qa', status: 'idle', task: '', progress: 0, parentId: 'master' },
      { id: 'security', name: 'Security', role: 'security', status: 'idle', task: '', progress: 0, parentId: 'master' },
      { id: 'devops', name: 'DevOps', role: 'devops', status: 'idle', task: '', progress: 0, parentId: 'master' },
    ]
  }

  function updateAgent(agentId: string, updates: Partial<AgentNode>) {
    const agent = agents.value.find(a => a.id === agentId)
    if (agent) Object.assign(agent, updates)
  }

  function setActiveAgent(agentId: string) {
    activeAgentId.value = agentId
  }

  function addFileChange(change: ComponentChange) {
    fileChanges.value.unshift(change)
    if (fileChanges.value.length > 50) fileChanges.value.pop()
  }

  function addBrowserChange(change: ComponentChange) {
    browserChanges.value.unshift(change)
    if (browserChanges.value.length > 50) browserChanges.value.pop()
  }

  function toggleComponent(component: keyof typeof componentPanel.value) {
    componentPanel.value[component] = !componentPanel.value[component]
  }

  function setSessionId(id: string | null) {
    sessionId.value = id
  }

  function reset() {
    initDefaultAgents()
    activeAgentId.value = 'master'
    sessionId.value = null
    fileChanges.value = []
    browserChanges.value = []
    overallProgress.value = 0
    panelMode.value = 'chat'
    resetWorkflow()
  }

  function updateFromWebSocket(data: { nodes: any[]; root_ids: string[] }) {
    if (data.nodes?.length) {
      agents.value = data.nodes.map(n => ({
        id: n.id,
        name: n.name,
        role: n.role,
        status: n.status,
        task: n.task || '',
        progress: n.progress || 0,
        parentId: n.parent_id || null,
        output: n.output,
      }))
    }
  }

  // 工作流
  function startWorkflow(wfId: string, rounds: string[][]) {
    const status: Record<string, string> = {}
    const results: Record<string, { progress: number; output: string }> = {}
    for (const round of rounds) {
      for (const eid of round) {
        status[eid] = 'idle'
        results[eid] = { progress: 0, output: '' }
      }
    }
    workflow.value = {
      workflowId: wfId,
      status: 'running',
      currentRound: 0,
      totalRounds: rounds.length,
      executionRounds: rounds,
      expertStatus: status,
      expertResults: results,
    }
  }

  function updateCurrentRound(round: number) {
    workflow.value.currentRound = round
  }

  function updateExpertStatus(expertId: string, status: string, result?: { progress: number; output: string }) {
    workflow.value.expertStatus[expertId] = status
    if (result) workflow.value.expertResults[expertId] = result
  }

  function updateWorkflowStatus(status: WorkflowInfo['status']) {
    workflow.value.status = status
  }

  function resetWorkflow() {
    workflow.value = {
      workflowId: null,
      status: 'idle',
      currentRound: 0,
      totalRounds: 0,
      executionRounds: [],
      expertStatus: {},
      expertResults: {},
    }
  }

  return {
    // State
    agents,
    activeAgentId,
    sessionId,
    componentPanel,
    fileChanges,
    browserChanges,
    overallProgress,
    sidebarExpanded,
    panelMode,
    workflow,
    // Getters
    getChildren,
    rootAgents,
    activeAgent,
    agentStats,
    isWorkflowRunning,
    isWorkflowWaiting,
    // Actions
    initDefaultAgents,
    updateAgent,
    setActiveAgent,
    addFileChange,
    addBrowserChange,
    toggleComponent,
    setSessionId,
    reset,
    updateFromWebSocket,
    startWorkflow,
    updateCurrentRound,
    updateExpertStatus,
    updateWorkflowStatus,
    resetWorkflow,
  }
})
