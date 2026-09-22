import concepts from '@/api/concepts'
import pconstants from '@/constants/parameters'

/*
 ** Check if parameter is a constant (text or number) and format it properly
 */
async function formatConstantParameterValue(parameter) {
  const result = { ...parameter }
  let resp = null

  if (parameter.selectedValues && !Array.isArray(parameter.selectedValues)) {
    if (parameter.name === pconstants.NUM_VALUE) {
      const numData = {
        value: parameter.selectedValues,
        library_name: 'Sponsor',
        template_parameter: true,
      }
      resp = await concepts.create(numData, 'numeric-values')
    } else if (parameter.name === pconstants.TEXT_VALUE) {
      const textData = {
        name: parameter.selectedValues,
        name_sentence_case: parameter.selectedValues.toLowerCase(),
        library_name: 'Sponsor',
        template_parameter: true,
      }
      resp = await concepts.create(textData, 'text-values')
    }
    if (resp) {
      result.selectedValues = []
      result.selectedValues[0] = {
        name: resp.data.name,
        type: result.name,
        uid: resp.data.uid,
      }
    }
  }
  return result
}

/*
 ** Format parameter values in a way compatible with what API expects.
 */
async function formatParameterValues(parameters, onlyDefaultValues) {
  const result = []
  let position = 1

  for (let parameter of parameters) {
    if (onlyDefaultValues && !parameter.saveAsDefault) {
      position += 1
      continue
    }
    let conjunction = ''
    if (parameter.selectedSeparator) {
      conjunction = parameter.selectedSeparator.trim()
    }
    let index = 1
    const values = []
    const value = null

    parameter = await formatConstantParameterValue(parameter)
    if (parameter.selectedValues.length || !onlyDefaultValues) {
      parameter.selectedValues.forEach((value) => {
        values.push({
          index: index,
          type: parameter.name,
          name: value.name,
          uid: value.uid,
        })
        index += 1
      })
      result.push({
        position: position,
        conjunction: conjunction,
        terms: values,
        value: value,
      })
    }
    position += 1
  }
  return result
}

function getSeparator(conjunction) {
  if (conjunction === ',') {
    return ', '
  }
  return ' ' + conjunction + ' '
}

/*
 ** Load parameter values received from the API
 */
function loadParameterValues(parameterValues, parameters) {
  let index = 0
  parameterValues.forEach((item) => {
    if (item.terms.length) {
      item.terms.forEach((value) => {
        if (
          value.type === pconstants.NUM_VALUE ||
          value.type === pconstants.TEXT_VALUE
        ) {
          parameters[index] = {
            name: value.type,
            selectedSeparator: '',
            selectedValues: value.name,
          }
        } else {
          parameters[index].selectedSeparator = getSeparator(item.conjunction)
          if (parameters[index].selectedValues) {
            parameters[index].selectedValues.push({
              name: value.name,
              uid: value.uid,
              type: value.type,
            })
          } else {
            parameters[index].selectedValues = [
              {
                name: value.name,
                uid: value.uid,
                type: value.type,
              },
            ]
          }
        }
      })
    } else {
      parameters[index].skip = true
      parameters[index].selectedValues = []
    }
    index += 1
  })
}

export default {
  formatParameterValues,
  loadParameterValues,
}
