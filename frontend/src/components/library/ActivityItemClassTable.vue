<template>
  <NNTable
    ref="table"
    table-id="library-activity-item-classes-table"
    :headers="headers"
    :items="items"
    :items-length="total"
    item-value="uid"
    column-data-resource="activity-item-classes"
    :history-config="{
      dataFetcher: fetchAuditTrail,
      changeField: 'change_description',
      title: $t('_global.audit_trail'),
    }"
    :export-config="{
      objectLabel: 'ActivityItemClasses',
      dataUrl: '/activity-item-classes',
    }"
    @filter="fetchItems"
  >
    <template #[`item.actions`]="{ item }">
      <ActionsMenu :actions="actions" :item="item" />
    </template>
    <template #[`item.name`]="{ item }">
      <router-link
        :to="{ name: 'ActivityItemClassOverview', params: { id: item.uid } }"
        class="text-decoration-none"
      >
        {{ item.name }}
      </router-link>
    </template>
    <template #[`item.nci_concept_id`]="{ item }">
      <NCIConceptLink :concept-id="item.nci_concept_id" />
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
      <StatusChip :status="item.status" />
    </template>
  </NNTable>
  <ActivityItemClassForm
    :open="showForm"
    :edited-item-class="activeItemClass"
    @close="closeForm"
    @save="refreshTable"
  />
  <v-dialog
    v-model="showHistory"
    persistent
    :fullscreen="$globals.historyDialogFullscreen"
    @keydown.esc="closeHistory"
  >
    <HistoryTable
      :title="historyTitle"
      :headers="historyHeaders"
      :items="historyItems"
      :items-total="historyItems.length"
      :change-field="'change_description'"
      export-name="ActivityItemClass"
      @close="closeHistory"
    />
  </v-dialog>
</template>

<script setup>
import { inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ActivityItemClassForm from '@/components/library/ActivityItemClassForm.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import NCIConceptLink from '@/components/tools/NCIConceptLink.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import api from '@/api/activityItemClasses'
import statuses from '@/constants/statuses'
import filteringParameters from '@/utils/filteringParameters'

const { t } = useI18n()
const roles = inject('roles')
const notificationHub = inject('notificationHub')

const items = ref([])
const total = ref(0)
const table = ref()
const showForm = ref(false)
const activeItemClass = ref({})
const showHistory = ref(false)
const historyItems = ref([])
const historyTitle = ref('')

const headers = [
  { title: '', key: 'actions', width: '1%' },
  { key: 'name', title: t('_global.name') },
  { key: 'display_name', title: t('ActivityItemClassTable.display_name') },
  { key: 'definition', title: t('_global.definition') },
  { key: 'nci_concept_id', title: t('ActivityItemClassTable.nci_concept_id') },
  { key: 'start_date', title: t('_global.modified') },
  { key: 'author_username', title: t('_global.modified_by') },
  { key: 'version', title: t('_global.version') },
  { key: 'status', title: t('_global.status') },
]

const historyHeaders = [
  { key: 'name', title: t('_global.name') },
  { key: 'display_name', title: t('ActivityItemClassForm.display_name') },
  { key: 'order', title: t('_global.order') },
  { key: 'nci_concept_id', title: t('ActivityItemClassTable.nci_concept_id') },
  { key: 'definition', title: t('_global.definition') },
  { key: 'status', title: t('_global.status') },
  { key: 'version', title: t('_global.version') },
]

const actions = [
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: (item) => item.status === statuses.DRAFT,
    accessRole: roles.LIBRARY_WRITE,
    click: editItemClass,
  },
  {
    label: t('_global.approve'),
    icon: 'mdi-check-decagram',
    iconColor: 'success',
    condition: (item) => item.status === statuses.DRAFT,
    accessRole: roles.LIBRARY_WRITE,
    click: approveItemClass,
  },
  {
    label: t('_global.new_version'),
    icon: 'mdi-plus-circle-outline',
    iconColor: 'primary',
    condition: (item) => item.status === statuses.FINAL,
    accessRole: roles.LIBRARY_WRITE,
    click: newItemClassVersion,
  },
  {
    label: t('_global.inactivate'),
    icon: 'mdi-close-octagon-outline',
    iconColor: 'primary',
    condition: (item) => item.status === statuses.FINAL,
    accessRole: roles.LIBRARY_WRITE,
    click: inactivateItemClass,
  },
  {
    label: t('_global.reactivate'),
    icon: 'mdi-undo-variant',
    iconColor: 'primary',
    condition: (item) => item.status === statuses.RETIRED,
    accessRole: roles.LIBRARY_WRITE,
    click: reactivateItemClass,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    accessRole: roles.LIBRARY_READ,
    click: openHistory,
  },
]

const fetchItems = (filters, options, filtersUpdated) => {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  params.is_nsv = false
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
    is_nsv: false,
  }
  const resp = await api.getVersions(data)
  return resp.data
}

function refreshTable() {
  table.value.filterTable()
}

function editItemClass(item) {
  activeItemClass.value = item
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  activeItemClass.value = {}
}

function notifySuccess(key) {
  notificationHub.add({ msg: t(key), type: 'success' })
  refreshTable()
}

function approveItemClass(item) {
  api.approve(item.uid).then(() => {
    notifySuccess('ActivityItemClassTable.approve_success')
  })
}

function newItemClassVersion(item) {
  api.newVersion(item.uid).then(() => {
    notifySuccess('ActivityItemClassTable.new_version_success')
  })
}

function inactivateItemClass(item) {
  api.inactivate(item.uid).then(() => {
    notifySuccess('ActivityItemClassTable.inactivate_success')
  })
}

function reactivateItemClass(item) {
  api.reactivate(item.uid).then(() => {
    notifySuccess('ActivityItemClassTable.reactivate_success')
  })
}

async function openHistory(item) {
  historyTitle.value = t('ActivityItemClassTable.history_title', {
    name: item.name,
  })
  const resp = await api.getActivityItemClassVersions(item.uid)
  historyItems.value = resp.data
  showHistory.value = true
}

function closeHistory() {
  showHistory.value = false
  historyItems.value = []
}
</script>
