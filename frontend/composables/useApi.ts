const DEFAULT_TIMEOUT = 30000

export function useApi() {
  const config = useRuntimeConfig()
  const baseURL = config.public.apiBase as string

  async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const url = `${baseURL}${path}`
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT)

    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      // 从 localStorage 自动附加 Bearer token（兼容 SSR 无 window 环境）
      if (typeof window !== 'undefined') {
        const token = localStorage.getItem('token')
        if (token) {
          headers['Authorization'] = `Bearer ${token}`
        }
      }
      const options: RequestInit = {
        method,
        headers,
        signal: controller.signal,
      }
      if (body) options.body = JSON.stringify(body)

      const res = await fetch(url, options)
      clearTimeout(timeoutId)

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || 'Request failed')
      }
      if (res.status === 204) return undefined as T
      return res.json()
    } catch (error) {
      clearTimeout(timeoutId)
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Request timeout')
      }
      throw error
    }
  }

  return {
    get: <T>(path: string) => request<T>('GET', path),
    post: <T>(path: string, body: unknown) => request<T>('POST', path, body),
    patch: <T>(path: string, body: unknown) => request<T>('PATCH', path, body),
    del: <T>(path: string) => request<T>('DELETE', path),
  }
}
