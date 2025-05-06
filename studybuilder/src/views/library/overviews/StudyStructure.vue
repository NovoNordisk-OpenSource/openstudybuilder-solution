<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('StudyStructuresOverview.title') }}
      <HelpButton :help-text="$t('_help.StudyStructuresOverview.general')" />
    </div>
    <NNTable
      ref="table"
      :headers="headers"
      :items="items"
      :items-length="total"
      column-data-resource="studies/structure-overview"
      hide-default-switches
      item-value="uid"
      export-data-url="studies/structure-overview"
      export-object-label="StudyStructuresOverview"
      @filter="fetchStructures"
    >
      <template #[`item.study_ids`]="{ item }">
        <div v-html="item.study_ids" />
      </template>
    </NNTable>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import NNTable from '@/components/tools/NNTable.vue'
import studyApi from '@/api/study'
import filteringParameters from '@/utils/filteringParameters'
import HelpButton from '@/components/tools/HelpButton.vue'

const { t } = useI18n()

const items = ref([])
const total = ref(0)

const headers = [
  { title: t('StudyStructuresOverview.arms'), key: 'arms' },
  {
    title: t('StudyStructuresOverview.pre_treatment_epochs'),
    key: 'pre_treatment_epochs',
  },
  {
    title: t('StudyStructuresOverview.treatment_epochs'),
    key: 'treatment_epochs',
  },
  {
    title: t('StudyStructuresOverview.post_treatment_epochs'),
    key: 'post_treatment_epochs',
  },
  {
    title: t('StudyStructuresOverview.no_treatment_epochs'),
    key: 'no_treatment_epochs',
  },
  {
    title: t('StudyStructuresOverview.no_treatment_elements'),
    key: 'no_treatment_elements',
  },
  {
    title: t('StudyStructuresOverview.treatment_elements'),
    key: 'treatment_elements',
  },
  { title: t('StudyStructuresOverview.cohorts'), key: 'cohorts_in_study' },
  { title: t('StudyStructuresOverview.study_ids'), key: 'study_ids' },
]

function fetchStructures(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  studyApi.getStructureOverview(params).then((resp) => {
    items.value = resp.data.items.map((elm) => ({
      ...elm,
      study_ids: elm.study_ids.join(',<br>'),
    }))
    total.value = resp.data.total
  })
}
</script>
