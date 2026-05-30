import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Прокси на сервер приложения Flask (раздел 2.5.1): запросы /api идут на backend.
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: process.env.API_TARGET || 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
})
