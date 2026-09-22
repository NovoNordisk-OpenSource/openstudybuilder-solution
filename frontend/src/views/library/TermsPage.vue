<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('CodelistTermsView.terms_listing') }}
      <HelpButton :help-text="$t('_help.CtTermsTable.general')" />
    </div>
    <TermTable />
  </div>
</template>

<script setup>
import TermTable from '@/components/library/TermTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'
</script>
