<template>
  <InstanceTable
    type="objective"
    :instances="objectives"
    base-url="/objectives"
    export-object-label="Objectives"
    column-data-resource="objectives"
    :items-length="total"
    :fetching-function="fetchFilteredObjectives"
  />
</template>

<script>
import InstanceTable from './InstanceTable.vue'
import { useObjectivesStore } from '@/stores/library-objectives'
import { computed } from 'vue'

export default {
  components: {
    InstanceTable,
  },
  setup() {
    const objectivesStore = useObjectivesStore()

    return {
      fetchFilteredObjectives: objectivesStore.fetchFilteredObjectives,
      total: computed(() => objectivesStore.total),
      objectives: computed(() => objectivesStore.objectives),
    }
  },
}
</script>
