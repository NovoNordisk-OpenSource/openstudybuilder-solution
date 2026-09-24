import { defineStore } from 'pinia'
import study from '@/api/study'

export const useStudiesManageStore = defineStore('studiesManage', {
  state: () => ({
    studies: {
      items: [],
    },
    projects: [],
  }),

  getters: {
    getProjectByNumber: (state) => (number) => {
      return state.projects.find((project) => project.project_number === number)
    },
  },

  actions: {
    fetchStudies() {
      return study.getAll().then((resp) => {
        this.studies = resp.data
      })
    },
    addStudy(data) {
      return new Promise((resolve, reject) => {
        study
          .create(data)
          .then((resp) => {
            this.studies.items.unshift(resp.data)
            resolve(resp)
          })
          .catch((error) => {
            reject(error)
          })
      })
    },
    editStudyIdentification(uid, data) {
      return new Promise((resolve, reject) => {
        study
          .updateIdentification(uid, data)
          .then((resp) => {
            this.studies.items.filter((item, pos) => {
              if (item.uid === resp.data.uid) {
                this.studies.items[pos] = resp.data
                return true
              }
              return false
            })
            resolve(resp)
          })
          .catch((error) => {
            reject(error)
          })
      })
    },
    editStudyType(uid, data, parentUid) {
      return study.updateStudyType(uid, data, parentUid)
    },
    editStudyPopulation(uid, data, parentUid) {
      return study.updateStudyPopulation(uid, data, parentUid)
    },
    updateStudyIntervention(uid, data, parentUid) {
      return study.updateStudyIntervention(uid, data, parentUid)
    },
    fetchProjects() {
      return study.projects_all().then((resp) => {
        this.projects = resp.data.items
      })
    },
  },
})
