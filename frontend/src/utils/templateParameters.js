function getTemplateParametersFromTemplate(template) {
  const result = []
  let currentParam = null

  for (const c of template) {
    if (c === '[') {
      currentParam = ''
    } else if (c === ']') {
      if (currentParam) {
        result.push(currentParam)
      }
      currentParam = null
    } else if (currentParam !== null) {
      currentParam += c
    }
  }
  return result
}

export default {
  getTemplateParametersFromTemplate,
}
