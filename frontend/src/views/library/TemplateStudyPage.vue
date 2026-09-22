<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('TemplateStudy.title') }}
    </div>
    <TemplateStudyTable />
  </div>
</template>

<script setup>
import TemplateStudyTable from '@/components/library/TemplateStudyTable.vue'
</script>
