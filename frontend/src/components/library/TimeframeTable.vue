<template>
  <div>
    <InstanceTable
      type="timeframe"
      :instances="timeframesStore.timeframes"
      base-url="/timeframes"
      export-object-label="Timeframes"
      column-data-resource="timeframes"
      :items-length="timeframesStore.total"
      :fetching-function="timeframesStore.fetchFilteredTimeframes"
    />
  </div>
</template>

<script setup>
import InstanceTable from './InstanceTable.vue'
import { useTimeframesStore } from '@/stores/library-timeframes'

const timeframesStore = useTimeframesStore()
</script>
