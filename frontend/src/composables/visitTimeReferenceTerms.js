import { ref, computed } from 'vue'
import terms from '@/api/controlledTerminology/terms'
import visitConstants from '@/constants/visits'
import codelists from '@/utils/codelists'

export function useVisitTimeReferenceTerms() {
  const contactModes = ref([])
  const timeReferences = ref([])

  // Resolved by submission value (see constants/visits.js); an absent term resolves to null and is logged
  const globalAnchorTermUid = computed(() =>
    codelists.findTermUidBySubmissionValue(
      timeReferences.value,
      visitConstants.SUBMVAL_TIMEREF_GLOBAL_ANCHOR_VISIT,
      'Time Point Reference'
    )
  )

  const anchorVisitInGroupTermUid = computed(() =>
    codelists.findTermUidBySubmissionValue(
      timeReferences.value,
      visitConstants.SUBMVAL_TIMEREF_ANCHOR_VISIT_IN_VISIT_GROUP,
      'Time Point Reference'
    )
  )

  const virtualVisitContactModeUid = computed(() =>
    codelists.findTermUidBySubmissionValue(
      contactModes.value,
      visitConstants.SUBMVAL_CONTACT_MODE_VIRTUAL_VISIT,
      'Visit Contact Mode'
    )
  )

  function fetchVisitTimeReferenceTerms() {
    return Promise.all([
      terms.getTermsByCodelist('contactModes').then((resp) => {
        contactModes.value = resp.data.items
      }),
      terms.getTermsByCodelist('timepointReferences').then((resp) => {
        timeReferences.value = resp.data.items
      }),
    ])
  }

  return {
    contactModes,
    timeReferences,
    globalAnchorTermUid,
    anchorVisitInGroupTermUid,
    virtualVisitContactModeUid,
    fetchVisitTimeReferenceTerms,
  }
}
