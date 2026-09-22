import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSoaContentLoadingStore = defineStore(
  'soaContentLoading',
  () => {
    const loading = ref(false)

    function changeLoadingState() {
      loading.value = !loading.value
    }

    return {
      loading,
      changeLoadingState,
    }
  }
)
