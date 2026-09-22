function getInternalApiName(template, values) {
  /*
   * Shall return Template [value1 , value2] or Template [value1  value2], or Template [value1 or value2]
   *
   */
  if (!values || !values.length) {
    return template
  }
  let result = ''
  let paramIndex = 0
  let inParam = false
  for (const c of template) {
    if (c === '[') {
      inParam = true
    } else if (c === ']') {
      if (
        values[paramIndex].name !== 'TextValue' &&
        values[paramIndex].name !== 'NumericValue'
      ) {
        if (
          values[paramIndex].selectedValues &&
          values[paramIndex].selectedValues.length
        ) {
          const valueNames = values[paramIndex].selectedValues.map(
            (v) => v.name
          )
          const separator = values[paramIndex].selectedSeparator
            ? ' ' + values[paramIndex].selectedSeparator.trim() + ' '
            : '  '
          const concatenation = valueNames.join(separator)
          result += `[${concatenation}]`
        } else {
          result += `[${values[paramIndex].name}]`
        }
      } else {
        result += `[${values[paramIndex].selectedValues}]`
      }
      paramIndex++
      inParam = false
    } else if (!inParam) {
      result += c
    }
  }
  return result
}

export default { getInternalApiName }
