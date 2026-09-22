<template>
  <NNTable
    ref="table"
    table-id="library-codelists-table"
    :headers="headers"
    :items="codelists"
    :items-length="total"
    item-value="codelist_uid"
    density="compact"
    :column-data-resource="columnDataResource"
    :column-data-parameters="getPackageObject()"
    :library="library"
    :disable-filtering="!displayTableToolbar"
    :advanced-search="advancedSearch"
    :export-config="{
      dataUrlParams: exportUrlParams,
      objectLabel: 'Codelists',
      dataUrl: columnDataResource,
    }"
    @filter="fetchCodelists"
  >
    <template #actions="">
      <slot name="extraActions" />
      <v-btn
        v-if="!readOnly"
        data-cy="add-sponsor-codelist"
        class="ml-2"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        :disabled="!accessGuard.checkPermission($roles.LIBRARY_WRITE)"
        @click.stop="showCreationForm = true"
      >
        <v-icon>mdi-plus</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ $t('CodelistCreationForm.title') }}
        </v-tooltip>
      </v-btn>
    </template>
    <template #beforeSwitches="">
      <v-select
        v-model="selectedTerms"
        data-cy="search-with-terms-field"
        :label="$t('CodelistTable.search_with_terms')"
        :items="termsStore.terms"
        item-title="sponsor_preferred_name"
        item-value="term_uid"
        class="max-width-400 mt-6"
        bg-color="nnWhite"
        clear-icon="mdi-close"
        single-line
        clearable
        return-object
        multiple
        :loading="loading"
        clear-on-select
        @update:search="updateTerms"
      >
        <template #item="{ props }">
          <v-list-item v-bind="props" @click="props.onClick">
            <template #prepend="{ isActive }">
              <v-list-item-action start>
                <v-checkbox-btn :model-value="isActive" />
              </v-list-item-action>
            </template>
            <template #title>
              {{ props.title }}
            </template>
          </v-list-item>
        </template>
        <template #selection="{ index }">
          <div v-if="index === 0">
            <span>
              {{ termslabel }}
            </span>
          </div>
          <span v-if="index === 1" class="text-grey text-body-small mr-1">
            (+{{ selectedTerms.length - 1 }})
          </span>
        </template>
        <template #menu-header>
          <div class="border-b w-100 pa-2" @keydown.stop>
            <v-text-field
              v-model="search"
              :placeholder="$t('_global.search')"
              prepend-inner-icon="mdi-magnify"
              hide-details
              clearable
              @update:model-value="updateTerms"
            />
          </div>
        </template>
      </v-select>
      <v-select
        v-model="termsFilterOperator"
        data-cy="search-with-terms-operator-field"
        :items="operators"
        bg-color="nnWhite"
        single-line
        :label="$t('_global.operator')"
        class="ml-1 terms-operator mt-6 mr-2"
      />
    </template>
    <template #beforeToolbar>
      <slot name="beforeToolbar" />
    </template>
    <template #[`item.actions`]="{ item }">
      <ActionsMenu :actions="actions" :item="item" />
    </template>
    <template #[`item.name.template_parameter`]="{ item }">
      {{ $filters.yesno(item.name.template_parameter) }}
    </template>
    <template #[`item.name.status`]="{ item }">
      <StatusChip :status="item.name.status" />
    </template>
    <template #[`item.name.start_date`]="{ item }">
      {{ $filters.date(item.name.start_date) }}
    </template>
    <template #[`item.attributes.extensible`]="{ item }">
      {{ $filters.yesno(item.attributes.extensible) }}
    </template>
    <template #[`item.attributes.status`]="{ item }">
      <StatusChip :status="item.attributes.status" />
    </template>
    <template #[`item.attributes.start_date`]="{ item }">
      {{ $filters.date(item.attributes.start_date) }}
    </template>
  </NNTable>
  <v-dialog
    v-if="!readOnly"
    v-model="showCreationForm"
    persistent
    max-width="1200px"
  >
    <CodelistCreationForm
      :default-library-name="library"
      @close="showCreationForm = false"
      @created="goToCodelist"
    />
  </v-dialog>
  <v-dialog
    v-model="showSponsorValuesHistory"
    persistent
    :fullscreen="$globals.historyDialogFullscreen"
    @keydown.esc="closeHistory"
  >
    <HistoryTable
      :title="historyTitle"
      :headers="historyHeaders"
      :items="historyItems"
      :items-total="historyItems.length"
      @close="closeHistory"
    />
  </v-dialog>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import controlledTerminology from '@/api/controlledTerminology'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import CodelistCreationForm from '@/components/library/CodelistCreationForm.vue'
import dataFormating from '@/utils/dataFormating'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import filteringParameters from '@/utils/filteringParameters'
import { useAccessGuard } from '@/composables/accessGuard'
import { useTermsStore } from '@/stores/library-terms'
import _debounce from 'lodash/debounce'

const notificationHub = inject('notificationHub')
const roles = inject('roles')
const props = defineProps({
  catalogue: {
    type: String,
    default: null,
    required: false,
  },
  package: {
    type: Object,
    default: null,
    required: false,
  },
  readOnly: {
    type: Boolean,
    default: false,
  },
  columnDataResource: {
    type: String,
    default: null,
  },
  library: {
    type: String,
    default: null,
  },
  displayRowActions: {
    type: Boolean,
    default: true,
  },
  displayTableToolbar: {
    type: Boolean,
    default: true,
  },
  sponsor: {
    type: Boolean,
    default: false,
  },
  advancedSearch: {
    type: Boolean,
    default: false,
  },
})
const emit = defineEmits(['openCodelistTerms'])
const termsStore = useTermsStore()
const accessGuard = useAccessGuard()
const { t } = useI18n()
const router = useRouter()

const codelists = ref([])
const headers = ref([
  { title: '', key: 'actions', width: '1%' },
  { title: t('_global.library'), key: 'library_name' },
  {
    title: t('CtCatalogueTable.sponsor_pref_name'),
    key: 'name.name',
    width: '15%',
  },
  {
    title: t('CodelistAttributesForm.codelist_type'),
    key: 'name.codelist_type',
  },
  {
    title: t('CtCatalogueTable.template_parameter'),
    key: 'name.template_parameter',
  },
  { title: t('CtCatalogueTable.cd_status'), key: 'name.status' },
  { title: t('CtCatalogueTable.modified_name'), key: 'name.start_date' },
  { title: t('CtCatalogueTable.concept_id'), key: 'codelist_uid' },
  {
    title: t('CtCatalogueTable.submission_value'),
    key: 'attributes.submission_value',
  },
  { title: t('CtCatalogueTable.cd_name'), key: 'attributes.name' },
  {
    title: t('CtCatalogueTable.nci_pref_name'),
    key: 'attributes.nci_preferred_name',
  },
  {
    title: t('CtCatalogueTable.paired_with'),
    key: 'paired_codelist.name',
  },
  { title: t('CtCatalogueTable.extensible'), key: 'attributes.extensible' },
  { title: t('CtCatalogueTable.attr_status'), key: 'attributes.status' },
  {
    title: t('CtCatalogueTable.modified_attributes'),
    key: 'attributes.start_date',
  },
])

const historyHeaders = [
  { title: t('_global.library'), key: 'library_name' },
  { title: t('_global.name'), key: 'name' },
  {
    title: t('CtCatalogueTable.template_parameter'),
    key: 'template_parameter',
  },
  { title: t('HistoryTable.change_description'), key: 'change_description' },
  { title: t('_global.status'), key: 'status' },
  { title: t('_global.version'), key: 'version' },
]

const historyItems = ref([])
const loading = ref(false)
const showCreationForm = ref(false)
const showSponsorValuesHistory = ref(false)
const selectedCodelist = ref(null)
const total = ref(0)
const savedFilters = ref('')
const selectedTerms = ref([])
const search = ref('')
const operators = ['or', 'and']
const termsFilterOperator = ref('or')
const table = ref()

const historyTitle = computed(() => {
  if (selectedCodelist.value) {
    return t('CodelistTable.history_title', {
      codelist: selectedCodelist.value.codelist_uid,
    })
  }
  return ''
})

const termslabel = computed(() => {
  let label = ''
  let labelLength = selectedTerms.value.length === 1 ? 36 : 30
  if (selectedTerms.value[0].sponsor_preferred_name.length > 30) {
    label =
      selectedTerms.value[0].sponsor_preferred_name.substring(0, labelLength) +
      '...'
  } else {
    label = selectedTerms.value[0].sponsor_preferred_name
  }
  return label
})

const exportUrlParams = computed(() => {
  const params = {}
  if (props.library) {
    params.library_name = props.library
  }
  if (props.package) {
    params.package = props.package.name
  }
  if (props.catalogue && props.catalogue !== 'All') {
    params.catalogue_name = props.catalogue
  }
  return params
})

watch(selectedTerms, () => {
  fetchCodelists()
})
watch(termsFilterOperator, () => {
  fetchCodelists()
})

const filters = {}
if (props.library) {
  filters['codelists.library_name'] = { v: [props.library] }
}
termsStore.fetchTerms(filters, true).then(() => {
  loading.value = false
})

function getPackageObject() {
  const result = {}
  if (props.catalogue && props.catalogue !== 'All') {
    result.catalogue_name = props.catalogue
  }
  if (props.package) {
    result.package = props.package.name
  }
  return result
}

function fetchCodelists(filters, options, filtersUpdated) {
  if (!filters && savedFilters.value) {
    filters = savedFilters.value
  }
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  savedFilters.value = filters
  if (props.advancedSearch) {
    params.match_whole_words = table.value?.matchWholeWords
  }
  params.library_name = props.library
  if (props.package) {
    params.package = props.package.name
    if (props.sponsor) {
      params.is_sponsor = true
    }
  } else if (props.catalogue && props.catalogue !== 'All') {
    params.catalogue_name = props.catalogue
  }
  if (selectedTerms.value.length > 0) {
    const term_uids = []
    for (const term of selectedTerms.value) {
      for (const uid of term.term_uids) {
        term_uids.push(uid)
      }
    }
    params.term_filter = JSON.stringify({
      term_uids,
      operator: termsFilterOperator.value,
    })
  }
  controlledTerminology.getCodelists(params).then((resp) => {
    codelists.value = resp.data.items
    total.value = resp.data.total
  })
}

function goToCodelist(codelist) {
  router.push({
    name: 'CodeListDetail',
    params: {
      catalogue_name: codelist.catalogue_name,
      codelist_id: codelist.codelist_uid,
    },
  })
  notificationHub.add({ msg: t('CodelistCreationForm.add_success') })
}

function openCodelistDetail(codelist) {
  router.push({
    name: 'CodeListDetail',
    params: {
      catalogue_name: props.catalogue,
      codelist_id: codelist.codelist_uid,
    },
  })
}

function openCodelistTerms(codelist) {
  const params = { codelist }
  if (props.catalogue) {
    params.catalogueName = props.catalogue
  }
  if (props.package) {
    params.packageName = props.package.name
  }
  emit('openCodelistTerms', params)
}

async function openCodelistHistory(codelist) {
  selectedCodelist.value = codelist
  const resp = await controlledTerminology.getCodelistNamesVersions(
    codelist.codelist_uid
  )
  historyItems.value = resp.data
  for (const item of historyItems.value) {
    if (item.template_parameter !== undefined) {
      item.template_parameter = dataFormating.yesno(item.template_parameter)
    }
  }
  showSponsorValuesHistory.value = true
}

function closeHistory() {
  showSponsorValuesHistory.value = false
}

const updateTerms = _debounce(function () {
  loading.value = true
  if (search.value === null) {
    search.value = ''
  }
  const filters = { '*': { v: [search.value] } }

  if (props.library) {
    filters['codelists.library_name'] = { v: [props.library] }
  }

  termsStore.fetchTerms(filters, true).then(() => {
    loading.value = false
  })
}, 800)

function refresh() {
  table.value.filterTable()
}

const actions = [
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: () => !props.readOnly,
    accessRole: roles.LIBRARY_WRITE,
    click: openCodelistDetail,
  },
  {
    label: t('CodelistTable.show_terms'),
    icon: 'mdi-dots-horizontal-circle-outline',
    click: openCodelistTerms,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openCodelistHistory,
  },
]

if (!props.displayRowActions) {
  headers.value.splice(0, 1)
}

defineExpose({
  refresh,
})
</script>

<style scoped>
.terms-operator {
  max-width: 100px;
  margin-bottom: 1px;
}
.terms-search {
  max-width: 400px;
  margin-bottom: 1px;
}
</style>
