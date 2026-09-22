import DOMPurify from 'dompurify'

export function sanitizeHTML(dirtyHTML) {
  return DOMPurify.sanitize(dirtyHTML)
}

export function escapeHTML(htmlText) {
  return htmlText
    ?.replace(/&/g, '&amp;')
    ?.replace(/</g, '&lt;')
    ?.replace(/>/g, '&gt;')
    ?.replace(/"/g, '&quot;')
    ?.replace(/'/g, '&#039;')
}
