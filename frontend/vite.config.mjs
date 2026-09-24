import { execSync } from 'node:child_process'
import { existsSync, readFileSync } from 'node:fs'
import { isAbsolute, resolve } from 'node:path'
import { fileURLToPath, URL } from 'node:url'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify'

function readGitCommit() {
  const run = (cmd) =>
    execSync(cmd, { stdio: ['ignore', 'pipe', 'ignore'] })
      .toString()
      .trim()
  try {
    const sha = run('git rev-parse --short HEAD')
    const branch = run('git rev-parse --abbrev-ref HEAD')
    const dirty = run('git status --porcelain').length > 0
    const ref = branch && branch !== 'HEAD' ? `${branch}@${sha}` : sha
    return dirty ? `${ref}-dirty` : ref
  } catch {
    return null
  }
}

const VIRTUAL_OPENAPI_ID = '\0virtual:openapi-spec'

/**
 * Strip everything from an OpenAPI document that the demo mock backend
 * doesn't need to walk a successful response. Reduces the bundled spec
 * from ~6.9 MB to ~550 KB raw / ~35 KB gzipped.
 */
function compactOpenApiSpec(spec) {
  const out = {
    openapi: spec.openapi,
    info: spec.info,
    paths: {},
    components: { schemas: {} },
  }

  const refsToKeep = new Set()
  const REF_PREFIX = '#/components/schemas/'

  const collectRefs = (node) => {
    if (Array.isArray(node)) {
      for (const v of node) collectRefs(v)
    } else if (node && typeof node === 'object') {
      if (typeof node.$ref === 'string' && node.$ref.startsWith(REF_PREFIX)) {
        refsToKeep.add(node.$ref.slice(REF_PREFIX.length))
      }
      for (const v of Object.values(node)) collectRefs(v)
    }
  }

  const stripNoise = (node) => {
    if (Array.isArray(node)) {
      for (const v of node) stripNoise(v)
    } else if (node && typeof node === 'object') {
      delete node.description
      delete node.summary
      delete node.externalDocs
      delete node.deprecated
      delete node.operationId
      delete node.tags
      // `title` is intentionally kept: the runtime schema walker uses it as
      // a human-readable fallback for plain string fields.
      for (const v of Object.values(node)) stripNoise(v)
    }
  }

  for (const [path, item] of Object.entries(spec.paths ?? {})) {
    if (!item || typeof item !== 'object') continue
    const trimmedItem = {}
    for (const method of ['get', 'post', 'put', 'patch', 'delete']) {
      const op = item[method]
      if (!op) continue
      const responses = op.responses ?? {}
      const successResponses = {}
      for (const code of ['200', '201', '202']) {
        if (responses[code]) successResponses[code] = responses[code]
      }
      if (Object.keys(successResponses).length === 0) continue
      trimmedItem[method] = { responses: successResponses }
    }
    if (Object.keys(trimmedItem).length > 0) out.paths[path] = trimmedItem
  }

  collectRefs(out.paths)

  const schemas = spec.components?.schemas ?? {}
  const queue = [...refsToKeep]
  const kept = new Set()
  while (queue.length > 0) {
    const name = queue.pop()
    if (kept.has(name)) continue
    kept.add(name)
    const schema = schemas[name]
    if (!schema) continue
    const before = new Set(refsToKeep)
    collectRefs(schema)
    for (const ref of refsToKeep) {
      if (!before.has(ref) && !kept.has(ref)) queue.push(ref)
    }
  }
  for (const name of kept) {
    if (schemas[name]) out.components.schemas[name] = schemas[name]
  }

  stripNoise(out)
  return out
}

function openApiSpecPlugin(specPath) {
  return {
    name: 'studybuilder:openapi-spec',
    resolveId(id) {
      if (id === '@openapi-spec') return VIRTUAL_OPENAPI_ID
      return null
    },
    load(id) {
      if (id !== VIRTUAL_OPENAPI_ID) return null
      // Non-demo builds prune the dynamic imports that reach this module,
      // but Vite's dependency scanner still crawls the static import in
      // mockBackend.js. Return an empty stub so the scan resolves cleanly.
      if (!specPath) return 'export default {}'
      const raw = JSON.parse(readFileSync(specPath, 'utf-8'))
      const compact = compactOpenApiSpec(raw)
      return `export default ${JSON.stringify(compact)}`
    },
  }
}

const REPO_ROOT = fileURLToPath(new URL('.', import.meta.url))
// The demo backend generates mock responses from the API's OpenAPI spec,
// which lives in the sibling api/ project of this monorepo.
const DEFAULT_SPEC_PATH = fileURLToPath(
  new URL('../api/openapi.json', import.meta.url)
)

function resolveOpenApiPath(mode) {
  // VITE_OPENAPI_SPEC may be absolute or relative to the repo root.
  const env = loadEnv(mode, REPO_ROOT, '')
  const override = env.VITE_OPENAPI_SPEC?.trim()
  let resolved = DEFAULT_SPEC_PATH
  if (override) {
    resolved = isAbsolute(override) ? override : resolve(REPO_ROOT, override)
  }
  if (!existsSync(resolved)) {
    throw new Error(
      `[demo] OpenAPI spec not found at ${resolved}. ` +
        `Set VITE_OPENAPI_SPEC in .env.demo (or your shell) to point at openapi.json.`
    )
  }
  return resolved
}

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const isDemo = mode === 'demo'
  const openApiPath = isDemo ? resolveOpenApiPath(mode) : null
  const gitCommit = isDemo ? readGitCommit() : null

  return {
    define: {
      __DEMO_GIT_COMMIT__: JSON.stringify(gitCommit),
    },
    server: {
      host: true,
    },
    css: {
      preprocessorOptions: {
        sass: {
          api: 'modern-compiler',
          silenceDeprecations: ['if-function'],
        },
        scss: {
          api: 'modern-compiler',
          silenceDeprecations: ['if-function'],
        },
      },
    },
    plugins: [
      vue(),
      vuetify({ styles: { configFile: 'src/styles/settings.scss' } }),
      openApiSpecPlugin(openApiPath),
      {
        name: 'spa-fallback-for-dots',
        configureServer(server) {
          server.middlewares.use((req, _res, next) => {
            // Handle routes with version numbers (e.g., /overview/4.1, /parent-class-overview/1.0)
            // Vite treats dots as file extensions, so we need to handle these specially
            if (req.url.match(/\/\d+\.\d+$/)) {
              req.url = '/'
            }
            next()
          })
        },
      },
    ],
    assetsInclude: ['**/*.md'],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
  }
})
