// Dev server launcher: `npm run dev -- --port 5174 --api-port 8001 [--mode demo]`
// Any other arguments are forwarded to vite.
import { spawn } from 'node:child_process'
import { createRequire } from 'node:module'
import { dirname, join } from 'node:path'

const require = createRequire(import.meta.url)
const viteBin = join(
  dirname(require.resolve('vite/package.json')),
  'bin/vite.js'
)

const args = process.argv.slice(2)
const forwarded = []
const env = { ...process.env }

for (let i = 0; i < args.length; i++) {
  const arg = args[i]
  const match = /^--api-port(?:=(.*))?$/.exec(arg)
  if (match) {
    const value = match[1] ?? args[++i]
    if (!/^\d+$/.test(value ?? '')) {
      console.error(`--api-port requires a numeric port, got "${value}"`)
      process.exit(1)
    }
    env.API_PORT = value
  } else {
    forwarded.push(arg)
  }
}

// Fail instead of silently moving to another port when --port is taken.
if (forwarded.some((a) => a === '--port' || a.startsWith('--port='))) {
  forwarded.push('--strictPort')
}

const child = spawn(process.execPath, [viteBin, ...forwarded], {
  stdio: 'inherit',
  env,
})
child.on('exit', (code, signal) => process.exit(code ?? (signal ? 1 : 0)))
for (const sig of ['SIGINT', 'SIGTERM']) {
  process.on(sig, () => child.kill(sig))
}
