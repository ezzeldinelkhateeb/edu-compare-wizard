import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";
import { createProxyMiddleware } from 'http-proxy-middleware';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 5173,
    proxy: {
      '/api/health': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api\/health/, '/health')
      },
      // محاولة البورت 8001 أولاً
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        secure: false,
        configure: (proxy, options) => {
          proxy.on('error', (err, req, res) => {
            console.log('⚠️ فشل الاتصال بـ 8001، محاولة الاتصال بـ 8000...');
            // في حالة فشل 8001، جرب 8000
            const fallbackProxy = createProxyMiddleware({
              target: 'http://localhost:8000',
              changeOrigin: true,
              secure: false
            });
            fallbackProxy(req, res);
          });
        }
      }
    }
  },
  plugins: [
    react(),
    mode === 'development' &&
    componentTagger(),
  ].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
