import { defineStore } from 'pinia'
import study from '@/api/study'

export const useStudyDataSuppliersStore = defineStore('studyDataSuppliers', {
  state: () => ({
    studyDataSuppliers: [],
    totalItems: 0,
    loading: false,
  }),

  getters: {
    sortedStudyDataSuppliers: (state) => {
      // Group study data suppliers by activity or other criteria if needed
      return state.studyDataSuppliers
    },
  },

  actions: {
    async fetchStudyDataSuppliers(params) {
      this.loading = true
      try {
        const studyUid = params.studyUid
        delete params.studyUid

        // Add total_count by default if not specified
        if (!Object.prototype.hasOwnProperty.call(params, 'total_count')) {
          params.total_count = true
        }

        const resp = await study.getStudyDataSuppliers(studyUid, params)
        this.studyDataSuppliers = resp.data.items
        this.totalItems = resp.data.total || 0
        return resp
      } finally {
        this.loading = false
      }
    },

    async getHeaders(studyUid, params) {
      return study.getStudyDataSuppliersHeaders(studyUid, params)
    },

    async getStudyDataSupplier(studyUid, studyDataSupplierUid) {
      return study.getStudyDataSupplier(studyUid, studyDataSupplierUid)
    },

    async updateStudyDataSupplier(studyUid, studyDataSupplierUid, data) {
      return study.updateStudyDataSupplier(studyUid, studyDataSupplierUid, data)
    },

    async updateStudyDataSupplierOrder(studyUid, studyDataSupplierUid, order) {
      return study.updateStudyDataSupplierOrder(
        studyUid,
        studyDataSupplierUid,
        order
      )
    },

    async deleteStudyDataSupplier(studyUid, studyDataSupplierUid) {
      return study.deleteStudyDataSupplier(studyUid, studyDataSupplierUid)
    },

    async getStudyDataSuppliersAuditTrail(studyUid) {
      return study.getStudyDataSuppliersAuditTrail(studyUid)
    },

    async fetchStudyDataSupplierAuditTrail(studyUid, studyDataSupplierUid) {
      return study.getStudyDataSupplierAuditTrail(
        studyUid,
        studyDataSupplierUid
      )
    },

    async syncStudyDataSuppliers(studyUid, suppliers) {
      return study.syncStudyDataSuppliers(studyUid, suppliers)
    },
  },
})
