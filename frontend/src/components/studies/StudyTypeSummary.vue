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
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import study from '@/api/study'
import StudyMetadataSummary from './StudyMetadataSummary.vue'
import StudyDefineForm from './StudyDefineForm.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useFeatureFlagsStore } from '@/stores/feature-flags'

const { t } = useI18n()
const studiesGeneralStore = useStudiesGeneralStore()
const featureFlagsStore = useFeatureFlagsStore()

const metadata = ref({})
const loading = ref(false)

const typeParams = [
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
const migrationParams = [
  {
    label: t('StudyDefineForm.migrated_study_indicator'),
    name: 'migrated_study_indicator',
    valuesDisplay: 'yesno',
    readOnly: true,
  },
  {
    label: t('StudyDefineForm.migrated_study_comment'),
    name: 'migrated_study_comment',
    readOnly: true,
  },
]
const params = computed(() =>
  featureFlagsStore.getFeatureFlag('study_migration_details')
    ? [...typeParams, ...migrationParams]
    : typeParams
)

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
      // The migration fields live in identification metadata, which this
      // response includes by default
      const { high_level_study_design, identification_metadata } =
        resp.data.current_metadata
      metadata.value = {
        ...high_level_study_design,
        // Not set means not migrated, so show No rather than blank
        migrated_study_indicator: Boolean(
          identification_metadata?.migrated_study_indicator
        ),
        migrated_study_comment: identification_metadata?.migrated_study_comment,
      }
    })
    .finally(() => {
      loading.value = false
    })
}
</script>
