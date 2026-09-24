import timeframes from '@/api/timeframes'
import { defineStore } from 'pinia'

export const useTimeframesStore = defineStore('timeframes', {
  state: () => ({
    timeframes: [],
    total: 0,
  }),

  actions: {
    fetchTimeframes() {
      return timeframes.get().then((resp) => {
        this.timeframes = resp.data.items
        this.total = resp.data.total
      })
    },
    fetchFilteredTimeframes(data) {
      return timeframes.getFiltered(data).then((resp) => {
        this.timeframes = resp.data.items
        this.total = resp.data.total
      })
    },
  },
})
