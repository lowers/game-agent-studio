<template>
  <div class="flex flex-col h-full" :class="isDark ? 'dark' : ''">
    <!-- 头部 -->
    <div class="h-14 flex items-center justify-between px-4 border-b transition-colors duration-200" :class="isDark ? 'border-[#2D2D2D]' : 'border-[#E5E7EB]'">
      <h2 class="font-semibold flex items-center gap-2" :class="isDark ? 'text-white' : 'text-[#1A1D23]'">
        <span>📖</span>
        <span>LLM Wiki</span>
      </h2>
      <button @click="refreshWiki" class="transition-colors duration-200" :class="isDark ? 'text-[#9CA3AF] hover:text-[#60A5FA]' : 'text-[#6B7280] hover:text-[#4A80F0]'">
        🔄
      </button>
    </div>

    <!-- 搜索栏 -->
    <div class="p-4 space-y-3 border-b transition-colors duration-200" :class="isDark ? 'border-[#2D2D2D]' : 'border-[#E5E7EB]'">
      <div class="flex gap-2">
        <input
          v-model="searchQuery"
          @keyup.enter="searchWiki"
          type="text"
          placeholder="搜索错误关键词..."
          class="flex-1 px-3 py-2 rounded-lg border transition-all duration-200 focus:outline-none focus:ring-2"
          :class="isDark
            ? 'bg-[#1E1E1E] border-[#2D2D2D] text-white placeholder-[#9CA3AF] focus:border-[#4A80F0] focus:ring-[#4A80F0]/20'
            : 'bg-white border-[#E5E7EB] text-[#1A1D23] placeholder-[#9CA3AF] focus:border-[#4A80F0] focus:ring-[#4A80F0]/20'"
        />
        <button
          @click="searchWiki()"
          class="px-4 py-2 rounded-lg transition-all duration-200 text-white font-medium text-sm"
          :class="isDark ? 'bg-[#60A5FA] hover:bg-[#93C5FD]' : 'bg-[#4A80F0] hover:bg-[#6B9AF5]'"
        >
          搜索
        </button>
      </div>

      <!-- 筛选器 -->
      <div class="flex gap-2 flex-wrap">
        <select
          v-model="selectedType"
          @change="searchWiki()"
          class="px-3 py-2 rounded-lg border transition-all duration-200 focus:outline-none text-sm"
          :class="isDark
            ? 'bg-[#1E1E1E] border-[#2D2D2D] text-[#D1D5DB] focus:border-[#4A80F0]'
            : 'bg-white border-[#E5E7EB] text-[#6B7280] focus:border-[#4A80F0]'"
        >
          <option value="">全部类型</option>
          <option v-for="type in errorTypes" :key="type.value" :value="type.value">
            {{ type.label }}
          </option>
        </select>

        <select
          v-model="selectedAgent"
          @change="searchWiki()"
          class="px-3 py-2 rounded-lg border transition-all duration-200 focus:outline-none text-sm"
          :class="isDark
            ? 'bg-[#1E1E1E] border-[#2D2D2D] text-[#D1D5DB] focus:border-[#4A80F0]'
            : 'bg-white border-[#E5E7EB] text-[#6B7280] focus:border-[#4A80F0]'"
        >
          <option value="">全部 Agent</option>
          <option value="master">Master</option>
          <option value="planner">Planner</option>
          <option value="architect">Architect</option>
          <option value="programmer">Programmer</option>
          <option value="qa">QA</option>
          <option value="security">Security</option>
          <option value="devops">DevOps</option>
        </select>
      </div>
    </div>

    <!-- 统计概览 -->
    <div v-if="stats" class="p-4 border-b transition-colors duration-200" :class="isDark ? 'border-[#2D2D2D]' : 'border-[#E5E7EB]'">
      <div class="grid grid-cols-2 gap-3">
        <div class="p-3 rounded-lg" :class="isDark ? 'bg-[#1E1E1E]' : 'bg-[#F8F9FB]'">
          <div class="text-2xl font-bold" :class="isDark ? 'text-[#60A5FA]' : 'text-[#4A80F0]'">{{ stats.total_entries }}</div>
          <div class="text-xs" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">总条目数</div>
        </div>
        <div class="p-3 rounded-lg" :class="isDark ? 'bg-[#1E1E1E]' : 'bg-[#F8F9FB]'">
          <div class="text-2xl font-bold text-yellow-400">{{ stats.avg_occurrence }}</div>
          <div class="text-xs" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">平均出现次数</div>
        </div>
      </div>
    </div>

    <!-- 条目列表 -->
    <div class="flex-1 overflow-y-auto scrollbar-thin">
      <div v-if="loading" class="p-8 text-center" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">
        <div class="animate-spin inline-block mr-2">⏳</div>
        加载 Wiki 中...
      </div>

      <div v-else-if="entries.length === 0" class="p-8 text-center" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">
        <div class="text-4xl mb-4">📚</div>
        <p>暂无 Wiki 条目</p>
        <p class="text-sm mt-1">错误记录会自动同步到这里</p>
      </div>

      <div v-else class="divide-y" :class="isDark ? 'divide-[#2D2D2D]' : 'divide-[#E5E7EB]'">
        <div
          v-for="entry in entries"
          :key="entry.id"
          @click="selectEntry(entry)"
          class="p-4 cursor-pointer transition-all duration-150"
          :class="[
            selectedEntry?.id === entry.id ? (isDark ? 'bg-[#4A80F0]/10' : 'bg-[#4A80F0]/10') : '',
            isDark ? 'hover:bg-[#2D2D2D]' : 'hover:bg-[#F8F9FB]'
          ]"
        >
          <div class="flex items-start justify-between gap-2">
            <h3 class="font-medium text-sm leading-relaxed" :class="isDark ? 'text-[#F9FAFB]' : 'text-[#1A1D23]'">{{ entry.error_title }}</h3>
            <span
              class="flex-shrink-0 text-xs px-2 py-0.5 rounded"
              :class="getBadgeClass(entry.error_type)"
            >
              {{ getBadgeLabel(entry.error_type) }}
            </span>
          </div>
          <p class="text-sm mt-1 leading-relaxed" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">{{ entry.error_description }}</p>
          <div class="flex items-center gap-2 mt-2 text-xs" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">
            <span>{{ entry.occurrence_count }} 次</span>
            <span v-if="entry.related_agent" class="px-2 py-0.5 rounded" :class="isDark ? 'bg-[#2D2D2D]' : 'bg-[#F3F4F6]'">#{{ entry.related_agent }}</span>
            <span class="ml-auto">{{ formatDate(entry.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 详情面板 -->
    <div v-if="selectedEntry" class="border-t transition-colors duration-200" :class="isDark ? 'border-[#2D2D2D]' : 'border-[#E5E7EB]'">
      <div class="p-4">
        <div class="flex items-center justify-between mb-3">
          <h3 class="font-semibold" :class="isDark ? 'text-white' : 'text-[#1A1D23]'">修复方案</h3>
          <button @click="selectedEntry = null" class="transition-colors duration-200" :class="isDark ? 'text-[#9CA3AF] hover:text-white' : 'text-[#6B7280] hover:text-[#1A1D23]'">✕</button>
        </div>

        <div class="space-y-3">
          <!-- 原始错误 -->
          <div class="p-3 rounded-lg" :class="isDark ? 'bg-[#2D2D2D] border border-[#EF4444]/20' : 'bg-[#FEE2E2] border border-[#EF4444]/20'">
            <div class="text-xs mb-1" :class="isDark ? 'text-[#EF4444]' : 'text-[#EF4444]'">❌ 错误</div>
            <p class="text-sm leading-relaxed" :class="isDark ? 'text-[#F9FAFB]' : 'text-[#1A1D23]'">{{ selectedEntry.error_description }}</p>
            <pre v-if="selectedEntry.code_snippet" class="mt-2 p-2 rounded text-xs overflow-x-auto" :class="isDark ? 'bg-[#121212] text-[#D1D5DB]' : 'bg-[#F8F9FB] text-[#6B7280]'">{{ selectedEntry.code_snippet }}</pre>
          </div>

          <!-- 修复方案 -->
          <div class="p-3 rounded-lg" :class="isDark ? 'bg-[#2D2D2D] border border-[#059669]/20' : 'bg-[#ECFDF5] border border-[#059669]/20'">
            <div class="text-xs mb-1" :class="isDark ? 'text-[#10B981]' : 'text-[#059669]'">✅ 修复</div>
            <p class="text-sm leading-relaxed" :class="isDark ? 'text-[#F9FAFB]' : 'text-[#1A1D23]'">{{ selectedEntry.fix_description }}</p>
            <pre v-if="selectedEntry.fix_code_snippet" class="mt-2 p-2 rounded text-xs overflow-x-auto" :class="isDark ? 'bg-[#121212] text-[#D1D5DB]' : 'bg-[#F8F9FB] text-[#6B7280]'">{{ selectedEntry.fix_code_snippet }}</pre>
          </div>

          <!-- 反馈 -->
          <div class="flex gap-2 pt-2">
            <button
              @click="submitFeedback(selectedEntry.id, true)"
              class="flex-1 py-2 rounded-lg transition-all duration-200 text-sm font-medium"
              :class="isDark ? 'bg-[#059669]/10 text-[#10B981] hover:bg-[#059669]/20' : 'bg-[#059669]/10 text-[#059669] hover:bg-[#059669]/20'"
            >
              👍 有帮助
            </button>
            <button
              @click="submitFeedback(selectedEntry.id, false)"
              class="flex-1 py-2 rounded-lg transition-all duration-200 text-sm font-medium"
              :class="isDark ? 'bg-[#EF4444]/10 text-[#EF4444] hover:bg-[#EF4444]/20' : 'bg-[#EF4444]/10 text-[#EF4444] hover:bg-[#EF4444]/20'"
            >
              👎 无帮助
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useApi } from '~/composables/useApi'
import { useTheme } from '~/composables/useTheme'

const api = useApi()
const { isDark } = useTheme()

const entries = ref<any[]>([])
const stats = ref<any>(null)
const selectedEntry = ref<any>(null)
const loading = ref(false)
const searchQuery = ref('')
const selectedType = ref('')
const selectedAgent = ref('')

const errorTypes = [
  { value: 'syntax', label: '语法错误' },
  { value: 'logic', label: '逻辑错误' },
  { value: 'security', label: '安全问题' },
  { value: 'performance', label: '性能问题' },
  { value: 'architecture', label: '架构问题' },
  { value: 'api_integration', label: 'API 集成' },
  { value: 'database', label: '数据库' },
  { value: 'dependency', label: '依赖问题' },
  { value: 'other', label: '其他' },
]

// 加载 Wiki 条目
async function loadWiki() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (searchQuery.value) params.append('search', searchQuery.value)
    if (selectedType.value) params.append('error_type', selectedType.value)
    if (selectedAgent.value) params.append('related_agent', selectedAgent.value)
    params.append('limit', '50')

    const data = await api.get(`/wiki?${params.toString()}`) as any
    entries.value = data.items || []
  } catch (e) {
    console.error('加载 Wiki 失败:', e)
  } finally {
    loading.value = false
  }
}

// 加载统计数据
async function loadStats() {
  try {
    stats.value = await api.get('/wiki/stats')
  } catch (e) {
    console.error('加载统计失败:', e)
  }
}

// 搜索
function searchWiki() {
  loadWiki()
}

// 刷新
function refreshWiki() {
  loadWiki()
  loadStats()
}

// 选择条目
function selectEntry(entry: any) {
  selectedEntry.value = selectedEntry.value?.id === entry.id ? null : entry
}

// 提交反馈
async function submitFeedback(entryId: number, helpful: boolean) {
  try {
    await api.post(`/wiki/${entryId}/feedback?helpful=${helpful}`, null)
    // 更新本地数据
    const entry = entries.value.find(e => e.id === entryId)
    if (entry) {
      entry.helpfulness_score = Math.min(1, Math.max(0, entry.helpfulness_score + (helpful ? 0.1 : -0.05)))
    }
  } catch (e) {
    console.error('提交反馈失败:', e)
  }
}

// 辅助函数
function getBadgeClass(type: string): string {
  const colors: Record<string, string> = {
    syntax: 'bg-red-500/20 text-red-500',
    logic: 'bg-orange-500/20 text-orange-500',
    security: 'bg-red-600/20 text-red-600',
    performance: 'bg-yellow-500/20 text-yellow-500',
    architecture: 'bg-purple-500/20 text-purple-500',
    api_integration: 'bg-blue-500/20 text-blue-500',
    database: 'bg-green-600/20 text-green-600',
    dependency: 'bg-pink-500/20 text-pink-500',
    other: 'bg-gray-500/20 text-gray-400',
  }
  return colors[type] || 'bg-gray-500/20 text-gray-400'
}

function getBadgeLabel(type: string): string {
  return errorTypes.find(t => t.value === type)?.label || type
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

onMounted(() => {
  loadWiki()
  loadStats()
})
</script>
