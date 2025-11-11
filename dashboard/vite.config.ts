import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/es': {
        target: 'https://es.zippyops.com',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/es/, ''),
        secure: false,
      },
    },
  },
});



