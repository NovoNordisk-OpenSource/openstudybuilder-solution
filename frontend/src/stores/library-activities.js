import { ref } from 'vue'
import { defineStore } from 'pinia'
import activitiesApi from '@/api/activities'

export const useLibraryActivitiesStore = defineStore(
  'libraryActivities',
  () => {
    const activityGroups = ref([])
    const activitySubGroups = ref([])

    function getGroupsAndSubgroups(filters = null, operator = 'and') {
      const params = { page_size: 0, operator }
      if (filters) {
        params.filters = filters
      }
      return Promise.all([
        activitiesApi.get(params, 'activity-sub-groups').then((resp) => {
          activitySubGroups.value = resp.data.items
        }),
        activitiesApi.get(params, 'activity-groups').then((resp) => {
          activityGroups.value = resp.data.items
        }),
      ])
    }

    return {
      activityGroups,
      activitySubGroups,
      getGroupsAndSubgroups,
    }
  }
)
