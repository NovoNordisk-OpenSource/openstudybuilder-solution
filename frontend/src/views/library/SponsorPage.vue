<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('SponsorView.title') }}
      <HelpButton :help-text="$t('_help.CtSponsorTable.general')" />
    </div>
    <SponsorTable :catalogue_name="$route.params.catalogue_name" />
  </div>
</template>

<script>
import SponsorTable from '@/components/library/SponsorTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'

export default {
  components: {
    SponsorTable,
    HelpButton,
  },
}
</script>
