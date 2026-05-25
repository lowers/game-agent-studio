/**
 * 路由认证守卫
 * 保护需要登录的页面：/admin, /workbench
 */
export default defineNuxtRouteMiddleware((to) => {
  // 仅保护特定路由
  const protectedRoutes = ['/admin', '/workbench']
  const needsAuth = protectedRoutes.some(route => to.path.startsWith(route))

  if (!needsAuth) return

  // 检查 token（兼容 SSR）
  if (typeof window === 'undefined') return

  const token = localStorage.getItem('token')
  if (!token) {
    return navigateTo('/')
  }
})
