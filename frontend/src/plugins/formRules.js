import { i18n } from '@/plugins/i18n'

const formValidationRules = {
  required: function (value) {
    let result = true
    if (value === undefined || value === null) {
      result = false
    } else if (Array.isArray(value) && !value.length) {
      result = false
    } else {
      result = !!String(value).trim().length
    }
    return result || i18n.t('_errors.required')
  },

  requiredIfNotNA: function (value, target) {
    let valueIsSet = value !== undefined && value !== null
    if (valueIsSet && typeof value === 'object') {
      if (Object.keys(value).length === 0) {
        valueIsSet = false
      }
    }
    const result = valueIsSet || target === 'true' || target === true
    return result || i18n.t('_errors.required')
  },

  atleastone: function (value, target) {
    const valueIsUnset =
      value === undefined || value === null || Object.keys(value).length === 0
    const targetIsUnset =
      target === undefined ||
      target === null ||
      Object.keys(target).length === 0
    const result = !(valueIsUnset && targetIsUnset)

    return result || i18n.t('_errors.select_at_least_one')
  },

  oneselected: function (value, target) {
    const valueIsUnset =
      value === undefined || value === null || Object.keys(value).length === 0
    const targetIsUnset =
      target === undefined ||
      target === null ||
      Object.keys(target).length === 0
    const result = !(!valueIsUnset && !targetIsUnset)
    return result || i18n.t('_errors.exclusive_select')
  },

  max: function (value, length) {
    let result = true
    if (value !== undefined && value !== null) {
      if (Array.isArray(value)) {
        result = value.every((val) => formValidationRules.max(val, length))
      } else {
        result = [...String(value)].length <= Number(length)
      }
    }
    return result || i18n.t('_errors.max_length_reached', { length })
  },

  max_value: function (value, max) {
    let result = true
    if (value !== undefined && value !== null) {
      if (Array.isArray(value)) {
        result =
          value.length > 0 &&
          value.every((val) => formValidationRules.max_value(val, max))
      } else {
        result = Number(value) <= Number(max)
      }
    }
    return result || i18n.t('_errors.max_value_reached', { max })
  },

  min_value: function (value, min) {
    let result = true
    if (value !== undefined && value !== null) {
      if (Array.isArray(value)) {
        result =
          value.length > 0 &&
          value.every((val) => formValidationRules.min_value(val, min))
      } else {
        result = Number(value) >= Number(min)
      }
    }
    return result || i18n.t('_errors.min_value_reached', { min })
  },

  numeric: function (value) {
    let result = true
    if (value !== undefined && value !== null) {
      const testValue = (val) => {
        const strValue = String(val)
        return strValue.length === 0 || /^[0-9]+$/.test(strValue)
      }

      result = Array.isArray(value) ? value.every(testValue) : testValue(value)
    }
    return result || i18n.t('_errors.numeric')
  },

  sameAs: function (value, target) {
    let result = true
    if (value !== undefined && value !== null) {
      result = value.toLowerCase() === [target].join(',').toLowerCase()
    }
    return result || i18n.t('_errors.identical_name')
  },

  uppercaseAlphanumeric: function (value) {
    let result = true
    if (value !== undefined && value !== null && String(value).length > 0) {
      result = /^[A-Z0-9]+$/.test(String(value))
    }
    return result || i18n.t('_errors.uppercase_alphanumeric')
  },

  oneOfTwo: function (first, second, errorMessage) {
    let result = false
    if (first || second) {
      result = true
    }
    return result || errorMessage
  },
}

export default {
  install: (app) => {
    app.provide('formRules', formValidationRules)
  },
}
