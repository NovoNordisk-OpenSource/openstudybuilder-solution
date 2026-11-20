const PLACEHOLDER_REGEX = /\[([^[\]]+)\]/g

/*
 ** Split a template name into literal and placeholder parts.
 **
 ** A placeholder is `[NAME]` where NAME contains no bracket and is one of the
 ** template's parameter names. Any other bracket text is literal, e.g.
 ** `[see note]` or the outer brackets of `[a [Activity] b]`.
 ** Placeholder parts carry the parameter name without brackets.
 */
function splitTemplate(template, parameterNames) {
  const result = []

  if (typeof template !== 'string') {
    return result
  }
  const names = new Set(parameterNames || [])
  let lastIndex = 0
  for (const match of template.matchAll(PLACEHOLDER_REGEX)) {
    if (!names.has(match[1])) {
      continue
    }
    if (match.index > lastIndex) {
      result.push({
        isParameter: false,
        value: template.slice(lastIndex, match.index),
      })
    }
    result.push({ isParameter: true, value: match[1] })
    lastIndex = match.index + match[0].length
  }
  if (lastIndex < template.length) {
    result.push({ isParameter: false, value: template.slice(lastIndex) })
  }
  return result
}

function getTemplateParametersFromTemplate(template, parameterNames) {
  return splitTemplate(template, parameterNames)
    .filter((part) => part.isParameter)
    .map((part) => part.value)
}

/*
 ** Encode literal brackets as HTML entities, the way the API does when it
 ** generates an instance name, so that the only raw brackets left in an
 ** instance name are filled placeholders.
 */
function escapeBrackets(text) {
  return text.replaceAll('[', '&#91;').replaceAll(']', '&#93;')
}

export default {
  splitTemplate,
  getTemplateParametersFromTemplate,
  escapeBrackets,
}
