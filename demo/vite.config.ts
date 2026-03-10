import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const proxyConfig = {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
  '/blocks': {
    target: 'http://localhost:1234',
    changeOrigin: true,
    rewrite: (path: string) => path.replace(/^\/blocks/, ''),
  },
};

export default defineConfig({
  plugins: [react()],
  base: './',
  server: {
    proxy: proxyConfig,
  },
  preview: {
    proxy: proxyConfig,
  },
})
