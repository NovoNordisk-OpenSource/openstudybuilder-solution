import { defineStore } from 'pinia'
import dataSuppliers from '@/api/dataSuppliers'

export const useDataSuppliersStore = defineStore('dataSuppliers', {
  state: () => ({
    items: [],
    totalItems: 0,
  }),

  actions: {
    fetchDataSuppliers(params) {
      if (!params) {
        params.total_count = true
      }
      return dataSuppliers.get({ params }).then((resp) => {
        this.items = resp.data.items
        this.totalItems = resp.data.total
      })
    },
  },
})
