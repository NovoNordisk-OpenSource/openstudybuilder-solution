import { defineStore } from 'pinia'
import units from '@/api/units'

export const useUnitsStore = defineStore('units', {
  state: () => ({
    units: [],
    total: 0,
  }),

  actions: {
    fetchUnits(params) {
      return units.get({ params }).then((resp) => {
        this.units = resp.data.items
        this.total = resp.data.total
      })
    },
    addUnit(data) {
      return units.create(data).then((resp) => {
        this.units.unshift(resp.data)
      })
    },
    updateUnit({ uid, data }) {
      return units.edit(uid, data).then((resp) => {
        this.units.filter((item, pos) => {
          if (item.uid === uid) {
            this.units[pos] = resp.data
            return true
          }
          return false
        })
      })
    },
  },
})
