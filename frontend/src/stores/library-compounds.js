import { ref } from 'vue'
import { defineStore } from 'pinia'
import dictionaries from '@/api/dictionaries'

export const useCompoundsStore = defineStore('compounds', () => {
  const substances = ref([])

  function fetchSubstances() {
    return dictionaries.getSubstances().then((resp) => {
      substances.value = resp.data.items
    })
  }

  return { substances, fetchSubstances }
})
