import { defineStore } from 'pinia'
import study from '@/api/study'

export const useStudyActivitiesStore = defineStore('studyActivities', {
  state: () => ({
    studyActivities: [],
    studyActivityInstances: [],
  }),

  getters: {
    sortedStudyActivities: (state) => {
      const result = {}
      for (const studyActivity of state.studyActivities) {
        const fgroup = studyActivity.study_soa_group.soa_group_term_name
        if (!result[fgroup]) {
          result[fgroup] = {}
        }
        const group =
          studyActivity.study_activity_group &&
          studyActivity.study_activity_group.activity_group_name
            ? studyActivity.study_activity_group.activity_group_name
            : '(not selected)'
        const subgroup =
          studyActivity.study_activity_subgroup &&
          studyActivity.study_activity_subgroup.activity_subgroup_name
            ? studyActivity.study_activity_subgroup.activity_subgroup_name
            : '(not selected)'
        if (!result[fgroup][group]) {
          result[fgroup][group] = {}
        }
        if (!result[fgroup][group][subgroup]) {
          result[fgroup][group][subgroup] = []
        }
        result[fgroup][group][subgroup].push(studyActivity)
      }
      return result
    },
  },

  actions: {
    async fetchStudyActivities(params) {
      const studyUid = params.studyUid
      delete params.studyUid
      if (!Object.prototype.hasOwnProperty.call(params, 'page_size')) {
        params.page_size = 0
      }
      if (!Object.prototype.hasOwnProperty.call(params, 'page_number')) {
        params.page_number = 1
      }
      const resp = await study.getStudyActivities(studyUid, params)
      this.studyActivities = resp.data.items
      return resp
    },
    async fetchStudyActivityInstances(params) {
      const studyUid = params.studyUid
      delete params.studyUid
      if (!Object.prototype.hasOwnProperty.call(params, 'page_size')) {
        params.page_size = 0
      }
      if (!Object.prototype.hasOwnProperty.call(params, 'page_number')) {
        params.page_number = 1
      }
      const resp = await study.getStudyActivityInstances(studyUid, params)
      this.studyActivityInstances = resp.data.items
      return resp
    },
    updateStudyActivityInstanceToLatest(studyUid, instanceUid) {
      return study.updateStudyActivityInstanceToLatest(studyUid, instanceUid)
    },
    updateStudyActivityInstance(studyUid, instanceUid, data) {
      return study.updateStudyActivityInstance(studyUid, instanceUid, data)
    },
    batchSelectStudyActivityInstances(studyUid, data) {
      return study.batchSelectStudyActivityInstances(studyUid, data)
    },
    deleteStudyActivityInstance(studyUid, instanceUid) {
      return study.deleteStudyActivityInstance(studyUid, instanceUid)
    },
  },
})
