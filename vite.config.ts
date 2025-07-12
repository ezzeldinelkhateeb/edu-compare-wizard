import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
   server: {
     host: "localhost",
     port: 5177,
     strictPort: true,
     hmr: {
       port: 5177
     },
     proxy: {
       '/api/health': {
         target: 'http://localhost:8001',
         changeOrigin: true,
         secure: false,
         timeout: 300000, // 5 minutes
         proxyTimeout: 300000, // 5 minutes
         rewrite: (path) => path.replace(/^\/api\/health/, '/health')
       },
       // توجيه جميع طلبات API إلى البورت 8001
       '/api': {
         target: 'http://localhost:8001',
         changeOrigin: true,
         secure: false,
         timeout: 300000, // 5 minutes for long-running requests
         proxyTimeout: 300000, // 5 minutes for proxy timeout
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
