import DOMPurify from 'dompurify'

export function sanitizeHTML(dirtyHTML, { allowAttrPattern } = {}) {
  if (!allowAttrPattern) {
    return DOMPurify.sanitize(dirtyHTML)
  }
  const hook = (_node, data) => {
    if (allowAttrPattern.test(data.attrName)) {
      data.forceKeepAttr = true
    }
  }
  DOMPurify.addHook('uponSanitizeAttribute', hook)
  try {
    return DOMPurify.sanitize(dirtyHTML)
  } finally {
    DOMPurify.removeHook('uponSanitizeAttribute', hook)
  }
}

export function escapeHTML(htmlText) {
  return htmlText
    ?.replace(/&/g, '&amp;')
    ?.replace(/</g, '&lt;')
    ?.replace(/>/g, '&gt;')
    ?.replace(/"/g, '&quot;')
    ?.replace(/'/g, '&#039;')
}
