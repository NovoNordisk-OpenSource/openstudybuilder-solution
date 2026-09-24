<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('EndpointTemplatesView.title') }}
      <HelpButton :help-text="$t('_help.EndpointTemplatesTable.general')" />
    </div>
    <EndpointTemplateTable />
  </div>
</template>

<script>
import EndpointTemplateTable from '@/components/library/EndpointTemplateTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'

export default {
  components: {
    EndpointTemplateTable,
    HelpButton,
  },
}
</script>
