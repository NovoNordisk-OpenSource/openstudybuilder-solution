<template>
  <span
    v-if="term?.term_uid"
    :class="{ 'text-error': term.date_conflict }"
    :title="title"
  >
    <router-link
      :to="{ name: 'CodelistTermDetail', params: { term_id: term.term_uid } }"
    >
      {{ term.term_name }}
    </router-link>
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
