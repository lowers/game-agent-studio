<template>
  <div class="min-h-screen transition-colors duration-300" :class="isDark ? 'bg-[#111827]' : 'bg-[#F9FAFB]'">
    <!-- 顶部导航 -->
    <nav class="flex items-center justify-between px-6 py-3 border-b" :class="isDark ? 'border-[#374151]' : 'border-[#E5E7EB]'">
      <div class="flex items-center gap-3">
        <NuxtLink
          to="/"
          class="p-2 rounded-lg transition-colors duration-200"
          :class="isDark ? 'hover:bg-[#374151] text-[#9CA3AF]' : 'hover:bg-[#F3F4F6] text-[#6B7280]'"
        >
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
        </NuxtLink>
        <h1 class="text-lg font-semibold" :class="isDark ? 'text-white' : 'text-[#1A1D23]'">设置</h1>
      </div>
    </nav>

    <div class="max-w-2xl mx-auto px-6 py-8 space-y-6">
      <!-- 用户信息卡片 -->
      <div class="rounded-2xl p-6" :class="isDark ? 'bg-[#1F2937]' : 'bg-white'">
        <h2 class="text-base font-semibold mb-4" :class="isDark ? 'text-white' : 'text-[#1A1D23]'">
          用户信息
        </h2>
        <div v-if="user" class="space-y-3">
          <div class="flex items-center justify-between py-2">
            <span class="text-sm" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">用户名</span>
            <span class="text-sm font-medium" :class="isDark ? 'text-white' : 'text-[#1A1D23]'">{{ user.name }}</span>
          </div>
          <div class="flex items-center justify-between py-2 border-t" :class="isDark ? 'border-[#374151]' : 'border-[#E5E7EB]'">
            <span class="text-sm" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">邮箱</span>
            <span class="text-sm font-medium" :class="isDark ? 'text-white' : 'text-[#1A1D23]'">{{ user.email }}</span>
          </div>
          <div class="flex items-center justify-between py-2 border-t" :class="isDark ? 'border-[#374151]' : 'border-[#E5E7EB]'">
            <span class="text-sm" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">状态</span>
            <span class="px-2 py-0.5 rounded-full text-xs font-medium" :class="user.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'">
              {{ user.is_active ? '活跃' : '已禁用' }}
            </span>
          </div>
        </div>
        <div v-else class="text-center py-4">
          <p class="text-sm" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">未登录</p>
          <NuxtLink
            to="/login"
            class="inline-block mt-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200"
            :class="isDark ? 'bg-[#4A80F0] text-white hover:bg-[#6B9AF5]' : 'bg-[#4A80F0] text-white hover:bg-[#6B9AF5]'"
          >
            去登录
          </NuxtLink>
        </div>
      </div>

      <!-- LLM 配置卡片 -->
      <div class="rounded-2xl p-6" :class="isDark ? 'bg-[#1F2937]' : 'bg-white'">
        <h2 class="text-base font-semibold mb-4" :class="isDark ? 'text-white' : 'text-[#1A1D23]'">
          LLM 配置
        </h2>
        <p class="text-sm mb-4" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">
          配置 AI 模型的 API Key 和相关参数
        </p>

        <form @submit.prevent="saveLLMConfig" class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-1.5" :class="isDark ? 'text-[#D1D5DB]' : 'text-[#374151]'">
              API Key
            </label>
            <input
              v-model="llmForm.apiKey"
              type="password"
              class="w-full px-4 py-2.5 rounded-lg border text-sm transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-accent/50"
              :class="isDark
                ? 'bg-[#111827] border-[#374151] text-white placeholder-[#6B7280]'
                : 'bg-white border-[#D1D5DB] text-[#1A1D23] placeholder-[#9CA3AF]'"
              placeholder="sk-..."
            />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1.5" :class="isDark ? 'text-[#D1D5DB]' : 'text-[#374151]'">
              Base URL（可选）
            </label>
            <input
              v-model="llmForm.baseUrl"
              type="url"
              class="w-full px-4 py-2.5 rounded-lg border text-sm transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-accent/50"
              :class="isDark
                ? 'bg-[#111827] border-[#374151] text-white placeholder-[#6B7280]'
                : 'bg-white border-[#D1D5DB] text-[#1A1D23] placeholder-[#9CA3AF]'"
              placeholder="https://api.openai.com/v1"
            />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1.5" :class="isDark ? 'text-[#D1D5DB]' : 'text-[#374151]'">
              模型名称
            </label>
            <input
              v-model="llmForm.model"
              type="text"
              class="w-full px-4 py-2.5 rounded-lg border text-sm transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-accent/50"
              :class="isDark
                ? 'bg-[#111827] border-[#374151] text-white placeholder-[#6B7280]'
                : 'bg-white border-[#D1D5DB] text-[#1A1D23] placeholder-[#9CA3AF]'"
              placeholder="gpt-4"
            />
          </div>

          <!-- 状态提示 -->
          <div
            v-if="llmStatus"
            class="p-3 rounded-lg text-sm"
            :class="llmStatus.success
              ? (isDark ? 'bg-green-900/30 text-green-400' : 'bg-green-50 text-green-600')
              : (isDark ? 'bg-red-900/30 text-red-400' : 'bg-red-50 text-red-600')"
          >
            {{ llmStatus.message }}
          </div>

          <div class="flex gap-3">
            <button
              type="submit"
              :disabled="llmSaving"
              class="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 disabled:opacity-50"
              :class="isDark ? 'bg-[#4A80F0] text-white hover:bg-[#6B9AF5]' : 'bg-[#4A80F0] text-white hover:bg-[#6B9AF5]'"
            >
              {{ llmSaving ? '保存中...' : '保存配置' }}
            </button>
            <button
              type="button"
              @click="verifyLLMConfig"
              :disabled="llmVerifying"
              class="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 disabled:opacity-50"
              :class="isDark ? 'bg-[#374151] text-[#D1D5DB] hover:bg-[#4B5563]' : 'bg-[#F3F4F6] text-[#374151] hover:bg-[#E5E7EB]'"
            >
              {{ llmVerifying ? '验证中...' : '验证连接' }}
            </button>
          </div>
        </form>
      </div>

      <!-- 迁移说明 -->
      <div class="rounded-2xl p-6" :class="isDark ? 'bg-[#1F2937]' : 'bg-white'">
        <h2 class="text-base font-semibold mb-2" :class="isDark ? 'text-white' : 'text-[#1A1D23]'">
          迁移说明
        </h2>
        <p class="text-sm" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">
          LLM 配置保存在浏览器的 localStorage 中，不会随项目迁移。迁移后需要重新配置。
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { isDark } = useTheme()
const { user, isAuthenticated } = useAuth()
const api = useApi()

// LLM 配置表单
const llmForm = reactive({
  apiKey: '',
  baseUrl: '',
  model: '',
})

const llmSaving = ref(false)
const llmVerifying = ref(false)
const llmStatus = ref<{ success: boolean; message: string } | null>(null)

// 从 localStorage 加载配置
onMounted(() => {
  if (typeof window !== 'undefined') {
    llmForm.apiKey = localStorage.getItem('llm_api_key') || ''
    llmForm.baseUrl = localStorage.getItem('llm_base_url') || ''
    llmForm.model = localStorage.getItem('llm_model') || ''
  }
})

async function saveLLMConfig() {
  llmSaving.value = true
  llmStatus.value = null
  try {
    // 保存到 localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('llm_api_key', llmForm.apiKey)
      localStorage.setItem('llm_base_url', llmForm.baseUrl)
      localStorage.setItem('llm_model', llmForm.model)
    }
    // 同步到后端
    await api.post('/llm/configure', {
      provider: 'openai',
      api_key: llmForm.apiKey,
      base_url: llmForm.baseUrl,
    })
    llmStatus.value = { success: true, message: '配置已保存' }
  } catch (e: any) {
    llmStatus.value = { success: false, message: e.message || '保存失败' }
  } finally {
    llmSaving.value = false
  }
}

async function verifyLLMConfig() {
  llmVerifying.value = true
  llmStatus.value = null
  try {
    await api.post('/llm/verify', {
      provider: 'openai',
      api_key: llmForm.apiKey,
      base_url: llmForm.baseUrl,
      model: llmForm.model,
    })
    llmStatus.value = { success: true, message: 'API Key 验证成功' }
  } catch (e: any) {
    llmStatus.value = { success: false, message: e.message || '验证失败' }
  } finally {
    llmVerifying.value = false
  }
}
</script>
