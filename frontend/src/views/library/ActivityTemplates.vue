<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('ActivityTemplatesView.title') }}
      <HelpButton :help-text="$t('_help.ActivityTemplatesTable.general')" />
    </div>
    <ActivityTemplateTable />
  </div>
</template>

<script>
import ActivityTemplateTable from '@/components/library/ActivityTemplateTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'

export default {
  components: {
    ActivityTemplateTable,
    HelpButton,
  },
}
</script>
