<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('StudyRegistryIdentifiersView.title') }} ({{ studyId }})
      <HelpButton :help-text="$t('_help.RegistryIdentifiersTable.general')" />
    </div>
    <RegistryIdentifiersSummary />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import RegistryIdentifiersSummary from '@/components/studies/RegistryIdentifiersSummary.vue'
import HelpButton from '@/components/tools/HelpButton.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const studiesGeneralStore = useStudiesGeneralStore()

const studyId = computed(() => studiesGeneralStore.studyId)
</script>
