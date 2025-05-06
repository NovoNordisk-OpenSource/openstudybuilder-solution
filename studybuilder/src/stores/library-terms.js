import { defineStore } from 'pinia'
import controlledTerminology from '@/api/controlledTerminology'

export const useTermsStore = defineStore('terms', {
  state: () => ({
    terms: [],
  }),

  actions: {
    async fetchTerms(filters, inCodelist) {
      const params = {
        page_size: 40,
        compact_response: true,
        in_codelist: inCodelist,
      }
      if (filters) {
        params.filters = filters
      }
      const resp = await controlledTerminology.getCodelistTermsNames(params)
      const nameMap = {}
      resp.data.items.forEach((item) => {
        if (nameMap[item.sponsor_preferred_name]) {
          nameMap[item.sponsor_preferred_name].push(item.term_uid)
        } else {
          nameMap[item.sponsor_preferred_name] = [item.term_uid]
        }
      })
      const items = []
      for (const name in nameMap) {
        items.push({
          sponsor_preferred_name: name,
          term_uids: nameMap[name],
        })
      }
      this.terms = items
    },
    reset() {
      this.terms = []
    },
  },
})
