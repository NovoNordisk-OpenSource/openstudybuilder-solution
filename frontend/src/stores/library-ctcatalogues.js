import { defineStore } from 'pinia'
import controlledTerminology from '@/api/controlledTerminology'

export const useCtCataloguesStore = defineStore('ctcatalogues', {
  state: () => ({
    catalogues: [],
    currentCataloguePage: 1,
  }),

  actions: {
    fetchCatalogues() {
      return controlledTerminology.getCatalogues().then((resp) => {
        this.catalogues = resp.data
      })
    },
  },
})
