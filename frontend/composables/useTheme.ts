import { ref, onMounted, onUnmounted } from 'vue'

// 模块级 ref，所有组件共享同一个主题状态
const isDark = ref(false)
const isInitialized = ref(false)

let listeners: (() => void)[] = []

function notifyListeners() {
  listeners.forEach(fn => fn())
}

function applyTheme(dark: boolean) {
  isDark.value = dark
  if (process.client) {
    if (dark) {
      document.documentElement.setAttribute('data-theme', 'dark')
    } else {
      document.documentElement.removeAttribute('data-theme')
    }
  }
}

function readTheme(): boolean {
  if (!process.client) return false
  const saved = localStorage.getItem('theme')
  if (saved === 'dark') return true
  if (saved === 'light') return false
  // 跟随系统偏好
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

export function useTheme() {
  function sync() {
    applyTheme(readTheme())
  }

  function toggleTheme() {
    if (!process.client) return
    const newValue = !isDark.value
    localStorage.setItem('theme', newValue ? 'dark' : 'light')
    applyTheme(newValue)
    // 触发 storage 事件，让同页面其他实例同步
    window.dispatchEvent(new StorageEvent('storage', {
      key: 'theme',
      newValue: newValue ? 'dark' : 'light',
    }))
  }

  function setTheme(dark: boolean) {
    if (!process.client) return
    localStorage.setItem('theme', dark ? 'dark' : 'light')
    applyTheme(dark)
    window.dispatchEvent(new StorageEvent('storage', {
      key: 'theme',
      newValue: dark ? 'dark' : 'light',
    }))
  }

  onMounted(() => {
    if (!isInitialized.value) {
      sync()
      isInitialized.value = true
    }

    const handler = (e: StorageEvent) => {
      if (e.key === 'theme') {
        sync()
      }
    }
    window.addEventListener('storage', handler)

    // 监听系统主题变化
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const mediaHandler = (e: MediaQueryListEvent) => {
      const saved = localStorage.getItem('theme')
      if (!saved) {
        applyTheme(e.matches)
      }
    }
    mediaQuery.addEventListener('change', mediaHandler)

    return () => {
      window.removeEventListener('storage', handler)
      mediaQuery.removeEventListener('change', mediaHandler)
    }
  })

  return {
    isDark,
    toggleTheme,
    setTheme,
  }
}
