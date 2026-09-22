import objectives from '@/api/objectives'
import { defineStore } from 'pinia'

export const useObjectivesStore = defineStore('objectives', {
  state: () => ({
    objectives: [],
    total: 0,
  }),

  actions: {
    fetchObjectives() {
      return objectives.get().then((resp) => {
        this.objectives = resp.data.items
        this.total = resp.data.total
      })
    },
    fetchFilteredObjectives(data) {
      return objectives.getFiltered(data).then((resp) => {
        this.objectives = resp.data.items
        this.total = resp.data.total
      })
    },
  },
})
