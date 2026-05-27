<template>
  <div class="min-h-screen flex items-center justify-center px-4" :class="isDark ? 'bg-[#111827]' : 'bg-[#F9FAFB]'">
    <div class="w-full max-w-md">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="w-16 h-16 rounded-2xl bg-accent-bg flex items-center justify-center mx-auto mb-4">
          <svg class="w-8 h-8 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
          </svg>
        </div>
        <h1 class="text-2xl font-bold" :class="isDark ? 'text-white' : 'text-[#1A1D23]'">
          Game Agent Studio
        </h1>
        <p class="text-sm mt-1" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">
          AI 驱动的游戏开发平台
        </p>
      </div>

      <!-- 表单卡片 -->
      <div class="rounded-2xl p-6 shadow-lg" :class="isDark ? 'bg-[#1F2937]' : 'bg-white'">
        <!-- 切换标签 -->
        <div class="flex mb-6 rounded-lg p-1" :class="isDark ? 'bg-[#111827]' : 'bg-[#F3F4F6]'">
          <button
            v-for="tab in tabs"
            :key="tab.value"
            class="flex-1 py-2 text-sm font-medium rounded-md transition-all duration-200"
            :class="mode === tab.value
              ? (isDark ? 'bg-[#374151] text-white' : 'bg-white text-[#1A1D23] shadow-sm')
              : (isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]')"
            @click="mode = tab.value"
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- 错误提示 -->
        <div
          v-if="error"
          class="mb-4 p-3 rounded-lg text-sm"
          :class="isDark ? 'bg-red-900/30 text-red-400' : 'bg-red-50 text-red-600'"
        >
          {{ error }}
        </div>

        <!-- 登录表单 -->
        <form v-if="mode === 'login'" @submit.prevent="handleLogin" class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-1.5" :class="isDark ? 'text-[#D1D5DB]' : 'text-[#374151]'">
              邮箱
            </label>
            <input
              v-model="loginForm.email"
              type="email"
              required
              class="w-full px-4 py-2.5 rounded-lg border text-sm transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-accent/50"
              :class="isDark
                ? 'bg-[#111827] border-[#374151] text-white placeholder-[#6B7280]'
                : 'bg-white border-[#D1D5DB] text-[#1A1D23] placeholder-[#9CA3AF]'"
              placeholder="your@email.com"
            />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1.5" :class="isDark ? 'text-[#D1D5DB]' : 'text-[#374151]'">
              密码
            </label>
            <input
              v-model="loginForm.password"
              type="password"
              required
              class="w-full px-4 py-2.5 rounded-lg border text-sm transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-accent/50"
              :class="isDark
                ? 'bg-[#111827] border-[#374151] text-white placeholder-[#6B7280]'
                : 'bg-white border-[#D1D5DB] text-[#1A1D23] placeholder-[#9CA3AF]'"
              placeholder="输入密码"
            />
          </div>
          <button
            type="submit"
            :disabled="loading"
            class="w-full py-2.5 rounded-lg text-sm font-medium transition-all duration-200 disabled:opacity-50"
            :class="isDark
              ? 'bg-[#4A80F0] text-white hover:bg-[#6B9AF5]'
              : 'bg-[#4A80F0] text-white hover:bg-[#6B9AF5]'"
          >
            {{ loading ? '登录中...' : '登录' }}
          </button>
        </form>

        <!-- 注册表单 -->
        <form v-else @submit.prevent="handleRegister" class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-1.5" :class="isDark ? 'text-[#D1D5DB]' : 'text-[#374151]'">
              用户名
            </label>
            <input
              v-model="registerForm.name"
              type="text"
              required
              class="w-full px-4 py-2.5 rounded-lg border text-sm transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-accent/50"
              :class="isDark
                ? 'bg-[#111827] border-[#374151] text-white placeholder-[#6B7280]'
                : 'bg-white border-[#D1D5DB] text-[#1A1D23] placeholder-[#9CA3AF]'"
              placeholder="你的名字"
            />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1.5" :class="isDark ? 'text-[#D1D5DB]' : 'text-[#374151]'">
              邮箱
            </label>
            <input
              v-model="registerForm.email"
              type="email"
              required
              class="w-full px-4 py-2.5 rounded-lg border text-sm transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-accent/50"
              :class="isDark
                ? 'bg-[#111827] border-[#374151] text-white placeholder-[#6B7280]'
                : 'bg-white border-[#D1D5DB] text-[#1A1D23] placeholder-[#9CA3AF]'"
              placeholder="your@email.com"
            />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1.5" :class="isDark ? 'text-[#D1D5DB]' : 'text-[#374151]'">
              密码
            </label>
            <input
              v-model="registerForm.password"
              type="password"
              required
              minlength="6"
              class="w-full px-4 py-2.5 rounded-lg border text-sm transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-accent/50"
              :class="isDark
                ? 'bg-[#111827] border-[#374151] text-white placeholder-[#6B7280]'
                : 'bg-white border-[#D1D5DB] text-[#1A1D23] placeholder-[#9CA3AF]'"
              placeholder="至少 6 位密码"
            />
          </div>
          <button
            type="submit"
            :disabled="loading"
            class="w-full py-2.5 rounded-lg text-sm font-medium transition-all duration-200 disabled:opacity-50"
            :class="isDark
              ? 'bg-[#4A80F0] text-white hover:bg-[#6B9AF5]'
              : 'bg-[#4A80F0] text-white hover:bg-[#6B9AF5]'"
          >
            {{ loading ? '注册中...' : '注册' }}
          </button>
        </form>
      </div>

      <!-- 返回首页 -->
      <div class="text-center mt-6">
        <NuxtLink
          to="/"
          class="text-sm transition-colors duration-200"
          :class="isDark ? 'text-[#9CA3AF] hover:text-white' : 'text-[#6B7280] hover:text-[#1A1D23]'"
        >
          ← 返回首页
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { isDark } = useTheme()
const { login, register, isAuthenticated } = useAuth()
const router = useRouter()

const mode = ref<'login' | 'register'>('login')
const loading = ref(false)
const error = ref('')

const tabs = [
  { label: '登录', value: 'login' as const },
  { label: '注册', value: 'register' as const },
]

const loginForm = reactive({
  email: '',
  password: '',
})

const registerForm = reactive({
  name: '',
  email: '',
  password: '',
})

// 已登录时跳转到首页
watch(isAuthenticated, (val) => {
  if (val) router.push('/')
}, { immediate: true })

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await login({ email: loginForm.email, password: loginForm.password })
  } catch (e: any) {
    error.value = e.message || '登录失败'
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  error.value = ''
  loading.value = true
  try {
    await register({
      name: registerForm.name,
      email: registerForm.email,
      password: registerForm.password,
    })
  } catch (e: any) {
    error.value = e.message || '注册失败'
  } finally {
    loading.value = false
  }
}
</script>
