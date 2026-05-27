/**
 * 用户认证状态管理
 */
interface User {
  id: number
  email: string
  name: string
  is_active: boolean
}

interface LoginPayload {
  email: string
  password: string
}

interface RegisterPayload {
  email: string
  password: string
  name: string
}

interface TokenResponse {
  access_token: string
  token_type: string
}

export function useAuth() {
  const api = useApi()
  const user = useState<User | null>('auth-user', () => null)
  const isAuthenticated = computed(() => !!user.value)

  /**
   * 从 localStorage 加载 token 并获取用户信息
   */
  async function loadUser() {
    if (typeof window === 'undefined') return

    const token = localStorage.getItem('token')
    if (!token) {
      user.value = null
      return
    }

    try {
      const userData = await api.get<User>('/auth/me')
      user.value = userData
    } catch {
      // token 无效或过期
      localStorage.removeItem('token')
      user.value = null
    }
  }

  /**
   * 登录
   */
  async function login(payload: LoginPayload): Promise<void> {
    const data = await api.post<TokenResponse>('/auth/login', payload)
    localStorage.setItem('token', data.access_token)
    await loadUser()
  }

  /**
   * 注册
   */
  async function register(payload: RegisterPayload): Promise<void> {
    const data = await api.post<TokenResponse>('/auth/register', payload)
    localStorage.setItem('token', data.access_token)
    await loadUser()
  }

  /**
   * 登出
   */
  function logout() {
    localStorage.removeItem('token')
    user.value = null
    navigateTo('/')
  }

  /**
   * 初始化时加载用户
   */
  onMounted(() => {
    loadUser()
  })

  return {
    user,
    isAuthenticated,
    login,
    register,
    logout,
    loadUser,
  }
}
