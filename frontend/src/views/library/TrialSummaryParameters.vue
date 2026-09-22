<template>
  <div class="px-4">
    <div data-cy="page-title" class="page-title d-flex align-center">
      {{ $t('TrialSummaryParameters.title') }}
    </div>
    <TrialSummaryParametersTable />
  </div>
</template>

<script setup>
import TrialSummaryParametersTable from '@/components/library/TrialSummaryParametersTable.vue'
</script>
