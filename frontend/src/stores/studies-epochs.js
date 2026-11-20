import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import studyEpochsApi from '@/api/studyEpochs'
import units from '@/api/units'
import unitConstants from '@/constants/units'
import visitConstants from '@/constants/visits'
import { useFeatureFlagsStore } from '@/stores/feature-flags'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export const useEpochsStore = defineStore('epochs', () => {
  const featureFlagsStore = useFeatureFlagsStore()
  const studiesGeneralStore = useStudiesGeneralStore()

  const studyEpochs = ref([])
  const studyVisits = ref([])
  const totalVisits = ref(0)
  const allowedConfigs = ref([])
  const studyTimeUnits = ref([])
  // null means not known (pending or failed), never a guess at assisted or manual
  const manualVisitMode = ref(null)
  const visitModeKnown = computed(() => manualVisitMode.value !== null)
  let visitModeRequestId = 0

  function fetchStudyVisitMode(studyUid) {
    // Reset first: the store outlives a change of study, so a stale mode must not linger
    manualVisitMode.value = null
    const requestId = ++visitModeRequestId
    return studyEpochsApi
      .getStudyVisitMode(studyUid)
      .then((resp) => {
        if (requestId === visitModeRequestId) {
          manualVisitMode.value = resp.data.manual_visit_mode
        }
      })
      .catch((error) => {
        // The repository interceptor has already shown the error toast.
        console.error('Failed to load study visit mode', error)
      })
  }

  function setStudyVisitMode(studyUid, manual) {
    return studyEpochsApi.setStudyVisitMode(studyUid, manual).then((resp) => {
      manualVisitMode.value = resp.data.manual_visit_mode
    })
  }

  // Lag time started as legacy MMA data: study_epoch_lag_time shows all three
  // fields, but only on studies migrated from MMA (the flag is global, the
  // marker is per study). AE lag time is also wanted on new studies, so
  // study_epoch_ae_lag_time shows that one field on every study.
  const visibleLagTimeFields = computed(() => {
    if (
      featureFlagsStore.getFeatureFlag('study_epoch_lag_time') &&
      studiesGeneralStore.migratedStudy
    ) {
      return ['ae_lag_time', 'hypo_lag_time', 'ce_lag_time']
    }
    if (featureFlagsStore.getFeatureFlag('study_epoch_ae_lag_time')) {
      return ['ae_lag_time']
    }
    return []
  })

  function fetchStudyVisits(studyUid, params) {
    return studyEpochsApi.getStudyVisits(studyUid, params).then((resp) => {
      studyVisits.value = resp.data.items
    })
  }

  function fetchFilteredStudyVisits(data) {
    const studyUid = data.studyUid
    delete data.studyUid
    return studyEpochsApi.getStudyVisits(studyUid, data).then((resp) => {
      studyVisits.value = resp.data.items
      totalVisits.value = resp.data.total
    })
  }

  // Strips naming the API rejects unless it's the user's to give; works on a copy
  function sanitizeNonManuallyDefinedVisitPayload(data) {
    if (
      manualVisitMode.value !== false ||
      data.visit_class === visitConstants.CLASS_MANUALLY_DEFINED_VISIT
    ) {
      return data
    }
    const sanitized = { ...data }
    delete sanitized.visit_number
    delete sanitized.unique_visit_number
    delete sanitized.visit_short_name
    delete sanitized.visit_name
    return sanitized
  }

  function getStudyVisitPreview({ studyUid, input }) {
    return studyEpochsApi.getStudyVisitPreview(
      studyUid,
      sanitizeNonManuallyDefinedVisitPayload(input)
    )
  }

  // Callers saving several visits in a row pass refreshEpochs: false and refresh once at the end
  async function addStudyVisit({ studyUid, input, refreshEpochs = true }) {
    await studyEpochsApi.addStudyVisit(
      studyUid,
      sanitizeNonManuallyDefinedVisitPayload(input)
    )
    if (refreshEpochs) {
      await fetchStudyEpochs({ studyUid })
    }
  }

  async function updateStudyVisit({
    studyUid,
    studyVisitUid,
    input,
    refreshEpochs = true,
  }) {
    await studyEpochsApi.updateStudyVisit(
      studyUid,
      studyVisitUid,
      sanitizeNonManuallyDefinedVisitPayload(input)
    )
    if (refreshEpochs) {
      await fetchStudyEpochs({ studyUid })
    }
  }

  async function deleteStudyVisit({ studyUid, studyVisitUid }) {
    await studyEpochsApi.deleteStudyVisit(studyUid, studyVisitUid)
    await fetchStudyEpochs({ studyUid })
  }

  function fetchStudyEpochs({ studyUid, data }) {
    return studyEpochsApi.getStudyEpochs(studyUid, data).then((resp) => {
      studyEpochs.value = resp.data.items
    })
  }

  function fetchFilteredStudyEpochs(data) {
    const studyUid = data.study_uid
    delete data.study_uid
    return studyEpochsApi.getFilteredEpochs(studyUid, data).then((resp) => {
      studyEpochs.value = resp.data.items
    })
  }

  function fetchAllowedConfigs() {
    return studyEpochsApi.getAllowedConfigs().then((resp) => {
      allowedConfigs.value = resp.data
    })
  }

  async function addStudyEpoch({ studyUid, input }) {
    return studyEpochsApi.addStudyEpoch(studyUid, input).then((resp) => {
      studyEpochs.value.unshift(resp.data)
    })
  }
  async function updateStudyEpoch({ studyUid, studyEpochUid, input }) {
    return studyEpochsApi
      .updateStudyEpoch(studyUid, studyEpochUid, input)
      .then((resp) => {
        studyEpochs.value.filter((item, pos) => {
          if (item.uid === resp.data.uid) {
            studyEpochs.value[pos] = resp.data
            return true
          }
          return false
        })
      })
  }

  function deleteStudyEpoch({ studyUid, studyEpochUid }) {
    return studyEpochsApi.deleteStudyEpoch(studyUid, studyEpochUid).then(() => {
      studyEpochs.value = studyEpochs.value.filter(function (item) {
        return item.uid !== studyEpochUid
      })
    })
  }

  function fetchStudyTimeUnits() {
    return units
      .getBySubset(unitConstants.TIME_UNIT_SUBSET_STUDY_TIME)
      .then((resp) => {
        studyTimeUnits.value = resp.data.items
      })
  }

  return {
    studyEpochs,
    studyVisits,
    totalVisits,
    allowedConfigs,
    studyTimeUnits,
    visibleLagTimeFields,
    manualVisitMode,
    visitModeKnown,
    fetchStudyVisitMode,
    setStudyVisitMode,
    fetchStudyVisits,
    fetchFilteredStudyVisits,
    getStudyVisitPreview,
    addStudyVisit,
    updateStudyVisit,
    deleteStudyVisit,
    fetchStudyEpochs,
    fetchFilteredStudyEpochs,
    fetchAllowedConfigs,
    addStudyEpoch,
    updateStudyEpoch,
    deleteStudyEpoch,
    fetchStudyTimeUnits,
  }
})
