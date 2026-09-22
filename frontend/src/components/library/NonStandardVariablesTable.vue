<template>
  <NNTable
    ref="table"
    :headers="headers"
    :items="items"
    :items-length="total"
    :history-data-fetcher="fetchAuditTrail"
    :history-title="$t('_global.audit_trail')"
    history-change-field="change_description"
    item-value="uid"
    :export-config="{
      objectLabel: 'NonStandardVariables',
      dataUrl: '/activity-item-classes',
      dataUrlParams: { is_nsv: true },
    }"
    column-data-resource="activity-item-classes"
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
      <ActionsMenu :actions="rowActions" :item="item" />
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

const { t } = useI18n()
const notificationHub = inject('notificationHub')

const items = ref([])
const total = ref(0)
const table = ref()
const showCreationForm = ref(false)
const showHistory = ref(false)
const historyItems = ref([])
const selectedItem = ref(null)
const editedItem = ref(null)
const confirm = ref()

const rowActions = [
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions?.find((action) => action === 'edit'),
    click: editItem,
  },
  {
    label: t('_global.approve'),
    icon: 'mdi-check-decagram',
    iconColor: 'success',
    condition: (item) =>
      item.possible_actions?.find((action) => action === 'approve'),
    click: approveItem,
  },
  {
    label: t('_global.new_version'),
    icon: 'mdi-plus-circle-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions?.find((action) => action === 'new_version'),
    click: createNewVersion,
  },
  {
    label: t('_global.inactivate'),
    icon: 'mdi-close-octagon-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions?.find((action) => action === 'inactivate'),
    click: inactivateItem,
  },
  {
    label: t('_global.reactivate'),
    icon: 'mdi-undo-variant',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions?.find((action) => action === 'reactivate'),
    click: reactivateItem,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: (item) =>
      item.possible_actions?.find((action) => action === 'delete'),
    click: deleteItem,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
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
    key: 'data_type.name',
    title: t('NonStandardVariablesTable.data_type'),
  },
  {
    key: 'non_standard_variable.length',
    title: t('NonStandardVariablesTable.length'),
  },
  {
    key: 'valid_codelists',
    title: t('NonStandardVariablesTable.codelist_codes'),
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
  { key: 'status', title: t('_global.status') },
]

const historyTitle = computed(() => {
  if (selectedItem.value) {
    return t('NonStandardVariablesTable.history_title', {
      uid: selectedItem.value.uid,
    })
  }
  return ''
})

const fetchItems = (filters, options, filtersUpdated) => {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  params.is_nsv = true
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
  await api.inactivate(item.uid)
  notificationHub.add({
    msg: t('NonStandardVariablesTable.inactivate_success'),
    type: 'success',
  })
  table.value?.filterTable()
}

async function reactivateItem(item) {
  await api.reactivate(item.uid)
  notificationHub.add({
    msg: t('NonStandardVariablesTable.reactivate_success'),
    type: 'success',
  })
  table.value?.filterTable()
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
