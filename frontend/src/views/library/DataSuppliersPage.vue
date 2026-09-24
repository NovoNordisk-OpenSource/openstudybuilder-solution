<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('DataSupplierView.title') }}
      <HelpButton
        :help-text="$t('_help.DataSupplierView.DataSupplierTable.general')"
      />
    </div>
    <DataSupplierTable />
  </div>
</template>

<script>
import DataSupplierTable from '@/components/library/DataSupplierTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'

export default {
  components: {
    DataSupplierTable,
    HelpButton,
  },
}
</script>
