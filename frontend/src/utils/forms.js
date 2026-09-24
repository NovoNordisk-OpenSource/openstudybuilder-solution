import _isEqual from 'lodash/isEqual'

/*
 ** Compute differences between 2 forms, first form being considered as
 ** the reference one. If any difference is found in form2, it will be returned in a new Object.
 */
function getDifferences(form1, form2) {
  const keys1 = Object.keys(form1).sort()
  const keys2 = Object.keys(form2).sort()
  const result = {}

  for (const key of keys1) {
    if (!_isEqual(form1[key], form2[key])) {
      result[key] = form2[key]
    }
  }
  for (const key of keys2) {
    if (!keys1.includes(key)) {
      result[key] = form2[key]
    }
  }
  return result
}

export default {
  getDifferences,
}
