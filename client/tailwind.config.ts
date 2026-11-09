import type { Config } from 'tailwindcss'

export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        kiwi: {
          // Primary Brand Green (from kiwi-icon.svg path 3 #0DAA26)
          flesh: '#0DAA26',
          'flesh-50': '#F0FDF2',
          'flesh-100': '#E4FFB0', // pastel flesh green from path 4
          'flesh-200': '#C5F87E',
          'flesh-600': '#0B8F20',
          'flesh-700': '#086E18',
          'flesh-800': '#065713',
          'flesh-900': '#04420E',

          // Electric Lime (from kiwi-icon.svg path 5 #84DD00)
          lime: '#84DD00',
          'lime-50': '#F7FFE5',
          'lime-100': '#E4FFB0',
          'lime-600': '#72BF00',
          'lime-700': '#5B9900',

          // Coral Accent (from kiwi-icon.svg path 6 #FF6767)
          coral: '#FF6767',
          'coral-50': '#FFF0F0',
          'coral-100': '#FFE0E0',
          'coral-600': '#E55252',
          'coral-700': '#C83B3B',

          // Pastel Kiwi Flesh (from kiwi-icon.svg path 4 #E4FFB0)
          pastel: '#E4FFB0',
          'pastel-50': '#F7FFE8',

          // Contrast neutrals
          rind: '#0DAA26',
          ink: '#111827',
          'ink-600': '#374151',
          'ink-muted': '#6B7280',
          surface: '#F8F9F5',
        },
      },
      fontFamily: {
        sans: ['"Host Grotesk"', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        display: ['"Unbounded"', 'sans-serif'],
        heading: ['"Host Grotesk"', 'sans-serif'],
      },
      borderRadius: {
        card: '1.25rem',
        capsule: '9999px',
      },
      boxShadow: {
        soft: '0 4px 20px -2px rgba(0, 0, 0, 0.05)',
        lift: '0 12px 32px -4px rgba(0, 0, 0, 0.09)',
        floating: '0 8px 30px -4px rgba(0, 0, 0, 0.08), 0 2px 8px -2px rgba(0, 0, 0, 0.04)',
      },
      keyframes: {
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'scale-in': {
          from: { opacity: '0', transform: 'scale(0.97)' },
          to: { opacity: '1', transform: 'scale(1)' },
        },
        'slide-up': {
          from: { opacity: '0', transform: 'translateY(6px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'fade-in': 'fade-in 0.15s ease-out',
        'scale-in': 'scale-in 0.18s cubic-bezier(0.16, 1, 0.3, 1)',
        'slide-up': 'slide-up 0.18s ease-out',
      },
    },
  },
  plugins: [],
} satisfies Config
