import criteria from '@/api/criteria'
import { defineStore } from 'pinia'

export const useCriteriaStore = defineStore('criteria', {
  state: () => ({
    criteria: [],
    total: 0,
  }),

  actions: {
    fetchCriteria() {
      return criteria.get().then((resp) => {
        this.criteria = resp.data.items
        this.total = resp.data.total
      })
    },
    fetchFilteredCriteria(data) {
      return criteria.getFiltered(data).then((resp) => {
        this.criteria = resp.data.items
        this.total = resp.data.total
      })
    },
  },
})
