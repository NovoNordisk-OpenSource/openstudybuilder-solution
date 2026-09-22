<template>
  <div>
    <div class="mt-6 d-flex align-center">
      <v-card-title class="text-headline-small">
        {{ $t('StudyProtocolElementsView.procedures_and_activities') }}
      </v-card-title>
    </div>
    <UnderConstruction />
  </div>
</template>

<script>
import UnderConstruction from '@/components/layout/UnderConstruction.vue'

export default {
  components: {
    UnderConstruction,
  },
}
</script>
