<template>
  <div class="d-flex align-center">
    <v-autocomplete
      v-model="studyById"
      :label="$t('StudyQuickSelectForm.study_id')"
      :items="studiesWithId"
      item-title="current_metadata.identification_metadata.study_id"
      return-object
      :rules="[(value) => formRules.atleastone(value, studyByAcronym)]"
      variant="outlined"
      rounded="lg"
      density="compact"
      clearable
      @update:model-value="autoPopulateAcronym"
    />
    <span class="mx-4">{{ $t('StudyQuickSelectForm.and_or') }}</span>
    <v-autocomplete
      v-model="studyByAcronym"
      :label="$t('StudyQuickSelectForm.study_acronym')"
      :items="studiesWithAcronym"
      item-title="current_metadata.identification_metadata.study_acronym"
      return-object
      :rules="[(value) => formRules.atleastone(value, studyById)]"
      variant="outlined"
      rounded="lg"
      density="compact"
      clearable
      @update:model-value="autoPopulateId"
    />
  </div>
</template>

<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import studyApi from '@/api/study'

// eslint-disable-next-line no-unused-vars
const props = defineProps({
  modelValue: {
    type: Object,
    default: null,
  },
})
const emit = defineEmits(['update:modelValue'])

const formRules = inject('formRules')

const studies = ref([])
const studyById = ref(null)
const studyByAcronym = ref(null)

const studiesWithId = computed(() => {
  return studies.value.filter(
    (study) => study.current_metadata.identification_metadata.study_id !== null
  )
})
const studiesWithAcronym = computed(() => {
  return studies.value.filter(
    (study) =>
      study.current_metadata.identification_metadata.study_acronym !== null
  )
})

onMounted(() => {
  const params = {
    sort_by: { 'current_metadata.identification_metadata.study_id': true },
    page_size: 0,
  }
  studyApi.get(params).then((resp) => {
    studies.value = resp.data.items
  })
})

function autoPopulateAcronym(study) {
  if (study && study.current_metadata.identification_metadata.study_acronym) {
    studyByAcronym.value = study
  }
  emit('update:modelValue', study)
}
function autoPopulateId(study) {
  if (study && study.current_metadata.identification_metadata.study_id) {
    studyById.value = study
  }
  emit('update:modelValue', study)
}
</script>
