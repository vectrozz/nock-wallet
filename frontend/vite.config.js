import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    open: false,  // Ne pas ouvrir le navigateur automatiquement
    watch: {
      usePolling: true  // Nécessaire pour le hot-reload dans Docker
    }
  },
  root: '.',
  build: {
    outDir: 'dist',
    rollupOptions: {
      input: {
        main: './index.html'
      }
    }
  }
})