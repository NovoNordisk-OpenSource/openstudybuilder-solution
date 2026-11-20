import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSoaContentLoadingStore = defineStore(
  'soaContentLoading',
  () => {
    const loading = ref(false)

    function setLoading(value) {
      loading.value = value
    }

    return {
      loading,
      setLoading,
    }
  }
)
