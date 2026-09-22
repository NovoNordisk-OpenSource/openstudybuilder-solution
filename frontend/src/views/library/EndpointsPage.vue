<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('EndpointsView.title') }}
      <HelpButton :help-text="$t('_help.EndpointsTable.general')" />
    </div>
    <EndpointTable />
  </div>
</template>

<script>
import EndpointTable from '@/components/library/EndpointTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'

export default {
  components: {
    EndpointTable,
    HelpButton,
  },
}
</script>
