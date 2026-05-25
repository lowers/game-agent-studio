<template>
  <div class="flex gap-3" :class="role === 'user' ? 'flex-row-reverse' : ''">
    <!-- 头像 -->
    <div
      class="w-8 h-8 rounded-full shrink-0 flex items-center justify-center text-xs font-medium"
      :class="role === 'user' ? 'bg-brand-base text-white' : isDark ? 'bg-bg-secondary text-brand-base' : 'bg-card text-brand-base'"
    >
      {{ role === 'user' ? '我' : 'AI' }}
    </div>

    <!-- 气泡 -->
    <div
      class="py-3 px-4 text-sm leading-relaxed"
      :class="role === 'user'
        ? 'bg-brand-base text-white rounded-2xl rounded-tr-none'
        : isDark
          ? 'bg-bg-secondary text-text-primary rounded-2xl rounded-tl-none'
          : 'bg-card text-text-primary rounded-2xl rounded-tl-none'"
    >
      {{ content }}
      <span v-if="streaming" class="typing-cursor" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  role: 'user' | 'assistant'
  content: string
  streaming?: boolean
}>()

const { isDark } = useTheme()
</script>

<style scoped>
.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  background: var(--brand-base);
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: blink 1s step-end infinite;
}
@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
</style>
