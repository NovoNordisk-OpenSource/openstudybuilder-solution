import { ref } from 'vue'
import { defineStore } from 'pinia'
import api from '@/api/featureFlags'

export const useFeatureFlagsStore = defineStore('featureFlags', () => {
  const featureFlags = ref({})

  async function fetchFeatureFlags() {
    const resp = await api.get()
    featureFlags.value = {}
    for (const flag of resp.data) {
      featureFlags.value[flag.name] = flag.enabled
    }
  }

  function getFeatureFlag(name) {
    return featureFlags.value[name] || false
  }

  return { featureFlags, fetchFeatureFlags, getFeatureFlag }
})
