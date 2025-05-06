<template>
  <NNTable
    ref="table"
    key="endpointTable1"
    :headers="headers"
    :items="formatedStudyEndpoints"
    item-value="study_endpoint_uid"
    :column-data-resource="
      !sortMode
        ? `studies/${studiesGeneralStore.selectedStudy.uid}/study-endpoints`
        : undefined
    "
    :export-data-url="exportDataUrl"
    export-object-label="StudyEndpoints"
    :items-length="studiesEndpointsStore.total"
    :history-data-fetcher="fetchEndpointsHistory"
    :history-title="$t('StudyEndpointsTable.global_history_title')"
    :history-html-fields="historyHtmlFields"
    :loading="loading"
    :disable-filtering="sortMode"
    :hide-default-body="sortMode && formatedStudyEndpoints.length > 0"
    @filter="fetchEndpoints"
  >
    <template #afterSwitches>
      <div :title="$t('NNTableTooltips.reorder_content')">
        <v-switch
          v-model="sortMode"
          :label="$t('NNTable.reorder_content')"
          hide-details
          class="mr-6"
          color="primary"
          :disabled="!accessGuard.checkPermission($roles.STUDY_WRITE)"
        />
      </div>
    </template>
    <template #tbody>
      <tbody v-show="sortMode" ref="parent">
        <tr
          v-for="endpoint in formatedStudyEndpoints"
          :key="endpoint.study_endpoint_uid"
        >
          <td>
            <v-icon size="small"> mdi-sort </v-icon>
          </td>
          <td>{{ endpoint.order }}</td>
          <td><CTTermDisplay :term="endpoint.endpoint_level" /></td>
          <td><CTTermDisplay :term="endpoint.endpoint_sublevel" /></td>
          <td>
            <NNParameterHighlighter
              v-if="endpoint.endpoint"
              :name="endpoint.endpoint.name"
              :show-prefix-and-postfix="false"
            />
            <NNParameterHighlighter
              v-else
              :name="endpoint.template.name"
              :show-prefix-and-postfix="false"
            />
          </td>
          <td>{{ endpoint.units }}</td>
          <td>
            <NNParameterHighlighter
              v-if="endpoint.timeframe"
              :name="endpoint.timeframe.name"
              :show-prefix-and-postfix="false"
            />
            <span v-else>{{ $t('StudyEndpointForm.select_later') }}</span>
          </td>
          <td>
            <NNParameterHighlighter
              v-if="endpoint.study_objective"
              :name="endpoint.study_objective.objective.name"
              :show-prefix-and-postfix="false"
            />
            <span v-else>{{ $t('StudyEndpointForm.select_later') }}</span>
          </td>
          <td>{{ $filters.date(endpoint.start_date) }}</td>
          <td>{{ endpoint.author_username }}</td>
        </tr>
      </tbody>
    </template>
    <template #actions="">
      <slot name="extraActions" />
      <v-btn
        class="ml-2"
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        :title="$t('StudyEndpointsTable.add_endpoint')"
        :disabled="
          !accessGuard.checkPermission($roles.STUDY_WRITE) ||
          studiesGeneralStore.selectedStudyVersion !== null
        "
        icon="mdi-plus"
        @click.stop="showForm = true"
      />
    </template>
    <template #[`item.endpoint_level.sponsor_preferred_name`]="{ item }">
      <CTTermDisplay :term="item.endpoint_level" />
    </template>
    <template #[`item.endpoint_sublevel.sponsor_preferred_name`]="{ item }">
      <CTTermDisplay :term="item.endpoint_sublevel" />
    </template>
    <template #[`item.actions`]="{ item }">
      <ActionsMenu
        :actions="actions"
        :item="item"
        :badge="actionsMenuBadge(item)"
      />
    </template>
    <template #[`item.start_date`]="{ item }">
      {{ $filters.date(item.start_date) }}
    </template>
    <template #[`item.endpoint.name`]="{ item }">
      <div class="d-flex">
        <NNParameterHighlighter
          v-if="item.endpoint"
          :name="item.endpoint.name"
          :show-prefix-and-postfix="false"
        />
        <NNParameterHighlighter
          v-else
          :name="item.template.name"
          :show-prefix-and-postfix="false"
        />
        <v-tooltip
          v-if="item.endpoint && item.endpoint.name.length > 254"
          location="bottom"
        >
          <template #activator="{ props }">
            <v-icon
              class="mb-2 ml-1"
              v-bind="props"
              color="red"
              icon="mdi-alert-circle-outline"
            />
          </template>
          <span>{{ $t('StudyEndpointForm.endpoint_title_warning') }}</span>
        </v-tooltip>
      </div>
    </template>
    <template #[`item.study_objective.objective.name`]="{ item }">
      <NNParameterHighlighter
        v-if="item.study_objective"
        :name="item.study_objective.objective.name"
        :show-prefix-and-postfix="false"
      />
      <span v-else>{{ $t('StudyEndpointForm.select_later') }}</span>
    </template>
    <template #[`item.timeframe.name`]="{ item }">
      <NNParameterHighlighter
        v-if="item.timeframe"
        :name="item.timeframe.name"
        :show-prefix-and-postfix="false"
      />
      <span v-else>{{ $t('StudyEndpointForm.select_later') }}</span>
    </template>
  </NNTable>
  <v-dialog
    v-model="showForm"
    persistent
    fullscreen
    content-class="fullscreen-dialog"
  >
    <EndpointForm
      :study-endpoint="selectedStudyEndpoint"
      :current-study-endpoints="studiesEndpointsStore.studyEndpoints"
      class="fullscreen-dialog"
      @close="closeForm"
    />
  </v-dialog>
  <EndpointEditForm
    :open="showEditForm"
    :study-endpoint="selectedStudyEndpoint"
    @close="closeEditForm"
  />
  <v-dialog
    v-model="showHistory"
    persistent
    :fullscreen="$globals.historyDialogFullscreen"
    @keydown.esc="closeHistory"
  >
    <HistoryTable
      :title="studyEndpointHistoryTitle"
      :headers="headers"
      :items="endpointHistoryItems"
      :items-total="endpointHistoryItems.length"
      :html-fields="historyHtmlFields"
      @close="closeHistory"
    />
  </v-dialog>
  <ConfirmDialog ref="confirm" width="600" />
  <v-snackbar v-model="snackbar" color="error" location="top">
    <v-icon class="mr-2"> mdi-alert </v-icon>
    {{ $t('StudyEndpointsTable.sort_help_msg') }}
  </v-snackbar>
</template>

<script setup>
import study from '@/api/study'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import CTTermDisplay from '@/components/tools/CTTermDisplay.vue'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter.vue'
import EndpointEditForm from '@/components/studies/EndpointEditForm.vue'
import EndpointForm from '@/components/studies/EndpointForm.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import statuses from '@/constants/statuses'
import NNTable from '@/components/tools/NNTable.vue'
import filteringParameters from '@/utils/filteringParameters'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudiesEndpointsStore } from '@/stores/studies-endpoints'
import { computed, onMounted, inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDragAndDrop } from '@formkit/drag-and-drop/vue'

const { t } = useI18n()
const eventBusEmit = inject('eventBusEmit')
const roles = inject('roles')
const studiesGeneralStore = useStudiesGeneralStore()
const studiesEndpointsStore = useStudiesEndpointsStore()
const accessGuard = useAccessGuard()
const table = ref()
const confirm = ref()

const [parent, formatedStudyEndpoints] = useDragAndDrop([], {
  onDragend: (event) => {
    const newOrder =
      event.draggedNode.data.value.order -
      (event.state.initialIndex - event.state.targetIndex)
    changeOrder(event.draggedNode.data.value.study_endpoint_uid, newOrder)
  },
})

const abortConfirm = ref(false)
const actions = [
  {
    label: t('StudyEndpointsTable.update_timeframe_version_retired'),
    icon: 'mdi-alert-outline',
    iconColor: 'orange',
    condition: isTimeframeRetired || !studiesGeneralStore.selectedStudyVersion,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('StudyEndpointsTable.update_timeframe_version'),
    icon: 'mdi-bell-ring-outline',
    iconColorFunc: itemUpdateAborted,
    condition:
      timeframeNeedsUpdate || !studiesGeneralStore.selectedStudyVersion,
    click: updateTimeframeVersion,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('StudyEndpointsTable.update_endpoint_version_retired'),
    icon: 'mdi-alert-outline',
    iconColor: 'orange',
    condition: isEndpointRetired || !studiesGeneralStore.selectedStudyVersion,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('StudyEndpointsTable.update_endpoint_version'),
    icon: 'mdi-bell-ring-outline',
    iconColorFunc: itemUpdateAborted,
    condition: endpointNeedsUpdate || !studiesGeneralStore.selectedStudyVersion,
    click: updateEndpointVersion,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    click: editStudyEndpoint,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    click: deleteEndpoint,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openEndpointHistory,
  },
]
const endpointHistoryItems = ref([])
const headers = [
  { title: '', key: 'actions', width: '1%' },
  {
    title: t('StudyEndpointsTable.order'),
    key: 'order',
    width: '5%',
  },
  {
    title: t('StudyEndpointsTable.endpoint_level'),
    key: 'endpoint_level.sponsor_preferred_name',
  },
  {
    title: t('StudyEndpointsTable.endpoint_sub_level'),
    key: 'endpoint_sublevel.sponsor_preferred_name',
  },
  {
    title: t('StudyEndpointsTable.endpoint_title'),
    key: 'endpoint.name',
    width: '25%',
  },
  {
    title: t('StudyEndpointsTable.units'),
    key: 'units',
    width: '10%',
  },
  {
    title: t('StudyEndpointsTable.time_frame'),
    key: 'timeframe.name',
    width: '25%',
  },
  {
    title: t('StudyEndpointsTable.objective'),
    key: 'study_objective.objective.name',
    filteringName: 'study_objective.objective.name',
    width: '25%',
  },
  { title: t('_global.modified'), key: 'start_date', width: '10%' },
  {
    title: t('_global.modified_by'),
    key: 'author_username',
    width: '10%',
  },
]
const historyHtmlFields = [
  'endpoint.name',
  'timeframe.name',
  'study_objective.objective.name',
]
const selectedStudyEndpoint = ref(null)
const showEditForm = ref(false)
const showForm = ref(false)
const showHistory = ref(false)
const snackbar = ref(false)
const loading = ref(false)
const sortMode = ref(false)

const exportDataUrl = computed(() => {
  return `studies/${studiesGeneralStore.selectedStudy.uid}/study-endpoints`
})
const studyEndpointHistoryTitle = computed(() => {
  if (selectedStudyEndpoint.value) {
    return t('StudyEndpointsTable.study_endpoint_history_title', {
      studyEndpointUid: selectedStudyEndpoint.value.study_endpoint_uid,
    })
  }
  return ''
})

onMounted(() => {
  studiesGeneralStore.fetchAllUnits()
  studiesGeneralStore.fetchEndpointLevels()
  studiesGeneralStore.fetchEndpointSubLevels()
})

function fetchEndpoints(filters, options, filtersUpdated) {
  loading.value = true
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  params.studyUid = studiesGeneralStore.selectedStudy.uid
  studiesEndpointsStore.fetchStudyEndpoints(params).then((resp) => {
    formatedStudyEndpoints.value = transformItems(resp.data.items)
    loading.value = false
  })
}

async function fetchEndpointsHistory() {
  const resp = await study.getStudyEndpointsAuditTrail(
    studiesGeneralStore.selectedStudy.uid
  )
  return transformItems(resp.data)
}

function actionsMenuBadge(item) {
  if (endpointNeedsUpdate(item) || timeframeNeedsUpdate(item)) {
    return {
      color: 'error',
      icon: 'mdi-bell-outline',
    }
  }
  if (!item.endpoint && item.template && item.template.parameters.length > 0) {
    return {
      color: 'error',
      icon: 'mdi-exclamation',
    }
  }
  return null
}

function timeframeNeedsUpdate(item) {
  if (item.latest_timeframe) {
    if (!isTimeframeRetired(item)) {
      return item.timeframe.version !== item.latest_timeframe.version
    }
  }
  return false
}

function isTimeframeRetired(item) {
  if (item.latest_timeframe) {
    return item.latest_timeframe.status === statuses.RETIRED
  }
  return false
}

async function updateTimeframeVersion(item) {
  const options = {
    type: 'warning',
    width: 1000,
    cancelLabel: t('StudyObjectivesTable.keep_old_version'),
    agreeLabel: t('StudyObjectivesTable.use_new_version'),
  }
  const message =
    t('StudyEndpointsTable.update_timeframe_version_alert') +
    ' ' +
    t('StudyEndpointsTable.previous_version') +
    ' ' +
    item.timeframe.name_plain +
    ' ' +
    t('StudyEndpointsTable.new_version') +
    ' ' +
    item.latest_timeframe.name_plain

  if (await confirm.value.open(message, options)) {
    const args = {
      studyUid: item.study_uid,
      studyEndpointUid: item.study_endpoint_uid,
    }
    studiesEndpointsStore
      .updateStudyEndpointTimeframeLatestVersion(args)
      .then(() => {
        eventBusEmit('notification', {
          msg: t('StudyObjectivesTable.update_version_successful'),
        })
      })
  } else {
    abortConfirm.value = true
    const args = {
      studyUid: item.study_uid,
      studyEndpointUid: item.study_endpoint_uid,
    }
    studiesEndpointsStore.updateStudyEndpointAcceptVersion(args)
  }
}

function endpointNeedsUpdate(item) {
  if (item.latest_endpoint) {
    if (!isEndpointRetired(item)) {
      return item.endpoint.version !== item.latest_endpoint.version
    }
  }
  return false
}

function isEndpointRetired(item) {
  if (item.latest_endpoint) {
    return item.latest_endpoint.status === statuses.RETIRED
  }
  return false
}

function itemUpdateAborted(item) {
  return item.acceptedVersion ? '' : 'error'
}

async function updateEndpointVersion(item) {
  const options = {
    type: 'warning',
    width: 1200,
    cancelLabel: t('StudyObjectivesTable.keep_old_version'),
    agreeLabel: t('StudyObjectivesTable.use_new_version'),
  }
  const message =
    t('StudyEndpointsTable.update_endpoint_version_alert') +
    ' ' +
    t('StudyEndpointsTable.previous_version') +
    ' ' +
    item.endpoint.name_plain +
    ' ' +
    t('StudyEndpointsTable.new_version') +
    ' ' +
    item.latest_endpoint.name_plain

  if (await confirm.value.open(message, options)) {
    const args = {
      studyUid: item.study_uid,
      studyEndpointUid: item.study_endpoint_uid,
    }
    studiesEndpointsStore
      .updateStudyEndpointEndpointLatestVersion(args)
      .then(() => {
        eventBusEmit('notification', {
          msg: t('StudyEndpointsTable.update_version_successful'),
        })
      })
  } else {
    abortConfirm.value = true
    const args = {
      studyUid: item.study_uid,
      studyEndpointUid: item.study_endpoint_uid,
    }
    await studiesEndpointsStore.updateStudyEndpointAcceptVersion(args)
  }
}

function closeForm() {
  showForm.value = false
  selectedStudyEndpoint.value = null
  table.value.filterTable()
}

function closeEditForm() {
  showEditForm.value = false
  selectedStudyEndpoint.value = null
  table.value.filterTable()
}

function editStudyEndpoint(studyEndpoint) {
  selectedStudyEndpoint.value = studyEndpoint
  showEditForm.value = true
}

function displayUnits(units) {
  const unitNames = units.units.map((unit) => unit.name)
  if (unitNames.length > 1) {
    return unitNames.join(` ${units.separator} `)
  }
  return unitNames[0]
}

async function deleteEndpoint(studyEndpoint) {
  const options = { type: 'warning' }
  const endpoint = studyEndpoint.endpoint
    ? studyEndpoint.endpoint.name_plain
    : '(unnamed)'

  if (
    await confirm.value.open(
      t('StudyEndpointsTable.confirm_delete', { endpoint }),
      options
    )
  ) {
    // Make sure to set current studyObjective so the list of
    // endpoints is updated after deletion
    studiesEndpointsStore
      .deleteStudyEndpoint({
        studyUid: studiesGeneralStore.selectedStudy.uid,
        studyEndpointUid: studyEndpoint.study_endpoint_uid,
      })
      .then(() => {
        eventBusEmit('notification', {
          msg: t('StudyEndpointsTable.delete_success'),
        })
        table.value.filterTable()
      })
  }
}

function closeHistory() {
  selectedStudyEndpoint.value = null
  showHistory.value = false
}

async function openEndpointHistory(studyEndpoint) {
  selectedStudyEndpoint.value = studyEndpoint
  const resp = await study.getStudyEndpointAuditTrail(
    studiesGeneralStore.selectedStudy.uid,
    studyEndpoint.study_endpoint_uid
  )
  endpointHistoryItems.value = transformItems(resp.data)
  showHistory.value = true
}

function changeOrder(endpointUid, newOrder) {
  study
    .updateStudyEndpointOrder(
      studiesGeneralStore.selectedStudy.uid,
      endpointUid,
      newOrder
    )
    .then(() => {
      table.value.filterTable()
    })
    .catch(() => {
      table.value.filterTable()
    })
}

function transformItems(items) {
  const result = []
  for (const item of items) {
    const newItem = { ...item }
    if (item.endpoint_units && item.endpoint_units.units) {
      newItem.units = displayUnits(item.endpoint_units)
    }
    result.push(newItem)
  }
  return result
}
</script>
<style scoped>
.roundChip {
  width: 25px;
  justify-content: space-evenly;
}
tbody tr td {
  border-left-style: outset;
  border-bottom-style: outset;
  border-width: 1px !important;
  border-color: rgb(var(--v-theme-nnFadedBlue200)) !important;
}
</style>
