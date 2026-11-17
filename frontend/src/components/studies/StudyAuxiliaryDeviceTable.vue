<template>
  <div>
    <NNTable
      ref="table"
      table-id="studies-auxiliary-devices-table"
      :headers="headers"
      :default-headers="defaultHeaders"
      :items="auxiliaryDevices"
      item-value="uid"
      fixed-header
      :items-length="total"
      :column-data-resource="exportDataUrl"
      hide-default-switches
      table-height="auto"
      :hide-default-body="sortMode && auxiliaryDevices.length > 0"
      :history-config="{
        dataFetcher: fetchAuxiliaryDevicesHistory,
        title: $t('StudyAuxiliaryDeviceTable.global_history_title'),
      }"
      :export-config="{
        objectLabel: 'AuxiliaryDevices',
        dataUrl: exportDataUrl,
      }"
      @filter="fetchAuxiliaryDevices"
    >
      <template #afterSwitches>
        <div
          :title="
            reorderBlocked
              ? $t('StudyAuxiliaryDeviceTable.reorder_blocked')
              : $t('NNTableTooltips.reorder_content')
          "
          class="ml-4"
        >
          <v-switch
            v-model="sortMode"
            :label="$t('NNTable.reorder_content')"
            hide-details
            class="mr-6"
            :disabled="
              !accessGuard.checkPermission($roles.STUDY_WRITE) ||
              studiesGeneralStore.selectedStudyVersion !== null ||
              reorderBlocked
            "
          />
        </div>
      </template>
      <template #tbody>
        <tbody v-show="sortMode" ref="parent">
          <tr v-for="device in auxiliaryDevices" :key="device.uid">
            <!-- follow the visible columns so the column picker can't misalign cells -->
            <td v-for="col in sortModeColumns" :key="col.key">
              <v-icon v-if="col.key === 'actions'" size="small">
                mdi-sort
              </v-icon>
              <template v-else-if="col.key === 'start_date'">
                {{ $filters.dateRelative(device.start_date) }}
              </template>
              <template v-else>{{ device[col.key] }}</template>
            </td>
          </tr>
        </tbody>
      </template>
      <template #actions="">
        <v-btn
          data-cy="create-auxiliary-device"
          class="ml-2"
          icon
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          :disabled="
            !accessGuard.checkPermission($roles.STUDY_WRITE) ||
            studiesGeneralStore.selectedStudyVersion !== null
          "
          @click="createAuxiliaryDevice()"
        >
          <v-icon>mdi-plus</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('StudyAuxiliaryDeviceForm.add_title') }}
          </v-tooltip>
        </v-btn>
      </template>
      <template #[`item.actions`]="{ item }">
        <div class="pr-0 mr-0">
          <ActionsMenu :actions="actions" :item="item" />
        </div>
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
    <StudyAuxiliaryDeviceForm :open="showForm" @close="closeForm" />
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
    <v-dialog
      v-model="showHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeHistory"
    >
      <HistoryTable
        :title="auxiliaryDeviceHistoryTitle"
        :headers="headers"
        :items="historyItems"
        :items-total="historyItems.length"
        @close="closeHistory"
      />
    </v-dialog>
  </div>
</template>

<script setup>
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StudyAuxiliaryDeviceForm from './StudyAuxiliaryDeviceForm.vue'
import filteringParameters from '@/utils/filteringParameters'
import study from '@/api/study'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { computed, inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDragAndDrop } from '@formkit/drag-and-drop/vue'

const [parent, auxiliaryDevices] = useDragAndDrop([], {
  onDragend: (event) => {
    const newOrder =
      event.draggedNode.data.value.order -
      (event.state.initialIndex - event.state.targetIndex)
    changeOrder(event.draggedNode.data.value.uid, newOrder)
  },
})

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const roles = inject('roles')
const studiesGeneralStore = useStudiesGeneralStore()
const accessGuard = useAccessGuard()
const table = ref()
const confirm = ref()

// no edit action — backend has no PATCH-fields endpoint for auxiliary devices
const actions = [
  {
    label: t('StudyAuxiliaryDeviceTable.remove_device'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    click: deleteAuxiliaryDevice,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openHistory,
  },
]
const headers = [
  { title: '', key: 'actions', width: '1%' },
  { title: '#', key: 'order', width: '5%' },
  {
    title: t('StudyAuxiliaryDevice.device'),
    key: 'auxiliary_device_name',
  },
  {
    title: t('StudyAuxiliaryDevice.submission_value'),
    key: 'auxiliary_device_submission_value',
  },
  // no separate sponsor preferred name column, Device already shows it
  {
    title: t('StudyAuxiliaryDevice.nci_preferred_name'),
    key: 'auxiliary_device_nci_preferred_name',
  },
  { title: t('_global.definition'), key: 'auxiliary_device_definition' },
  {
    title: t('StudyAuxiliaryDevice.algorithm'),
    key: 'auxiliary_device_algorithm',
  },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.modified_by'), key: 'author_username' },
]
const hiddenByDefault = ['order', 'start_date', 'author_username']
const defaultHeaders = headers.filter((h) => !hiddenByDefault.includes(h.key))
// NNTable renders visible columns in headers order, selectedColumns is in pick order
const sortModeColumns = computed(() =>
  headers.filter((h) =>
    table.value?.selectedColumns.some((c) => c.key === h.key)
  )
)
const historyItems = ref([])
const selectedAuxiliaryDevice = ref(null)
const showForm = ref(false)
const showHistory = ref(false)
const total = ref(0)
const sortMode = ref(false)
const reorderBlocked = ref(false)

const exportDataUrl = computed(() => {
  return `studies/${studiesGeneralStore.selectedStudy.uid}/study-auxiliary-devices`
})
const auxiliaryDeviceHistoryTitle = computed(() => {
  if (selectedAuxiliaryDevice.value) {
    return t('StudyAuxiliaryDeviceTable.item_history_title', {
      uid: selectedAuxiliaryDevice.value.uid,
    })
  }
  return ''
})

function fetchAuxiliaryDevices(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  // drag and drop maps row positions to the study order, which only holds for
  // the unfiltered list sorted by order
  reorderBlocked.value =
    Boolean(params.filters) ||
    Boolean(
      options?.sortBy?.some((s) => s.key !== 'order' || s.order !== 'asc')
    )
  if (reorderBlocked.value) sortMode.value = false
  study
    .getStudyAuxiliaryDevices(studiesGeneralStore.selectedStudy.uid, params)
    .then((resp) => {
      auxiliaryDevices.value = resp.data.items
      total.value = resp.data.total
    })
}

async function fetchAuxiliaryDevicesHistory() {
  const resp = await study.getStudyAuxiliaryDevicesAuditTrail(
    studiesGeneralStore.selectedStudy.uid
  )
  return resp.data
}

function createAuxiliaryDevice() {
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  table.value.filterTable()
}

async function deleteAuxiliaryDevice(item) {
  const options = { type: 'warning' }
  const context = { name: item.auxiliary_device_name }
  const msg = t('StudyAuxiliaryDeviceTable.confirm_delete', context)
  if (!(await confirm.value.open(msg, options))) {
    return
  }
  study
    .deleteStudyAuxiliaryDevice(studiesGeneralStore.selectedStudy.uid, item.uid)
    .then(() => {
      notificationHub.add({
        msg: t('StudyAuxiliaryDeviceTable.delete_success'),
      })
      table.value.filterTable()
    })
}

async function openHistory(item) {
  selectedAuxiliaryDevice.value = item
  const resp = await study.getStudyAuxiliaryDeviceAuditTrail(
    studiesGeneralStore.selectedStudy.uid,
    item.uid
  )
  historyItems.value = resp.data
  showHistory.value = true
}

function closeHistory() {
  showHistory.value = false
}

function changeOrder(deviceUid, newOrder) {
  study
    .updateStudyAuxiliaryDeviceOrder(
      studiesGeneralStore.selectedStudy.uid,
      deviceUid,
      newOrder
    )
    .then(() => {
      table.value.filterTable()
    })
    .catch(() => {
      table.value.filterTable()
    })
}
</script>

<style scoped>
tbody tr td {
  border-left-style: outset;
  border-bottom-style: outset;
  border-width: 1px !important;
  border-color: rgb(var(--v-theme-nnFadedBlue200)) !important;
}

:deep(.v-data-table__th) {
  background-color: rgb(var(--v-theme-nnTableHeaderDark)) !important;
}
</style>
