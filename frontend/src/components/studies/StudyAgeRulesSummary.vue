<template>
  <StudyMetadataSummary
    :metadata="metadata"
    :params="params"
    :loading="loading"
    :first-col-label="$t('StudyAgeRulesSummary.info_column')"
    :with-reason-for-missing="false"
    with-definition
    persistent-dialog
    component="high_level_study_design"
    @updated="onMetadataUpdated"
  >
    <template #form="{ closeHandler, openHandler, formKey }">
      <StudyAgeRulesForm
        :key="formKey"
        :open="openHandler"
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
import studyMetadataForms from '@/utils/studyMetadataForms'
import StudyMetadataSummary from './StudyMetadataSummary.vue'
import StudyAgeRulesForm from './StudyAgeRulesForm.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const { t } = useI18n()
const studiesGeneralStore = useStudiesGeneralStore()

const metadata = ref({})
const loading = ref(false)

const params = computed(() => [
  {
    label: t('StudyAgeRulesForm.age_at_baseline_rule'),
    name: 'age_at_baseline_rule_code',
    valuesDisplay: 'term',
    definition: studyMetadataForms.getTermDefinition(
      metadata.value.age_at_baseline_rule_code,
      studiesGeneralStore.ageAtBaselineRuleCodes
    ),
  },
  {
    label: t('StudyAgeRulesForm.age_group_rule'),
    name: 'age_group_rule_code',
    valuesDisplay: 'term',
    definition: studyMetadataForms.getTermDefinition(
      metadata.value.age_group_rule_code,
      studiesGeneralStore.ageGroupRuleCodes
    ),
  },
])

onMounted(() => {
  studiesGeneralStore.fetchAgeAtBaselineRuleCodes()
  studiesGeneralStore.fetchAgeGroupRuleCodes()
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
