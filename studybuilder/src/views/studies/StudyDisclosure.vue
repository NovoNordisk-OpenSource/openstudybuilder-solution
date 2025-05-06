<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('StudyDisclosure.study_disclosure') }}
    </div>
    <div class="mt-4 pb-2 tableDiv elevation-4">
      <StudyDisclosureTable />
    </div>
  </div>
</template>

<script setup>
import StudyDisclosureTable from '@/components/studies/StudyDisclosureTable.vue'
</script>
<style>
.tableDiv {
  background-color: white;
  border-top-right-radius: 12px;
  border-top-left-radius: 12px;
  border-bottom-left-radius: 12px;
  border-bottom-right-radius: 12px;
}
</style>
