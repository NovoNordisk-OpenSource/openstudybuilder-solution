<template>
  <StudyMetadataSummary
    :metadata="metadata"
    :params="params"
    :loading="loading"
    :first-col-label="$t('StudyTypeSummary.info_column')"
    persistent-dialog
    copy-from-study
    component="high_level_study_design"
    @updated="onMetadataUpdated"
  >
    <template #form="{ closeHandler, openHandler, dataToCopy, formKey }">
      <StudyDefineForm
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
import StudyMetadataSummary from './StudyMetadataSummary.vue'
import StudyDefineForm from './StudyDefineForm.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const { t } = useI18n()
const studiesGeneralStore = useStudiesGeneralStore()

const metadata = ref({})
const loading = ref(false)

const params = [
  {
    label: t('StudyDefineForm.studytype'),
    name: 'study_type_code',
    valuesDisplay: 'term',
  },
  {
    label: t('StudyDefineForm.trialtype'),
    name: 'trial_type_codes',
    valuesDisplay: 'terms',
  },
  {
    label: t('StudyDefineForm.trialphase'),
    name: 'trial_phase_code',
    valuesDisplay: 'term',
  },
  {
    label: t('StudyDefineForm.development_stage'),
    name: 'development_stage_code',
    valuesDisplay: 'term',
  },
  {
    label: t('StudyDefineForm.extensiontrial'),
    name: 'is_extension_trial',
    valuesDisplay: 'yesno',
  },
  {
    label: t('StudyDefineForm.adaptivedesign'),
    name: 'is_adaptive_design',
    valuesDisplay: 'yesno',
  },
  {
    label: t('StudyDefineForm.studystoprule'),
    name: 'study_stop_rules',
  },
  {
    label: t('StudyDefineForm.confirmed_resp_min_duration'),
    name: 'confirmed_response_minimum_duration',
    valuesDisplay: 'duration',
  },
  {
    label: t('StudyDefineForm.post_auth_safety_indicator'),
    name: 'post_auth_indicator',
    valuesDisplay: 'yesno',
  },
]

onMounted(() => {
  studiesGeneralStore.fetchUnits()
  studiesGeneralStore.fetchStudyTypes()
  studiesGeneralStore.fetchTrialIntentTypes()
  studiesGeneralStore.fetchTrialPhases()
  studiesGeneralStore.fetchTrialTypes()
  studiesGeneralStore.fetchNullValues()
  studiesGeneralStore.fetchDevelopmentStageCodes()
  fetchMetadata()
})

function onMetadataUpdated() {
  fetchMetadata()
}

function fetchMetadata() {
  loading.value = true
  study
    .getHighLevelStudyDesignMetadata(studiesGeneralStore.selectedStudy.uid)
    .then((resp) => {
      metadata.value = resp.data.current_metadata.high_level_study_design
    })
    .finally(() => {
      loading.value = false
    })
}
</script>
