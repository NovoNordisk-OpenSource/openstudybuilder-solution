<template>
  <div class="mt-6 d-flex align-center">
    <v-card-title class="text-headline-small">
      {{ $t('StudyProtocolElementsView.title_page') }}
    </v-card-title>
  </div>
  <v-data-table
    class="mt-2"
    :headers="headers"
    :items="items"
    :loading="loading"
    hide-default-footer
  />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import study from '@/api/study'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const { t } = useI18n()
const studiesGeneralStore = useStudiesGeneralStore()

const headers = [
  {
    title: t('ProtocolTitlePage.title_page_elements'),
    key: 'label',
    width: '30%',
  },
  { title: t('ProtocolTitlePage.values'), key: 'value' },
]
const items = ref([])
const loading = ref(false)

onMounted(() => {
  loading.value = true
  study
    .getStudyProtocolTitle(studiesGeneralStore.selectedStudy.uid)
    .then((resp) => {
      items.value = [
        {
          label: t('ProtocolTitlePage.protocol_title'),
          value: resp.data.study_title,
        },
        {
          label: t('ProtocolTitlePage.protocol_short_title'),
          value: resp.data.study_short_title,
        },
        {
          label: t('ProtocolTitlePage.substance_name'),
          value: resp.data.substance_name,
        },
        {
          label: t('ProtocolTitlePage.utn'),
          value: resp.data.universal_trial_number_utn,
        },
        {
          label: t('ProtocolTitlePage.eudract_number'),
          value: resp.data.eudract_id,
        },
        {
          label: t('ProtocolTitlePage.ind_number'),
          value: resp.data.ind_number,
        },
        {
          label: t('ProtocolTitlePage.study_phase'),
          value: resp.data.trial_phase_code?.name,
        },
        {
          label: t('ProtocolTitlePage.development_stage'),
          value: resp.data.development_stage_code?.name,
        },
        {
          label: t('ProtocolTitlePage.protocol_version'),
          value: resp.data.protocol_header_version,
        },
      ]
      loading.value = false
    })
})
</script>
