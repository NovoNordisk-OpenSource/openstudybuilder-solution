import { i18n } from '@/plugins/i18n'

// Python's \d, \w, \s and \b are Unicode-aware and JS's are not, and Python's
// $ also matches before a trailing newline. On printable ASCII the two
// engines agree, so the browser only pre-checks those values; the API
// validates every study number regardless.
const PRINTABLE_ASCII = /^[\x20-\x7e]*$/

function clearEmptyHtml(html) {
  const regex = /^\s*(?:<[^>]+>\s*)+$/
  if (regex.test(html)) {
    return null
  }
  return html
}

function validateStudyNumber(value, regexSetting) {
  if (value === undefined || value === null || value === '') {
    return true
  }
  const text = String(value)
  const regex = toFullMatchRegex(regexSetting?.regex)
  if (!regex || !PRINTABLE_ASCII.test(text) || regex.test(text)) {
    return true
  }
  return regexSetting.message || i18n.t('StudyForm.number_format_error')
}

function toFullMatchRegex(pattern) {
  if (!pattern) {
    return null
  }
  try {
    // Mirrors re.fullmatch. The "u" flag makes Python-only syntax (\A, \Z,
    // (?P<...>), {,n}, inline flags) a SyntaxError instead of a silent
    // mismatch, so such patterns are left to the API.
    return new RegExp(`^(?:${pattern})$`, 'u')
  } catch {
    return null
  }
}

export default {
  clearEmptyHtml,
  validateStudyNumber,
}
