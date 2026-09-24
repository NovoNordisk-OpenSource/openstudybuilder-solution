<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('ActivityInstructionsView.title') }}
      <HelpButton :help-text="$t('_help.ActivityInstructionTable.general')" />
    </div>
    <ActivityInstructionTable />
  </div>
</template>

<script>
import ActivityInstructionTable from '@/components/library/ActivityInstructionTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'

export default {
  components: {
    ActivityInstructionTable,
    HelpButton,
  },
}
</script>
