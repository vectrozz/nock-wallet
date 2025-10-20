import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    host: '0.0.0.0', // Expose to network
    port: 3000,
    open: true
  }
})