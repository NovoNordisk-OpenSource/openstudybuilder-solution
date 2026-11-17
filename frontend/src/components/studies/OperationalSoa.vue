<template>
  <div v-resize="onResize" class="pa-4 bg-white" style="overflow-x: auto">
    <div class="d-flex align-center mb-4">
      <v-switch
        v-model="expandAllRows"
        :label="$t('DetailedFlowchart.expand_all')"
        hide-details
        class="ml-2 flex-grow-0"
        @update:model-value="toggleAllRowState"
      />
      <v-switch
        v-model="showFlowchartGroups"
        :label="$t('DetailedFlowchart.show_flowchart_groups')"
        hide-details
        class="ml-6 flex-grow-0"
        :disabled="selectedStudyVersion !== null"
      />
      <v-spacer />
      <v-menu rounded location="bottom">
        <template #activator="{ props }">
          <v-btn
            color="nnGreen1"
            icon
            size="small"
            class="ml-2 text-white"
            v-bind="props"
            :loading="soaContentLoadingStore.loading"
          >
            <v-icon>mdi-download-outline</v-icon>
            <v-tooltip activator="parent" location="top">
              {{ $t('DataTableExportButton.export') }}
            </v-tooltip>
          </v-btn>
        </template>
        <v-list>
          <v-list-item link @click="download(soaDownloads.csvDownload)">
            <v-list-item-title>CSV</v-list-item-title>
          </v-list-item>
          <v-list-item link @click="download(soaDownloads.excelDownload)">
            <v-list-item-title>EXCEL</v-list-item-title>
          </v-list-item>
          <v-list-item link @click="download(soaDownloads.docxDownload)">
            <v-list-item-title>DOCX</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </div>
    <div
      ref="tableContainer"
      class="sticky-header"
      :style="`height: ${tableHeight}px`"
    >
      <table :aria-label="$t('DetailedFlowchart.table_caption')">
        <thead>
          <tr ref="firstHeader">
            <th width="2%" rowspan="4" scope="col" />
            <th width="25%" rowspan="4" scope="col">
              {{ $t('DetailedFlowchart.activities') }}
            </th>
            <th width="10%" scope="col">
              {{ $t('DetailedFlowchart.study_epoch') }}
            </th>
            <template v-if="soaContent">
              <th
                v-for="(cell, index) in soaEpochRow"
                :key="`epoch-${index}`"
                scope="col"
              >
                {{ cell.text }}
              </th>
            </template>
            <template v-else>
              <th colspan="2" scope="col" />
            </template>
          </tr>
          <tr ref="secondHeader">
            <th :style="`top: ${firstHeaderHeight}px`" scope="col">
              {{ $t('DetailedFlowchart.visit_short_name') }}
            </th>
            <template v-if="soaContent">
              <th
                v-for="(cell, index) in soaVisitRow"
                :key="`shortName-${index}`"
                :style="`top: ${firstHeaderHeight}px`"
                scope="col"
              >
                <div class="d-flex align-center">
                  {{ cell.text }}
                </div>
              </th>
            </template>
            <template v-else>
              <th
                colspan="2"
                :style="`top: ${firstHeaderHeight}px`"
                scope="col"
              />
            </template>
          </tr>
          <tr ref="thirdHeader">
            <template v-if="soaContent">
              <th
                v-for="(cell, index) in soaDayRow"
                :key="`week-${index}`"
                :style="`top: ${thirdHeaderRowTop}px`"
                scope="col"
              >
                {{ cell.text }}
              </th>
            </template>
            <template v-else>
              <th
                colspan="2"
                :style="`top: ${thirdHeaderRowTop}px`"
                scope="col"
              />
            </template>
          </tr>
          <tr>
            <th :style="`top: ${fourthHeaderRowTop}px`" scope="col">
              {{ $t('DetailedFlowchart.visit_window') }}
            </th>
            <template v-if="soaContent">
              <th
                v-for="(cell, index) in soaWindowRow"
                :key="`window-${index}`"
                :style="`top: ${fourthHeaderRowTop}px`"
                scope="col"
              >
                {{ cell.text }}
              </th>
            </template>
            <template v-else>
              <th
                colspan="2"
                :style="`top: ${fourthHeaderRowTop}px`"
                scope="col"
              />
            </template>
          </tr>
        </thead>
        <tbody>
          <template v-for="row in soaRows" :key="`row-${row.displayUid}`">
            <tr v-if="showSoaRow(row)" :class="getSoaRowClasses(row)">
              <td>
                <v-btn
                  v-if="row.cells[0].style !== 'activityInstance'"
                  :icon="getDisplayButtonIcon(`row-${row.displayUid}`)"
                  variant="text"
                  class="expand-btn"
                  @click="toggleRowState(`row-${row.displayUid}`)"
                />
              </td>
              <td :class="getSoaFirstCellClasses(row.cells[0])">
                <div v-if="row.cells[0].style !== 'activityInstance'">
                  {{ row.cells[0].text }}
                </div>
                <a
                  v-else
                  href="#"
                  class="font-weight-regular"
                  @click.prevent="
                    redirectToActivityInstance(row.cells[0].refs[0].uid)
                  "
                >
                  {{ row.cells[0].text }}
                </a>
              </td>
              <td />
              <td
                v-for="(cell, cellIndex) in row.cells.slice(1)"
                :key="`cell-${cellIndex}`"
              >
                {{ cell.text }}
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUpdated, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import study from '@/api/study'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useSoaContentLoadingStore } from '@/stores/soa-content-loading'
import scheduleMethods from '@/utils/scheduleMethods'
import {
  applySavedExpandState,
  assignRowDisplayUids,
  buildRowsDisplayState,
} from '@/utils/soaDisplayState'
import soaDownloads from '@/utils/soaDownloads'

const props = defineProps({
  update: {
    type: Number,
    default: 0,
  },
})

// Epoch, visit, day/week and window rows precede the data rows
const HEADER_ROW_COUNT = 4

const router = useRouter()
const studiesGeneralStore = useStudiesGeneralStore()
const soaContentLoadingStore = useSoaContentLoadingStore()

const selectedStudy = computed(() => studiesGeneralStore.selectedStudy)
const selectedStudyVersion = computed(
  () => studiesGeneralStore.selectedStudyVersion
)

const tableContainer = ref(null)
const firstHeader = ref(null)
const secondHeader = ref(null)
const thirdHeader = ref(null)

const rowsDisplayState = ref({})
const tableHeight = ref(500)
const soaContent = ref(null)
const expandAllRows = ref(false)
const firstHeaderHeight = ref(0)
const secondHeaderHeight = ref(0)
const thirdHeaderHeight = ref(0)
const showFlowchartGroups = ref(false)

const soaEpochRow = computed(() =>
  soaContent.value ? soaContent.value.rows[0].cells.slice(1) : []
)
const soaVisitRow = computed(() =>
  soaContent.value ? soaContent.value.rows[1].cells.slice(1) : []
)
const soaDayRow = computed(() =>
  soaContent.value ? soaContent.value.rows[2].cells : []
)
const soaWindowRow = computed(() =>
  soaContent.value ? soaContent.value.rows[3].cells.slice(1) : []
)
// Rows without cells are dropped here so the template and helpers can rely on row.cells[0]
const soaRows = computed(() =>
  soaContent.value
    ? soaContent.value.rows
        .slice(HEADER_ROW_COUNT)
        .filter((row) => row.cells?.length)
    : []
)
const thirdHeaderRowTop = computed(
  () => firstHeaderHeight.value + secondHeaderHeight.value
)
const fourthHeaderRowTop = computed(
  () =>
    firstHeaderHeight.value + secondHeaderHeight.value + thirdHeaderHeight.value
)

watch(
  () => props.update,
  () => loadSoaContent()
)

onUpdated(() => {
  firstHeaderHeight.value = firstHeader.value.clientHeight
  secondHeaderHeight.value = secondHeader.value.clientHeight
  thirdHeaderHeight.value = thirdHeader.value.clientHeight
})

onMounted(() => {
  loadSoaContent()
})

async function redirectToActivityInstance(instanceUid) {
  const resp = await study.getStudyActivityInstance(
    selectedStudy.value.uid,
    instanceUid
  )
  router.push({
    name: 'ActivityInstanceOverview',
    params: { id: resp.data.activity_instance.uid },
  })
}

function toggleAllRowState(value) {
  for (const key in rowsDisplayState.value) {
    rowsDisplayState.value[key].value = value
  }
}

function hasParent(state) {
  return state?.parent !== undefined && state?.parent !== null
}

function hasCollapsedAncestor(displayUid) {
  let state = rowsDisplayState.value[`row-${displayUid}`]
  while (hasParent(state)) {
    const parentKey = `row-${state.parent}`
    state = rowsDisplayState.value[parentKey]
    if (!state) {
      console.warn(`Key ${parentKey} not found in rowsDisplayState`)
      return false
    }
    // Top-level soaGroup rows only collapse their children while they are shown
    const isCollapsible = showFlowchartGroups.value || hasParent(state)
    if (isCollapsible && !state.value) {
      return true
    }
  }
  return false
}

function showSoaRow(row) {
  const visible = !hasCollapsedAncestor(row.displayUid)
  switch (row.cells[0].style) {
    case 'soaGroup':
      return showFlowchartGroups.value
    case 'group':
      return !showFlowchartGroups.value || visible
    default:
      return visible
  }
}

function onResize() {
  tableHeight.value =
    window.innerHeight - tableContainer.value.getBoundingClientRect().y - 60
}

function snapshotExpandState() {
  const snapshot = {}
  for (const key in rowsDisplayState.value) {
    snapshot[key] = rowsDisplayState.value[key].value
  }
  return snapshot
}

let latestLoadRequestId = 0

async function loadSoaContent() {
  // A reload can be requested while the previous one is still running; only the latest response is applied
  const requestId = ++latestLoadRequestId
  soaContentLoadingStore.setLoading(true)
  let dataRows
  try {
    const resp = await study.getStudyProtocolFlowchart(
      selectedStudy.value.uid,
      { layout: 'operational' }
    )
    if (requestId !== latestLoadRequestId) {
      return
    }
    dataRows = resp.data.rows.slice(HEADER_ROW_COUNT)
    assignRowDisplayUids(dataRows)
    soaContent.value = resp.data
  } finally {
    if (requestId === latestLoadRequestId) {
      soaContentLoadingStore.setLoading(false)
    }
  }

  // Entries and parent links are rebuilt on every load; expansion values of rows that
  // survive the reload are carried over by display uid. The first load stays collapsed.
  const previousExpandState = Object.keys(rowsDisplayState.value).length
    ? snapshotExpandState()
    : null
  const newRowsDisplayState = buildRowsDisplayState(
    dataRows,
    scheduleMethods.isActivityRow
  )
  if (previousExpandState) {
    applySavedExpandState(newRowsDisplayState, previousExpandState)
  }
  rowsDisplayState.value = newRowsDisplayState
}

function getSoaFirstCellClasses(cell) {
  switch (cell.style) {
    case 'soaGroup':
    case 'group':
      return 'text-strong'
    case 'subGroup':
      return 'subgroup'
    case 'activity':
    case 'activityPlaceholder':
    case 'activityPlaceholderSubmitted':
      return 'activity'
    default:
      return 'activityInstance'
  }
}

function getSoaRowClasses(row) {
  switch (row.cells[0].style) {
    case 'soaGroup':
      return 'flowchart text-uppercase'
    case 'group':
      return 'group'
    case 'activityPlaceholder':
      return 'bg-warning'
    case 'activityPlaceholderSubmitted':
      return 'bg-yellow'
    default:
      return ''
  }
}

function getCurrentDisplayValue(rowKey) {
  return rowsDisplayState.value[rowKey]?.value ?? false
}

function getDisplayButtonIcon(rowKey) {
  return getCurrentDisplayValue(rowKey)
    ? 'mdi-chevron-down'
    : 'mdi-chevron-right'
}

function toggleRowState(rowKey) {
  const state = rowsDisplayState.value[rowKey]
  if (state) {
    state.value = !state.value
  }
}

async function download(downloadFn) {
  soaContentLoadingStore.setLoading(true)
  try {
    await downloadFn('operational')
  } finally {
    soaContentLoadingStore.setLoading(false)
  }
}
</script>

<style lang="scss" scoped>
table {
  width: 100%;
  text-align: left;
  border-spacing: 0px;
  border-collapse: collapse;
}
thead {
  background-color: rgb(var(--v-theme-tableGray));
  font-weight: 600;
}
tr {
  padding: 4px;
}
tbody tr {
  border-bottom: 1px solid rgb(var(--v-theme-greyBackground));
}
th {
  vertical-align: bottom;
  background-color: rgb(var(--v-theme-tableGray));
}
th,
td {
  padding: 6px;
  font-size: 14px !important;
}
.sticky-header {
  overflow-y: auto;

  thead th {
    position: sticky;
    top: 0;
    z-index: 3;
  }
}
.flowchart {
  background-color: rgb(var(--v-theme-dfltBackgroundLight1));
}
.group {
  background-color: rgb(var(--v-theme-dfltBackgroundLight2));
}
.subgroup {
  font-weight: 600;
  padding-left: 20px;
}
.activity {
  padding-left: 30px;
}
.activityInstance {
  padding-left: 40px;
  font-style: italic;
}
.text-strong {
  font-weight: 600;
}
.expand-btn {
  height: 30px;
  width: 10px;
}
</style>
