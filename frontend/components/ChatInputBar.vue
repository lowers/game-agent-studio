<template>
  <div class="shrink-0 border-t p-4" :class="isDark ? 'bg-[#0d0d15]/80 backdrop-blur-sm border-[#1a1a2e]' : 'bg-white border-border'">
    <div class="max-w-3xl mx-auto flex gap-3">
      <input
        ref="inputRef"
        :value="modelValue"
        type="text"
        :placeholder="placeholder"
        :disabled="loading"
        class="flex-1 px-4 py-3 rounded-xl border text-sm transition-all duration-200 focus:outline-none"
        :class="isDark
          ? 'bg-[#1a1a2e] border-[#00f0ff]/20 text-white placeholder-[#00f0ff]/40 focus:border-[#00f0ff]/50 focus:ring-2 focus:ring-[#00f0ff]/20 neon-input'
          : 'bg-card border-border text-text-primary placeholder-text-muted focus:border-brand-base focus:ring-2 focus:ring-brand-base/20'"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
        @keydown.enter.exact.prevent="$emit('send')"
      />
      <button
        @click="$emit('send')"
        :disabled="!modelValue.trim() || loading"
        class="px-5 rounded-xl text-sm font-medium transition-all duration-200 shrink-0 relative overflow-hidden"
        :class="modelValue.trim() && !loading
          ? isDark
            ? 'bg-[#00f0ff]/10 text-[#00f0ff] border border-[#00f0ff]/30 hover:bg-[#00f0ff]/20 hover:border-[#00f0ff]/50 active:scale-[0.98]'
            : 'bg-brand-base text-white hover:bg-brand-hover active:scale-[0.98]'
          : isDark
            ? 'bg-[#1a1a2e] text-[#00f0ff]/30 border border-[#1a1a2e] cursor-not-allowed'
            : 'bg-gray-200 text-gray-400 cursor-not-allowed'"
      >
        <span class="relative z-10">{{ loading ? '思考中' : '发送' }}</span>
        <div v-if="isDark && modelValue.trim() && !loading" class="absolute inset-0 bg-gradient-to-r from-transparent via-[#00f0ff]/10 to-transparent animate-shimmer"></div>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  modelValue: string
  loading: boolean
  placeholder: string
}>()

defineEmits<{
  'update:modelValue': [value: string]
  send: []
}>()

const inputRef = ref<HTMLInputElement>()
const { isDark } = useTheme()

defineExpose({ focus: () => {
  if (inputRef.value) {
    ;(inputRef.value as HTMLInputElement).focus()
  }
} })
</script>

<style scoped>
.neon-input:focus {
  box-shadow: 0 0 10px rgba(0, 240, 255, 0.2),
              0 0 20px rgba(0, 240, 255, 0.1);
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.animate-shimmer {
  animation: shimmer 2s infinite;
}
</style>
