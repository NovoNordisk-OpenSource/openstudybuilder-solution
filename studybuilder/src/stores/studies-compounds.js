import { defineStore } from 'pinia'
import study from '@/api/study'

export const useStudiesCompoundsStore = defineStore('studiesCompounds', {
  state: () => ({
    studyCompounds: [],
    studyCompoundTotal: 0,
    studyCompounds__Loading: false,
    studyCompoundDosings: [],
    studyCompoundDosingTotal: 0,
  }),

  getters: {
    getStudyCompoundsByTypeOfTreatment: (state) => (typeOfTreatmentUid) => {
      return state.studyCompounds.filter(
        (item) => item.type_of_treatment.term_uid === typeOfTreatmentUid
      )
    },
    getNAStudyCompoundsByTypeOfTreatment: (state) => (typeOfTreatmentUid) => {
      return state.studyCompounds.filter(
        (item) =>
          item.type_of_treatment.term_uid === typeOfTreatmentUid &&
          !item.compound
      )
    },
    getStudyCompoundDosingsByStudyCompound: (state) => {
      const result = {}
      for (const compoundDosing of state.studyCompoundDosings) {
        const uid = compoundDosing.study_compound.study_compound_uid
        if (result[uid] === undefined) {
          result[uid] = []
        }
        result[uid].push(compoundDosing)
      }
      return result
    },
  },

  actions: {
    async fetchStudyCompounds(data) {
      this.studyCompounds__Loading = true
      let respData
      const studyUid = data.studyUid
      delete data.studyUid
      await study.getStudyCompounds(studyUid, data).then((resp) => {
        this.studyCompounds = resp.data.items
        this.studyCompoundTotal = resp.data.total
        this.studyCompounds__Loading = false
        respData = resp
      })
      return respData
    },
    addStudyCompound({ studyUid, data }) {
      study.selectStudyCompound(studyUid, data).then((resp) => {
        this.studyCompounds.push(resp.data)
      })
    },
    updateStudyCompound({ studyUid, studyCompoundUid, data }) {
      return study
        .updateStudyCompound(studyUid, studyCompoundUid, data)
        .then((resp) => {
          this.studyCompounds.filter((item, pos) => {
            if (item.study_compound_uid === studyCompoundUid) {
              this.studyCompounds[pos] = resp.data
              return true
            }
            return false
          })
        })
    },
    deleteStudyCompound(studyUid, studyCompoundUid) {
      return study.deleteStudyCompound(studyUid, studyCompoundUid).then(() => {
        this.studyCompounds = this.studyCompounds.filter(function (item) {
          return item.study_compound_uid !== studyCompoundUid
        })
      })
    },
    fetchStudyCompoundDosings(studyUid) {
      study.getStudyCompoundDosings(studyUid).then((resp) => {
        this.studyCompoundDosings = resp.data.items
        this.studyCompoundDosingTotal = resp.data.total
      })
    },
    addStudyCompoundDosing({ studyUid, data }) {
      return study.addStudyCompoundDosing(studyUid, data).then(() => {
        this.studyCompoundDosings.unshift(data)
      })
    },
    updateStudyCompoundDosing({ studyUid, studyCompoundDosingUid, data }) {
      delete data.study_compound
      return study
        .updateStudyCompoundDosing(studyUid, studyCompoundDosingUid, data)
        .then((resp) => {
          this.studyCompoundDosings.filter((item, pos) => {
            if (item.study_compound_dosing_uid === studyCompoundDosingUid) {
              this.studyCompoundDosings[pos] = resp.data
              return true
            }
            return false
          })
        })
    },
    deleteStudyCompoundDosing(studyUid, studyCompoundDosingUid) {
      return study
        .deleteStudyCompoundDosing(studyUid, studyCompoundDosingUid)
        .then(() => {
          this.studyCompoundDosings = this.studyCompoundDosings.filter(
            function (item) {
              return item.study_compound_dosing_uid !== studyCompoundDosingUid
            }
          )
        })
    },
  },
})
