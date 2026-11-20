<template>
  <!-- What is still to be dealt with on a row of the review tables: open findings still
       to be decided, and informational ones still to be acknowledged. Settled findings
       are history and not counted. Nothing outstanding reads as a green all-clear. -->
  <div class="d-flex flex-wrap" data-cy="standards-import-finding-issues">
    <v-chip
      v-if="open"
      size="small"
      variant="flat"
      color="error"
      prepend-icon="mdi-alert-outline"
      class="mr-1 my-1"
    >
      {{ $t('StandardsImport.review_open_count', open) }}
    </v-chip>
    <v-chip
      v-if="informational"
      size="small"
      variant="tonal"
      color="warning"
      prepend-icon="mdi-help-circle-outline"
      class="mr-1 my-1"
    >
      {{ $t('StandardsImport.review_informational_count', informational) }}
    </v-chip>
    <v-chip
      v-if="!open && !informational"
      size="small"
      variant="flat"
      color="success"
      prepend-icon="mdi-check-circle-outline"
    >
      {{ $t('StandardsImport.review_open_issues', 0) }}
    </v-chip>
  </div>
</template>

<script setup>
defineProps({
  open: {
    type: Number,
    default: 0,
  },
  informational: {
    type: Number,
    default: 0,
  },
})
</script>
