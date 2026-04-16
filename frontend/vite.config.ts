import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from 'tailwindcss'
import autoprefixer from 'autoprefixer'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  css: {
    postcss: { plugins: [tailwindcss, autoprefixer] },
  },
  server: {
    port: 5173,
    proxy: {
      '/api/ws': { target: 'ws://localhost:7860', ws: true, changeOrigin: true },
      '/api': { target: 'http://localhost:7860', changeOrigin: true },
    },
  },
  build: { outDir: 'dist', sourcemap: false },
})
