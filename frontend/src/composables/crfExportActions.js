import { computed, defineAsyncComponent, shallowRef } from 'vue'
import { useFeatureFlagsStore } from '@/stores/feature-flags'

// Export actions contributed by extensions to the CRF viewers (Library → CRF
// Viewer, and the CRF Builder's CRF Viewer tab). Each
// src/extensions/*/crf-viewer/exportActions.js default-exports an array of
// { title, icon?, featureFlag?, component }; see src/extensions/README.md.
const extensionExportActionModules = import.meta.glob(
  '@/extensions/*/crf-viewer/exportActions.js',
  { eager: true, import: 'default' }
)

const registeredExportActions = Object.entries(
  extensionExportActionModules
).flatMap(([path, actions]) => {
  if (!Array.isArray(actions)) {
    console.error(
      `Ignoring CRF Viewer export actions from ${path}: not an array`
    )
    return []
  }
  return actions.flatMap((action, index) => {
    if (typeof action?.component !== 'function') {
      console.error(
        `Ignoring CRF Viewer export action #${index} from ${path}: component must be a loader function`
      )
      return []
    }
    return [
      {
        ...action,
        key: `${path}#${index}`,
        icon: action.icon || 'mdi-file-export-outline',
        dialog: defineAsyncComponent(action.component),
      },
    ]
  })
})

export function useCrfExportActions() {
  const featureFlagsStore = useFeatureFlagsStore()

  const exportActions = computed(() =>
    registeredExportActions.filter(
      (action) =>
        !action.featureFlag ||
        featureFlagsStore.getFeatureFlag(action.featureFlag) !== false
    )
  )
  // Shallow: the action holds a component definition, which must not be made reactive
  const activeExportAction = shallowRef(null)

  function openExportAction(action) {
    activeExportAction.value = action
  }

  function closeExportAction() {
    activeExportAction.value = null
  }

  return {
    exportActions,
    activeExportAction,
    openExportAction,
    closeExportAction,
  }
}
