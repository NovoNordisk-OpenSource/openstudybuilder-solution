<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('ObjectivesView.title') }}
      <HelpButton :help-text="$t('_help.ObjectivesTable.general')" />
    </div>
    <ObjectiveTable />
  </div>
</template>

<script>
import ObjectiveTable from '@/components/library/ObjectiveTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'

export default {
  components: {
    ObjectiveTable,
    HelpButton,
  },
}
</script>
