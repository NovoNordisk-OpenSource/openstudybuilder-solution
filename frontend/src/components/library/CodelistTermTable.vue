<template>
  <CodelistSummary
    :codelist-names="codelistNames"
    :codelist-attributes="codelistAttributes"
  />
  <NNTable
    table-id="library-codelist-terms-table"
    :headers="headers"
    :items="terms"
    :items-length="total"
    class="mt-4"
    column-data-resource="ct/codelists/terms"
    :codelist-uid="codelistUid"
    :column-data-parameters="{ include_removed: showRemoved }"
    :export-config="{
      dataUrlParams: exportUrlParams,
      objectLabel: 'Terms',
      dataUrl: 'ct/codelists/terms',
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
    <template #[`item.end_date`]="{ item }">
      {{
        item.end_date ? $filters.date(item.end_date) : $t('_global.date_null')
      }}
    </template>
    <template #[`item.name_status`]="{ item }">
      <StatusChip :status="item.name_status" />
    </template>
    <template #[`item.name_date`]="{ item }">
      {{ $filters.date(item.name_date) }}
    </template>
    <template #[`item.attributes_status`]="{ item }">
      <StatusChip :status="item.attributes_status" />
    </template>
    <template #[`item.attributes_date`]="{ item }">
      {{ $filters.date(item.attributes_date) }}
    </template>
    <template #[`item.actions`]="{ item }">
      <ActionsMenu :actions="actions" :item="item" />
    </template>
    <template #afterSwitches>
      <v-switch
        v-model="showRemoved"
        :label="$t('CodelistTermsView.show_removed')"
        hide-details
        @update:model-value="fetchTerms()"
      />
    </template>
  </NNTable>
  <v-dialog
    v-model="showCreationForm"
    persistent
    max-width="1024px"
    content-class="top-dialog"
  >
    <CodelistTermCreationForm
      :catalogue-names="codelistNames.catalogue_names"
      :codelist-uid="codelistNames.codelist_uid"
      :codelist-name="codelistNames.name"
      :default-library-name="codelistNames.library_name"
      @close="closeForm"
      @created="goToTerm"
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
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import controlledTerminology from '@/api/controlledTerminology'
import codelistApi from '@/api/controlledTerminology/codelists'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import CodelistSummary from '@/components/library/CodelistSummary.vue'
import CodelistTermCreationForm from '@/components/library/CodelistTermCreationForm.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import filteringParameters from '@/utils/filteringParameters'
import codelists from '@/utils/codelists'
import { useAccessGuard } from '@/composables/accessGuard'

const { t } = useI18n()
const router = useRouter()
const accessGuard = useAccessGuard()
const notificationHub = inject('notificationHub')
const roles = inject('roles')
const props = defineProps({
  codelistUid: {
    type: String,
    default: null,
  },
  package: {
    type: Object,
    default: null,
  },
  catalogueName: {
    type: String,
    default: null,
  },
})

const actions = [
  {
    label: t('CodelistTermTable.edit'),
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

const codelistNames = ref({})
const codelistAttributes = ref({})
const showRemoved = ref(false)

const headers = [
  { title: '', key: 'actions', width: '1%' },
  { title: t('_global.order'), key: 'order', width: '4%' },
  {
    title: t('CodelistTermsView.submission_value'),
    key: 'submission_value',
    width: '5%',
  },
  {
    title: t('CodelistTermsView.added_date'),
    key: 'start_date',
    width: '5%',
  },
  {
    title: t('CodelistTermsView.removed_date'),
    key: 'end_date',
    width: '5%',
  },
  { title: t('_global.library'), key: 'library_name', width: '7%' },
  {
    title: t('CodelistTermsView.sponsor_name'),
    key: 'sponsor_preferred_name',
    width: '10%',
  },
  {
    title: t('CodelistTermsView.name_status'),
    key: 'name_status',
    width: '5%',
  },
  {
    title: t('CodelistTermsView.name_date'),
    key: 'name_date',
    width: '5%',
  },
  { title: t('CtCatalogueTable.concept_id'), key: 'concept_id', width: '5%' },

  {
    title: t('CtCatalogueTable.nci_pref_name'),
    key: 'nci_preferred_name',
    width: '10%',
  },
  { title: t('_global.definition'), key: 'definition', width: '10%' },
  {
    title: t('CodelistTermsView.attr_status'),
    key: 'attributes_status',
    width: '5%',
  },
  {
    title: t('CodelistTermsView.attr_date'),
    key: 'attributes_date',
    width: '5%',
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
  return { codelist_uid: props.codelistUid }
})

watch(
  () => props.package,
  (newValue, oldValue) => {
    if (newValue !== oldValue) {
      fetchTerms()
    }
  }
)

onMounted(() => {
  controlledTerminology.getCodelistNames(props.codelistUid).then((resp) => {
    codelistNames.value = resp.data
  })
  controlledTerminology
    .getCodelistAttributes(props.codelistUid)
    .then((resp) => {
      codelistAttributes.value = resp.data
    })
})

function fetchTerms(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  params.include_removed = showRemoved.value
  if (props.package) {
    params.package = props.package.name
  }
  codelistApi.getCodelistTerms(props.codelistUid, params).then((resp) => {
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
function closeForm() {
  showCreationForm.value = false
  fetchTerms()
}
function goToTerm(term) {
  editTerm(term)
  notificationHub.add({
    msg: t('CodelistTermCreationForm.add_success'),
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
        codelist_id: term.codelist_uid,
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
    item.order = codelists.getTermOrderInCodelist(item, props.codelistUid)
    return item
  })
  showHistory.value = true
}
async function openCTValuesHistory(term) {
  selectedTerm.value = term
  historyType = 'termAttributes'
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
  historyType = ''
  selectedTerm.value = {}
}
</script>
