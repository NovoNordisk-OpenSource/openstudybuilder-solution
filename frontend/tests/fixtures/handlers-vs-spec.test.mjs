import { test } from 'node:test'
import { readFileSync } from 'node:fs'
import { resolve, isAbsolute } from 'node:path'

import { studyHandlers } from '../../src/demo/fixtures/studies.js'
import { libraryHandlers } from '../../src/demo/fixtures/library.js'

// Validate that every hand-tuned demo handler returns a payload that conforms
// to the success-response schema declared by the OpenAPI spec. This catches
// drift when the API renames a field, adds a required property, or tightens
// an enum — the schema walker happily generates from the new shape, but the
// hand-tuned overrides are frozen until somebody updates them.
//
// Validates only what we care about for drift detection: required props,
// type compatibility, enum membership, $ref resolution. Skips numeric
// constraints, string formats, and additionalProperties — schemas that
// change on those axes don't tend to break demo mode in practice.

const REPO_ROOT = process.cwd()
// The API's OpenAPI spec lives in the sibling api/ project of this monorepo.
const DEFAULT_SPEC = resolve(REPO_ROOT, '../api/openapi.json')

function resolveSpecPath() {
  const override = process.env.VITE_OPENAPI_SPEC?.trim()
  if (!override) return DEFAULT_SPEC
  return isAbsolute(override) ? override : resolve(REPO_ROOT, override)
}

const SPEC_PATH = resolveSpecPath()
const spec = JSON.parse(readFileSync(SPEC_PATH, 'utf-8'))
const componentSchemas = spec.components?.schemas ?? {}

/* ----- spec → operation index (mirrors mockBackend.compileOperations) ----- */

const SUCCESS_CODES = ['200', '201', '202']

function templateToRegex(template) {
  const escaped = template.replaceAll(/[.+^${}()|[\]\\]/g, String.raw`\$&`)
  const withParams = escaped.replaceAll(/\\\{[^}]+\\\}/g, '[^/]+')
  return new RegExp(`^${withParams}$`)
}

function pickResponseSchema(operation) {
  const responses = operation.responses ?? {}
  for (const code of SUCCESS_CODES) {
    const json = responses[code]?.content?.['application/json']
    if (json?.schema) return json.schema
  }
  return null
}

function compileOps() {
  const out = []
  for (const [template, item] of Object.entries(spec.paths ?? {})) {
    if (!item || typeof item !== 'object') continue
    for (const method of ['get', 'post', 'put', 'patch', 'delete']) {
      const op = item[method]
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
  out.sort(
    (a, b) =>
      a.paramCount - b.paramCount || b.template.length - a.template.length
  )
  return out
}

const ops = compileOps()

function findOp(method, path) {
  for (const op of ops) {
    if (op.method === method && op.regex.test(path)) return op
  }
  return null
}

/* ----- regex → sample path ----- */

function sampleForParam(name) {
  if (name === 'uid') return 'Study_000001'
  return `Demo_${name}`
}

function regexToSamplePath(re) {
  let s = re.source
  if (s.startsWith('^')) s = s.slice(1)
  if (s.endsWith('$')) s = s.slice(0, -1)
  s = s.replaceAll(String.raw`\/`, '/').replaceAll(String.raw`\.`, '.')
  s = s.replaceAll(/\(\?<([^>]+)>[^)]+\)/g, (_, name) => sampleForParam(name))
  return s
}

function extractRouteParams(re, sample) {
  const m = sample.match(re)
  return m?.groups ?? {}
}

/* ----- schema validator ----- */

function jsonType(v) {
  if (v === null) return 'null'
  if (Array.isArray(v)) return 'array'
  if (typeof v === 'number') return Number.isInteger(v) ? 'integer' : 'number'
  return typeof v
}

function validateRef(value, schema, path, errors, depth) {
  const refName = schema.$ref.replace('#/components/schemas/', '')
  const resolved = componentSchemas[refName]
  if (!resolved) {
    errors.push({ path, msg: `unresolved $ref ${schema.$ref}` })
    return errors
  }
  return validate(value, resolved, path, errors, depth + 1)
}

function validateUnion(value, variants, path, errors, depth) {
  let best = null
  for (const v of variants) {
    const trial = []
    validate(value, v, path, trial, depth + 1)
    if (trial.length === 0) return errors
    if (best === null || trial.length < best.length) best = trial
  }
  const sample = best[0]?.msg ?? 'no detail'
  errors.push({
    path,
    msg: `did not match any of ${variants.length} variants (closest: ${sample})`,
  })
  return errors
}

function validateNull(schema, path, errors) {
  const allowsNull =
    schema.type === 'null' ||
    (Array.isArray(schema.type) && schema.type.includes('null')) ||
    schema.nullable === true
  if (!allowsNull)
    errors.push({ path, msg: `null not allowed (type ${schema.type})` })
  return errors
}

function validateType(actual, schema, path, errors) {
  const expected = Array.isArray(schema.type)
    ? schema.type
    : schema.type
      ? [schema.type]
      : null
  if (!expected) return true
  let ok = expected.includes(actual)
  if (!ok && expected.includes('number') && actual === 'integer') ok = true
  if (!ok) {
    errors.push({
      path,
      msg: `expected type ${expected.join('|')}, got ${actual}`,
    })
    return false
  }
  return true
}

function validate(value, schema, path, errors, depth) {
  if (depth > 30) return errors
  if (schema == null) return errors

  if (schema.$ref) return validateRef(value, schema, path, errors, depth)

  if (schema.allOf) {
    for (const s of schema.allOf) validate(value, s, path, errors, depth + 1)
    return errors
  }
  if (schema.anyOf || schema.oneOf) {
    return validateUnion(
      value,
      schema.anyOf || schema.oneOf,
      path,
      errors,
      depth
    )
  }

  if (value === null) return validateNull(schema, path, errors)

  const actual = jsonType(value)
  if (!validateType(actual, schema, path, errors)) return errors

  if (Array.isArray(schema.enum) && !schema.enum.includes(value)) {
    errors.push({
      path,
      msg: `value ${JSON.stringify(value)} not in enum [${schema.enum.map((e) => JSON.stringify(e)).join(', ')}]`,
    })
    return errors
  }

  if (actual === 'object') {
    for (const req of schema.required ?? []) {
      if (!(req in value)) {
        errors.push({
          path: `${path}.${req}`,
          msg: 'required property missing',
        })
      }
    }
    if (schema.properties) {
      for (const [k, propSchema] of Object.entries(schema.properties)) {
        if (k in value) {
          validate(value[k], propSchema, `${path}.${k}`, errors, depth + 1)
        }
      }
    }
  }
  if (actual === 'array' && schema.items) {
    for (let i = 0; i < value.length; i++) {
      validate(value[i], schema.items, `${path}[${i}]`, errors, depth + 1)
    }
  }
  return errors
}

/* ----- test cases ----- */

const cases = [
  ...studyHandlers.map((h) => ({ ...h, source: 'studyHandlers' })),
  ...libraryHandlers.map((h) => ({ ...h, source: 'libraryHandlers' })),
]

function syntheticCtx(handler, samplePath) {
  return {
    method: handler.method,
    path: samplePath,
    params: {},
    data: {},
    state: {},
    persist: () => {},
    clone: (v) => (v == null ? v : structuredClone(v)),
    specInfo: spec.info,
    routeParams: extractRouteParams(handler.regex, samplePath),
  }
}

for (const handler of cases) {
  const samplePath = regexToSamplePath(handler.regex)
  const label = `${handler.method} ${samplePath} (${handler.source})`

  test(label, async (t) => {
    const op = findOp(handler.method, samplePath)
    if (op === null) {
      t.skip(`no OpenAPI operation matches ${handler.method} ${samplePath}`)
      return
    }
    if (op.responseSchema == null) {
      t.skip(`OpenAPI op for ${label} has no JSON success-response schema`)
      return
    }

    const result = await handler.respond(syntheticCtx(handler, samplePath))
    const status = result?.status ?? 200
    if (status >= 400) {
      t.skip(`handler returned status ${status} (skipped — error path)`)
      return
    }

    const errors = validate(result?.data ?? null, op.responseSchema, '$', [], 0)
    if (errors.length > 0) {
      const shown = errors
        .slice(0, 15)
        .map((e) => `  ${e.path}: ${e.msg}`)
        .join('\n')
      const more =
        errors.length > 15 ? `\n  ... and ${errors.length - 15} more` : ''
      throw new Error(
        `${errors.length} schema mismatch(es) for ${label}\n` +
          `against ${op.method} ${op.template}:\n${shown}${more}`
      )
    }
  })
}
