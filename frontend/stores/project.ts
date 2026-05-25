import { defineStore } from 'pinia'

export interface Project {
  id: number
  name: string
  description: string | null
  status: 'draft' | 'active' | 'archived'
  complexity: 'simple' | 'medium' | 'complex'
  created_at: string
  updated_at: string
}

export interface ProjectCreateOptions {
  auto_start_workflow?: boolean
}

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const current = ref<Project | null>(null)
  const loading = ref(false)

  const { get, post, patch, del } = useApi()

  async function fetchAll() {
    loading.value = true
    try {
      projects.value = await get<Project[]>('/projects/')
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id: number) {
    loading.value = true
    try {
      current.value = await get<Project>(`/projects/${id}`)
    } finally {
      loading.value = false
    }
  }

  async function create(name: string, description?: string, options?: ProjectCreateOptions) {
    const payload: any = { name, description }
    if (options?.auto_start_workflow) {
      payload.auto_start_workflow = true
    }
    const p = await post<Project>('/projects/', payload)
    projects.value.push(p)
    return p
  }

  async function update(id: number, data: Partial<Project>) {
    const p = await patch<Project>(`/projects/${id}`, data)
    const idx = projects.value.findIndex(x => x.id === id)
    if (idx !== -1) projects.value[idx] = p
    if (current.value?.id === id) current.value = p
    return p
  }

  async function remove(id: number) {
    await del(`/projects/${id}`)
    projects.value = projects.value.filter(x => x.id !== id)
    if (current.value?.id === id) current.value = null
  }

  return { projects, current, loading, fetchAll, fetchOne, create, update, remove }
})
