import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
// @ts-expect-error Development-only middleware is intentionally kept outside the browser TypeScript graph.
import { m2InternalDevPlugin } from './m2-internal-dev-plugin.mjs'

export default defineConfig(({ mode }) => {
  const internalEnv = loadEnv(mode, '.', 'M2_')

  return {
    plugins: [
      react(),
      m2InternalDevPlugin({
        root: internalEnv.M2_INTERNAL_ROOT,
        sqlitePath: internalEnv.M2_SQLITE_PATH,
      }),
    ],
    server: {
      host: '127.0.0.1',
      port: 5173,
    },
  }
})

