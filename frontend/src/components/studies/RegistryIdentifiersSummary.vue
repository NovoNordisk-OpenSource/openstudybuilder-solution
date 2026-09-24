<template>
  <StudyMetadataSummary
    :metadata="identifiers"
    :params="params"
    :loading="loading"
    :first-col-label="
      $t('StudyRegistryIdentifiersSummary.registry_identifiers')
    "
    :fullscreen-form="false"
    form-max-width="1000px"
    component="registry_identifiers"
    :disable-edit="studiesGeneralStore.selectedStudy.study_parent_part"
  >
    <template #form="{ closeHandler, openHandler, formKey }">
      <RegistryIdentifiersForm
        :key="formKey"
        :open="openHandler"
        @close="closeHandler"
        @updated="onIdentifiersUpdated"
      />
    </template>
  </StudyMetadataSummary>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import study from '@/api/study'
import RegistryIdentifiersForm from './RegistryIdentifiersForm.vue'
import StudyMetadataSummary from './StudyMetadataSummary.vue'
import studyConstants from '@/constants/study'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { i18n } from '@/plugins/i18n'

const studiesGeneralStore = useStudiesGeneralStore()

const identifiers = ref({})
const loading = ref(false)

const params = computed(() => {
  const result = []
  for (const key of studyConstants.REGISTRY_IDENTIFIERS) {
    result.push({
      label: i18n.t(`RegistryIdentifiersForm.${key}`),
      name: key,
      nullValueName: `${key}_null_value_code`,
    })
  }
  return result
})

function onIdentifiersUpdated() {
  fetchIdentifiers()
}

onMounted(() => {
  studiesGeneralStore.fetchNullValues()
  fetchIdentifiers()
})

function fetchIdentifiers() {
  loading.value = true
  study
    .getStudy(studiesGeneralStore.studyUid, false)
    .then((resp) => {
      identifiers.value =
        resp.data.current_metadata.identification_metadata.registry_identifiers
    })
    .finally(() => {
      loading.value = false
    })
}
</script>
