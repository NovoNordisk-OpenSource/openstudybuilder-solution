<template>
  <NNTable
    ref="table"
    table-id="library-units-table"
    :headers="headers"
    :items="units"
    :items-length="total"
    item-value="uid"
    sort-desc
    column-data-resource="concepts/unit-definitions"
    :export-config="{
      objectLabel: 'Units',
      dataUrl: 'concepts/unit-definitions',
    }"
    @filter="getUnits"
  >
    <template #actions="">
      <v-btn
        class="ml-2"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        data-cy="add-unit"
        :disabled="!accessGuard.checkPermission($roles.LIBRARY_WRITE)"
        @click.stop="showForm = true"
      >
        <v-icon>mdi-plus</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ $t('UnitForm.add_title') }}
        </v-tooltip>
      </v-btn>
    </template>
    <template #[`item.master_unit`]="{ item }">
      {{ $filters.yesno(item.master_unit) }}
    </template>
    <template #[`item.display_unit`]="{ item }">
      {{ $filters.yesno(item.display_unit) }}
    </template>
    <template #[`item.unit_subsets`]="{ item }">
      {{ displayList(item.unit_subsets) }}
    </template>
    <template #[`item.ct_units`]="{ item }">
      {{ displayList(item.ct_units) }}
    </template>
    <template #[`item.convertible_unit`]="{ item }">
      {{ $filters.yesno(item.convertible_unit) }}
    </template>
    <template #[`item.si_unit`]="{ item }">
      {{ $filters.yesno(item.si_unit) }}
    </template>
    <template #[`item.us_conventional_unit`]="{ item }">
      {{ $filters.yesno(item.us_conventional_unit) }}
    </template>
    <template #[`item.use_molecular_weight`]="{ item }">
      {{ $filters.yesno(item.use_molecular_weight) }}
    </template>
    <template #[`item.use_complex_unit_conversion`]="{ item }">
      {{ $filters.yesno(item.use_complex_unit_conversion) }}
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
    <template #[`item.ucum_unit`]="{ item }">
      <v-edit-dialog v-model:return-value="item.ucum_unit">
        <span v-if="item.ucum_unit">{{ item.ucum_unit.code }}</span>
        <v-icon v-else> mdi-table-search </v-icon>
        <template #input>
          <StudybuilderUCUMField v-model="item.ucum_unit" />
        </template>
      </v-edit-dialog>
    </template>
    <template #[`item.actions`]="{ item }">
      <ActionsMenu :actions="actions" :item="item" />
    </template>
  </NNTable>
  <UnitForm :open="showForm" :unit="activeUnit" @close="close()" />
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
      :items-total="historyItems.length"
      @close="closeHistory"
    />
  </v-dialog>
</template>

<script setup>
import { computed, ref, inject } from 'vue'
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import UnitForm from '@/components/library/UnitForm.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import StudybuilderUCUMField from '@/components/tools/StudybuilderUCUMField.vue'
import unitsApi from '@/api/units'
import { useAccessGuard } from '@/composables/accessGuard'
import { useUnitsStore } from '@/stores/units'
import filteringParameters from '@/utils/filteringParameters'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import { useI18n } from 'vue-i18n'

const unitsStore = useUnitsStore()
const accessGuard = useAccessGuard()
const { t } = useI18n()
const roles = inject('roles')

const total = computed(() => {
  return unitsStore.total
})

const units = computed(() => {
  return unitsStore.units
})

const historyTitle = computed(() => {
  if (activeUnit.value) {
    return t('UnitTable.history_title', {
      name: activeUnit.value.name,
    })
  }
  return ''
})

const headers = [
  { title: '', key: 'actions', width: '1%' },
  { title: t('_global.library'), key: 'library_name' },
  { title: t('_global.name'), key: 'name' },
  { title: t('UnitTable.master_unit'), key: 'master_unit' },
  { title: t('UnitTable.display_unit'), key: 'display_unit' },
  {
    title: t('UnitTable.unit_subsets'),
    key: 'unit_subsets',
    filteringName: 'unit_subsets.name',
  },
  { title: t('UnitTable.ucum_unit'), key: 'ucum.name' },
  {
    title: t('UnitTable.ct_units'),
    key: 'ct_units',
    filteringName: 'ct_units.name',
    width: '10%',
  },
  {
    title: t('UnitTable.convertible_unit'),
    key: 'convertible_unit',
  },
  { title: t('UnitTable.si_unit'), key: 'si_unit' },
  {
    title: t('UnitTable.us_conventional_unit'),
    key: 'us_conventional_unit',
  },
  {
    title: t('UnitTable.unit_dimension'),
    key: 'unit_dimension.term_name',
    filteringName: 'unit_dimension.name',
  },
  { title: t('UnitTable.legacy_code'), key: 'legacy_code' },
  {
    title: t('UnitTable.molecular_weight'),
    key: 'use_molecular_weight',
  },
  {
    title: t('UnitTable.complex_conversion'),
    key: 'use_complex_unit_conversion',
  },
  {
    title: t('UnitTable.conversion_factor'),
    key: 'conversion_factor_to_master',
  },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.status'), key: 'status' },
  { title: t('_global.version'), key: 'version' },
]
const actions = [
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: (item) => item.status === 'Draft',
    accessRole: roles.LIBRARY_WRITE,
    click: editUnit,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: (item) =>
      item.status === 'Draft' && parseFloat(item.version) < 1,
    accessRole: roles.LIBRARY_WRITE,
    click: deleteUnit,
  },
  {
    label: t('_global.new_version'),
    icon: 'mdi-plus-circle-outline',
    iconColor: 'primary',
    condition: (item) => item.status === 'Final',
    accessRole: roles.LIBRARY_WRITE,
    click: newUnitVersion,
  },
  {
    label: t('_global.approve'),
    icon: 'mdi-check-decagram',
    iconColor: 'success',
    condition: (item) => item.status === 'Draft',
    accessRole: roles.LIBRARY_WRITE,
    click: approveUnit,
  },
  {
    label: t('_global.inactivate'),
    icon: 'mdi-close-octagon-outline',
    iconColor: 'primary',
    condition: (item) => item.status === 'Final',
    accessRole: roles.LIBRARY_WRITE,
    click: inactivateUnit,
  },
  {
    label: t('_global.reactivate'),
    icon: 'mdi-undo-variant',
    iconColor: 'primary',
    condition: (item) => item.status === 'Retired',
    accessRole: roles.LIBRARY_WRITE,
    click: reactivateUnit,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    accessRole: roles.LIBRARY_READ,
    click: openUnitHistory,
  },
]
const showForm = ref(false)
const localFilters = ref('')
const activeUnit = ref({})
const historyItems = ref([])
const showHistory = ref(false)
const table = ref()

function displayList(items) {
  return items.map((item) => item.term_name).join(', ')
}

function getUnits(filters, options, filtersUpdated) {
  if (filters) {
    localFilters.value = filters
  }
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  unitsStore.fetchUnits(params)
}

function editUnit(item) {
  activeUnit.value = item
  showForm.value = true
}

function deleteUnit(item) {
  unitsApi.delete(item.uid).then(() => {
    table.value.filterTable()
  })
}

function newUnitVersion(item) {
  unitsApi.newVersion(item.uid).then(() => {
    table.value.filterTable()
  })
}

function approveUnit(item) {
  unitsApi.approve(item.uid).then(() => {
    table.value.filterTable()
  })
}

function inactivateUnit(item) {
  unitsApi.inactivate(item.uid).then(() => {
    table.value.filterTable()
  })
}

function reactivateUnit(item) {
  unitsApi.reactivate(item.uid).then(() => {
    table.value.filterTable()
  })
}

function close() {
  showForm.value = false
  activeUnit.value = {}
  table.value.filterTable()
}

async function openUnitHistory(item) {
  activeUnit.value = item
  const resp = await unitsApi.getUnitHistory(item.uid)
  historyItems.value = transformItems(resp.data)
  showHistory.value = true
}

function transformItems(items) {
  for (const item of items) {
    item.ct_units = item.ct_units.map((set) => set.name).join(', ')
    item.unit_subsets = item.unit_subsets.map((set) => set.name).join(', ')
  }
  return items
}

function closeHistory() {
  showHistory.value = false
}
</script>
