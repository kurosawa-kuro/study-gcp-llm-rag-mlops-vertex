import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../api/static',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/query': 'http://localhost:8080',
      '/ingest': 'http://localhost:8080',
      '/health': 'http://localhost:8080',
    },
  },
})
