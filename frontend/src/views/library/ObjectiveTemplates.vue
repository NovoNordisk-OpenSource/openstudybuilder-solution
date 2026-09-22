<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('ObjectiveTemplatesView.title') }}
      <HelpButton :help-text="$t('_help.ObjectiveTemplatesTable.general')" />
    </div>
    <ObjectiveTemplateTable />
  </div>
</template>

<script>
import ObjectiveTemplateTable from '@/components/library/ObjectiveTemplateTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'

export default {
  components: {
    ObjectiveTemplateTable,
    HelpButton,
  },
}
</script>
