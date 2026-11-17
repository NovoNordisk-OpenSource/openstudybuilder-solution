import templateParameters from '@/utils/templateParameters'

function getInternalApiName(template, values) {
  /*
   * Shall return Template [value1 , value2] or Template [value1  value2], or Template [value1 or value2]
   *
   * Literal brackets of the template and brackets inside values are encoded as
   * HTML entities, as the API does when it generates the instance name.
   */
  if (!values) {
    return template
  }
  const escape = templateParameters.escapeBrackets
  const parts = templateParameters.splitTemplate(
    template,
    values.map((value) => value.name)
  )
  let result = ''
  let paramIndex = 0
  for (const part of parts) {
    if (!part.isParameter) {
      result += escape(part.value)
      continue
    }
    const value = values[paramIndex]
    paramIndex++
    if (!value) {
      continue
    }
    if (value.name !== 'TextValue' && value.name !== 'NumericValue') {
      if (value.selectedValues && value.selectedValues.length) {
        const valueNames = value.selectedValues.map((v) => escape(v.name))
        const separator = value.selectedSeparator
          ? ' ' + value.selectedSeparator.trim() + ' '
          : '  '
        const concatenation = valueNames.join(separator)
        result += `[${concatenation}]`
      } else {
        result += `[${value.name}]`
      }
    } else {
      result += `[${escape(String(value.selectedValues))}]`
    }
  }
  return result
}

export default { getInternalApiName }
