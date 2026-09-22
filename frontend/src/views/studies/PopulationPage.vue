<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('StudyPopulationView.title') }} ({{ studiesGeneralStore.studyId }})
      <HelpButton :help-text="$t('_help.StudyPopulationTable.general')" />
    </div>
    <StudyPopulationSummary />
  </div>
</template>

<script setup>
import StudyPopulationSummary from '@/components/studies/StudyPopulationSummary.vue'
import HelpButton from '@/components/tools/HelpButton.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const studiesGeneralStore = useStudiesGeneralStore()
</script>
