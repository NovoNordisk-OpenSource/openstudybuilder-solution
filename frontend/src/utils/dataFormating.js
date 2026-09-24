import { i18n } from '@/plugins/i18n'

function lagTimes(value) {
  return value
    .map(
      (item) => `${item.sdtm_domain_label}: ${item.value} ${item.unit_label}`
    )
    .join(', ')
}

function numericValue(value) {
  return `${value.value} ${value.unit_label}`
}

function numericValues(value) {
  return value.map((item) => numericValue(item)).join(', ')
}

function pharmacologicalClasses(value) {
  if (value === undefined || value === null) {
    return ''
  }
  return value
    .map((item) =>
      item !== null && item.pclass_name
        ? `${item.pclass_name} (${item.pclass_id})`
        : null
    )
    .filter((pclass) => pclass !== null)
    .join(', ')
}

function yesno(value) {
  if (value === undefined || value === null) {
    return ''
  }
  return value ? i18n.t('_global.yes') : i18n.t('_global.no')
}

function substances(value) {
  return value
    .map((item) => `${item.substance_name} (${item.substance_unii})`)
    .join(', ')
}

function names(value) {
  if (value === undefined || value === null) {
    return ''
  }
  return value.map((item) => `${item.name}`).join(', ')
}

function itemNames(value) {
  if (value === undefined || value === null) {
    return ''
  }
  value = value
    .map((item) => (item.item_name ? `${item.item_name}` : ''))
    .join(', ')
    .replaceAll(' ,', '')
  if (value === ',' || value === ', ') {
    return ''
  }
  return value
}

function terms(value) {
  if (!value) {
    return ''
  }
  return value.map((item) => item.name.sponsor_preferred_name).join(', ')
}

function footnoteSymbol(value) {
  if (!value) {
    return ''
  }
  const alfabet = 'abcdefghijklmnopqrstuvwxyz'
  const alfabetArray = alfabet.split('')

  if (value <= 25) {
    return alfabetArray[value - 1]
  } else {
    return `z${value - 25}`
  }
}

export default {
  lagTimes,
  numericValue,
  numericValues,
  pharmacologicalClasses,
  substances,
  yesno,
  names,
  terms,
  itemNames,
  footnoteSymbol,
}
