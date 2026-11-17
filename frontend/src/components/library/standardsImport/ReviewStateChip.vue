<template>
  <!-- Where one row stands in the review walkthrough. Both review tables show this, and
       for a term it is inherited from the codelists holding it rather than set on the
       term - hence the tooltip naming who marked it, which is a codelist reviewer. -->
  <v-chip size="small" variant="tonal" :color="color">
    {{ label }}
    <v-tooltip v-if="review.reviewed_by" location="top">
      <template #activator="{ props }">
        <v-icon v-bind="props" size="12" class="ml-1">
          mdi-information-outline
        </v-icon>
      </template>
      {{ review.reviewed_by }}
      <template v-if="review.reviewed_at">
        &mdash; {{ review.reviewed_at }}
      </template>
    </v-tooltip>
  </v-chip>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  review: {
    type: Object,
    default: () => ({ status: 'NOT_REVIEWED' }),
  },
})

const color = computed(() => {
  switch (props.review.status) {
    case 'REVIEWED':
      return 'success'
    // NOT_REVIEWED, and REVIEWED_STALE - a record exists, but a later analysis reopened
    // something on it. Both still want someone to look.
    default:
      return 'warning'
  }
})

const label = computed(() =>
  t(`StandardsImport.review_${props.review.status.toLowerCase()}`)
)
</script>
