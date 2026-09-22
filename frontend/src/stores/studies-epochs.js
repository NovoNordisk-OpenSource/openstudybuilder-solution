import { ref } from 'vue'
import { defineStore } from 'pinia'
import studyEpochsApi from '@/api/studyEpochs'
import units from '@/api/units'
import unitConstants from '@/constants/units'
import visitConstants from '@/constants/visits'

export const useEpochsStore = defineStore('epochs', () => {
  const studyEpochs = ref([])
  const studyVisits = ref([])
  const totalVisits = ref(0)
  const allowedConfigs = ref([])
  const studyTimeUnits = ref([])

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

  function sanitizeNonManuallyDefinedVisitPayload(data) {
    delete data.visit_number
    delete data.unique_visit_number
    delete data.visit_short_name
    delete data.visit_name
  }

  function getStudyVisitPreview({ studyUid, input }) {
    if (input.visit_class !== visitConstants.CLASS_MANUALLY_DEFINED_VISIT) {
      sanitizeNonManuallyDefinedVisitPayload(input)
    }
    return studyEpochsApi.getStudyVisitPreview(studyUid, input)
  }

  async function addStudyVisit({ studyUid, input }) {
    if (input.visit_class !== visitConstants.CLASS_MANUALLY_DEFINED_VISIT) {
      sanitizeNonManuallyDefinedVisitPayload(input)
    }
    await studyEpochsApi.addStudyVisit(studyUid, input)
    await fetchStudyEpochs({ studyUid })
  }

  function updateStudyVisit({ studyUid, studyVisitUid, input }) {
    if (input.visit_class !== visitConstants.CLASS_MANUALLY_DEFINED_VISIT) {
      sanitizeNonManuallyDefinedVisitPayload(input)
    }
    return studyEpochsApi
      .updateStudyVisit(studyUid, studyVisitUid, input)
      .then(() => {
        fetchStudyEpochs({ studyUid })
      })
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
