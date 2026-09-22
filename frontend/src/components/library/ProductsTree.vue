<template>
  <div class="pa-4 pb-0 bg-white d-flex align-center" style="overflow-x: auto">
    <v-text-field
      v-model="search"
      clearable
      clear-icon="mdi-close"
      prepend-inner-icon="mdi-magnify"
      :label="$t('_global.search')"
      single-line
      color="nnBaseBlue"
      hide-details
      style="min-width: 240px; max-width: 300px"
      class="searchFieldLabel ml-0"
      data-cy="search-field"
      @update:model-value="delayedFetchItems()"
    />
    <v-spacer />
    <v-btn
      size="small"
      color="nnBaseBlue"
      class="ml-2"
      :title="$t('MedicinalProductForm.add_title')"
      :disabled="!accessGuard.checkPermission($roles.LIBRARY_WRITE)"
      icon="mdi-plus"
      variant="outlined"
      @click.stop="showForm = true"
    />
    <v-btn
      size="small"
      variant="outlined"
      color="nnBaseBlue"
      class="ml-2"
      :title="$t('NNTableTooltips.filters')"
      data-cy="filters-button"
      :active="showFilterBar"
      icon="mdi-filter-outline"
      @click="enableFiltering"
    />
    <DataTableExportButton
      class="ml-2"
      object-label="medicinal-products"
      data-url="concepts/medicinal-products"
      :headers="headers"
      filters="{}"
      data-cy="export-data-button"
      @export="confirmExport"
    />
    <v-btn
      class="ml-2"
      size="small"
      variant="outlined"
      color="nnBaseBlue"
      :title="$t('NNTableTooltips.history')"
      icon="mdi-history"
      @click="openGlobalHistory"
    />
  </div>
  <div class="pa-4 bg-white">
    <v-fade-transition>
      <v-toolbar
        v-show="showFilterBar"
        flat
        class="filteringBar py-1"
        color="nnGray200"
      >
        <slot name="afterFilter" />
        <v-slide-group show-arrows class="mb-5">
          <FilterAutocomplete
            v-for="item in filters"
            :key="item.title"
            :filters="userFilters"
            :load-filters="loadFilters"
            :clear-input="trigger"
            :item="item"
            :resource="['concepts/medicinal-products']"
            :table-items="medicinalProducts"
            @filter="fetchItems"
          />
        </v-slide-group>
        <v-spacer />
        <v-btn
          prepend-icon="mdi-close"
          color="nnWhite"
          variant="flat"
          class="mr-3 mb-5 clearAllBtn"
          rounded
          :text="$t('NNTableTooltips.clear_filters_content')"
          @click="clearFilters()"
        />
      </v-toolbar>
    </v-fade-transition>
    <v-progress-linear
      v-if="loading"
      class="mt-2"
      color="primary"
      indeterminate
    />
    <MedicinalProductOverview
      v-for="product in medicinalProducts"
      :key="product.uid"
      :product="product"
      class="my-4"
    >
      <template #prepend>
        <ActionsMenu :actions="actions" :item="product" />
      </template>
    </MedicinalProductOverview>

    <v-divider />

    <TableLikePagination
      v-model:page-number="currentPageNumber"
      v-model:items-per-page="itemsPerPage"
      :total="totalProducts"
      :current-page="medicinalProducts"
      @update:page-number="fetchItems()"
      @update:items-per-page="fetchItems()"
    />
  </div>
  <v-dialog
    v-model="showForm"
    fullscreen
    persistent
    content-class="fullscreen-dialog"
  >
    <MedicinalProductForm
      :medicinal-product-uid="selectedItem ? selectedItem.uid : null"
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
      :headers="historyHeaders"
      :items="historyItems"
      :items-total="historyItems.length"
      change-field="change_description"
      @close="showHistory = false"
    />
  </v-dialog>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAccessGuard } from '@/composables/accessGuard'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import FilterAutocomplete from '@/components/tools/FilterAutocomplete.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import MedicinalProductForm from '@/components/library/MedicinalProductForm.vue'
import MedicinalProductOverview from '@/components/library/MedicinalProductOverview.vue'
import TableLikePagination from '@/components/tools/TableLikePagination.vue'
import medicinalProductsApi from '@/api/concepts/medicinalProducts'
import dataFormating from '@/utils/dataFormating'
import filteringParameters from '@/utils/filteringParameters'
import _debounce from 'lodash/debounce'
import DataTableExportButton from '@/components/tools/DataTableExportButton.vue'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const roles = inject('roles')
const props = defineProps({
  tabClickedAt: {
    type: Number,
    default: null,
  },
})
const accessGuard = useAccessGuard()
const loading = ref(false)
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
  { title: t('_global.name'), key: 'name' },
  { title: t('MedicinalProduct.compound'), key: 'compound.name' },
  { title: t('MedicinalProduct.dose'), key: 'dose_values_label' },
  { title: t('MedicinalProduct.frequency'), key: 'dose_frequencies_label' },
  { title: t('MedicinalProduct.delivery_device'), key: 'delivery_device.name' },
  { title: t('MedicinalProduct.dispenser'), key: 'dispenser.name' },
  { title: t('_global.version'), key: 'version' },
  { title: t('_global.status'), key: 'status' },
]

const filters = [
  { title: t('MedicinalProduct.compound'), key: 'compound.name' },
  { title: t('_global.name'), key: 'name' },
  // { title: t('MedicinalProduct.dose'), key: 'dose_values' }, // Fix this!
  { title: t('MedicinalProduct.frequency'), key: 'dose_frequencies.name' },
  { title: t('MedicinalProduct.delivery_device'), key: 'delivery_device.name' },
  { title: t('MedicinalProduct.dispenser'), key: 'dispenser.name' },
  { title: t('_global.status'), key: 'status' },
  { title: t('_global.version'), key: 'version' },
]

const medicinalProducts = ref([])
const totalProducts = ref(0)

const historyItems = ref([])
const selectedItem = ref(null)
const showForm = ref(false)
const showHistory = ref(false)
const confirm = ref()
const search = ref('')
const showFilterBar = ref(false)
const trigger = ref(0)
const loadFilters = ref(false)
const itemsPerPage = ref(10)
const currentPageNumber = ref(1)
let userFilters = '{}'

const historyTitle = computed(() => {
  if (selectedItem.value) {
    return t('ProductsTree.history_title', { product: selectedItem.value.uid })
  }
  return t('_global.audit_trail')
})

const historyHeaders = computed(() => {
  if (selectedItem.value) {
    return headers
  }
  const result = [...headers]
  result.unshift({
    title: t('_global.uid'),
    key: 'uid',
  })
  return result
})

watch(
  () => props.tabClickedAt,
  () => {
    fetchItems()
  }
)

onMounted(() => {
  fetchItems()
})

function fetchItems(inputParams) {
  loading.value = true
  const params = filteringParameters.prepareParameters()
  const filters = JSON.parse(userFilters)

  if (inputParams) {
    if (inputParams.data.length) {
      filters[inputParams.column] = { v: inputParams.data }
    } else if (filters[inputParams.column]) {
      delete filters[inputParams.column]
    }
  }
  params.filters = filters
  userFilters = JSON.stringify(filters)
  if (search.value) {
    params.filters['*'] = { v: [search.value] }
  }
  params.page_number = currentPageNumber.value
  params.page_size = itemsPerPage.value
  medicinalProductsApi.getFiltered(params).then((resp) => {
    medicinalProducts.value = resp.data.items
    totalProducts.value = resp.data.total
    loading.value = false
  })
}

const delayedFetchItems = _debounce(fetchItems, 300)

function enableFiltering() {
  showFilterBar.value = !showFilterBar.value
  loadFilters.value = true
}

function clearFilters() {
  userFilters = '{}'
  search.value = null
  trigger.value += 1
}

function closeForm() {
  showForm.value = false
  selectedItem.value = null
}

function editItem(item) {
  selectedItem.value = item
  showForm.value = true
}

function approveItem(item) {
  medicinalProductsApi.approve(item.uid).then(() => {
    fetchItems()
    notificationHub.add({
      msg: t('ProductsTree.approve_success'),
      type: 'success',
    })
  })
}

async function deleteItem(item) {
  const options = { type: 'warning' }
  const product = item.name
  if (
    await confirm.value.open(
      t('ProductsTree.confirm_delete', { product }),
      options
    )
  ) {
    await medicinalProductsApi.deleteObject(item.uid)
    fetchItems()
    notificationHub.add({
      msg: t('ProductsTree.delete_success'),
      type: 'success',
    })
  }
}

function createNewVersion(item) {
  medicinalProductsApi.newVersion(item.uid).then(() => {
    fetchItems()
    notificationHub.add({
      msg: t('ProductsTree.new_version_success'),
      type: 'success',
    })
  })
}

function inactivateItem(item) {
  medicinalProductsApi.inactivate(item.uid).then(() => {
    fetchItems()
    notificationHub.add({
      msg: t('ProductsTree.inactivate_success'),
      type: 'success',
    })
  })
}

function reactivateItem(item) {
  medicinalProductsApi.reactivate(item.uid).then(() => {
    fetchItems()
    notificationHub.add({
      msg: t('ProductsTree.reactivate_success'),
      type: 'success',
    })
  })
}

async function openHistory(item) {
  selectedItem.value = item
  const resp = await medicinalProductsApi.getVersions(selectedItem.value.uid)
  resp.data.map((product) => {
    product.dose_values_label = getDoseLabel(product.dose_values)
    product.dose_frequencies_label = getFrequencyLabel(product.dose_frequencies)
    return product
  })
  historyItems.value = resp.data
  showHistory.value = true
}

async function openGlobalHistory() {
  const resp = await medicinalProductsApi.getAllVersions({ page_size: 0 })
  resp.data.items.map((product) => {
    product.dose_values_label = getDoseLabel(product.dose_values)
    product.dose_frequencies_label = getFrequencyLabel(product.dose_frequencies)
    return product
  })
  historyItems.value = resp.data.items
  showHistory.value = true
}

function getDoseLabel(dose_values) {
  const result = dose_values
    .map((dose) => `${dose.value} ${dose.unit_label}`)
    .join(', ')
  return result || '-'
}

function getFrequencyLabel(dose_frequencies) {
  return dataFormating.names(dose_frequencies || []) || '-'
}

async function confirmExport(resolve) {
  resolve(true)
}
</script>

<style scoped>
.filteringBar {
  height: 50px;
  border-radius: 4px;
}
</style>
