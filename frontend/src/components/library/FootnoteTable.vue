<template>
  <div>
    <InstanceTable
      type="footnote"
      :instances="footnotesStore.footnotes"
      base-url="/footnotes"
      export-object-label="Footnotes"
      column-data-resource="footnotes"
      :items-length="footnotesStore.total"
      :fetching-function="footnotesStore.fetchFilteredFootnotes"
    />
  </div>
</template>

<script setup>
import InstanceTable from './InstanceTable.vue'
import { useFootnotesStore } from '@/stores/library-footnotes'

const footnotesStore = useFootnotesStore()
</script>
