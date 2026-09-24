import activityInstructions from '@/api/activityInstructions'
import { defineStore } from 'pinia'

export const useActivityInstructionsStore = defineStore(
  'activityInstructions',
  {
    state: () => ({
      activityInstructions: [],
      total: 0,
    }),

    actions: {
      fetchActivityInstructions() {
        return activityInstructions.get().then((resp) => {
          this.activityInstructions = resp.data.items
          this.total = resp.data.total
        })
      },
      fetchFilteredActivityInstructions(data) {
        return activityInstructions.getFiltered(data).then((resp) => {
          this.activityInstructions = resp.data.items
          this.total = resp.data.total
        })
      },
    },
  }
)
