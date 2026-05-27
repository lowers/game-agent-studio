<template>
  <div class="flex gap-3" :class="role === 'user' ? 'flex-row-reverse' : ''">
    <!-- 头像 -->
    <div
      class="w-8 h-8 rounded-full shrink-0 flex items-center justify-center text-xs font-medium"
      :class="role === 'user' ? 'bg-brand-base text-white' : isError ? 'bg-red-500/10 text-red-500' : isDark ? 'bg-[#00f0ff]/10 text-[#00f0ff]' : 'bg-card text-brand-base'"
    >
      {{ role === 'user' ? '我' : isError ? '!' : 'AI' }}
    </div>

    <!-- 气泡 -->
    <div
      class="py-3 px-4 text-sm leading-relaxed max-w-[80%]"
      :class="bubbleClasses"
    >
      <div v-if="isError" class="flex items-start gap-2">
        <svg class="w-5 h-5 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
        </svg>
        <div>
          <p class="font-medium mb-1">{{ errorTitle }}</p>
          <p class="text-xs opacity-80">{{ errorMessage }}</p>
        </div>
      </div>
      <template v-else>
        {{ content }}
        <span v-if="streaming" class="typing-cursor" />
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  role: 'user' | 'assistant'
  content: string
  streaming?: boolean
}>()

const { isDark } = useTheme()

const isError = computed(() => {
  return props.role === 'assistant' && props.content.startsWith('错误：')
})

const errorTitle = computed(() => {
  if (!isError.value) return ''
  const message = props.content.replace('错误：', '')
  if (message.includes('timeout') || message.includes('超时')) {
    return '请求超时'
  }
  if (message.includes('network') || message.includes('网络')) {
    return '网络错误'
  }
  if (message.includes('API') || message.includes('api')) {
    return 'API 错误'
  }
  if (message.includes('empty') || message.includes('空')) {
    return '输入错误'
  }
  return '发生错误'
})

const errorMessage = computed(() => {
  if (!isError.value) return ''
  const message = props.content.replace('错误：', '')
  if (message.includes('timeout') || message.includes('超时')) {
    return 'AI 响应时间过长，请稍后重试或检查网络连接。'
  }
  if (message.includes('network') || message.includes('网络')) {
    return '无法连接到服务器，请检查网络连接后重试。'
  }
  if (message.includes('API') || message.includes('api')) {
    return 'API 调用失败，请检查 API Key 配置是否正确。'
  }
  if (message.includes('empty') || message.includes('空')) {
    return '消息不能为空，请输入内容后重试。'
  }
  return message
})

const bubbleClasses = computed(() => {
  if (isError.value) {
    return isDark.value
      ? 'bg-red-500/10 text-red-400 border border-red-500/20 rounded-2xl rounded-tl-none'
      : 'bg-red-50 text-red-600 border border-red-200 rounded-2xl rounded-tl-none'
  }
  if (props.role === 'user') {
    return 'bg-brand-base text-white rounded-2xl rounded-tr-none'
  }
  return isDark.value
    ? 'bg-[#1a1a2e] text-white rounded-2xl rounded-tl-none border border-[#1a1a2e]'
    : 'bg-card text-text-primary rounded-2xl rounded-tl-none'
})
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
