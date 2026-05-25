import type { Config } from 'tailwindcss'

export default {
  content: [
    './components/**/*.{vue,js,ts}',
    './layouts/**/*.vue',
    './pages/**/*.vue',
    './composables/**/*.{js,ts}',
    './app.vue',
  ],
  theme: {
    extend: {
      colors: {
        // 品牌色 - OKLCH 色彩系统
        brand: {
          base: 'var(--brand-base, oklch(0.65 0.18 250))',
          hover: 'var(--brand-hover, oklch(0.55 0.18 250))',
          dim: 'var(--brand-dim, oklch(0.45 0.15 250))',
          bg: 'var(--brand-bg, oklch(0.90 0.06 250))',
        },
        // 使用 CSS 变量，支持主题切换
        accent: {
          DEFAULT: 'var(--color-accent)',
          light: 'var(--color-accent-light)',
          bg: 'var(--color-accent-bg)',
        },
        'text': {
          primary: 'var(--color-text-primary)',
          secondary: 'var(--color-text-secondary)',
          tertiary: 'var(--color-text-tertiary)',
          inverse: 'var(--color-text-inverse)',
        },
        'bg': {
          primary: 'var(--color-bg-primary)',
          secondary: 'var(--color-bg-secondary)',
          surface: 'var(--color-bg-surface)',
          tertiary: 'var(--color-bg-tertiary)',
          border: 'var(--color-bg-border)',
          'border-light': 'var(--color-bg-border-light)',
        },
        'status': {
          green: 'oklch(0.65 0.20 150)',
          yellow: 'oklch(0.75 0.16 85)',
          red: 'oklch(0.60 0.22 30)',
        },
      },
      fontFamily: {
        sans: ['Inter', '"Noto Sans SC"', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        sm: '6px',
        DEFAULT: '8px',
        md: '12px',
        lg: '16px',
        xl: '20px',
        '2xl': '24px',
        'card': '16px',
      },
      boxShadow: {
        soft: '0 1px 3px oklch(0 0 0 / 0.04), 0 1px 2px oklch(0 0 0 / 0.02)',
        card: '0 2px 8px oklch(0 0 0 / 0.05)',
        pop: '0 4px 16px oklch(0 0 0 / 0.08), 0 2px 8px oklch(0 0 0 / 0.04)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-dot': 'pulseDot 1.4s ease-in-out infinite',
        'shimmer': 'shimmer 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseDot: {
          '0%, 100%': { opacity: '0.4' },
          '50%': { opacity: '1' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
    },
  },
  plugins: [],
} satisfies Config
