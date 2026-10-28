import { execFileSync } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const webRoot = path.dirname(fileURLToPath(import.meta.url))
execFileSync('python', [path.join(webRoot, '..', 'packaging', 'sync_frontend_version.py')], {
  cwd: path.join(webRoot, '..'),
  stdio: 'inherit',
})

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8765',
        changeOrigin: true,
      },
    },
  },
})
