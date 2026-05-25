export default defineNuxtConfig({
  devtools: { enabled: true },

  modules: [
    '@nuxtjs/tailwindcss',
    '@pinia/nuxt',
    '@vueuse/nuxt',
  ],

  app: {
    head: {
      title: 'Game Agent Studio',
      link: [
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Inter:wght@300;400;500;600;700&display=swap',
        },
      ],
    },
  },

  routeRules: {
    '/chat': { layout: 'default' } as Record<string, unknown>,
    '/workbench/**': { layout: 'workbench', middleware: 'auth' } as Record<string, unknown>,
    '/admin/**': { middleware: 'auth' } as Record<string, unknown>,
  },

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000/api',
      wsBase: process.env.NUXT_PUBLIC_WS_BASE || 'ws://localhost:8000/api/ws',
    },
  },

  vite: {
    server: {
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
        '/ws': {
          target: 'ws://localhost:8000',
          ws: true,
        },
      },
    },
  },

  compatibilityDate: '2025-01-01',
})
