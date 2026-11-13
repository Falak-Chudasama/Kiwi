import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5060,
    allowedHosts: ['kiwi.jam', '127.0.0.3', 'api.kiwi.jam', 'localhost'],
    proxy: {
      '/api': 'http://127.0.0.3:10000',
    },
  },
})
