function clearEmptyHtml(html) {
  const regex = /^\s*(?:<[^>]+>\s*)+$/
  if (regex.test(html)) {
    return null
  }
  return html
}
export default {
  clearEmptyHtml,
}
