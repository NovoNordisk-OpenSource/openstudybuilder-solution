<template>
  <div>
    <InstanceTable
      type="activity_instruction"
      :instances="activityInstructions"
      base-url="/activity-instructions"
      export-object-label="ActivityInstructions"
      column-data-resource="activity-instructions"
      :items-length="total"
      :fetching-function="fetchFilteredActivityInstructions"
    />
  </div>
</template>

<script>
import InstanceTable from './InstanceTable.vue'
import { useActivityInstructionsStore } from '@/stores/library-activity-instructions'
import { computed } from 'vue'

export default {
  components: {
    InstanceTable,
  },
  setup() {
    const activityInstructionsStore = useActivityInstructionsStore()

    return {
      fetchFilteredActivityInstructions:
        activityInstructionsStore.fetchFilteredActivityInstructions,
      total: computed(() => activityInstructionsStore.total),
      activityInstructions: computed(
        () => activityInstructionsStore.activityInstructions
      ),
    }
  },
}
</script>
