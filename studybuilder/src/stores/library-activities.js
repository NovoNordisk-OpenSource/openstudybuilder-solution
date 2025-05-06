import { ref } from 'vue'
import { defineStore } from 'pinia'
import activitiesApi from '@/api/activities'

export const useLibraryActivitiesStore = defineStore(
  'libraryActivities',
  () => {
    const activityGroups = ref([])
    const activitySubGroups = ref([])

    function getGroupsAndSubgroups() {
      activitiesApi
        .get({ page_size: 0 }, 'activity-sub-groups')
        .then((resp) => {
          activitySubGroups.value = resp.data.items
        })
      activitiesApi.get({ page_size: 0 }, 'activity-groups').then((resp) => {
        activityGroups.value = resp.data.items
      })
    }

    return {
      activityGroups,
      activitySubGroups,
      getGroupsAndSubgroups,
    }
  }
)
