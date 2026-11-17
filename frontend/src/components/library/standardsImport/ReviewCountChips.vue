<template>
  <!-- A row of small labelled numbers. Two columns of the review tables are the same
       shape - a handful of counts that only matter when non-zero - so they share this
       rather than each spelling out its own chips. -->
  <div v-if="shown.length" class="d-flex flex-wrap">
    <v-chip
      v-for="count in shown"
      :key="count.label"
      size="small"
      variant="tonal"
      :color="count.color"
      class="mr-1 my-1"
    >
      {{ count.label }} {{ count.value }}
    </v-chip>
  </div>
  <span v-else class="text-medium-emphasis">&mdash;</span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  // [{ label, value, color }] - a `value` of 0 is dropped.
  counts: {
    type: Array,
    default: () => [],
  },
})

const shown = computed(() => props.counts.filter((count) => count.value))
</script>
