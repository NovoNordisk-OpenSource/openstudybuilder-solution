import dataFormating from '@/utils/dataFormating'
import { DateTime } from 'luxon'

export default {
  /*
   ** Return a human readable version of the given date string.
   */
  date(value) {
    return DateTime.fromISO(value)
      .setLocale('en')
      .toLocaleString(DateTime.DATETIME_MED)
  },

  /*
   ** Display a boolean value as a yes/no alternative.
   */
  yesno(value) {
    return dataFormating.yesno(value)
  },

  /*
   ** Display a list of objects names
   */
  names(value) {
    return dataFormating.names(value)
  },

  /*
   ** Display a list of terms
   */
  terms(value) {
    return dataFormating.terms(value)
  },

  /*
   ** Display order as a letter, eg. 1 -> a, 2 ->b. Numbers after 26 (letter z) are converted to z1, z2...
   */
  footnoteSymbol(value) {
    return dataFormating.footnoteSymbol(value)
  },

  /*
   ** Display a list of objects names
   */
  itemNames(value) {
    return dataFormating.itemNames(value)
  },

  /*
   ** Display a list of items separated by a comma
   */
  itemList(value) {
    return value.join(', ')
  },
}

// /*
// ** Remove square brackets from the given value.
// */
// Vue.filter('stripBrackets', function (value) {
//   return value.replaceAll(/\[|\]/g, '')
// })

// /*
// ** Display a list of terms
// */
// Vue.filter('terms', dataFormating.terms)

// /*
// ** Display a list of objects names
// */
// Vue.filter('names', dataFormating.names)

// /*
// ** Display a list of objects names
// */
// Vue.filter('itemNames', dataFormating.itemNames)

// /*
// ** Display a list of lag times
// */
// Vue.filter('lagTimes', dataFormating.lagTimes)

// /*
// ** Display a list of substances
// */
// Vue.filter('substances', dataFormating.substances)

// /*
// ** Display a list of pharmacological classes
// */
// Vue.filter('pharmacologicalClasses', dataFormating.pharmacologicalClasses)

// /*
// ** Display a list of items separated by a comma
// */
// Vue.filter('itemList', function (value) {
//   return value.join(', ')
// })

// /*
// ** Display order as a letter, eg. 1 -> a, 2 ->b. Numbers after 26 (letter z) are converted to z1, z2...
// */
// Vue.filter('footnoteSymbol', dataFormating.footnoteSymbol)
