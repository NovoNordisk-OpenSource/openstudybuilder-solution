/**
 * In-browser mock backend for demo mode.
 *
 * Looks up the request path in the live OpenAPI spec, walks the success
 * response schema, and returns a synthetic body. No precomputed fixtures —
 * the spec is the single source of truth.
 *
 * Hand-tuned overrides in src/demo/fixtures/*.js take precedence and can
 * read/write persistent state via ctx.state.
 */

import openapi from '@openapi-spec'

import { loadDemoUser } from './demoAuth.js'
import { studyHandlers } from './fixtures/studies.js'
import { libraryHandlers } from './fixtures/library.js'

const STORAGE_KEY = 'studybuilder.demo.state.v1'
const MAX_DEPTH = 12
const SUCCESS_CODES = ['200', '201', '202']

const handHandlers = [...studyHandlers, ...libraryHandlers]
const componentSchemas = openapi.components?.schemas ?? {}
const operations = compileOperations(openapi)
const responseCache = new Map()

const state = loadState()

function loadState() {
  try {
    const raw = globalThis.localStorage?.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

function persistState() {
  try {
    globalThis.localStorage?.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch {
    /* quota — ignore */
  }
}

/* ----- spec → operation index ----- */

function compileOperations(spec) {
  const out = []
  const paths = spec.paths ?? {}
  for (const [template, pathItem] of Object.entries(paths)) {
    if (!pathItem || typeof pathItem !== 'object') continue
    for (const method of ['get', 'post', 'put', 'patch', 'delete']) {
      const op = pathItem[method]
      if (!op) continue
      out.push({
        method: method.toUpperCase(),
        template,
        regex: templateToRegex(template),
        paramCount: (template.match(/\{[^}]+\}/g) ?? []).length,
        responseSchema: pickResponseSchema(op),
      })
    }
  }
  // Fewer path parameters = more specific (literal `/headers` beats `/{uid}`).
  // Tie-break by longer template length.
  out.sort(
    (a, b) =>
      a.paramCount - b.paramCount || b.template.length - a.template.length
  )
  return out
}

function templateToRegex(template) {
  const escaped = template.replace(/[.+^${}()|[\]\\]/g, '\\$&')
  const withParams = escaped.replace(/\\\{[^}]+\\\}/g, '[^/]+')
  return new RegExp(`^${withParams}$`)
}

function pickResponseSchema(operation) {
  const responses = operation.responses ?? {}
  for (const code of SUCCESS_CODES) {
    const resp = responses[code]
    const json = resp?.content?.['application/json']
    if (json?.schema) return json.schema
  }
  return null
}

/* ----- schema walker ----- */

function resolveRef(ref) {
  if (!ref.startsWith('#/components/schemas/')) return null
  return componentSchemas[ref.slice('#/components/schemas/'.length)] ?? null
}

function pickExample(schema) {
  if (schema == null || typeof schema !== 'object') return undefined
  if (schema.example !== undefined) return schema.example
  if (schema.examples) {
    if (Array.isArray(schema.examples) && schema.examples.length > 0) {
      return schema.examples[0]
    }
    if (typeof schema.examples === 'object') {
      const first = Object.values(schema.examples)[0]
      if (first && typeof first === 'object' && 'value' in first)
        return first.value
      return first
    }
  }
  return undefined
}

function inferType(schema) {
  if (schema.properties || schema.additionalProperties) return 'object'
  if (schema.items) return 'array'
  return undefined
}

// Sensible demo values for commonly-named fields. Only applied when the schema
// for the field is a plain string/nullable-string with no enum, format, or
// example to drive the walker. Keeps lifecycle metadata coherent across the
// many schemas that share these field names.
const FIELD_DEFAULTS = {
  status: 'Final',
  study_status: 'DRAFT',
  version: '1.0',
  version_number: '1.0',
  change_description: 'Initial version',
  author_username: 'demo-user',
  user_initials: 'DEMO',
  start_date: '2026-01-01T00:00:00Z',
  end_date: null,
  date: '2026-01-01T00:00:00Z',
  modified_date: '2026-01-01T00:00:00Z',
  library_name: 'Sponsor',
}

// Field names whose value is an array of action literals the UI gates buttons
// on (e.g. v-if="possible_actions.find(a => a === 'edit')"). The OpenAPI spec
// declares these as plain string arrays without an enum, so the walker would
// otherwise emit synthetic placeholders ("Possible Actions A") that match
// nothing — leaving every gated edit/approve/new_version button hidden.
const ARRAY_FIELD_DEFAULTS = {
  possible_actions: ['edit', 'approve', 'new_version'],
}

// Field names whose value is a human-readable label of the enclosing entity.
// When we know the entity's schema name (e.g. "CTTerm"), we can produce
// "CT Term A" instead of the placeholder "string" the type walker emits.
const NAME_FIELDS = new Set([
  'name',
  'sponsor_preferred_name',
  'preferred_term',
  'name_sentence_case',
])

const DEFINITION_FIELDS = new Set(['definition'])

const SUBMISSION_VALUE_FIELDS = new Set(['submission_value'])

const CONCEPT_ID_FIELDS = new Set(['concept_id', 'nci_concept_id'])

// Visit-specific overrides. Within a paginated list each visit gets its own
// index (0, 1, 2, ...) and these counters track that — so /study-visits
// renders as Visit 1, Visit 2, ... at study days 1, 8, 15, etc.
const VISIT_FIELDS = {
  visit_name: (i) => `Visit ${i + 1}`,
  visit_subname: (i) => `Visit ${i + 1}`,
  visit_short_name: (i) => `V${i + 1}`,
  visit_number: (i) => i + 1,
  unique_visit_number: (i) => (i + 1) * 100,
  visit_subnumber: () => 0,
  order: (i) => i + 1,
  study_day_number: (i) => 1 + i * 7,
  study_duration_days: (i) => i * 7,
  study_week_number: (i) => 1 + i,
  study_duration_weeks: (i) => i,
}

// Field-key suffixes that signal "this is a label for a related entity".
// Stripping the suffix and title-casing the prefix gives a usable label —
// e.g. activity_group_name → "Activity Group", flowchart_group_term_uid →
// "Flowchart Group Term". Order matters: longer suffixes first.
const ENTITY_NAME_SUFFIXES = ['_short_name', '_name', '_uid']

function deriveLabelFromKey(key) {
  for (const suffix of ENTITY_NAME_SUFFIXES) {
    if (key.length > suffix.length && key.endsWith(suffix)) {
      const prefix = key.slice(0, -suffix.length)
      const words = prefix.split('_').filter(Boolean)
      if (words.length === 0) return null
      return words.map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
    }
  }
  return null
}

const SCHEMA_NAME_STRIPPED_PREFIXES = ['CustomPage_']
const SCHEMA_NAME_STRIPPED_SUFFIXES = [
  'JsonModel',
  'ListingModel',
  'Detailed',
  'Detail',
  'Compact',
  'Output',
  'Input',
  'Model',
]

function letterFor(index) {
  let n = index
  let s = ''
  for (;;) {
    s = String.fromCodePoint(65 + (n % 26)) + s
    n = Math.floor(n / 26) - 1
    if (n < 0) return s
  }
}

function humanizeSchemaName(refName) {
  if (!refName) return null
  let name = refName
  for (const prefix of SCHEMA_NAME_STRIPPED_PREFIXES) {
    if (name.startsWith(prefix)) name = name.slice(prefix.length)
  }
  name = name.replace(/_+$/, '')
  let changed = true
  while (changed) {
    changed = false
    for (const suffix of SCHEMA_NAME_STRIPPED_SUFFIXES) {
      if (name.length > suffix.length && name.endsWith(suffix)) {
        name = name.slice(0, -suffix.length)
        changed = true
      }
    }
  }
  if (!name) return null
  // PascalCase → spaces. Handle runs of caps ("CTTerm" → "CT Term") then
  // single boundaries ("ActivityGroup" → "Activity Group").
  return name
    .replace(/([A-Z]+)([A-Z][a-z])/g, '$1 $2')
    .replace(/([a-z\d])([A-Z])/g, '$1 $2')
    .trim()
}

function defaultByFieldName(key, schema, schemaLabel, index = 0) {
  if (schema == null || typeof schema !== 'object') return undefined
  if (schema.example !== undefined) return undefined
  if (schema.enum) return undefined
  if (schema.const !== undefined) return undefined
  if (schema.format) return undefined
  if (key in VISIT_FIELDS) return VISIT_FIELDS[key](index)
  const variants = schema.anyOf ?? schema.oneOf ?? [schema]
  if (key in ARRAY_FIELD_DEFAULTS) {
    const isArray = variants.some((v) => v && v.type === 'array')
    if (isArray) return [...ARRAY_FIELD_DEFAULTS[key]]
  }
  const stringy = variants.some(
    (v) => v && (v.type === 'string' || v.type === 'null')
  )
  if (!stringy) return undefined
  if (key in FIELD_DEFAULTS) return FIELD_DEFAULTS[key]
  const letter = letterFor(index)
  if (CONCEPT_ID_FIELDS.has(key)) {
    return `C${10001 + index}`
  }
  if (NAME_FIELDS.has(key) && schemaLabel) {
    if (key === 'name_sentence_case') {
      return `${schemaLabel.toLowerCase()} ${letter.toLowerCase()}`
    }
    return `${schemaLabel} ${letter}`
  }
  if (DEFINITION_FIELDS.has(key) && schemaLabel) {
    return `Definition for ${schemaLabel.toLowerCase()} ${letter}`
  }
  if (SUBMISSION_VALUE_FIELDS.has(key) && schemaLabel) {
    return `${schemaLabel.replace(/\s+/g, '').toUpperCase()}_${letter}`
  }
  const derivedLabel = deriveLabelFromKey(key)
  if (derivedLabel) {
    return `${derivedLabel} ${letter}`
  }
  return undefined
}

// CT term-shaped objects in some endpoints expose a flat `sponsor_preferred_name`
// in the schema, but UI templates also read `term.name.sponsor_preferred_name`
// (a sub-object that mirrors the same fields). The OpenAPI spec doesn't always
// document the sub-object, so synthesize it from the flat fields.
const NAME_SIBLING_SOURCE_FIELDS = [
  'sponsor_preferred_name',
  'sponsor_preferred_name_sentence_case',
  'term_uid',
]
function synthesizeNameSibling(obj) {
  if (obj == null || typeof obj !== 'object') return
  if ('name' in obj) return
  if (!('sponsor_preferred_name' in obj)) return
  const nameObj = {}
  for (const key of NAME_SIBLING_SOURCE_FIELDS) {
    if (key in obj) nameObj[key] = obj[key]
  }
  obj.name = nameObj
}

// Many list endpoints expose a `*_groupings: [{<x>_uid, <x>_name, ...}]`
// array, but UI templates also read flat siblings like `activity_group.name`
// (an array) that the OpenAPI spec doesn't actually describe. Synthesize
// those siblings from the groupings array so the table cells render.
function synthesizeGroupingSiblings(obj) {
  for (const key of Object.keys(obj)) {
    if (!key.endsWith('_groupings')) continue
    const groupings = obj[key]
    if (!Array.isArray(groupings) || groupings.length === 0) continue
    const sample = groupings[0]
    if (!sample || typeof sample !== 'object') continue
    const prefixes = new Set()
    for (const k of Object.keys(sample)) {
      if (k.endsWith('_uid')) {
        const prefix = k.slice(0, -'_uid'.length)
        if (`${prefix}_name` in sample) prefixes.add(prefix)
      }
    }
    for (const prefix of prefixes) {
      if (prefix in obj) continue
      obj[prefix] = {
        uid: groupings.map((g) => g?.[`${prefix}_uid`] ?? null),
        name: groupings.map((g) => g?.[`${prefix}_name`] ?? null),
      }
    }
  }
}

// For union types like `anyOf: [StudyVisitLite, StudyVisit]`, the UI typically
// reads fields from the richer member. Pick the variant with the most properties.
function countSchemaProperties(schema) {
  if (!schema || typeof schema !== 'object') return 0
  if (schema.$ref) {
    const resolved = resolveRef(schema.$ref)
    return resolved ? Object.keys(resolved.properties ?? {}).length : 0
  }
  return Object.keys(schema.properties ?? {}).length
}

function pickRichestVariant(variants) {
  let best = variants[0]
  let bestCount = countSchemaProperties(best)
  for (let i = 1; i < variants.length; i++) {
    const count = countSchemaProperties(variants[i])
    if (count > bestCount) {
      best = variants[i]
      bestCount = count
    }
  }
  return best
}

function isPaginatedShape(props) {
  if (!props || !('items' in props)) return false
  return 'total' in props || 'page' in props || 'size' in props
}

function generateFromSchema(
  schema,
  depth,
  seen,
  schemaLabel = null,
  index = 0,
  pageSize = 1,
  pageNumber = 1
) {
  if (depth > MAX_DEPTH) {
    console.warn(
      `[demo] schema walker hit MAX_DEPTH (${MAX_DEPTH}) at "${schemaLabel ?? '<root>'}"; subtree returned as null`
    )
    return null
  }
  if (schema == null) return null

  if (schema.$ref) {
    if (seen.has(schema.$ref)) return null
    const next = new Set(seen)
    next.add(schema.$ref)
    const resolved = resolveRef(schema.$ref)
    if (!resolved) return null
    const refName = schema.$ref.slice('#/components/schemas/'.length)
    const nextLabel = humanizeSchemaName(refName) ?? schemaLabel
    return generateFromSchema(
      resolved,
      depth + 1,
      next,
      nextLabel,
      index,
      pageSize,
      pageNumber
    )
  }

  const ex = pickExample(schema)
  if (ex !== undefined) return ex

  if (Array.isArray(schema.enum) && schema.enum.length > 0)
    return schema.enum[0]
  if (schema.default !== undefined) return schema.default
  if (schema.const !== undefined) return schema.const

  if (schema.anyOf || schema.oneOf) {
    const nonNull = (schema.anyOf ?? schema.oneOf).filter(
      (v) => v && v.type !== 'null'
    )
    if (nonNull.length === 0) return null
    const best = nonNull.length === 1 ? nonNull[0] : pickRichestVariant(nonNull)
    return generateFromSchema(
      best,
      depth + 1,
      seen,
      schemaLabel,
      index,
      pageSize,
      pageNumber
    )
  }
  if (schema.allOf) {
    const merged = {}
    for (const part of schema.allOf) {
      const v = generateFromSchema(
        part,
        depth + 1,
        seen,
        schemaLabel,
        index,
        pageSize,
        pageNumber
      )
      if (v && typeof v === 'object' && !Array.isArray(v))
        Object.assign(merged, v)
    }
    return merged
  }

  const type = schema.type ?? inferType(schema)

  if (type === 'object' || schema.properties) {
    const out = {}
    const props = schema.properties ?? {}
    const paginated = pageSize > 1 && isPaginatedShape(props)
    // Demo paging: total = pageSize + half a page so paging UIs show >1 page.
    const total = paginated ? pageSize + Math.floor(pageSize / 2) : 0
    const startIndex = paginated ? (pageNumber - 1) * pageSize : 0
    const endIndex = paginated ? Math.min(pageNumber * pageSize, total) : 0
    const itemCount = Math.max(0, endIndex - startIndex)
    for (const [key, propSchema] of Object.entries(props)) {
      if (paginated && key === 'items') {
        const itemSchema = propSchema?.items
        const arr = []
        if (itemSchema) {
          for (let i = 0; i < itemCount; i++) {
            const item = generateFromSchema(
              itemSchema,
              depth + 1,
              seen,
              schemaLabel,
              startIndex + i,
              1,
              1
            )
            if (item !== null) arr.push(item)
          }
        }
        out[key] = arr
        continue
      }
      const override = defaultByFieldName(key, propSchema, schemaLabel, index)
      out[key] =
        override === undefined
          ? generateFromSchema(
              propSchema,
              depth + 1,
              seen,
              schemaLabel,
              index,
              1,
              1
            )
          : override
    }
    if (paginated) {
      if ('total' in props) out.total = total
      if ('page' in props) out.page = pageNumber
      if ('size' in props) out.size = pageSize
    }
    synthesizeGroupingSiblings(out)
    synthesizeNameSibling(out)
    return out
  }
  if (type === 'array') {
    const itemSchema = schema.items
    if (!itemSchema) return []
    const item = generateFromSchema(
      itemSchema,
      depth + 1,
      seen,
      schemaLabel,
      index,
      1,
      1
    )
    return item === null ? [] : [item]
  }
  if (type === 'string') {
    if (schema.format === 'date-time') return '2026-01-01T00:00:00Z'
    if (schema.format === 'date') return '2026-01-01'
    if (schema.format === 'uuid') return '00000000-0000-0000-0000-000000000000'
    if (schema.format === 'email') return 'demo@example.com'
    if (schema.format === 'uri' || schema.format === 'url')
      return 'https://demo.invalid/'
    return schema.title ? `${schema.title}` : 'string'
  }
  if (type === 'integer' || type === 'number') return 0
  if (type === 'boolean') return false
  if (type === 'null') return null
  return null
}

function generateForOperation(op, pageSize = 1, pageNumber = 1) {
  const cacheKey = `${op.method} ${op.template} ${pageSize}:${pageNumber}`
  if (responseCache.has(cacheKey)) return clone(responseCache.get(cacheKey))
  const body = op.responseSchema
    ? generateFromSchema(
        op.responseSchema,
        0,
        new Set(),
        null,
        0,
        pageSize,
        pageNumber
      )
    : null
  responseCache.set(cacheKey, body)
  return clone(body)
}

const DEMO_PAGE_SIZE_DEFAULT = 10
const DEMO_PAGE_SIZE_MAX = 25

function resolvePageSize(params) {
  const raw = params?.page_size
  if (raw === undefined || raw === null || raw === '')
    return DEMO_PAGE_SIZE_DEFAULT
  const n = Number(raw)
  // page_size = 0 means "all" (after the repository.js -1→0 rewrite). Cap it.
  if (!Number.isFinite(n) || n <= 0) return DEMO_PAGE_SIZE_DEFAULT
  return Math.min(Math.floor(n), DEMO_PAGE_SIZE_MAX)
}

function resolvePageNumber(params) {
  const raw = params?.page_number
  if (raw === undefined || raw === null || raw === '') return 1
  const n = Number(raw)
  if (!Number.isFinite(n) || n < 1) return 1
  return Math.floor(n)
}

/* ----- adapter ----- */

function normalizePath(url) {
  const noQuery = url.split('?')[0]
  const stripped = noQuery.replace(/^https?:\/\/[^/]+/, '')
  return stripped.startsWith('/') ? stripped : '/' + stripped
}

const STATUS_TEXT = {
  200: 'OK',
  201: 'Created',
  204: 'No Content',
  400: 'Bad Request',
  403: 'Forbidden',
  404: 'Not Found',
  500: 'Internal Server Error',
}

// Path prefixes that are open to anonymous callers (and to any logged-in user
// regardless of roles). Keep this minimal — anything that the app needs before
// the user has signed in.
function isAnonAllowed(path) {
  return path === '/' || path === '/system' || path.startsWith('/system/')
}

const FEATURE_FLAG_READ_ROLES = ['Admin.Read', 'Library.Read', 'Study.Read']

function hasFeatureFlagRead(user) {
  return FEATURE_FLAG_READ_ROLES.some((role) => user?.roles?.includes(role))
}

const ADMIN_PREFIXES = [
  '/admin',
  '/configurations',
  '/user-preferences',
  '/notifications',
  '/data-completeness-tags',
]

function domainForPath(path) {
  if (
    path === '/studies' ||
    path.startsWith('/studies/') ||
    path.startsWith('/study-')
  ) {
    return 'Study'
  }
  for (const prefix of ADMIN_PREFIXES) {
    if (path === prefix || path.startsWith(prefix + '/')) return 'Admin'
  }
  return 'Library'
}

function requiredRoleForOperation(method, path) {
  if (isAnonAllowed(path)) return null
  const action = method === 'GET' ? 'Read' : 'Write'
  return `${domainForPath(path)}.${action}`
}

function buildResponse(config, status, data) {
  return {
    data,
    status,
    statusText: STATUS_TEXT[status] ?? '',
    headers: { 'content-type': 'application/json' },
    config,
    request: {},
  }
}

function matchHandHandler(method, path) {
  for (const handler of handHandlers) {
    if (handler.method !== method) continue
    const m = path.match(handler.regex)
    if (m) return { handler, params: m.groups ?? {} }
  }
  return null
}

function matchOperation(method, path) {
  for (const op of operations) {
    if (op.method !== method) continue
    if (op.regex.test(path)) return op
  }
  return null
}

function clone(value) {
  if (value === null || typeof value !== 'object') return value
  return JSON.parse(JSON.stringify(value))
}

function parseRequestBody(data) {
  if (data == null) return null
  if (typeof data === 'string') {
    try {
      return JSON.parse(data)
    } catch {
      return data
    }
  }
  return data
}

export function createDemoAdapter() {
  return async function demoAdapter(config) {
    const method = (config.method ?? 'get').toUpperCase()
    const path = normalizePath(config.url ?? '/')

    const required = requiredRoleForOperation(method, path)
    if (path === '/feature-flags' || path.startsWith('/feature-flags/')) {
      const user = loadDemoUser()
      const isWrite = method !== 'GET'
      if (isWrite) {
        if (!user?.roles?.includes('Admin.Write')) {
          return rejectWithAxiosError(
            config,
            buildResponse(config, 403, {
              message: `Demo backend: missing Admin.Write permission for ${method} ${path}`,
            })
          )
        }
      } else if (!hasFeatureFlagRead(user)) {
        return rejectWithAxiosError(
          config,
          buildResponse(config, 403, {
            message: `Demo backend: missing feature-flag read permission for ${method} ${path}`,
          })
        )
      }
    } else if (required) {
      const user = loadDemoUser()
      if (!user?.roles?.includes(required)) {
        return rejectWithAxiosError(
          config,
          buildResponse(config, 403, {
            message: `Demo backend: missing ${required} permission for ${method} ${path}`,
          })
        )
      }
    }

    const ctx = {
      method,
      path,
      params: config.params ?? {},
      data: parseRequestBody(config.data),
      state,
      persist: persistState,
      clone,
      specInfo: openapi.info,
    }

    // The demo adapter fully replaces axios, so requests never reach a real
    // network layer — Playwright's page.route() can't observe them. Record
    // writes here so smoke tests can assert on the actual submitted payload.
    if (method !== 'GET') {
      globalThis.__demoLastWrite = { method, path, body: ctx.data }
    }

    const matched = matchHandHandler(method, path)
    if (matched) {
      ctx.routeParams = matched.params
      try {
        const result = await matched.handler.respond(ctx)
        // `undefined` means "not this case" — fall through to the schema walker.
        if (result !== undefined) {
          const status = result?.status ?? (method === 'DELETE' ? 204 : 200)
          const response = buildResponse(config, status, result?.data ?? null)
          if (status >= 400) {
            return rejectWithAxiosError(config, response)
          }
          return response
        }
      } catch (err) {
        console.error('[demo] hand-handler error', method, path, err)
        return rejectWithAxiosError(
          config,
          buildResponse(config, 500, { message: err.message })
        )
      }
    }

    const op = matchOperation(method, path)
    if (op) {
      const body = generateForOperation(
        op,
        resolvePageSize(config.params),
        resolvePageNumber(config.params)
      )
      return buildResponse(config, method === 'DELETE' ? 204 : 200, body)
    }

    console.warn(`[demo] no spec entry for ${method} ${path}`)
    return rejectWithAxiosError(
      config,
      buildResponse(config, 404, {
        message: `Demo backend: no spec entry for ${method} ${path}`,
      })
    )
  }
}

function rejectWithAxiosError(config, response) {
  const error = new Error(
    response.data?.message ?? `Request failed with status ${response.status}`
  )
  error.response = response
  error.config = config
  error.isAxiosError = true
  return Promise.reject(error)
}

export function installDemoBackend(axiosInstance) {
  axiosInstance.defaults.adapter = createDemoAdapter()
  console.info(
    `[demo] mock backend installed (${operations.length} operations from spec)`
  )
}
