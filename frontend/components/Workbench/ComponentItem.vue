<template>
  <div class="rounded-lg overflow-hidden">
    <button
      @click="$emit('toggle')"
      class="w-full flex items-center justify-between px-3 py-2 transition-all duration-200"
      :class="isDark ? 'hover:bg-[#2D2D2D]' : 'hover:bg-gray-100'"
    >
      <div class="flex items-center gap-2 text-sm" :class="isDark ? 'text-[#D1D5DB]' : 'text-[#1A1D23]'">
        <span>{{ icon }}</span>
        <span>{{ title }}</span>
        <span v-if="badge" class="px-1.5 py-0.5 text-xs rounded" :class="isDark ? 'bg-[#4A80F0]/50 text-[#60A5FA]' : 'bg-[#4A80F0]/50 text-[#4A80F0]'">
          {{ badge }}
        </span>
      </div>
      <span class="text-xs transition-transform duration-200" :class="[expanded ? 'rotate-180' : '', isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]']">
        ▼
      </span>
    </button>
    <Transition
      enter-active-class="transition-all duration-200 ease-out"
      enter-from-class="opacity-0 -translate-y-2"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition-all duration-150 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 -translate-y-2"
    >
      <div v-show="expanded" class="px-3 py-2" :class="isDark ? 'bg-[#121212]/50' : 'bg-[#F8F9FB]/50'">
        <slot />
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { useTheme } from '~/composables/useTheme'

defineProps<{
  icon: string
  title: string
  expanded: boolean
  badge?: string | number
}>()

defineEmits<{
  (e: 'toggle'): void
}>()

const { isDark } = useTheme()
</script>
