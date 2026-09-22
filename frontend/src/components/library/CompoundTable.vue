<template>
  <NNTable
    table-id="library-compounds-table"
    :headers="headers"
    :items="compounds"
    :items-length="total"
    item-value="uid"
    density="compact"
    column-data-resource="concepts/compounds"
    :history-config="{
      dataFetcher: fetchGlobalAuditTrail,
      changeField: 'change_description',
      title: $t('_global.audit_trail'),
    }"
    :export-config="{ objectLabel: 'compounds', dataUrl: 'concepts/compounds' }"
    @filter="fetchItems"
  >
    <template #actions="">
      <v-btn
        color="nnBaseBlue"
        icon
        size="small"
        :disabled="!accessGuard.checkPermission($roles.LIBRARY_WRITE)"
        variant="outlined"
        @click.stop="showCompoundForm = true"
      >
        <v-icon>mdi-plus</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ $t('CompoundForm.add_title') }}
        </v-tooltip>
      </v-btn>
    </template>
    <template #[`item.actions`]="{ item }">
      <ActionsMenu :actions="actions" :item="item" />
    </template>
    <template #[`item.name`]="{ item }">
      <router-link :to="{ name: 'CompoundOverview', params: { id: item.uid } }">
        {{ item.name }}
      </router-link>
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
  <v-dialog
    v-model="showCompoundForm"
    fullscreen
    persistent
    content-class="fullscreen-dialog"
  >
    <CompoundForm
      :open="showCompoundForm"
      :compound-uid="selectedCompound ? selectedCompound.uid : null"
      @close="closeCompoundForm"
      @created="fetchItems"
      @updated="fetchItems"
    />
  </v-dialog>
  <v-dialog
    v-model="showHistory"
    persistent
    :fullscreen="$globals.historyDialogFullscreen"
    @keydown.esc="closeHistory"
  >
    <HistoryTable
      :title="historyTitle"
      :headers="headers"
      :items="historyItems"
      @close="closeHistory"
    />
  </v-dialog>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import CompoundForm from './CompoundForm.vue'
import compoundsApi from '@/api/concepts/compounds'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import { useAccessGuard } from '@/composables/accessGuard'
import filteringParameters from '@/utils/filteringParameters'

const notificationHub = inject('notificationHub')
const roles = inject('roles')
const { t } = useI18n()

const props = defineProps({
  tabClickedAt: {
    type: Number,
    default: null,
  },
})

const accessGuard = useAccessGuard()

const actions = [
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'edit'),
    accessRole: roles.LIBRARY_WRITE,
    click: editCompound,
  },
  {
    label: t('_global.approve'),
    icon: 'mdi-check-decagram',
    iconColor: 'success',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'approve'),
    accessRole: roles.LIBRARY_WRITE,
    click: approveCompound,
  },
  {
    label: t('_global.new_version'),
    icon: 'mdi-plus-circle-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'new_version'),
    accessRole: roles.LIBRARY_WRITE,
    click: createNewVersion,
  },
  {
    label: t('_global.inactivate'),
    icon: 'mdi-close-octagon-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'inactivate'),
    accessRole: roles.LIBRARY_WRITE,
    click: inactivateCompound,
  },
  {
    label: t('_global.reactivate'),
    icon: 'mdi-undo-variant',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'reactivate'),
    accessRole: roles.LIBRARY_WRITE,
    click: reactivateCompound,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'delete'),
    accessRole: roles.LIBRARY_WRITE,
    click: deleteCompound,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openHistory,
  },
]

const compounds = ref([])
const savedFilters = ref({})

const headers = [
  { title: '', key: 'actions', width: '5%' },
  { title: t('CompoundTable.compound_name'), key: 'name' },
  { title: t('_global.definition'), key: 'definition' },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.version'), key: 'version' },
  { title: t('_global.status'), key: 'status' },
]
const historyItems = ref([])
const selectedCompound = ref(null)
const showCompoundForm = ref(false)
const showHistory = ref(false)
const total = ref(0)
const confirm = ref()

const historyTitle = computed(() => {
  if (selectedCompound.value) {
    return t('CompoundTable.compound_history_title', {
      compound: selectedCompound.value.uid,
    })
  }
  return ''
})
watch(
  () => props.tabClickedAt,
  () => {
    fetchItems(savedFilters.value)
  }
)

function fetchItems(filters, options, filtersUpdated) {
  if (filters !== undefined) {
    savedFilters.value = filters
  }
  const params = filteringParameters.prepareParameters(
    options,
    savedFilters.value,
    filtersUpdated
  )
  compoundsApi.getFiltered(params).then((resp) => {
    compounds.value = resp.data.items
    total.value = resp.data.total
  })
}
function closeCompoundForm() {
  showCompoundForm.value = false
  selectedCompound.value = null
}
function editCompound(item) {
  // Resolve the row back to the fetched compound before editing
  const originalItem = compounds.value.find(
    (compound) => compound.uid === item.uid
  )
  selectedCompound.value = originalItem
  showCompoundForm.value = true
}
function approveCompound(item) {
  compoundsApi.approve(item.uid).then(() => {
    fetchItems()
    notificationHub.add({
      msg: t('CompoundTable.approve_success'),
      type: 'success',
    })
  })
}
async function deleteCompound(item) {
  const options = { type: 'warning' }
  const compound = item.name
  if (
    await confirm.value.open(
      t('CompoundTable.confirm_delete', { compound }),
      options
    )
  ) {
    await compoundsApi.deleteObject(item.uid)
    fetchItems()
    notificationHub.add({
      msg: t('CompoundTable.delete_success'),
      type: 'success',
    })
  }
}
function createNewVersion(item) {
  compoundsApi.newVersion(item.uid).then(() => {
    fetchItems()
    notificationHub.add({
      msg: t('CompoundTable.new_version_success'),
      type: 'success',
    })
  })
}
function inactivateCompound(item) {
  compoundsApi.inactivate(item.uid).then(() => {
    fetchItems()
    notificationHub.add({
      msg: t('CompoundTable.inactivate_success'),
      type: 'success',
    })
  })
}
function reactivateCompound(item) {
  compoundsApi.reactivate(item.uid).then(() => {
    fetchItems()
    notificationHub.add({
      msg: t('CompoundTable.reactivate_success'),
      type: 'success',
    })
  })
}
async function openHistory(item) {
  selectedCompound.value = item
  const resp = await compoundsApi.getVersions(selectedCompound.value.uid)
  historyItems.value = resp.data
  showHistory.value = true
}
function closeHistory() {
  showHistory.value = false
}
async function fetchGlobalAuditTrail(options) {
  const resp = await compoundsApi.getAllVersions(options)
  return resp.data.items
}
</script>
