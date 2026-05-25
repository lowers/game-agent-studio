<template>
  <div class="shrink-0 border-t p-4" :class="isDark ? 'bg-bg-primary border-border' : 'bg-white border-border'">
    <div class="max-w-3xl mx-auto flex gap-3">
      <input
        ref="inputRef"
        :value="modelValue"
        type="text"
        :placeholder="placeholder"
        :disabled="loading"
        class="flex-1 px-4 py-3 rounded-xl border text-sm transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-brand-base/20"
        :class="isDark
          ? 'bg-bg-secondary border-border text-white placeholder-text-muted focus:border-brand-base'
          : 'bg-card border-border text-text-primary placeholder-text-muted focus:border-brand-base'"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
        @keydown.enter.exact.prevent="$emit('send')"
      />
      <button
        @click="$emit('send')"
        :disabled="!modelValue.trim() || loading"
        class="px-5 rounded-xl text-sm font-medium transition-all duration-200 shrink-0"
        :class="modelValue.trim() && !loading
          ? 'bg-brand-base text-white hover:bg-brand-hover active:scale-[0.98]'
          : 'bg-gray-200 text-gray-400 cursor-not-allowed'"
      >
        {{ loading ? '思考中' : '发送' }}
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
