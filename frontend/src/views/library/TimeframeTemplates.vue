<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('TimeframeTemplatesView.title') }}
      <HelpButton :help-text="$t('_help.TimeframeTemplatesTable.general')" />
    </div>
    <TimeframeTemplateTable />
  </div>
</template>

<script>
import TimeframeTemplateTable from '@/components/library/TimeframeTemplateTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'

export default {
  components: {
    TimeframeTemplateTable,
    HelpButton,
  },
}
</script>
