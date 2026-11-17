import { computed } from 'vue'
import visitConstants from '@/constants/visits'
import codelists from '@/utils/codelists'
import { useEpochsStore } from '@/stores/studies-epochs'

// Special types resolve to term_uid by submission value (see constants/visits.js); an absent one is null
export function useVisitTypeTerms(visitTypes) {
  const epochsStore = useEpochsStore()

  function findVisitTypeUid(submissionValue) {
    return codelists.findTermUidBySubmissionValue(
      visitTypes.value,
      submissionValue,
      'VisitType'
    )
  }
  const unscheduledVisitTypeUid = computed(() =>
    findVisitTypeUid(visitConstants.SUBMVAL_VISIT_TYPE_UNSCHEDULED)
  )
  const nonVisitTypeUid = computed(() =>
    findVisitTypeUid(visitConstants.SUBMVAL_VISIT_TYPE_NON_VISIT)
  )
  const earlyDiscontinuationVisitTypeUid = computed(() =>
    findVisitTypeUid(visitConstants.SUBMVAL_VISIT_TYPE_EARLY_DISCONTINUATION)
  )
  // The types whose visit window is the fixed -9999/9999 placeholder.
  const fixedWindowVisitTypeUids = computed(() =>
    [
      unscheduledVisitTypeUid.value,
      nonVisitTypeUid.value,
      earlyDiscontinuationVisitTypeUid.value,
    ].filter(Boolean)
  )

  // Assisted mode excludes timing-less types; manual mode allows all but the global anchor
  function canDuplicateVisit(visit) {
    if (!visit || visit.is_global_anchor_visit) {
      return false
    }
    if (epochsStore.manualVisitMode === true) {
      return true
    }
    return (
      ![
        visitConstants.CLASS_NON_VISIT,
        visitConstants.CLASS_UNSCHEDULED_VISIT,
        visitConstants.CLASS_MANUALLY_DEFINED_VISIT,
      ].includes(visit.visit_class) &&
      visit.visit_subclass !==
        visitConstants.SUBCLASS_ANCHOR_VISIT_IN_GROUP_OF_SUBV &&
      !fixedWindowVisitTypeUids.value.includes(visit.visit_type?.term_uid)
    )
  }

  return {
    unscheduledVisitTypeUid,
    nonVisitTypeUid,
    earlyDiscontinuationVisitTypeUid,
    fixedWindowVisitTypeUids,
    canDuplicateVisit,
  }
}
