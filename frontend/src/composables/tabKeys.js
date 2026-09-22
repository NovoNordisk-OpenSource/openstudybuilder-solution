import { ref } from 'vue'

export function useTabKeys() {
  const tabKeys = ref({})

  const updateTabKey = (value) => {
    if (tabKeys.value[value] === undefined) {
      tabKeys.value[value] = 0
    }
    tabKeys.value[value]++
  }

  return { tabKeys, updateTabKey }
}
