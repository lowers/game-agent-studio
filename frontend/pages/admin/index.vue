<template>
  <div class="max-w-7xl mx-auto px-4 py-6" :class="isDark ? 'bg-[#121212]' : 'bg-[#F8F9FB]'">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-xl font-semibold" :class="isDark ? 'text-[#F9FAFB]' : 'text-[#1A1D23]'">管理后台</h1>
      <RetroButton variant="primary" @click="showCreate = true">新建项目</RetroButton>
    </div>

    <!-- Create project modal -->
    <div v-if="showCreate" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div class="rounded-2xl p-6 w-full max-w-md border"
        :class="isDark ? 'bg-[#1E1E1E] border-[#2D2D2D]' : 'bg-white border-[#E5E7EB]'">
        <h3 class="text-sm font-medium mb-4" :class="isDark ? 'text-[#60A5FA]' : 'text-[#4A80F0]'">新建项目</h3>
        <input
          v-model="newName"
          class="w-full rounded-xl px-3 py-2 text-sm outline-none mb-3 border transition-colors"
          :class="isDark
            ? 'bg-[#121212] border-[#2D2D2D] text-[#F9FAFB] placeholder-[#9CA3AF] focus:border-[#4A80F0]'
            : 'bg-[#F8F9FB] border-[#E5E7EB] text-[#1A1D23] placeholder-[#9CA3AF] focus:border-[#4A80F0]'"
          placeholder="项目名称"
        />
        <textarea
          v-model="newDesc"
          class="w-full rounded-xl px-3 py-2 text-sm outline-none mb-4 h-20 resize-none border transition-colors"
          :class="isDark
            ? 'bg-[#121212] border-[#2D2D2D] text-[#F9FAFB] placeholder-[#9CA3AF] focus:border-[#4A80F0]'
            : 'bg-[#F8F9FB] border-[#E5E7EB] text-[#1A1D23] placeholder-[#9CA3AF] focus:border-[#4A80F0]'"
          placeholder="项目描述（可选）"
        />
        <div class="flex gap-2 justify-end">
          <RetroButton @click="showCreate = false">取消</RetroButton>
          <RetroButton variant="primary" :disabled="!newName.trim()" @click="handleCreate">创建</RetroButton>
        </div>
      </div>
    </div>

    <!-- Stats row -->
    <div class="grid grid-cols-4 gap-3 mb-6">
      <BentoCard v-for="stat in stats" :key="stat.label">
        <div class="text-center">
          <div class="font-medium text-2xl" :class="stat.color">{{ stat.value }}</div>
          <div class="text-xs mt-1" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">{{ stat.label }}</div>
        </div>
      </BentoCard>
    </div>

    <!-- Main content -->
    <div class="grid grid-cols-3 gap-3">
      <!-- Project list -->
      <BentoCard title="项目列表" :col-span="2" class="max-h-[500px] overflow-y-auto">
        <div class="space-y-2">
          <div
            v-for="p in project.projects"
            :key="p.id"
            class="flex items-center justify-between px-3 py-2.5 rounded-lg transition-colors cursor-pointer group"
            :class="isDark ? 'bg-[#121212]/50 hover:bg-[#2D2D2D]' : 'bg-[#F8F9FB]/50 hover:bg-[#F3F4F6]'"
            @click="navigateTo(`/workbench/${p.id}`)"
          >
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-sm truncate" :class="isDark ? 'text-[#F9FAFB]' : 'text-[#1A1D23]'">{{ p.name }}</span>
                <span :class="['px-1.5 py-0.5 rounded text-[10px] font-medium', statusClass(p.status)]">{{ p.status }}</span>
              </div>
              <div class="text-xs mt-0.5 truncate" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">{{ p.description || '无描述' }}</div>
            </div>
            <div class="flex items-center gap-3">
              <span class="text-xs font-medium" :class="isDark ? 'text-[#D97706]' : 'text-[#D97706]'">{{ p.complexity }}</span>
              <span class="text-xs" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">{{ formatDate(p.created_at) }}</span>
              <button
                class="opacity-0 group-hover:opacity-100 text-xs transition-opacity"
                :class="isDark ? 'text-red-400 hover:text-red-300' : 'text-red-500 hover:text-red-600'"
                @click.stop="handleDelete(p.id)"
              >
                删除
              </button>
            </div>
          </div>
          <div v-if="project.projects.length === 0" class="text-center text-sm py-8" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">
            暂无项目，点击右上角创建
          </div>
        </div>
      </BentoCard>

      <!-- Agent panel -->
      <BentoCard title="Agent 面板">
        <div class="space-y-3">
          <div
            v-for="agent in agentList"
            :key="agent.id"
            class="px-3 py-2.5 rounded-lg border transition-colors"
            :class="isDark
              ? 'bg-[#121212]/50 border-[#4A80F0]/10 hover:border-[#4A80F0]/25'
              : 'bg-[#F8F9FB]/50 border-[#4A80F0]/10 hover:border-[#4A80F0]/25'"
          >
            <div class="flex items-center gap-2">
              <div class="w-2 h-2 rounded-full" :class="isDark ? 'bg-[#9CA3AF]' : 'bg-[#6B7280]'" />
              <span class="font-medium text-sm" :class="isDark ? 'text-[#F9FAFB]' : 'text-[#1A1D23]'">{{ agent.name }}</span>
            </div>
            <div class="text-xs mt-1 ml-4" :class="isDark ? 'text-[#9CA3AF]' : 'text-[#6B7280]'">{{ agent.description }}</div>
          </div>
        </div>
      </BentoCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useProjectStore } from '~/stores/project'

const project = useProjectStore()
const showCreate = ref(false)
const newName = ref('')
const newDesc = ref('')
const { isDark } = useTheme()

const stats = computed(() => [
  { label: '总项目', value: project.projects.length, color: isDark.value ? 'text-[#60A5FA]' : 'text-brand-base' },
  { label: '进行中', value: project.projects.filter(p => p.status === 'active').length, color: isDark.value ? 'text-[#FBBF24]' : 'text-[#D97706]' },
  { label: '已完成', value: project.projects.filter(p => p.status === 'archived').length, color: isDark.value ? 'text-[#34D399]' : 'text-[#059669]' },
  { label: '草稿', value: project.projects.filter(p => p.status === 'draft').length, color: isDark.value ? 'text-[#9CA3AF]' : 'text-[#6B7280]' },
])

const agentList = [
  { id: 'planner', name: '策划 Agent', description: '需求分析、任务拆分' },
  { id: 'architect', name: '架构 Agent', description: '技术选型、API 设计' },
  { id: 'programmer', name: '程序 Agent', description: '代码生成、功能实现' },
  { id: 'qa', name: 'QA Agent', description: '测试用例、质量检查' },
]

function statusClass(status: string) {
  if (isDark.value) {
    if (status === 'active') return 'bg-[rgba(251,191,36,0.15)] text-[#FBBF24]'
    if (status === 'archived') return 'bg-[rgba(52,211,153,0.15)] text-[#34D399]'
    return 'bg-[rgba(156,163,175,0.15)] text-[#9CA3AF]'
  }
  if (status === 'active') return 'bg-[rgba(217,119,6,0.1)] text-[#D97706]'
  if (status === 'archived') return 'bg-[rgba(5,150,105,0.1)] text-[#059669]'
  return 'bg-gray-100 text-[#6B7280]'
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

async function handleCreate() {
  if (!newName.value.trim()) return
  const p = await project.create(newName.value.trim(), newDesc.value.trim() || undefined, {
    auto_start_workflow: true,
  })
  newName.value = ''
  newDesc.value = ''
  showCreate.value = false
  navigateTo(`/workbench/${p.id}?autoStartWorkflow=true`, { replace: true })
}

async function handleDelete(id: number) {
  if (confirm('确定删除此项目？')) {
    await project.remove(id)
  }
}

onMounted(() => {
  project.fetchAll()
})
</script>
