<template>
  <div class="rounded-2xl border overflow-hidden shadow-sm" :class="isDark ? 'bg-[#1E1E1E] border-[#2D2D2D]' : 'bg-white border-[#E5E7EB]'">
    <!-- 面板标题 -->
    <div class="px-4 py-3 border-b flex items-center justify-between" :class="isDark ? 'border-[#2D2D2D]' : 'border-[#E5E7EB]'">
      <h3 class="text-sm font-medium flex items-center gap-2" :class="isDark ? 'text-[#F9FAFB]' : 'text-[#1A1D23]'">
        <span>📦</span> 组件
      </h3>
      <button
        @click="toggleAll"
        class="text-xs transition-colors duration-200"
        :class="isDark ? 'text-[#60A5FA] hover:text-[#93C5FD]' : 'text-[#4A80F0] hover:text-[#6B9AF5]'"
      >
        {{ allExpanded ? '收起全部' : '展开全部' }}
      </button>
    </div>

    <!-- 组件列表 -->
    <div class="p-2 space-y-1 max-h-64 overflow-y-auto scrollbar-thin">
      <!-- 浏览器变更 -->
      <ComponentItem
        icon="🌐"
        title="浏览器变更"
        :expanded="expanded['browser']"
        @toggle="expanded['browser'] = !expanded['browser']"
      >
        <div class="space-y-1 text-xs">
          <div class="flex items-center gap-2" :class="isDark ? 'text-status-green' : 'text-status-green'">
            <span>~</span>
            <span>index.html</span>
            <span :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">第23行修改</span>
          </div>
          <div class="flex items-center gap-2" :class="isDark ? 'text-[#60A5FA]' : 'text-[#4A80F0]'">
            <span>+</span>
            <span>style.css</span>
            <span :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">新增样式</span>
          </div>
        </div>
      </ComponentItem>

      <!-- 文件变更 -->
      <ComponentItem
        icon="📁"
        title="文件变更"
        :expanded="expanded['files']"
        @toggle="expanded['files'] = !expanded['files']"
      >
        <div class="space-y-1 text-xs">
          <div class="flex items-center gap-2" :class="isDark ? 'text-status-green' : 'text-status-green'">
            <span>+</span>
            <span>src/main.py</span>
          </div>
          <div class="flex items-center gap-2" :class="isDark ? 'text-status-yellow' : 'text-status-yellow'">
            <span>~</span>
            <span>src/config.py</span>
          </div>
          <div class="flex items-center gap-2" :class="isDark ? 'text-status-red' : 'text-status-red'">
            <span>-</span>
            <span>src/old.py</span>
          </div>
        </div>
      </ComponentItem>

      <!-- 任务进度 -->
      <ComponentItem
        icon="📊"
        title="任务进度"
        :expanded="expanded['progress']"
        @toggle="expanded['progress'] = !expanded['progress']"
      >
        <div class="space-y-2 text-xs">
          <div>
            <div class="flex justify-between mb-1">
              <span :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">整体进度</span>
              <span :class="isDark ? 'text-[#60A5FA]' : 'text-[#4A80F0]'">80%</span>
            </div>
            <div class="h-2 rounded-full overflow-hidden" :class="isDark ? 'bg-[#2D2D2D]' : 'bg-gray-200'">
              <div
                class="h-full rounded-full transition-all duration-500"
                :class="isDark ? 'bg-[#60A5FA]' : 'bg-[#4A80F0]'"
                style="width: 80%"
              ></div>
            </div>
          </div>
          <div class="flex justify-between" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">
            <span>已用时</span>
            <span>12:34</span>
          </div>
        </div>
      </ComponentItem>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  isDark?: boolean
}>()

const expanded = ref({
  browser: false,
  files: true,
  progress: false,
})

const allExpanded = computed(() => Object.values(expanded.value).every(v => v))

function toggleAll() {
  const newVal = !allExpanded.value
  Object.keys(expanded.value).forEach(k => {
    expanded.value[k as keyof typeof expanded.value] = newVal
  })
}
</script>
