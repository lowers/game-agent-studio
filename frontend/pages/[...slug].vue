<template>
  <div class="min-h-screen flex items-center justify-center transition-colors duration-300" :class="isDark ? 'bg-[#111827]' : 'bg-[#F9FAFB]'">
    <div class="text-center">
      <div class="text-8xl font-bold mb-4" :class="isDark ? 'text-[#374151]' : 'text-[#E5E7EB]'">404</div>
      <h1 class="text-xl font-medium mb-2" :class="isDark ? 'text-white' : 'text-[#1A1D23]'">页面未找到</h1>
      <p class="text-sm mb-8" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">
        你访问的页面 {{ $route.path }} 不存在
      </p>
      <NuxtLink
        to="/"
        class="inline-block px-5 py-2.5 rounded-xl text-sm font-medium text-white bg-[#4A80F0] hover:bg-[#6B9AF5] transition-all duration-200 active:scale-[0.98]"
      >
        返回首页
      </NuxtLink>
    </div>
  </div>
</template>

<script setup lang="ts">
const { isDark } = useTheme()
</script>
