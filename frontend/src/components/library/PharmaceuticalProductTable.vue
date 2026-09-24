<template>
  <NNTable
    table-id="library-pharmaceutical-products-table"
    :headers="headers"
    :items="products"
    :items-length="total"
    item-value="uid"
    density="compact"
    column-data-resource="concepts/pharmaceutical-products"
    :history-config="{
      dataFetcher: fetchGlobalAuditTrail,
      changeField: 'change_description',
      title: $t('_global.audit_trail'),
    }"
    :export-config="{
      objectLabel: 'pharmaceutical-products',
      dataUrl: 'concepts/pharmaceutical-products',
    }"
    @filter="fetchItems"
  >
    <template #actions="">
      <v-btn
        size="small"
        color="nnBaseBlue"
        :title="$t('PharmaceuticalProductForm.add_title')"
        :disabled="!accessGuard.checkPermission($roles.LIBRARY_WRITE)"
        icon="mdi-plus"
        variant="outlined"
        @click.stop="showForm = true"
      />
    </template>
    <template #[`item.derived_name`]="{ item }">
      <router-link
        :to="{
          name: 'PharmaceuticalProductOverview',
          params: { id: item.uid },
        }"
      >
        {{ item.derived_name }}
      </router-link>
    </template>
    <template #[`item.actions`]="{ item }">
      <ActionsMenu :actions="actions" :item="item" />
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
    v-model="showForm"
    fullscreen
    persistent
    content-class="fullscreen-dialog"
  >
    <PharmaceuticalProductForm
      :pharmaceutical-product-uid="selectedItem ? selectedItem.uid : null"
      :open="showForm"
      @close="closeForm"
      @created="fetchItems"
      @updated="fetchItems"
    />
  </v-dialog>
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
import { computed, inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAccessGuard } from '@/composables/accessGuard'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import NNTable from '@/components/tools/NNTable.vue'
import PharmaceuticalProductForm from '@/components/library/PharmaceuticalProductForm.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import api from '@/api/concepts/pharmaceuticalProducts'
import filteringParameters from '@/utils/filteringParameters'

const props = defineProps({
  tabClickedAt: {
    type: Number,
    default: null,
  },
})

const { t } = useI18n()
const accessGuard = useAccessGuard()
const notificationHub = inject('notificationHub')
const roles = inject('roles')

const products = ref([])
const total = ref(0)
const historyItems = ref([])
const showHistory = ref(false)
const showForm = ref(false)
const selectedItem = ref(null)
const confirm = ref()
const savedFilters = ref()

const actions = [
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'edit'),
    accessRole: roles.LIBRARY_WRITE,
    click: editItem,
  },
  {
    label: t('_global.approve'),
    icon: 'mdi-check-decagram',
    iconColor: 'success',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'approve'),
    accessRole: roles.LIBRARY_WRITE,
    click: approveItem,
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
    click: inactivateItem,
  },
  {
    label: t('_global.reactivate'),
    icon: 'mdi-undo-variant',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'reactivate'),
    accessRole: roles.LIBRARY_WRITE,
    click: reactivateItem,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'delete'),
    accessRole: roles.LIBRARY_WRITE,
    click: deleteItem,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openHistory,
  },
]
const headers = [
  { title: '', key: 'actions', width: '5%' },
  {
    title: t('PharmaceuticalProduct.title'),
    key: 'derived_name',
    noFilter: true,
  },
  {
    title: t('PharmaceuticalProduct.dosage_form'),
    key: 'dosage_form',
    noFilter: true,
  },
  {
    title: t('PharmaceuticalProduct.route_of_administration'),
    key: 'route_of_administration',
    noFilter: true,
  },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.version'), key: 'version' },
  { title: t('_global.status'), key: 'status' },
]

const historyTitle = computed(() => {
  if (selectedItem.value) {
    return t('PharmaceuticalProductTable.history_title', {
      product: selectedItem.value.uid,
    })
  }
  return ''
})

watch(
  () => props.tabClickedAt,
  () => {
    fetchItems()
  }
)

function closeForm() {
  showForm.value = false
  selectedItem.value = null
}

function fetchItems(filters, options, filtersUpdated) {
  if (filters !== undefined) {
    savedFilters.value = filters
  }
  const params = filteringParameters.prepareParameters(
    options,
    savedFilters.value,
    filtersUpdated
  )
  api.getFiltered(params).then((resp) => {
    products.value = transformItems(resp.data.items)
    total.value = resp.data.total
  })
}

function editItem(item) {
  selectedItem.value = item
  showForm.value = true
}

function approveItem(item) {
  api.approve(item.uid).then(() => {
    fetchItems()
    notificationHub.add({
      msg: t('PharmaceuticalProductTable.approve_success'),
      type: 'success',
    })
  })
}

async function deleteItem(item) {
  const options = { type: 'warning' }
  if (
    await confirm.value.open(
      t('PharmaceuticalProductTable.confirm_delete'),
      options
    )
  ) {
    await api.deleteObject(item.uid)
    fetchItems()
    notificationHub.add({
      msg: t('PharmaceuticalProductTable.delete_success'),
      type: 'success',
    })
  }
}

function createNewVersion(item) {
  api.newVersion(item.uid).then(() => {
    fetchItems()
    notificationHub.add({
      msg: t('PharmaceuticalProductTable.new_version_success'),
      type: 'success',
    })
  })
}

function inactivateItem(item) {
  api.inactivate(item.uid).then(() => {
    fetchItems()
    notificationHub.add({
      msg: t('PharmaceuticalProductTable.inactivate_success'),
      type: 'success',
    })
  })
}

function reactivateItem(item) {
  api.reactivate(item.uid).then(() => {
    fetchItems()
    notificationHub.add({
      msg: t('PharmaceuticalProductTable.reactivate_success'),
      type: 'success',
    })
  })
}

async function openHistory(item) {
  selectedItem.value = item
  const resp = await api.getVersions(selectedItem.value.uid)
  historyItems.value = transformItems(resp.data)
  showHistory.value = true
}

function transformItems(items) {
  const result = []
  for (const item of items) {
    const newItem = { ...item }
    if (item.dosage_forms.length) {
      newItem.dosage_form = item.dosage_forms[0].term_name
    }
    if (item.routes_of_administration.length) {
      newItem.route_of_administration =
        item.routes_of_administration[0].term_name
    }
    result.push(newItem)
  }
  return result
}

async function fetchGlobalAuditTrail(options) {
  const resp = await api.getAllVersions(options)
  return transformItems(resp.data.items)
}
</script>
