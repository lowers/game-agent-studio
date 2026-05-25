<template>
  <div class="flex gap-3">
    <div
      class="w-8 h-8 rounded-full shrink-0 flex items-center justify-center text-xs font-medium"
      :class="isDark ? 'bg-bg-secondary text-brand-base' : 'bg-card text-brand-base'"
    >
      AI
    </div>
    <div class="py-3 px-4 rounded-2xl rounded-tl-none" :class="isDark ? 'bg-bg-secondary' : 'bg-card'">
      <div class="flex items-center gap-1">
        <span class="text-xs" :class="isDark ? 'text-text-muted' : 'text-text-muted'">正在思考</span>
        <span class="flex gap-0.5">
          <span class="w-1 h-1 rounded-full animate-bounce" :class="isDark ? 'bg-brand-base' : 'bg-brand-base'" style="animation-delay:0s" />
          <span class="w-1 h-1 rounded-full animate-bounce" :class="isDark ? 'bg-brand-base' : 'bg-brand-base'" style="animation-delay:0.15s" />
          <span class="w-1 h-1 rounded-full animate-bounce" :class="isDark ? 'bg-brand-base' : 'bg-brand-base'" style="animation-delay:0.3s" />
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { isDark } = useTheme()
</script>
