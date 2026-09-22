<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('TimeframesView.title') }}
      <HelpButton :help-text="$t('_help.TimeframesTable.general')" />
    </div>
    <TimeframeTable />
  </div>
</template>

<script>
import TimeframeTable from '@/components/library/TimeframeTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'

export default {
  components: {
    TimeframeTable,
    HelpButton,
  },
  data() {
    return {
      tab: null,
    }
  },
}
</script>
