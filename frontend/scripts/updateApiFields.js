/**
 * Extract field paths and human-readable labels from an OpenAPI specification.
 */

const fs = require('node:fs')
const path = require('node:path')

const ALPHABET = 'abcdefghijklmnopqrstuvwxyz'

function titleize(name) {
  let result = ''
  let prevIsAlnum = false
  for (const ch of name) {
    const isAlpha = /[a-zA-Z]/.test(ch)
    if (isAlpha) {
      result += prevIsAlnum ? ch.toLowerCase() : ch.toUpperCase()
    } else {
      result += ch
    }
    prevIsAlnum = isAlpha
  }
  return result.replaceAll('_', ' ').replaceAll('Uid', 'UID')
}

function buildLabel(key) {
  const parts = key.split(',').reverse()

  if (parts.length === 1) {
    return titleize(parts[0]).trim()
  }

  let label = ''
  let prevWasIndex = false

  for (let idx = 0; idx < parts.length; idx++) {
    const part = parts[idx]

    if (ALPHABET.includes(part) && part.length === 1) {
      prevWasIndex = true
      continue
    }

    const title = titleize(part)
    if (prevWasIndex) {
      label += `${title} #{${parts[idx - 1]}} of `
    } else {
      label += `${title} of `
    }
    prevWasIndex = false
  }

  label = label.trim()
  if (label.endsWith('of')) {
    label = label.slice(0, -2).trim()
  }
  return label
}

function findNestedRef(schema) {
  if (schema.items && schema.items['$ref']) {
    return schema.items['$ref']
  }

  if (schema['$ref']) {
    return schema['$ref']
  }

  if (schema.anyOf) {
    for (const item of schema.anyOf) {
      if (item.items && item.items['$ref']) {
        return item.items['$ref']
      }
    }
    for (const item of schema.anyOf) {
      if (item['$ref']) {
        return item['$ref']
      }
    }
  }

  return null
}

/**
 * Recursively extract body field paths from an OpenAPI schema reference.
 * @returns {[string, string][]}
 */
function extractBodyFields(schemas, ref, suffix = '', depth = -1) {
  const results = []
  const schemaName = ref.split('/').pop()
  const properties = (schemas[schemaName] || {}).properties || {}

  for (const [fieldName, fieldSchema] of Object.entries(properties)) {
    const indexPrefix = depth > -1 ? `${ALPHABET[depth]},` : ''
    const currentPath = `${suffix}${indexPrefix}${fieldName},`

    const nestedRef = findNestedRef(fieldSchema)
    if (nestedRef) {
      results.push(
        ...extractBodyFields(schemas, nestedRef, currentPath, depth + 1)
      )
    }

    const key = currentPath.replace(/,$/, '')
    results.push([`body,${key}`, buildLabel(key)])
  }

  return results
}

function extractRefFromContent(content) {
  const jsonSchema = ((content || {})['application/json'] || {}).schema || {}
  return jsonSchema['$ref'] || (jsonSchema.items || {})['$ref'] || ''
}

/**
 * Extract all parameter and body field entries from an OpenAPI spec.
 * @returns {[string, string][]}
 */
function extractFields(data) {
  const results = []
  const schemas = data.components.schemas

  for (const pathObj of Object.values(data.paths)) {
    for (const operation of Object.values(pathObj)) {
      if (operation.parameters) {
        for (const param of operation.parameters) {
          const name = param.name.replace(/\[\]$/, '')
          const location = param.in
          results.push([
            `${location},${name},a`,
            `${name} #{a} in ${location} parameters`,
          ])
        }

        const bodyRef =
          ((
            ((operation.requestBody || {}).content || {})['application/json'] ||
            {}
          ).schema || {})['$ref'] || ''
        if (bodyRef) {
          results.push(...extractBodyFields(schemas, bodyRef))
        }
      }

      for (const response of Object.values(operation.responses || {})) {
        const bodyRef = extractRefFromContent(response.content)
        if (bodyRef) {
          results.push(...extractBodyFields(schemas, bodyRef))
        }
      }
    }
  }

  return results
}

const args = process.argv.slice(2)
const toStdout = args.includes('--stdout')
const positional = args.filter((a) => !a.startsWith('-'))
const openApiPath = positional[0]
const outputPath = positional[1]

const raw = fs.readFileSync(path.resolve(openApiPath), 'utf-8')
const data = JSON.parse(raw)
const results = extractFields(data)

const sortedEntries = [...new Map(results)].sort(([a], [b]) =>
  a.localeCompare(b)
)
const output = Object.fromEntries(sortedEntries)
const json = JSON.stringify(output, null, 2)

if (outputPath) {
  const resolved = path.resolve(outputPath)
  const existing = JSON.parse(fs.readFileSync(resolved, 'utf-8'))
  existing.api.fields = output
  fs.writeFileSync(resolved, JSON.stringify(existing, null, 4) + '\n', 'utf-8')
}

if (toStdout || !outputPath) {
  process.stdout.write(json + '\n')
}
