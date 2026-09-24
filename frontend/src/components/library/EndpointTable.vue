<template>
  <div>
    <InstanceTable
      type="endpoint"
      :instances="endpoints"
      base-url="/endpoints"
      export-object-label="Endpoints"
      column-data-resource="endpoints"
      :items-length="total"
      :fetching-function="fetchFilteredEndpoints"
    />
  </div>
</template>

<script>
import InstanceTable from './InstanceTable.vue'
import { useEndpointsStore } from '@/stores/library-endpoints'
import { computed } from 'vue'

export default {
  components: {
    InstanceTable,
  },
  setup() {
    const endpointsStore = useEndpointsStore()

    return {
      fetchFilteredEndpoints: endpointsStore.fetchFilteredEndpoints,
      total: computed(() => endpointsStore.total),
      endpoints: computed(() => endpointsStore.endpoints),
    }
  },
}
</script>
