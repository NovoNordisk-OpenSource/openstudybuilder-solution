import footnotes from '@/api/footnotes'
import { defineStore } from 'pinia'

export const useFootnotesStore = defineStore('footnotes', {
  state: () => ({
    footnotes: [],
    total: 0,
  }),

  actions: {
    fetchOFootnotes() {
      return footnotes.get().then((resp) => {
        this.footnotes = resp.data.items
        this.total = resp.data.total
      })
    },
    fetchFilteredFootnotes(data) {
      return footnotes.getFiltered(data).then((resp) => {
        this.footnotes = resp.data.items
        this.total = resp.data.total
      })
    },
  },
})
