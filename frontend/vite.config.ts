import { defineConfig, type Plugin } from 'vite'
import vue from '@vitejs/plugin-vue'
import { brotliCompressSync, gzipSync } from 'node:zlib'

function compressAssets(): Plugin {
  return {
    name: 'compress-assets',
    apply: 'build',
    generateBundle(_opts, bundle) {
      for (const name of Object.keys(bundle)) {
        const item = bundle[name]
        let source: string | undefined
        if (item.type === 'chunk') source = item.code
        else if (item.type === 'asset' && typeof item.source === 'string') source = item.source
        if (source === undefined || source.length < 1024) continue
        const buf = Buffer.from(source, 'utf8')
        this.emitFile({ type: 'asset', fileName: `${name}.gz`, source: gzipSync(buf) })
        this.emitFile({ type: 'asset', fileName: `${name}.br`, source: brotliCompressSync(buf) })
      }
    },
  }
}

export default defineConfig({
  plugins: [vue(), compressAssets()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.indexOf('node_modules') !== -1) {
            if (/[\\/](vue|vue-router|pinia)[\\/]/.test(id)) return 'vue-vendor'
            return 'vendor'
          }
        },
      },
    },
  },
  server: {
    host: true,
    port: 5173,
    allowedHosts: ['.monkeycode-ai.online'],
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
})
