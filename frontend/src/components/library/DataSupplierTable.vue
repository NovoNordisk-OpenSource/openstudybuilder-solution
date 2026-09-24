<template>
  <div>
    <NNTable
      ref="table"
      table-id="library-data-suppliers-table"
      :headers="headers"
      :items="dataSuppliers"
      item-value="uid"
      sort-desc
      :items-length="total"
      column-data-resource="data-suppliers"
      :export-config="{
        objectLabel: 'DataSuppliers',
        dataUrl: 'data-suppliers',
      }"
      @filter="getDataSuppliers"
    >
      <template #actions="">
        <v-btn
          class="ml-2"
          icon
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          data-cy="add-data-supplier"
          :disabled="!accessGuard.checkPermission($roles.LIBRARY_WRITE)"
          @click.stop="openForm()"
        >
          <v-icon>mdi-plus</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('DataSupplierView.DataSupplierTable.add_data_supplier') }}
          </v-tooltip>
        </v-btn>
      </template>
      <template #[`item.actions`]="{ item }">
        <ActionsMenu :actions="actions" :item="item" />
      </template>
      <template #[`item.status`]="{ item }">
        <StatusChip :status="item.status" />
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
    <DataSupplierForm
      :open="showForm"
      :selected-data-supplier="selectedDataSupplier"
      @close="closeForm"
    />
    <v-dialog
      v-model="showDataSupplierHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeDataSupplierHistory"
    >
      <HistoryTable
        :title="dataSupplierHistoryTitle"
        :headers="headers"
        :items="dataSupplierHistoryItems"
        @close="closeDataSupplierHistory"
      />
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, inject } from 'vue'
import { useI18n } from 'vue-i18n'
import NNTable from '@/components/tools/NNTable.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import dataSuppliersApi from '@/api/dataSuppliers'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import filteringParameters from '@/utils/filteringParameters'
import DataSupplierForm from '@/components/library/DataSupplierForm.vue'
import { useAccessGuard } from '@/composables/accessGuard'
import { useDataSuppliersStore } from '@/stores/data-suppliers'

const dataSuppliersStore = useDataSuppliersStore()
const accessGuard = useAccessGuard()
const { t } = useI18n()
const roles = inject('roles')
const table = ref()

const total = computed(() => {
  return dataSuppliersStore.totalItems
})

const dataSuppliers = computed(() => {
  return dataSuppliersStore.items
})

const dataSupplierHistoryTitle = computed(() => {
  if (selectedDataSupplier.value) {
    return t('DataSuppliers.data_supplier_history_title', {
      dataSupplierUid: selectedDataSupplier.value.uid,
    })
  }
  return ''
})

const actions = [
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'edit'),
    accessRole: roles.LIBRARY_WRITE,
    click: edit,
  },
  {
    label: t('_global.inactivate'),
    icon: 'mdi-close-octagon-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'inactivate'),
    accessRole: roles.LIBRARY_WRITE,
    click: inactivateDataSupplier,
  },
  {
    label: t('_global.reactivate'),
    icon: 'mdi-undo-variant',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'reactivate'),
    accessRole: roles.LIBRARY_WRITE,
    click: reactivateDataSupplier,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openDataSupplierHistory,
  },
]
const headers = [
  { title: '', key: 'actions', width: '1%' },
  { title: t('_global.name'), key: 'name' },
  { title: t('_global.description'), key: 'description' },
  { title: t('_global.order'), key: 'order' },
  {
    title: t('DataSupplierView.DataSupplierTable.api_base_url'),
    key: 'api_base_url',
  },
  {
    title: t('DataSupplierView.DataSupplierTable.ui_base_url'),
    key: 'ui_base_url',
  },
  {
    title: t('DataSupplierView.DataSupplierTable.supplier_type'),
    key: 'supplier_type.name',
  },
  {
    title: t('DataSupplierView.DataSupplierTable.origin_source'),
    key: 'origin_source.name',
  },
  {
    title: t('DataSupplierView.DataSupplierTable.origin_type'),
    key: 'origin_type.name',
  },
  { title: t('_global.author'), key: 'author_username' },
  { title: t('_global.modified'), key: 'start_date' },
  {
    title: t('_global.change_description'),
    key: 'change_description',
  },
  { title: t('_global.version'), key: 'version' },
  { title: t('_global.status'), key: 'status' },
]
const showForm = ref(false)
const showDataSupplierHistory = ref(false)
const selectedDataSupplier = ref(null)
const filtersRef = ref('')
const dataSupplierHistoryItems = ref([])

function inactivateDataSupplier(item) {
  dataSuppliersApi.inactivate(item.uid).then(() => {
    table.value.filterTable()
  })
}
function reactivateDataSupplier(item) {
  dataSuppliersApi.reactivate(item.uid).then(() => {
    table.value.filterTable()
  })
}
function edit(item) {
  dataSuppliersApi.getDataSupplier(item.uid).then((resp) => {
    selectedDataSupplier.value = resp.data
    showForm.value = true
  })
}
async function openDataSupplierHistory(dataSupplier) {
  selectedDataSupplier.value = dataSupplier
  const resp = await dataSuppliersApi.getAuditTrail(dataSupplier.uid)
  dataSupplierHistoryItems.value = resp.data
  showDataSupplierHistory.value = true
}
function closeDataSupplierHistory() {
  showDataSupplierHistory.value = false
  selectedDataSupplier.value = null
}
function openForm() {
  selectedDataSupplier.value = null
  showForm.value = true
}
function closeForm() {
  selectedDataSupplier.value = null
  showForm.value = false
  table.value.filterTable()
}
function getDataSuppliers(filters, options, filtersUpdated) {
  if (filters) {
    filtersRef.value = filters
  }
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  dataSuppliersStore.fetchDataSuppliers(params)
}
</script>
