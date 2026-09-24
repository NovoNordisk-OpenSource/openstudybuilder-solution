const IGNORED_ERROR_PATTERNS = [
  /^\[demo\] no spec entry for /,
  /^\[demo\] schema walker hit MAX_DEPTH/,
  // GroupOverview.vue logs this before falling back to /overview; the demo
  // backend deliberately 404s /details to avoid a TDZ bug in the happy path.
  /^Error fetching group details: /,
]

export function setupConsoleSpy(page) {
  const errors = []

  function isIgnored(text) {
    return IGNORED_ERROR_PATTERNS.some((re) => re.test(text))
  }

  page.on('console', (msg) => {
    if (msg.type() !== 'error') return
    const text = msg.text()
    if (!isIgnored(text)) {
      errors.push(`console.error: ${text}`)
    }
  })

  page.on('pageerror', (err) => {
    errors.push(`pageerror: ${err.message}`)
  })

  return {
    errors,
    assertClean() {
      if (errors.length > 0) {
        throw new Error(
          `Unexpected browser errors on "${page.url()}":\n` +
            errors.map((e) => `  - ${e}`).join('\n')
        )
      }
    },
  }
}
