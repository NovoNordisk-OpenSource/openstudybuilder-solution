<template>
  <CTTermDisplay
    v-if="param.valuesDisplay === 'term'"
    :term="metadata[param.name]"
  />
  <template v-else-if="param.valuesDisplay === 'terms'">
    <template
      v-for="(term, index) in metadata[param.name] || []"
      :key="`${param.name}-${term.term_uid}`"
    >
      <CTTermDisplay :term="term" />
      <span v-if="index !== metadata[param.name].length - 1">, </span>
    </template>
  </template>
  <span v-else>{{ displayValue }}</span>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import CTTermDisplay from '@/components/tools/CTTermDisplay.vue'

const { t } = useI18n()

const props = defineProps({
  param: {
    type: Object,
    required: true,
  },
  metadata: {
    type: Object,
    default: () => ({}),
  },
})

function yesnoDisplay(value) {
  return value ? t('_global.yes') : t('_global.no')
}

function durationDisplay(value) {
  return `${value.duration_value} ${value.duration_unit_code.name}`
}

function dictionaryTermsDisplay(value) {
  return value.map((item) => item.name).join(', ')
}

const displayFunctions = {
  yesno: yesnoDisplay,
  duration: durationDisplay,
  dictionaryTerms: dictionaryTermsDisplay,
}

const displayValue = computed(() => {
  const param = props.param
  let values = props.metadata[param.name]
  if (
    param.name === 'sex_of_participants_code' &&
    values !== undefined &&
    values !== null
  ) {
    values = values.name
  }
  if (param.name === 'study_stop_rules' && values == null) {
    return t('StudyDefineForm.none')
  }
  if (
    values !== undefined &&
    values !== null &&
    param.valuesDisplay &&
    !['term', 'terms'].includes(param.valuesDisplay) &&
    param.name !== 'sex_of_participants_code'
  ) {
    const fn = displayFunctions[param.valuesDisplay]
    return fn ? fn(values) : values
  }
  return values
})
</script>
