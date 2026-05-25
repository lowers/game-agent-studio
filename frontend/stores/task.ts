import { defineStore } from 'pinia'

export interface Task {
  id: number
  module_id: number
  name: string
  status: 'todo' | 'in_progress' | 'review' | 'done'
  assigned_agent: string | null
  priority: number
  dependencies: number[]
  created_at: string
}

export const useTaskStore = defineStore('task', () => {
  const tasks = ref<Task[]>([])
  const loading = ref(false)

  const { get, post, patch, del } = useApi()

  async function fetchByProject(projectId: number) {
    loading.value = true
    try {
      tasks.value = await get<Task[]>(`/projects/${projectId}/tasks`)
    } finally {
      loading.value = false
    }
  }

  async function create(data: { module_id: number; name: string; assigned_agent?: string; priority?: number }) {
    const t = await post<Task>('/tasks/', data)
    tasks.value.push(t)
    return t
  }

  async function update(id: number, data: Partial<Task>) {
    const t = await patch<Task>(`/tasks/${id}`, data)
    const idx = tasks.value.findIndex(x => x.id === id)
    if (idx !== -1) tasks.value[idx] = t
    return t
  }

  async function remove(id: number) {
    await del(`/tasks/${id}`)
    tasks.value = tasks.value.filter(x => x.id !== id)
  }

  return { tasks, loading, fetchByProject, create, update, remove }
})
