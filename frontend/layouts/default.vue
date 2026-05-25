<template>
  <div class="min-h-screen flex flex-col" :class="isDark ? 'dark' : ''">
    <!-- Nav bar -->
    <nav class="border-b px-5 py-3 flex items-center justify-between shrink-0" :class="isDark ? 'bg-[#111827] border-[#374151]' : 'bg-[#F9FAFB] border-[#E5E7EB]'">
      <NuxtLink to="/" class="flex items-center gap-2">
        <div class="w-6 h-6 rounded-full bg-[#4A80F0] flex items-center justify-center">
          <span class="text-white text-xs font-bold">G</span>
        </div>
        <span class="text-sm font-medium" :class="isDark ? 'text-white' : 'text-[#1A1D23]'">游戏开发助手</span>
      </NuxtLink>
      <div class="flex items-center gap-4">
        <NuxtLink
          to="/"
          class="text-sm transition-colors"
          :class="isDark ? 'text-[#9CA3AF] hover:text-white' : 'text-[#6B7280] hover:text-[#1A1D23]'"
          active-class="!text-[#4A80F0] font-medium"
        >
          对话
        </NuxtLink>
        <NuxtLink
          to="/admin"
          class="text-sm transition-colors"
          :class="isDark ? 'text-[#9CA3AF] hover:text-white' : 'text-[#6B7280] hover:text-[#1A1D23]'"
          active-class="!text-[#4A80F0] font-medium"
        >
          项目
        </NuxtLink>
        <!-- 主题切换按钮 -->
        <button
          @click="toggleTheme"
          class="w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-200"
          :class="isDark ? 'bg-[#2D2D2D] text-yellow-400 hover:bg-[#3D3D3D]' : 'bg-gray-100 text-[#6B7280] hover:bg-gray-200'"
          :title="isDark ? '切换到浅色主题' : '切换到深色主题'"
        >
          <span v-if="isDark" class="text-sm">☀️</span>
          <span v-else class="text-sm">🌙</span>
        </button>
      </div>
    </nav>

    <!-- Page content -->
    <main class="flex-1 min-h-0">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
const { isDark, toggleTheme } = useTheme()
</script>
