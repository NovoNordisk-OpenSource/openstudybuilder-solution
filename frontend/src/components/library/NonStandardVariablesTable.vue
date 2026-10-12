<template>
  <div class="d-flex flex-column align-center mb-4 mt-4">
    <v-btn-toggle
      v-model="selectedStatusTab"
      mandatory
      density="compact"
      color="nnBaseBlue"
      divided
      variant="outlined"
      class="layoutSelector"
      @update:model-value="onStatusTabChange"
    >
      <v-btn v-for="tab in statusTabs" :key="tab.value" :value="tab.value">
        {{ tab.label }}
      </v-btn>
    </v-btn-toggle>
  </div>
  <!-- is_nsv: true restricts header autocomplete values to NSV items only; ActivityItemClassTable passes false. Both share the same column-data-resource. -->
  <NNTable
    ref="table"
    table-id="library-non-standard-variables-table"
    :headers="headers"
    :items="items"
    :items-length="total"
    item-value="uid"
    :history-config="{
      dataFetcher: fetchAuditTrail,
      changeField: 'change_description',
      title: $t('_global.audit_trail'),
    }"
    :export-config="{
      objectLabel: 'NonStandardVariables',
      dataUrl: '/activity-item-classes',
      dataUrlParams: { is_nsv: true },
    }"
    column-data-resource="activity-item-classes"
    :column-data-parameters="{ is_nsv: true }"
    :filters-modify-function="modifyFilters"
    hide-default-switches
    @filter="fetchItems"
  >
    <template #actions="">
      <v-btn
        data-cy="add-non-standard-variable"
        class="ml-2"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        @click.stop="showCreationForm = true"
      >
        <v-icon>mdi-plus</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ $t('NonStandardVariablesTable.add_nsv') }}
        </v-tooltip>
      </v-btn>
    </template>
    <template #[`item.actions`]="{ item }">
      <v-progress-circular
        v-if="processingUids.has(item.uid)"
        indeterminate
        color="nnBaseBlue"
        size="20"
        width="2"
      />
      <ActionsMenu v-else :actions="rowActions" :item="item" />
    </template>
    <template #[`item.name`]="{ item }">
      <router-link
        :to="{ name: 'ActivityItemClassOverview', params: { id: item.uid } }"
      >
        {{ item.name }}
      </router-link>
    </template>
    <template #[`item.nci_concept_id`]="{ item }">
      <NCIConceptLink :concept-id="item.nci_concept_id" />
    </template>
    <template #[`item.non_standard_variable.is_multiple`]="{ item }">
      {{ $filters.yesno(item.non_standard_variable?.is_multiple) }}
    </template>
    <template #[`item.non_standard_variable.is_cdisc_defined`]="{ item }">
      {{ $filters.yesno(item.non_standard_variable?.is_cdisc_defined) }}
    </template>
    <template #[`item.valid_codelists`]="{ item }">
      {{
        (item.valid_codelists || []).map((c) => c.submission_value).join(', ')
      }}
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
    <template #[`item.status`]="{ item }">
      <StatusChip v-if="item.status" :status="item.status" />
    </template>
  </NNTable>
  <NonStandardVariableForm
    :open="showCreationForm"
    :edited-item="editedItem"
    @close="closeForm"
    @created="onCreated"
    @updated="onUpdated"
  />
  <v-dialog
    v-model="showHistory"
    persistent
    :fullscreen="$globals.historyDialogFullscreen"
    @keydown.esc="showHistory = false"
  >
    <HistoryTable
      :title="historyTitle"
      :headers="headers"
      :items="historyItems"
      @close="showHistory = false"
    />
  </v-dialog>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
</template>

<script setup>
import { computed, inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import NCIConceptLink from '@/components/tools/NCIConceptLink.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import NonStandardVariableForm from '@/components/library/NonStandardVariableForm.vue'
import api from '@/api/activityItemClasses'
import filteringParameters from '@/utils/filteringParameters'
import statuses from '@/constants/statuses'
import _isEmpty from 'lodash/isEmpty'
import { DEMO_MODE } from '@/demo/isDemoMode'

const { t } = useI18n()
const roles = inject('roles')
const notificationHub = inject('notificationHub')

const items = ref([])
const total = ref(0)
const table = ref()
const showCreationForm = ref(false)
const showHistory = ref(false)
const historyItems = ref([])
const selectedItem = ref(null)
const editedItem = ref(null)
const processingUids = ref(new Set())
const confirm = ref()
const selectedStatusTab = ref('all')

// The demo mock backend synthesizes list responses from the OpenAPI schema
// alone (see mockBackend.js) and never varies `status` per row, so no real
// approve/new-version action can produce an actual Final-to-Draft change to
// smoke-test against. This lets a test simulate that external change
// directly. It's also the only way to change a row without a click, which
// matters here: clicking anything else on the page (e.g. a row action)
// closes any open filter dropdown via Vuetify's outside-click handling,
// defeating the very "row changes while the dropdown stays open" scenario
// this is meant to cover.
if (DEMO_MODE) {
  globalThis.__demoSimulateNsvRowChange = (index, patch) => {
    if (!items.value[index]) return
    items.value = items.value.map((item, i) =>
      i === index ? { ...item, ...patch } : item
    )
  }
}

const statusTabs = [
  { value: 'all', label: 'All' },
  { value: 'final', label: 'Final' },
  { value: 'draft', label: 'Draft' },
  { value: 'retired', label: 'Retired' },
]

const rowActions = [
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions?.find((action) => action === 'edit'),
    accessRole: roles.LIBRARY_WRITE,
    click: editItem,
  },
  {
    label: t('_global.approve'),
    icon: 'mdi-check-decagram',
    iconColor: 'success',
    condition: (item) =>
      item.possible_actions?.find((action) => action === 'approve'),
    accessRole: roles.LIBRARY_WRITE,
    click: approveItem,
  },
  {
    label: t('_global.new_version'),
    icon: 'mdi-plus-circle-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions?.find((action) => action === 'new_version'),
    accessRole: roles.LIBRARY_WRITE,
    click: createNewVersion,
  },
  {
    label: t('_global.inactivate'),
    icon: 'mdi-close-octagon-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions?.find((action) => action === 'inactivate'),
    accessRole: roles.LIBRARY_WRITE,
    click: inactivateItem,
  },
  {
    label: t('_global.reactivate'),
    icon: 'mdi-undo-variant',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions?.find((action) => action === 'reactivate'),
    accessRole: roles.LIBRARY_WRITE,
    click: reactivateItem,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: (item) =>
      item.possible_actions?.find((action) => action === 'delete'),
    accessRole: roles.LIBRARY_WRITE,
    click: deleteItem,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    accessRole: roles.LIBRARY_READ,
    click: openHistory,
  },
]

const headers = [
  { title: '', key: 'actions', width: '1%' },
  {
    key: 'non_standard_variable.code',
    title: t('NonStandardVariablesTable.nsv_code'),
  },
  { key: 'display_name', title: t('NonStandardVariablesTable.nsv_label') },
  { key: 'name', title: t('_global.name') },
  {
    key: 'nci_concept_id',
    title: t('NonStandardVariablesTable.nci_concept_id'),
  },
  {
    key: 'nci_concept_name',
    title: t('NonStandardVariablesTable.nci_concept_name'),
  },
  {
    key: 'non_standard_variable.is_multiple',
    title: t('NonStandardVariablesTable.multiple'),
  },
  {
    key: 'non_standard_variable.is_cdisc_defined',
    title: t('NonStandardVariablesTable.is_cdisc_defined'),
  },
  {
    key: 'semtcdt.name',
    title: t('NonStandardVariablesTable.data_type'),
  },
  {
    key: 'non_standard_variable.nsvxmldt',
    title: t('NonStandardVariablesTable.nsvxmldt'),
  },
  {
    key: 'non_standard_variable.length',
    title: t('NonStandardVariablesTable.length'),
  },
  {
    key: 'valid_codelists',
    title: t('NonStandardVariablesTable.codelist_codes'),
    filteringName: 'valid_codelists.submission_value',
    historyFilter: (value) =>
      (value || []).map((c) => c.submission_value).join(', '),
  },
  {
    key: 'non_standard_variable.origin_type.name',
    title: t('NonStandardVariablesTable.origin_type'),
  },
  {
    key: 'non_standard_variable.origin_source.name',
    title: t('NonStandardVariablesTable.origin_source'),
  },
  {
    key: 'non_standard_variable.algorithm',
    title: t('NonStandardVariablesTable.algorithm'),
  },
  { key: 'definition', title: t('_global.definition') },
  {
    key: 'non_standard_variable.derivation_rule',
    title: t('NonStandardVariablesTable.derivation_rule'),
  },
  { key: 'start_date', title: t('_global.modified') },
  { key: 'author_username', title: t('_global.modified_by') },
  { key: 'version', title: t('_global.version') },
  { key: 'status', title: t('_global.status'), noFilter: true },
]

const historyTitle = computed(() => {
  if (selectedItem.value) {
    return t('NonStandardVariablesTable.history_title', {
      uid: selectedItem.value.uid,
    })
  }
  return ''
})

function normalizeFiltersObject(filters) {
  if (_isEmpty(filters)) {
    return {}
  }
  if (typeof filters === 'string') {
    try {
      const parsedFilters = JSON.parse(filters)
      return parsedFilters && typeof parsedFilters === 'object'
        ? parsedFilters
        : {}
    } catch {
      return {}
    }
  }
  if (typeof filters === 'object') {
    return filters
  }
  return {}
}

function getSelectedStatusValue() {
  if (selectedStatusTab.value === 'final') {
    return statuses.FINAL
  }
  if (selectedStatusTab.value === 'retired') {
    return statuses.RETIRED
  }
  if (selectedStatusTab.value === 'draft') {
    return statuses.DRAFT
  }
  return null
}

function onStatusTabChange() {
  table.value?.filterTable()
}

function modifyFilters(jsonFilter, params) {
  const selectedStatusValue = getSelectedStatusValue()
  if (selectedStatusValue) {
    jsonFilter.status = { v: [selectedStatusValue] }
  } else {
    delete jsonFilter.status
  }
  return { jsonFilter, params }
}

const fetchItems = (filters, options, filtersUpdated) => {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  params.is_nsv = true
  const selectedStatusValue = getSelectedStatusValue()
  if (selectedStatusValue) {
    const filtersObj = normalizeFiltersObject(params.filters)
    filtersObj.status = { v: [selectedStatusValue] }
    params.filters = filtersObj
  }
  if (params.filters && typeof params.filters === 'object') {
    params.filters = JSON.stringify(params.filters)
  }
  api.getAll(params).then((resp) => {
    items.value = resp.data.items
    total.value = resp.data.total
  })
}

const fetchAuditTrail = async (options) => {
  const data = {
    page_number: options.page,
    page_size: options.itemsPerPage,
    total_count: true,
    is_nsv: true,
  }
  const resp = await api.getVersions(data)
  return resp.data
}

async function deleteItem(item) {
  const confirmed = await confirm.value.open(
    t('NonStandardVariablesTable.confirm_delete'),
    { type: 'warning' }
  )
  if (!confirmed) return
  await api.delete(item.uid)
  notificationHub.add({
    msg: t('NonStandardVariablesTable.delete_success'),
    type: 'success',
  })
  table.value?.filterTable()
}

async function openHistory(item) {
  selectedItem.value = item
  const resp = await api.getActivityItemClassVersions(item.uid)
  historyItems.value = resp.data
  showHistory.value = true
}

async function approveItem(item) {
  await api.approve(item.uid)
  notificationHub.add({
    msg: t('NonStandardVariablesTable.approve_success'),
    type: 'success',
  })
  table.value?.filterTable()
}

async function createNewVersion(item) {
  await api.newVersion(item.uid)
  notificationHub.add({
    msg: t('NonStandardVariablesTable.new_version_success'),
    type: 'success',
  })
  table.value?.filterTable()
}

async function inactivateItem(item) {
  processingUids.value.add(item.uid)
  try {
    await api.inactivate(item.uid)
    notificationHub.add({
      msg: t('NonStandardVariablesTable.inactivate_success'),
      type: 'success',
    })
    table.value?.filterTable()
  } finally {
    processingUids.value.delete(item.uid)
  }
}

async function reactivateItem(item) {
  processingUids.value.add(item.uid)
  try {
    await api.reactivate(item.uid)
    notificationHub.add({
      msg: t('NonStandardVariablesTable.reactivate_success'),
      type: 'success',
    })
    table.value?.filterTable()
  } finally {
    processingUids.value.delete(item.uid)
  }
}

async function editItem(item) {
  const resp = await api.get(item.uid)
  editedItem.value = resp.data
  showCreationForm.value = true
}

function closeForm() {
  showCreationForm.value = false
  editedItem.value = null
}

function onCreated() {
  closeForm()
  table.value?.filterTable()
}

function onUpdated() {
  closeForm()
  table.value?.filterTable()
}
</script>

<style scoped>
.layoutSelector {
  border-color: rgb(var(--v-theme-nnBaseBlue));
}

.layoutSelector :deep(.v-btn) {
  text-transform: none;
}
</style>
