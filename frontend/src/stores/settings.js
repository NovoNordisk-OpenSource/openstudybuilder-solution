import { ref } from 'vue'
import { defineStore } from 'pinia'
import systemSettings from '@/api/settings'

export const useSettingsStore = defineStore('settings', () => {
  // null until GET /system/settings succeeds; until then the study number
  // field skips its browser pre-check and the API validates instead.
  const settings = ref(null)
  let settingsPromise = null

  // Settings only change on redeploy, so every form shares one request per
  // session. A failed request is not cached, so the next caller retries.
  function fetchSettings() {
    if (settings.value) {
      return Promise.resolve(settings.value)
    }
    if (!settingsPromise) {
      settingsPromise = systemSettings
        .getSettings()
        .then((resp) => {
          settings.value = resp.data
          return settings.value
        })
        .catch((error) => {
          // The repository interceptor has already shown the error toast.
          console.error('Failed to load system settings', error)
          return null
        })
        .finally(() => {
          settingsPromise = null
        })
    }
    return settingsPromise
  }

  return { settings, fetchSettings }
})
