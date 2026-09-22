<template>
  <v-btn
    :color="color"
    :variant="variant"
    readonly
    tabindex="-1"
    size="small"
    rounded
    class="text-none"
    style="pointer-events: none; cursor: default"
  >
    {{ status }}
  </v-btn>
</template>

<script setup>
import { computed } from 'vue'
import statuses from '@/constants/statuses'

const props = defineProps({
  status: {
    type: String,
    default: '',
  },
  outlined: {
    type: Boolean,
    default: false,
  },
})

const color = computed(() => {
  if (
    props.status === statuses.FINAL ||
    props.status === statuses.STUDY_DRAFT
  ) {
    return 'green'
  }
  if (props.status === statuses.RETIRED) {
    return 'orange'
  }
  if (props.status === statuses.STUDY_RELEASED) {
    return 'info'
  }
  if (props.status === statuses.STUDY_LOCKED) {
    return 'red'
  }
  return 'secondary'
})

const variant = computed(() => {
  return props.outlined ? 'outlined' : 'tonal'
})
</script>
