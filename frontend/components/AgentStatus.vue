<template>
  <div class="flex items-center gap-3 px-3 py-2.5 rounded bg-bg/50 border border-brand-dim/15">
    <div
      :class="[
        'w-2.5 h-2.5 rounded-full flex-shrink-0',
        statusColor,
        status === 'working' ? 'agent-pulse' : '',
      ]"
    />
    <div class="flex-1 min-w-0">
      <div class="font-medium text-sm text-text-primary">{{ agentName }}</div>
      <div v-if="task" class="text-xs text-text-muted truncate mt-0.5">{{ task }}</div>
    </div>
    <span class="text-xs font-medium" :class="statusTextColor">{{ statusLabel }}</span>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  agentName: string
  status: 'idle' | 'working' | 'done' | 'error'
  task?: string
}>()

const statusColor = computed(() => {
  switch (props.status) {
    case 'working': return 'bg-brand-base'
    case 'done': return 'bg-green-500'
    case 'error': return 'bg-red-500'
    default: return 'bg-text-muted'
  }
})

const statusTextColor = computed(() => {
  switch (props.status) {
    case 'working': return 'text-brand-base'
    case 'done': return 'text-green-500'
    case 'error': return 'text-red-500'
    default: return 'text-text-muted'
  }
})

const statusLabel = computed(() => {
  switch (props.status) {
    case 'working': return '运行中'
    case 'done': return '完成'
    case 'error': return '错误'
    default: return '空闲'
  }
})
</script>
