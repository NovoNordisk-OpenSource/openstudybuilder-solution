<template>
  <StudyMetadataSummary
    :metadata="metadata"
    :params="params"
    :loading="loading"
    :first-col-label="$t('StudyInterventionTypeSummary.intervention_type_info')"
    persistent-dialog
    copy-from-study
    component="study_intervention"
    @updated="onMetadataUpdated"
  >
    <template #form="{ closeHandler, openHandler, formKey, dataToCopy }">
      <InterventionTypeForm
        :key="formKey"
        :open="openHandler"
        :initial-data="dataToCopy"
        @updated="onMetadataUpdated"
        @close="closeHandler"
      />
    </template>
  </StudyMetadataSummary>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import study from '@/api/study'
import InterventionTypeForm from './InterventionTypeForm.vue'
import StudyMetadataSummary from './StudyMetadataSummary.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const { t } = useI18n()
const studiesGeneralStore = useStudiesGeneralStore()

const metadata = ref({})
const loading = ref(false)

const params = [
  {
    label: t('StudyInterventionTypeForm.intervention_type'),
    name: 'intervention_type_code',
    valuesDisplay: 'term',
  },
  {
    label: t('StudyDefineForm.studyintent'),
    name: 'trial_intent_types_codes',
    valuesDisplay: 'terms',
  },
  {
    label: t('StudyInterventionTypeForm.added_to_et'),
    name: 'add_on_to_existing_treatments',
    valuesDisplay: 'yesno',
  },
  {
    label: t('StudyInterventionTypeForm.control_type'),
    name: 'control_type_code',
    valuesDisplay: 'term',
  },
  {
    label: t('StudyInterventionTypeForm.intervention_model'),
    name: 'intervention_model_code',
    valuesDisplay: 'term',
  },
  {
    label: t('StudyInterventionTypeForm.randomised'),
    name: 'is_trial_randomised',
    valuesDisplay: 'yesno',
  },
  {
    label: t('StudyInterventionTypeForm.strfactor'),
    name: 'stratification_factor',
  },
  {
    label: t('StudyInterventionTypeForm.blinding_schema'),
    name: 'trial_blinding_schema_code',
    valuesDisplay: 'term',
  },
  {
    label: t('StudyInterventionTypeForm.planned_st_length'),
    name: 'planned_study_length',
    valuesDisplay: 'duration',
  },
]

onMounted(() => {
  studiesGeneralStore.fetchUnits()
  studiesGeneralStore.fetchTrialBlindingSchemas()
  studiesGeneralStore.fetchControlTypes()
  studiesGeneralStore.fetchInterventionModels()
  studiesGeneralStore.fetchTrialIntentTypes()
  studiesGeneralStore.fetchInterventionTypes()
  fetchMetadata()
})

function onMetadataUpdated() {
  fetchMetadata()
}

function fetchMetadata() {
  loading.value = true
  study
    .getStudyInterventionMetadata(studiesGeneralStore.selectedStudy.uid)
    .then((resp) => {
      metadata.value = resp.data.current_metadata.study_intervention
    })
    .finally(() => {
      loading.value = false
    })
}
</script>
