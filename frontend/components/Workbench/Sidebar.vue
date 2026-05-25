<template>
  <aside class="w-56 h-full flex flex-col bg-gradient-to-b from-base-bg to-base-surface border-r border-base-border">
    <!-- Logo -->
    <div class="h-14 flex items-center px-4 border-b border-base-border">
      <div class="flex items-center gap-2">
        <span class="text-2xl">🎮</span>
        <span class="text-accent font-bold">Agent Studio</span>
      </div>
    </div>

    <!-- 导航菜单 -->
    <nav class="p-2 space-y-1">
      <NuxtLink
        to="/chat"
        class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-text-tertiary hover:text-accent hover:bg-accent/20 transition-all"
        active-class="!text-accent !bg-accent/30"
      >
        <span>💬</span>
        <span>需求沟通</span>
      </NuxtLink>

      <NuxtLink
        to="/workbench"
        class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-text-tertiary hover:text-accent hover:bg-accent/20 transition-all"
        active-class="!text-accent !bg-accent/30"
      >
        <span>🖥️</span>
        <span>工作台</span>
      </NuxtLink>

      <NuxtLink
        to="/admin"
        class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-text-tertiary hover:text-accent hover:bg-accent/20 transition-all"
        active-class="!text-accent !bg-accent/30"
      >
        <span>📁</span>
        <span>项目列表</span>
      </NuxtLink>
    </nav>

    <!-- 分隔线 -->
    <div class="mx-3 border-t border-base-border my-2"></div>

    <!-- 项目/Agent 树 -->
    <div class="flex-1 overflow-y-auto p-3">
      <h3 class="text-xs uppercase text-text-tertiary mb-3 font-medium tracking-wider">
        当前项目
      </h3>

      <div v-if="currentProject || workbenchStore.agents.length > 0" class="space-y-1">
        <!-- 项目名 -->
        <div v-if="currentProject" class="text-sm text-text-primary font-medium px-2 py-1">
          {{ currentProject.name }}
        </div>

        <!-- Agent 树 -->
        <AgentTree
          :agents="workbenchStore.agents.length > 0 ? workbenchStore.agents : projectAgents"
          :active-agent="activeAgent"
          @select="onAgentSelect"
        />
      </div>

      <div v-else class="text-sm text-text-tertiary px-2 py-4 text-center">
        暂无打开的项目
      </div>
    </div>

    <!-- 底部设置 -->
    <div class="p-3 border-t border-base-border">
      <button class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-text-tertiary hover:text-accent hover:bg-accent/20 transition-all">
        <span>⚙️</span>
        <span>设置</span>
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { useProjectStore } from '~/stores/project'
import { useWorkbenchStore } from '~/stores/workbench'

const projectStore = useProjectStore()
const workbenchStore = useWorkbenchStore()

const currentProject = computed(() => projectStore.current)
const activeAgent = computed(() => workbenchStore.activeAgentId)

const projectAgents = computed(() => [
  { id: 'master', name: 'Master', status: 'idle', task: '', progress: 0, parentId: null },
  { id: 'planner', name: 'Planner', status: 'idle', task: '', progress: 0, parentId: 'master' },
  { id: 'architect', name: 'Architect', status: 'idle', task: '', progress: 0, parentId: 'master' },
  { id: 'programmer', name: 'Programmer', status: 'idle', task: '', progress: 0, parentId: 'master' },
  { id: 'qa', name: 'QA', status: 'idle', task: '', progress: 0, parentId: 'master' },
])

// 点击 Agent 树节点
function onAgentSelect(agentId: string) {
  workbenchStore.setActiveAgent(agentId)
}
</script>
