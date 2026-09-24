<template>
  <span :class="{ 'text-error': term?.date_conflict }" :title="title">
    {{ term?.sponsor_preferred_name }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  term: {
    type: Object,
    default: () => ({}),
  },
})

const title = computed(() => {
  return props.term?.date_conflict ? t('CTTermDisplay.conflict_title') : ''
})
</script>
