<template>
  <StudyMetadataSummary
    :metadata="metadata"
    :params="params"
    :first-col-label="$t('StudyPopulationSummary.info_column')"
    persistent-dialog
    copy-from-study
    component="study_population"
    @updated="onMetadataUpdated"
  >
    <template #form="{ closeHandler, openHandler, formKey, dataToCopy }">
      <StudyPopulationForm
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
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import study from '@/api/study'
import StudyMetadataSummary from './StudyMetadataSummary.vue'
import StudyPopulationForm from './StudyPopulationForm.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const { t } = useI18n()
const studiesGeneralStore = useStudiesGeneralStore()

const metadata = ref({})

const params = [
  {
    label: t('StudyPopulationForm.therapeuticarea'),
    name: 'therapeutic_area_codes',
    valuesDisplay: 'dictionaryTerms',
  },
  {
    label: t('StudyPopulationForm.disease_condition'),
    name: 'disease_condition_or_indication_codes',
    valuesDisplay: 'dictionaryTerms',
  },
  {
    label: t('StudyPopulationForm.stable_disease_min_duration'),
    name: 'stable_disease_minimum_duration',
    valuesDisplay: 'duration',
  },
  {
    label: t('StudyPopulationForm.healthy_subjects'),
    name: 'healthy_subject_indicator',
    valuesDisplay: 'yesno',
  },
  {
    label: t('StudyPopulationForm.diagnosis_group'),
    name: 'diagnosis_group_codes',
    valuesDisplay: 'dictionaryTerms',
  },
  {
    label: t('StudyPopulationForm.relapse_criteria'),
    name: 'relapse_criteria',
  },
  {
    label: t('StudyPopulationForm.number_of_expected_subjects'),
    name: 'number_of_expected_subjects',
  },
  {
    label: t('StudyPopulationForm.rare_disease_indicator'),
    name: 'rare_disease_indicator',
    valuesDisplay: 'yesno',
  },
  {
    label: t('StudyPopulationForm.sex_of_study_participants'),
    name: 'sex_of_participants_code',
    valuesDisplay: 'term',
  },
  {
    label: t('StudyPopulationForm.planned_min_age'),
    name: 'planned_minimum_age_of_subjects',
    valuesDisplay: 'duration',
  },
  {
    label: t('StudyPopulationForm.planned_max_age'),
    name: 'planned_maximum_age_of_subjects',
    valuesDisplay: 'duration',
  },
  {
    label: t('StudyPopulationForm.pediatric_study_indicator'),
    name: 'pediatric_study_indicator',
    valuesDisplay: 'yesno',
  },
  {
    label: t('StudyPopulationForm.pediatric_investigation_plan_indicator'),
    name: 'pediatric_investigation_plan_indicator',
    valuesDisplay: 'yesno',
  },
  {
    label: t('StudyPopulationForm.pediatric_postmarket_study_indicator'),
    name: 'pediatric_postmarket_study_indicator',
    valuesDisplay: 'yesno',
  },
]

studiesGeneralStore.fetchUnits()
studiesGeneralStore.fetchSnomedTerms()
studiesGeneralStore.fetchSexOfParticipants()
fetchMetadata()

function onMetadataUpdated() {
  fetchMetadata()
}

function fetchMetadata() {
  study
    .getStudyPopulationMetadata(studiesGeneralStore.selectedStudy.uid)
    .then((resp) => {
      metadata.value = resp.data.current_metadata.study_population
    })
}
</script>
