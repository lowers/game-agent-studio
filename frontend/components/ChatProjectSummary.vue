<template>
  <div class="p-5 rounded-2xl border" :class="isDark ? 'bg-[#111827] border-[#374151]' : 'bg-white border-[#E5E7EB]'">
    <h3 class="text-sm font-medium mb-4 text-accent">项目概要确认</h3>
    <div class="grid grid-cols-2 gap-3 text-xs mb-5">
      <div>
        <span :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">名称</span>
        <p class="mt-0.5" :class="isDark ? 'text-white' : 'text-[#1A1D23]'">{{ summary.name }}</p>
      </div>
      <div>
        <span :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">类型</span>
        <p class="mt-0.5" :class="isDark ? 'text-white' : 'text-[#1A1D23]'">{{ summary.game_type }}</p>
      </div>
      <div>
        <span :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">复杂度</span>
        <p class="mt-0.5" :class="isDark ? 'text-white' : 'text-[#1A1D23]'">{{ complexityLabel }}</p>
      </div>
      <div v-if="summary.suggested_agents?.length">
        <span :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">所需 Agent</span>
        <p class="mt-0.5" :class="isDark ? 'text-white' : 'text-[#1A1D23]'">{{ summary.suggested_agents.join(', ') }}</p>
      </div>
    </div>
    <div class="flex gap-3">
      <button
        class="flex-1 py-2.5 rounded-xl text-sm font-medium text-white transition-all duration-200 bg-[#4A80F0] hover:bg-[#6B9AF5] active:scale-[0.98]"
        @click="$emit('confirm')"
      >
        确认开发
      </button>
      <button
        class="flex-1 py-2.5 rounded-xl text-sm font-medium transition-all duration-200"
        :class="isDark ? 'bg-[#1F2937] text-[#D1D5DB] hover:bg-[#374151]' : 'bg-[#F3F4F6] text-[#6B7280] hover:bg-[#E5E7EB]'"
        @click="$emit('modify')"
      >
        修改需求
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  summary: { name: string; game_type: string; complexity?: string; suggested_agents?: string[] }
}>()

defineEmits<{
  confirm: []
  modify: []
}>()

const { isDark } = useTheme()

const complexityMap: Record<string, string> = { simple: '简单', medium: '中等', complex: '复杂' }
const complexityLabel = computed(() => complexityMap[props.summary.complexity || ''] || props.summary.complexity || '')
</script>
