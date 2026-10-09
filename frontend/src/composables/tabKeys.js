import { ref } from 'vue'

export function useTabKeys(options = {}) {
  const { persist = false } = options
  const tabKeys = ref({})

  const updateTabKey = (value) => {
    if (tabKeys.value[value] === undefined) {
      tabKeys.value[value] = 0
    }
    if (persist) {
      return
    }
    tabKeys.value[value]++
  }

  return { tabKeys, updateTabKey }
}
