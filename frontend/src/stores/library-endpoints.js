import endpoints from '@/api/endpoints'
import { defineStore } from 'pinia'

export const useEndpointsStore = defineStore('endpoints', {
  state: () => ({
    endpoints: [],
    total: 0,
  }),

  actions: {
    fetchEndpoints() {
      return endpoints.get().then((resp) => {
        this.endpoints = resp.data.items
        this.total = resp.data.total
      })
    },
    fetchFilteredEndpoints(data) {
      return endpoints.getFiltered(data).then((resp) => {
        this.endpoints = resp.data.items
        this.total = resp.data.total
      })
    },
  },
})
