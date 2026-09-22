<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('SponsorDataModels.sdtm_title') }}
      <HelpButton />
    </div>
    <Suspense>
      <SponsorModelsView uid="SDTMIG" />
    </Suspense>
  </div>
</template>

<script setup>
import HelpButton from '@/components/tools/HelpButton.vue'
import SponsorModelsView from '@/components/library/SponsorModelsView.vue'
</script>
