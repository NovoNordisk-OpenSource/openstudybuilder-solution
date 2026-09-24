<template>
  <v-autocomplete
    :model-value="modelValue"
    :label="$t('StudyQuickSelectForm.study_id_or_acronym')"
    :items="sortedStudies"
    :item-title="getStudyDisplayName"
    return-object
    :rules="[formRules.required]"
    clearable
    :loading="isLoading"
    :disabled="isLoading"
    @update:model-value="emit('update:modelValue', $event)"
  />
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import studyApi from '@/api/study'

const props = defineProps({
  modelValue: {
    type: Object,
    default: null,
  },
  data: {
    type: Array,
    default: undefined,
  },
  loading: {
    type: Boolean,
    default: undefined,
  },
})
const emit = defineEmits(['update:modelValue'])

const formRules = inject('formRules')

const studies = ref([])
const internalLoading = ref(false)
const isLoading = computed(() => props.loading ?? internalLoading.value)

onMounted(() => {
  if (props.data === undefined) {
    internalLoading.value = true
    studyApi
      .getIds()
      .then((resp) => {
        studies.value = resp.data
      })
      .finally(() => {
        internalLoading.value = false
      })
  }
})

watch(
  () => props.data,
  (newData) => {
    if (newData !== undefined) {
      studies.value = newData
    }
  },
  { immediate: true }
)

const sortedStudies = computed(() => {
  return studies.value.slice().sort((a, b) => {
    const nameA = getStudyDisplayName(a) || ''
    const nameB = getStudyDisplayName(b) || ''
    return nameA.localeCompare(nameB)
  })
})

function getStudyDisplayName(study) {
  const id =
    study?.id ?? study?.current_metadata?.identification_metadata?.study_id

  const acronym =
    study?.acronym ??
    study?.current_metadata?.identification_metadata?.study_acronym

  const subpartAcronym =
    study?.subpart_acronym ??
    study?.current_metadata?.identification_metadata?.subpart_acronym ??
    ''

  if (id && subpartAcronym) {
    return `${id} (${subpartAcronym})`
  }
  if (id && acronym) {
    return `${id} (${acronym})`
  }
  if (subpartAcronym) {
    return subpartAcronym
  }
  if (acronym) {
    return acronym
  }
  if (id) {
    return id
  }
  return null
}
</script>
