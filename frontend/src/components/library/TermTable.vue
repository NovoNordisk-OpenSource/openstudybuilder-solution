<template>
  <NNTable
    table-id="library-terms-table"
    :headers="headers"
    :items="terms"
    :items-length="total"
    item-value="term_uid"
    class="mt-4"
    column-data-resource="ct/terms"
    :fixed-column-data="{
      'codelists.codelist_name': [$t('_global.none')],
      'codelists.codelist_submission_value': [$t('_global.none')],
    }"
    :export-config="{
      dataUrlParams: exportUrlParams,
      objectLabel: 'Terms',
      dataUrl: 'ct/terms',
    }"
    @filter="fetchTerms"
  >
    <template #actions>
      <v-btn
        v-if="codelistAttributes.extensible"
        class="ml-2"
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        data-cy="add-term-button"
        :title="$t('CodelistTermCreationForm.title')"
        :disabled="!accessGuard.checkPermission($roles.LIBRARY_WRITE)"
        icon="mdi-plus"
        @click.stop="showCreationForm = true"
      />
    </template>
    <template #[`item.name.status`]="{ item }">
      <StatusChip :status="item.name.status" />
    </template>
    <template #[`item.name.start_date`]="{ item }">
      {{ $filters.date(item.name.start_date) }}
    </template>
    <template #[`item.attributes.status`]="{ item }">
      <StatusChip :status="item.attributes.status" />
    </template>
    <template #[`item.attributes.start_date`]="{ item }">
      {{ $filters.date(item.attributes.start_date) }}
    </template>
    <template #[`item.actions`]="{ item }">
      <ActionsMenu :actions="actions" :item="item" />
    </template>
    <template #[`item.codelists.submission_value`]="{ item }">
      <div v-html="submissionValuesDisplay(item)" />
    </template>
    <template #[`item.codelists.codelist_name`]="{ item }">
      <div v-html="codelistNamesDisplay(item)" />
    </template>
    <template #[`item.codelists.codelist_submission_value`]="{ item }">
      <div v-html="codelistSubmvalsDisplay(item)" />
    </template>
  </NNTable>
  <v-dialog
    v-model="showCreationForm"
    persistent
    max-width="1024px"
    content-class="top-dialog"
  >
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
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import controlledTerminology from '@/api/controlledTerminology'
import termsApi from '@/api/controlledTerminology/terms'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import filteringParameters from '@/utils/filteringParameters'
import { useAccessGuard } from '@/composables/accessGuard'

const { t } = useI18n()
const router = useRouter()
const accessGuard = useAccessGuard()
const notificationHub = inject('notificationHub')
const roles = inject('roles')
const props = defineProps({})

const actions = [
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    accessRole: roles.LIBRARY_WRITE,
    click: editTerm,
  },
  {
    label: t('CtCatalogueTable.remove_term'),
    icon: 'mdi-delete-outline',
    iconColor: 'primary',
    click: removeTerm,
    accessRole: roles.LIBRARY_WRITE,
    condition: () => codelistAttributes.value.extensible,
  },
  {
    label: t('CodelistTermTable.open_sponsor_history'),
    icon: 'mdi-history',
    click: openSponsorValuesHistory,
  },
  {
    label: t('CodelistTermTable.open_ct_history'),
    icon: 'mdi-history',
    click: openCTValuesHistory,
  },
]

const codelistAttributes = ref({})

const headers = [
  { title: '', key: 'actions', width: '1%' },
  { title: t('_global.library'), key: 'library_name' },
  {
    title: t('TermsView.sponsor_name'),
    key: 'name.sponsor_preferred_name',
  },
  { title: t('TermsView.name_status'), key: 'name.status' },
  {
    title: t('TermsView.name_date'),
    key: 'name.start_date',
  },
  { title: t('CtCatalogueTable.concept_id'), key: 'attributes.concept_id' },
  {
    title: t('TermsView.codelist_names'),
    key: 'codelists.codelist_name',
  },
  {
    title: t('TermsView.codelist_submvals'),
    key: 'codelists.codelist_submission_value',
  },
  {
    title: t('TermsView.submission_values'),
    key: 'codelists.submission_value',
  },
  {
    title: t('CtCatalogueTable.nci_pref_name'),
    key: 'attributes.nci_preferred_name',
  },
  { title: t('_global.definition'), key: 'attributes.definition' },
  {
    title: t('CodelistTermsView.attr_status'),
    key: 'attributes.status',
  },
  {
    title: t('CodelistTermsView.attr_date'),
    key: 'attributes.start_date',
  },
]
const historyItems = ref([])
const historyHeaders = ref([])
let historyType = ''
const selectedTerm = ref({})
const showCreationForm = ref(false)
const showHistory = ref(false)
const terms = ref([])
const total = ref(0)

const historyTitleLabel = computed(() => {
  return historyType === 'termName'
    ? t('CodelistTermTable.history_label_name', {
        term: selectedTerm.value.term_uid,
      })
    : t('CodelistTermTable.history_label_attributes', {
        term: selectedTerm.value.term_uid,
      })
})
const exportUrlParams = computed(() => {
  return {}
})

watch(
  () => props.package,
  (newValue, oldValue) => {
    if (newValue !== oldValue) {
      fetchTerms()
    }
  }
)

onMounted(() => {})

function submissionValuesDisplay(item) {
  let display = ''
  item.codelists.forEach((element) => {
    display += '&#9679; ' + element.submission_value + '</br>'
  })
  return display
}
function codelistNamesDisplay(item) {
  let display = ''
  item.codelists.forEach((element) => {
    display += '&#9679; ' + element.codelist_name + '</br>'
  })
  return display
}
function codelistSubmvalsDisplay(item) {
  let display = ''
  item.codelists.forEach((element) => {
    display += '&#9679; ' + element.codelist_submission_value + '</br>'
  })
  return display
}

function fetchTerms(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  if (params.filters) {
    // Replace any placeholder text for null with proper null value
    const json_filters = JSON.parse(params.filters)
    for (const key in json_filters) {
      for (const [index, value] of json_filters[key].v.entries()) {
        if (value === t('_global.none')) {
          json_filters[key].v[index] = null
        }
      }
    }
    params.filters = JSON.stringify(json_filters)
  }
  if (props.package) {
    params.package = props.package.name
  }

  termsApi.getAll(params).then((resp) => {
    terms.value = resp.data.items
    total.value = resp.data.total
    // Sponsor terms do not have a concept id.
    // Show the term uid for these.
    for (const term of terms.value) {
      if (term.concept_id === null) {
        term._concept_id = term.term_uid
      } else {
        term._concept_id = term.concept_id
      }
    }
  })
}
function removeTerm(term) {
  controlledTerminology
    .removeTermFromCodelist(props.codelistUid, term.term_uid)
    .then(() => {
      fetchTerms()
      notificationHub.add({
        msg: t('CodelistTermCreationForm.remove_success'),
      })
    })
}
function editTerm(term) {
  if (props.package) {
    router.push({
      name: 'CtPackageTermDetail',
      params: {
        catalogue_name: props.catalogueName,
        package_name: props.package ? props.package.name : '',
        codelist_id: term.codelist_uid,
        term_id: term.term_uid,
      },
    })
  } else {
    router.push({
      name: 'CodelistTermDetail',
      params: {
        catalogue_name: props.catalogueName,
        term_id: term.term_uid,
      },
    })
  }
}
async function openSponsorValuesHistory(term) {
  selectedTerm.value = term
  historyType = 'termName'
  historyHeaders.value = [
    {
      title: t('CodeListDetail.sponsor_pref_name'),
      key: 'sponsor_preferred_name',
    },
    {
      title: t('CodelistTermDetail.sentence_case_name'),
      key: 'sponsor_preferred_name_sentence_case',
    },
    { title: t('CodelistTermDetail.order'), key: 'order' },
    { title: t('_global.status'), key: 'status' },
    { title: t('_global.version'), key: 'version' },
  ]
  const resp = await controlledTerminology.getCodelistTermNamesVersions(
    selectedTerm.value.term_uid
  )
  historyItems.value = resp.data.map((item) => {
    return item
  })
  showHistory.value = true
}
async function openCTValuesHistory(term) {
  selectedTerm.value = term
  historyType = 'termAttributes'
  historyHeaders.value = [
    { title: t('CodelistTermDetail.concept_id'), key: 'term_uid' },
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
  historyType = ''
  selectedTerm.value = {}
}
</script>
