<template>
  <div class="space-y-0.5">
    <div v-for="agent in rootAgents" :key="agent.id" class="select-none">
      <!-- Agent Row -->
      <div
        class="flex items-center gap-2 px-2 py-1.5 rounded-lg cursor-pointer transition-all duration-150"
        :class="{
          'bg-[#4A80F0]/10 text-[#4A80F0]': agent.id === activeAgent,
          [isDark ? 'hover:bg-[#2D2D2D] text-[#D1D5DB]' : 'hover:bg-gray-100 text-[#6B7280]']: agent.id !== activeAgent
        }"
        @click="toggleAgent(agent.id)"
      >
        <!-- Expand/Collapse -->
        <svg v-if="getChildren(agent.id).length > 0"
          class="w-3 h-3 transition-transform shrink-0"
          :class="{ 'rotate-90': expandedAgents.has(agent.id) }"
          fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
        </svg>
        <div v-else class="w-3 shrink-0" />

        <!-- Status Dot -->
        <span class="relative flex h-2 w-2 shrink-0">
          <span v-if="agent.status === 'running'" class="absolute inline-flex h-full w-full rounded-full bg-status-green/50 animate-ping"></span>
          <span class="relative inline-flex rounded-full h-2 w-2" :class="statusColor(agent.status)" />
        </span>

        <!-- Name -->
        <span class="text-sm truncate flex-1">{{ agent.name }}</span>

        <!-- Progress -->
        <span v-if="agent.progress > 0" class="text-xs" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">{{ agent.progress }}%</span>
      </div>

      <!-- Children -->
      <div v-if="expandedAgents.has(agent.id)" class="ml-4 pl-2 border-l" :class="isDark ? 'border-[#2D2D2D]' : 'border-gray-200'">
        <div
          v-for="child in getChildren(agent.id)"
          :key="child.id"
          class="flex items-center gap-2 px-2 py-1.5 rounded-lg cursor-pointer transition-all duration-150"
          :class="{
            'bg-[#4A80F0]/10 text-[#4A80F0]': child.id === activeAgent,
            [isDark ? 'hover:bg-[#2D2D2D] text-[#D1D5DB]' : 'hover:bg-gray-100 text-[#6B7280]']: child.id !== activeAgent
          }"
          @click="setActive(child.id)"
        >
          <span class="relative flex h-2 w-2 shrink-0">
          <span v-if="child.status === 'running'" class="absolute inline-flex h-full w-full rounded-full bg-status-green/50 animate-ping"></span>
          <span class="relative inline-flex rounded-full h-2 w-2" :class="statusColor(child.status)" />
          </span>
          <span class="text-sm truncate flex-1">{{ child.name }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Agent {
  id: string
  name: string
  status: string
  task: string
  progress: number
  parentId: string | null
}

const props = defineProps<{
  agents: Agent[]
  activeAgent: string
  isDark?: boolean
}>()

const emit = defineEmits<{
  (e: 'select', id: string): void
}>()

const expandedAgents = ref(new Set(['master']))

const rootAgents = computed(() => props.agents.filter(a => a.parentId === null))

function getChildren(parentId: string) {
  return props.agents.filter(a => a.parentId === parentId)
}

function toggleAgent(id: string) {
  if (expandedAgents.value.has(id)) {
    expandedAgents.value.delete(id)
  } else {
    expandedAgents.value.add(id)
  }
}

function setActive(id: string) {
  emit('select', id)
}

function statusColor(status: string) {
  switch (status) {
    case 'running': return 'bg-status-green'
    case 'waiting': return 'bg-status-yellow'
    case 'done': return 'bg-[#4A80F0]'
    case 'error': return 'bg-status-red'
    default: return 'bg-gray-300'
  }
}
</script>
