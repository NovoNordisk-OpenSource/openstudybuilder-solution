import { ref } from 'vue'
import { defineStore } from 'pinia'
import statuses from '@/constants/statuses'
import activeSubstancesApi from '@/api/concepts/activeSubstances'
import termsApi from '@/api/controlledTerminology/terms'

export const useFormulationsStore = defineStore('formulations', () => {
  const activeSubstances = ref([])
  const adverseEvents = ref([])

  function fetchActiveSubstances() {
    activeSubstancesApi
      .getFiltered({
        page_size: 0,
        filters: { status: { v: [statuses.FINAL] } },
      })
      .then((resp) => {
        activeSubstances.value = resp.data.items
      })
  }

  function fetchAdverseEvents() {
    termsApi.getTermsByCodelist('adverseEvents', true).then((resp) => {
      adverseEvents.value = resp.data.items
    })
  }

  function initialize() {
    fetchActiveSubstances()
    fetchAdverseEvents()
  }

  return {
    activeSubstances,
    adverseEvents,
    fetchActiveSubstances,
    fetchAdverseEvents,
    initialize,
  }
})
