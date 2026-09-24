import libConstants from '@/constants/libraries'
import numericValuesWithUnit from '@/api/concepts/numericValuesWithUnit'

export function useNumericValues() {
  const createNumericValue = async (item) => {
    item.library_name = libConstants.LIBRARY_SPONSOR
    const resp = await numericValuesWithUnit.create(item)
    return resp.data.uid
  }

  const createNumericValues = async (items) => {
    const result = []
    for (const item of items) {
      if (item.value && item.unit_definition_uid) {
        result.push(await createNumericValue(item))
      }
    }
    return result
  }
  return { createNumericValue, createNumericValues }
}
