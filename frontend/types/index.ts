export interface Project {
  id: number
  name: string
  description: string | null
  status: 'draft' | 'active' | 'archived'
  complexity: 'simple' | 'medium' | 'complex'
  created_at: string
  updated_at: string
}

export interface Module {
  id: number
  project_id: number
  name: string
  description: string | null
  order: number
}

export interface Task {
  id: number
  module_id: number
  name: string
  status: 'todo' | 'in_progress' | 'review' | 'done'
  assigned_agent: 'planner' | 'architect' | 'programmer' | 'qa' | null
  priority: number
  dependencies: number[]
  created_at: string
}

export interface AgentMemory {
  id: number
  project_id: number
  trigger_keywords: string[]
  positive_pattern: string
  negative_pattern: string
  confidence: number
  created_at: string
  last_used_at: string | null
  usage_count: number
}

export interface Feedback {
  id: number
  task_id: number
  content: string
  type: 'bug' | 'suggestion' | 'praise'
  attachment: Record<string, any> | null
  created_at: string
}

export interface Build {
  id: number
  project_id: number
  version: string
  build_url: string | null
  platform: 'web' | 'unity' | 'unreal'
  status: 'pending' | 'success' | 'failed'
  log: string | null
  created_at: string
}

export interface DesignDoc {
  game_type: string
  protagonist: string
  core_gameplay: string
  enemies_collectibles: string
  win_condition: string
}

// === Agent 相关类型 ===

export type AgentRole = 'planner' | 'architect' | 'programmer' | 'qa'

export type AgentStatus = 'idle' | 'running' | 'blocked' | 'done' | 'error'

// 扩展的 Agent 状态信息
export interface AgentState {
  name: string                    // 中文名：策划/架构/程序/QA
  role: AgentRole                 // 英文标识
  status: AgentStatus
  task: string                    // 当前执行的任务描述
  progress: number                // 0-100 进度
  output_preview: string          // 当前输出预览（打字机效果）
  dependencies: AgentRole[]       // 依赖哪些 Agent
  blocked_by: AgentRole | null   // 被谁阻塞
  error_message: string | null
  started_at: string | null
  estimated_time: number | null   // 预估剩余时间（秒）
}

// Agent 相关信息（预设配置）
export interface AgentInfo {
  role: AgentRole
  name: string
  description: string
  color: string                   // UI 颜色
  icon: string                    // 图标
}

// === 对话状态类型 ===

export type ConversationState =
  | 'initial'
  | 'gathering_idea'
  | 'clarify_game_type'
  | 'clarify_core_mechanics'
  | 'clarify_characters'
  | 'clarify_visual'
  | 'clarify_technical'
  | 'evaluating'
  | 'refine_with_issues'
  | 'finalizing'
  | 'complete'

// 可行性评估信息
export interface EvaluationInfo {
  complexity_score: number        // 0-100
  complexity_label: string        // 简单/中等/复杂/非常复杂
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  is_feasible: boolean
  issues: Array<{
    severity: 'critical' | 'warning' | 'info'
    message: string
    suggestion: string
  }>
  warnings: string[]
  suggestions: string[]
}

// 对话消息
export interface ConversationMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  inquiry_topic?: string          // 问询主题
  evaluation?: EvaluationInfo     // 附加的评估信息
}

// === WebSocket 消息类型 ===

export interface WSMessage {
  type: string
  data?: any
}

// Agent 输出流消息
export interface AgentOutputMessage {
  type: 'agent_output'
  data: {
    agent: AgentRole
    chunk: string
    is_final: boolean
  }
}

// Agent 进度更新消息
export interface AgentProgressMessage {
  type: 'agent_progress'
  data: {
    agent: AgentRole
    progress: number
    message: string
  }
}

// Agent 阻塞/解锁消息
export interface AgentBlockedMessage {
  type: 'agent_blocked' | 'agent_unblocked'
  data: {
    agent: AgentRole
    blocked_by?: AgentRole
    reason?: string
  }
}

// Agent 状态更新消息
export interface AgentStatusMessage {
  type: 'agent_status'
  data: AgentState
}

// 工作流状态消息
export interface WorkflowStatusMessage {
  type: 'workflow_started' | 'workflow_completed' | 'workflow_error'
  data: {
    workflow_id?: string
    error?: string
  }
}

// === Agent 主动对话类型 ===

// Agent 向用户提问消息
export interface AgentQuestionMessage {
  type: 'agent_question'
  data: {
    agent: AgentRole
    question: string
    options: string[]        // 可选选项
    question_id?: string    // 问题ID，用于提交答案
  }
}

// 用户反馈消息
export interface UserFeedbackMessage {
  type: 'agent_feedback'
  data: {
    agent: AgentRole
    answer: string
    question_id?: string    // 如果有ID则优先使用
  }
}

// 扩展的消息角色类型
export type MessageRole = 'user' | 'assistant' | 'system' | 'agent_question' | 'agent_suggestion' | 'system_notification'

// 扩展的对话消息（支持 Agent 主动提问）
export interface ExtendedConversationMessage {
  id: string
  role: MessageRole
  content: string
  timestamp: string
  agent?: AgentRole                 // 如果是 Agent 消息，指明来源
  inquiry_topic?: string             // 问询主题
  evaluation?: EvaluationInfo       // 附加的评估信息
  options?: string[]                 // 如果是提问，显示选项
  question_id?: string               // 问题ID，用于提交答案
  requires_response?: boolean        // 是否需要用户回复
  metadata?: Record<string, any>     // 附加元数据
}

// 工作流状态类型
export type WorkflowStatus = 'idle' | 'running' | 'paused' | 'waiting_user' | 'completed' | 'interrupted' | 'error'

// 工作流上下文
export interface WorkflowContext {
  workflow_id: string
  status: WorkflowStatus
  agents: Record<AgentRole, AgentState>
  current_question?: AgentQuestionMessage['data']
}

// 任务状态消息
export interface TaskMessage {
  type: 'task_updated' | 'task_created'
  data: Task
}

// === Agent 树相关类型 ===

export type ExtendedAgentStatus = 'idle' | 'running' | 'waiting' | 'done' | 'error' | 'blocked'

export interface AgentNode {
  id: string
  name: string
  role: string
  agent_type: 'master' | 'parent' | 'child'
  status: ExtendedAgentStatus
  parent_id: string | null
  children: string[]
  current_task: string
  output: string
  progress: number
}

export interface AgentTreeData {
  nodes: AgentNode[]
  root_ids: string[]
}

// 聊天消息
export interface ChatMessage {
  type: 'chat_message'
  data: {
    agent: string
    content: string
    session_id?: string
  }
}

// 项目概要
export interface ProjectSummary {
  type: 'project_summary'
  data: {
    name: string
    description: string
    game_type: string
    core_mechanics: string[]
    target_users?: string
    complexity: 'simple' | 'medium' | 'complex'
    suggested_agents: string[]
  }
}

// 聊天模式状态
export interface ChatModeStatus {
  type: 'chat_mode'
  data: {
    state: 'clarifying' | 'confirmed' | 'ready'
    question?: string
    options?: string[]
  }
}

// Agent 树更新
export interface AgentTreeUpdate {
  type: 'agent_tree_update'
  data: AgentTreeData
}

// 确认开发请求
export interface ConfirmDevelopRequest {
  type: 'confirm_develop'
  data: {
    session_id: string
    approved: boolean
    modifications?: string
  }
}

// 统一的工作台消息类型
export type WorkbenchMessage =
  | AgentOutputMessage
  | AgentProgressMessage
  | AgentBlockedMessage
  | AgentStatusMessage
  | WorkflowStatusMessage
  | AgentQuestionMessage
  | ChatMessage
  | ProjectSummary
  | ChatModeStatus
  | AgentTreeUpdate
  | TaskMessage
