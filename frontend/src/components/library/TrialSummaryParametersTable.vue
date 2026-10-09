<template>
  <NNTable
    ref="tableRef"
    :table-id="tableId"
    :headers="headers"
    :items="items"
    :items-length="total"
    hide-default-switches
    item-value="concept_id"
    column-data-resource="ct/codelists/terms"
    codelist-uid="C66738"
    :export-config="{
      dataUrlParams: exportUrlParams,
      objectLabel: 'TrialSummaryParameters',
      dataUrl: 'ct/codelists/terms',
    }"
    @filter="fetchData"
  >
    <template #actions="">
      <v-btn
        data-cy="add-trial-summary-parameter-button"
        class="ml-2"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        @click="showForm = true"
      >
        <v-icon>mdi-plus</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ $t('TrialSummaryParameterForm.add_title') }}
        </v-tooltip>
      </v-btn>
    </template>
    <template #[`item.actions`]="{ item }">
      <ActionsMenu :actions="actions" :item="item" />
    </template>
    <template #[`item.submission_value_test_name`]="{ item }">
      {{ item.submission_value_test_name || '-' }}
    </template>
    <template #[`item.attributes_date`]="{ item }">
      {{ $filters.date(item.attributes_date) || '-' }}
    </template>
    <template #[`item.name_date`]="{ item }">
      {{ $filters.date(item.name_date) || '-' }}
    </template>
    <template #[`item.valid_null_flavor_terms`]="{ item }">
      <div
        v-if="
          item.valid_null_flavor_terms && item.valid_null_flavor_terms.length
        "
      >
        <div v-for="(term, index) in item.valid_null_flavor_terms" :key="index">
          {{ term.sponsor_preferred_name }}
        </div>
      </div>
    </template>
    <template #[`item.attributes_status`]="{ item }">
      <StatusChip :status="item.attributes_status" />
    </template>
    <template #[`item.name_status`]="{ item }">
      <StatusChip :status="item.name_status" />
    </template>
  </NNTable>
  <v-dialog
    v-model="showForm"
    fullscreen
    persistent
    content-class="fullscreen-dialog"
  >
    <TrialSummaryParameterForm
      @close="showForm = false"
      @added="tableRef.filterTable()"
    />
  </v-dialog>
  <v-dialog
    v-model="showHistory"
    persistent
    :fullscreen="$globals.historyDialogFullscreen"
    @keydown.esc="closeHistory"
  >
    <HistoryTable
      :title="historyTitleLabel"
      :headers="historyHeaders"
      :items="historyItems"
      @close="closeHistory"
    />
  </v-dialog>
</template>

<script setup>
import { ref, inject, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import NNTable from '@/components/tools/NNTable.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import TrialSummaryParameterForm from '@/components/library/TrialSummaryParameterForm.vue'
import codelistApi from '@/api/controlledTerminology/codelists'
import filteringParameters from '@/utils/filteringParameters'
import controlledTerminology from '@/api/controlledTerminology'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import { useFeatureFlagsStore } from '@/stores/feature-flags'

const { t } = useI18n()
const roles = inject('roles')
const router = useRouter()
const featureFlagsStore = useFeatureFlagsStore()

const showShortCode = computed(() =>
  featureFlagsStore.getFeatureFlag('ct_term_short_code')
)

// Own layout key per flag state: NNTable hides headers missing from the saved
// column layout, so a layout stored while the flag was off would keep the
// short_code column hidden after switching it on.
const tableId = computed(() =>
  showShortCode.value
    ? 'library-trial-summary-parameters-table-short-code'
    : 'library-trial-summary-parameters-table'
)

const headers = computed(() => [
  { title: '', key: 'actions', width: '1%' },
  { title: t('TrialSummaryParameters.library'), key: 'library_name' },
  {
    title: t('TrialSummaryParameters.sponsor_name'),
    key: 'sponsor_preferred_name',
  },
  { title: t('TrialSummaryParameters.code'), key: 'submission_value' },
  {
    title: t('TrialSummaryParameters.test_name_submission_value'),
    key: 'submission_value_test_name',
    parameters: { include_ts_parameters: true },
  },
  { title: t('TrialSummaryParameters.ct_name'), key: 'nci_preferred_name' },
  { title: t('TrialSummaryParameters.concept_id'), key: 'concept_id' },
  { title: t('TrialSummaryParameters.definition'), key: 'definition' },
  { title: t('TrialSummaryParameters.required_level'), key: 'required_level' },
  {
    title: t('TrialSummaryParameters.semantic_data_type'),
    key: 'semantic_data_type.sponsor_preferred_name',
    parameters: { include_ts_parameters: true },
  },
  {
    title: t('TrialSummaryParameters.response_code_list'),
    key: 'response_codelist.sponsor_preferred_name',
    parameters: { include_ts_parameters: true },
  },
  { title: t('TrialSummaryParameters.cardinality'), key: 'cardinality' },
  {
    title: t('TrialSummaryParameters.valid_null_flavor'),
    key: 'valid_null_flavor_terms',
  },
  { title: t('TrialSummaryParameters.notes'), key: 'notes' },
  ...(showShortCode.value
    ? [
        {
          title: t('TrialSummaryParameters.short_code'),
          key: 'short_code',
          parameters: { include_ts_parameters: true },
        },
      ]
    : []),
  {
    title: t('TrialSummaryParameters.osb_page_reference'),
    key: 'osb_page_reference',
    parameters: { include_ts_parameters: true },
  },
  {
    title: t('TrialSummaryParameters.osb_field_name'),
    key: 'osb_field_name',
    parameters: { include_ts_parameters: true },
  },
  { title: t('TrialSummaryParameters.name_status'), key: 'name_status' },
  {
    title: t('TrialSummaryParameters.name_modified_by'),
    key: 'name_author',
  },
  { title: t('TrialSummaryParameters.name_date'), key: 'name_date' },
  {
    title: t('TrialSummaryParameters.attributes_status'),
    key: 'attributes_status',
  },
  {
    title: t('TrialSummaryParameters.attributes_modified_by'),
    key: 'attributes_author',
  },
  {
    title: t('TrialSummaryParameters.attributes_date'),
    key: 'attributes_date',
  },
])

const actions = [
  {
    label: t('TrialSummaryParameters.view_or_edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    accessRole: roles.LIBRARY_WRITE,
    click: viewDetails,
  },
  {
    label: t('TrialSummaryParameters.open_sponsor_history'),
    icon: 'mdi-history',
    click: openSponsorValuesHistory,
  },
  {
    label: t('TrialSummaryParameters.open_ct_history'),
    icon: 'mdi-history',
    click: openCTValuesHistory,
  },
]

const items = ref([])
const total = ref(0)
const tableRef = ref()
const showForm = ref(false)

const exportUrlParams = computed(() => {
  return { codelist_uid: 'C66738', include_ts_parameters: true }
})

function fetchData(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  params.include_ts_parameters = true
  codelistApi.getCodelistTerms('C66738', params).then((resp) => {
    items.value = resp.data.items
    total.value = resp.data.total
  })
}

function viewDetails(item) {
  try {
    router.push({
      name: 'TrialParameterDetails',
      params: {
        term_id: item.term_uid,
      },
    })
  } catch (error) {
    console.error('Error navigating to details:', error)
  }
}

const selectedTerm = ref(null)
const historyType = ref('')
const historyHeaders = ref([])
const historyItems = ref([])
const showHistory = ref(false)

const historyTitleLabel = computed(() => {
  return historyType.value === 'termName'
    ? t('TrialSummaryParameters.history_label_name', {
        term: selectedTerm.value.term_uid,
      })
    : t('TrialSummaryParameters.history_label_attributes', {
        term: selectedTerm.value.term_uid,
      })
})

async function openSponsorValuesHistory(item) {
  selectedTerm.value = item
  historyType.value = 'termName'
  historyHeaders.value = [
    {
      title: t('TrialSummaryParameters.sponsor_name'),
      key: 'sponsor_preferred_name',
    },
    {
      title: t('CodelistTermDetail.sentence_case_name'),
      key: 'sponsor_preferred_name_sentence_case',
    },
    { title: t('_global.status'), key: 'status' },
    { title: t('_global.version'), key: 'version' },
  ]
  const resp = await controlledTerminology.getCodelistTermNamesVersions(
    selectedTerm.value.term_uid
  )
  historyItems.value = resp.data
  showHistory.value = true
}

async function openCTValuesHistory(item) {
  selectedTerm.value = item
  historyType.value = 'termAttributes'
  historyHeaders.value = [
    { title: t('CodelistTermDetail.concept_id'), key: 'concept_id' },
    {
      title: t('CodeListDetail.nci_pref_name'),
      key: 'nci_preferred_name',
    },
    { title: t('_global.definition'), key: 'definition' },
    { title: t('_global.status'), key: 'status' },
    { title: t('_global.version'), key: 'version' },
  ]
  const resp = await controlledTerminology.getCodelistTermAttributesVersions(
    selectedTerm.value.term_uid
  )
  historyItems.value = resp.data
  showHistory.value = true
}

function closeHistory() {
  showHistory.value = false
  selectedTerm.value = null
  historyType.value = ''
  historyHeaders.value = []
  historyItems.value = []
}
</script>
