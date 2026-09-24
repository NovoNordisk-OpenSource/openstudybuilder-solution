<template>
  <div>
    <InstanceTable
      :fetch-instances-extra-filters="extraFilters"
      type="criteria"
      :instances="criteria"
      base-url="/criteria"
      export-object-label="Criteria"
      column-data-resource="criteria"
      :items-length="total"
      :instance-type="criteriaType.term_uid"
      :fetching-function="fetchFilteredCriteria"
    />
  </div>
</template>

<script>
import InstanceTable from './InstanceTable.vue'
import { useCriteriaStore } from '@/stores/library-criteria'
import { computed } from 'vue'

export default {
  components: {
    InstanceTable,
  },
  props: {
    criteriaType: {
      type: Object,
      default: null,
    },
  },
  setup() {
    const criteriaStore = useCriteriaStore()

    return {
      fetchFilteredCriteria: criteriaStore.fetchFilteredCriteria,
      total: computed(() => criteriaStore.total),
      criteria: computed(() => criteriaStore.criteria),
    }
  },
  computed: {
    extraFilters() {
      return {
        'template.type.term_uid': {
          v: [this.criteriaType.term_uid],
          op: 'eq',
        },
      }
    },
  },
}
</script>
