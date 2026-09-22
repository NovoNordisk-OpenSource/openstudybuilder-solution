import { computed, onMounted } from 'vue'
import { useAppStore } from '@/stores/app'

export function useEditableLibraries() {
  const appStore = useAppStore()

  // Reuse the app store's cached editable-libraries list (already filtered
  // against EXCLUDED_LIBRARIES) instead of each form issuing its own
  // GET /libraries — the sidebar populates it once on app mount.
  const libraries = computed(() => appStore.ctLibraries)

  const showDropdown = computed(() => libraries.value.length > 1)

  onMounted(() => {
    // Falls back to fetching if the sidebar hasn't loaded the list yet (or
    // isn't mounted at all); fetchCtLibraries() is a no-op once loaded and
    // shares an in-flight request with any other concurrent caller.
    if (!appStore.ctLibrariesLoaded) {
      appStore.fetchCtLibraries()
    }
  })

  return { libraries, showDropdown }
}
