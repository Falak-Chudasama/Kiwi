import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        kiwi: {
          flesh: '#7FB240',
          'flesh-600': '#6C9A35',
          'flesh-700': '#5A812B',
          'flesh-50': '#F1F7E8',
          'flesh-100': '#E2EFD1',
          shell: '#86592F',
          'shell-600': '#714B28',
          'shell-50': '#F5EEE6',
          zest: '#B7D118',
          'zest-600': '#9DB414',
          cream: '#EDE6AF',
          'cream-100': '#F5F1D7',
          ink: '#303030',
          'ink-600': '#454545',
        },
      },
      fontFamily: {
        heading: ['Quicksand', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        body: ['Outfit', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        card: '1.5rem',
      },
      boxShadow: {
        soft: '0 8px 30px -12px rgba(48, 48, 48, 0.18)',
        lift: '0 16px 40px -14px rgba(48, 48, 48, 0.28)',
      },
      keyframes: {
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'pop-in': {
          from: { opacity: '0', transform: 'scale(0.96) translateY(6px)' },
          to: { opacity: '1', transform: 'scale(1) translateY(0)' },
        },
        'slide-up': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'fade-in': 'fade-in 0.15s ease-out',
        'pop-in': 'pop-in 0.18s cubic-bezier(0.16, 1, 0.3, 1)',
        'slide-up': 'slide-up 0.2s ease-out',
      },
    },
  },
  plugins: [],
} satisfies Config
