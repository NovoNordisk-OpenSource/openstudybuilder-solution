<template>
  <div class="px-4">
    <div class="d-flex page-title">
      {{ $t('UnitsView.title') }}
      <HelpButton
        :title="$t('_global.definition')"
        :help-text="$t('HelpMessages.units')"
      />
    </div>
    <UnitTable />
  </div>
</template>

<script>
import HelpButton from '@/components/tools/HelpButton.vue'
import UnitTable from '@/components/library/UnitTable.vue'

export default {
  components: {
    HelpButton,
    UnitTable,
  },
}
</script>
