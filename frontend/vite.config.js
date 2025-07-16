import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // send /api requests to your FastAPI backend
      '/api': 'https://new-dashboard-backend.onrender.com'
    }
  }
})
