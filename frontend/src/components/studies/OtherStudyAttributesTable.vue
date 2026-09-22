<template>
  <NNTable
    ref="tableRef"
    :headers="headers"
    :items="items"
    :items-length="total"
    :column-data-resource="`studies/${studiesGeneralStore.selectedStudy.uid}/study-other-attributes`"
    :export-config="{
      objectLabel: 'StudyOtherAttributes',
      dataUrl: exportDataUrl,
    }"
    hide-default-switches
    item-value="ts_parameter_term_uid"
    @filter="fetchData"
  >
    <template #actions="">
      <v-btn
        data-cy="add-other-study-attributes-button"
        class="ml-2"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        @click="showForm = true"
      >
        <v-icon>mdi-plus</v-icon>
        <v-tooltip activator="parent" location="top">
          Add/edit Other Study Attributes
        </v-tooltip>
      </v-btn>
    </template>
    <template #[`item.start_date`]="{ item }">
      <v-tooltip location="top">
        <template #activator="{ props }">
          <span v-bind="props">{{
            $filters.dateRelative(item.start_date)
          }}</span>
        </template>
        {{ $filters.date(item.start_date) }}
      </v-tooltip>
    </template>
  </NNTable>
  <v-dialog
    v-model="showForm"
    fullscreen
    persistent
    content-class="fullscreen-dialog"
  >
    <OtherStudyAttributesEditForm
      v-if="showForm"
      :edit-data="items"
      @close="closeAttributesForm()"
    />
  </v-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import NNTable from '@/components/tools/NNTable.vue'
import OtherStudyAttributesEditForm from './OtherStudyAttributesEditForm.vue'
import api from '@/api/study'
import filteringParameters from '@/utils/filteringParameters'

const { t } = useI18n()
const studiesGeneralStore = useStudiesGeneralStore()

const headers = [
  { title: t('OtherStudyAttributes.code'), key: 'code' },
  { title: t('OtherStudyAttributes.parameter'), key: 'parameter' },
  { title: t('OtherStudyAttributes.reference'), key: 'reference' },
  {
    title: t('OtherStudyAttributes.required_level'),
    key: 'required_level',
  },
  {
    title: t('OtherStudyAttributes.semantic_data_type'),
    key: 'semantic_data_type',
  },
  {
    title: t('OtherStudyAttributes.code_list'),
    key: 'response_codelist.sponsor_preferred_name',
  },
  { title: t('OtherStudyAttributes.parameter_value'), key: 'parameter_value' },
  { title: t('OtherStudyAttributes.notes'), key: 'notes' },
  {
    title: t('OtherStudyAttributes.null_flavor'),
    key: 'null_flavor.sponsor_preferred_name',
  },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.modified_by'), key: 'author_username' },
]

const items = ref([])
const total = ref(0)
const tableRef = ref()
const showForm = ref(false)

const exportDataUrl = computed(() => {
  return `studies/${studiesGeneralStore.selectedStudy.uid}/study-other-attributes`
})

async function fetchData(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  const resp = await api.getOtherAttributes(
    studiesGeneralStore.selectedStudy.uid,
    params
  )
  items.value = resp.data.items
  total.value = resp.data.total
}

function closeAttributesForm() {
  showForm.value = false
  tableRef.value.filterTable()
}
</script>
