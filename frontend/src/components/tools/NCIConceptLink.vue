<template>
  <a :href="termBrowserUrl" target="_blank"> {{ conceptId }} </a>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  conceptId: {
    type: String,
    default: '',
  },
})

const termBrowserUrl = computed(() => {
  return `https://evsexplore.semantics.cancer.gov/evsexplore/concept/ncit/${props.conceptId}`
})
</script>
