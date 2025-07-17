import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

// 从环境变量获取端口配置
const FRONTEND_PORT = process.env.FRONTEND_PORT || 2956;
const BACKEND_PORT = process.env.BACKEND_PORT || 8080;
const BACKEND_HOST = process.env.BACKEND_HOST || 'localhost';

export default defineConfig({
  plugins: [vue()],
  server: {
    port: FRONTEND_PORT,
    strictPort: true, // 如果端口被占用，不要尝试下一个端口
    proxy: {
      '^/api': {
        target: `http://${BACKEND_HOST}:${BACKEND_PORT}`,
        changeOrigin: true
      },
      '^/auth': {
        target: `http://${BACKEND_HOST}:${BACKEND_PORT}`,
        changeOrigin: true
      },
      '^/asr': {
        target: `http://${BACKEND_HOST}:${BACKEND_PORT}`,
        changeOrigin: true
      },
      '^/ws': {
        target: `ws://${BACKEND_HOST}:${BACKEND_PORT}`,
        changeOrigin: true,
        ws: true
      }
    }
  },
  define: {
    'process.env': {
      VITE_API_BASE_URL: JSON.stringify(`http://${BACKEND_HOST}:${BACKEND_PORT}`),
      VITE_WS_BASE_URL: JSON.stringify(`ws://${BACKEND_HOST}:${BACKEND_PORT}`)
    }
  }
}); 