import { ref } from 'vue'
import { defineStore } from 'pinia'
import api from '@/api/standardsImport/typeDescriptions'

export const useStandardsImportTypeDescriptionsStore = defineStore(
  'standardsImportTypeDescriptions',
  () => {
    const descriptions = ref({})
    const loaded = ref(false)

    async function fetchTypeDescriptions() {
      if (loaded.value) {
        return
      }
      const resp = await api.get()
      descriptions.value = resp.data
      loaded.value = true
    }

    function getValueDescription(enumKey, value) {
      return descriptions.value[enumKey]?.values?.[value] || null
    }

    return { descriptions, fetchTypeDescriptions, getValueDescription }
  }
)
