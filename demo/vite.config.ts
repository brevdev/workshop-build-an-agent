import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/blocks': {
        target: 'http://localhost:1234',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/blocks/, ''),
      },
    },
  },
})
