<template>
  <div
    :class="[
      'rounded-2xl p-4 transition-all duration-200 border',
      isDark ? 'bg-bg-secondary border-border-secondary hover:border-border' : 'bg-bg-primary border-border hover:border-border-secondary',
      colSpanClass,
    ]"
  >
    <div v-if="title" class="flex items-center gap-2 mb-3">
      <span class="font-medium text-sm" :class="isDark ? 'text-text-secondary' : 'text-text-secondary'">{{ title }}</span>
      <div class="flex-1 h-px" :class="isDark ? 'bg-bg-tertiary' : 'bg-border'" />
    </div>
    <slot />
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  title?: string
  colSpan?: 1 | 2 | 3
}>()

const { isDark } = useTheme()

const colSpanClass = computed(() => {
  if (!props.colSpan || props.colSpan === 1) return ''
  return `col-span-${props.colSpan}`
})
</script>
