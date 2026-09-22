<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('CRFExtensions.title') }}
    </div>
    <CrfExtensionsTable />
  </div>
</template>

<script setup>
import CrfExtensionsTable from '@/components/library/crfs/CrfExtensionsTable.vue'
</script>
