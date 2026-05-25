<template>
  <button
    :class="[
      'px-4 py-2 rounded-xl text-xs font-medium transition-all duration-150 inline-flex items-center justify-center gap-1.5',
      'disabled:opacity-40 disabled:cursor-not-allowed',
      variant === 'primary'
        ? (isDark ? 'bg-[#4A80F0] text-white hover:bg-[#6B9AF5] active:scale-[0.98]'
            : 'bg-[#4A80F0] text-white hover:bg-[#6B9AF5] active:scale-[0.98]')
        : (isDark ? 'bg-[#1E1E1E] text-[#D1D5DB] hover:bg-[#2D2D2D] active:scale-[0.98]'
            : 'bg-gray-100 text-[#6B7280] hover:bg-gray-200 active:scale-[0.98]'),
    ]"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  variant?: 'default' | 'primary' | 'ghost'
}>(), {
  variant: 'default',
})

const { isDark } = useTheme()
</script>
