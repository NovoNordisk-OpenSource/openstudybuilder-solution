import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSoaExpandStateStore = defineStore('soaExpandState', () => {
  const statesByStudy = ref({})

  function save(studyUid, state) {
    statesByStudy.value[studyUid] = state
  }

  function get(studyUid) {
    return statesByStudy.value[studyUid]
  }

  return {
    save,
    get,
  }
})
