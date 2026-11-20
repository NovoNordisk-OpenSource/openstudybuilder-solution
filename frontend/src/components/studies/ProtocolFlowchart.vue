<template>
  <div class="pa-4 bg-white">
    <v-row class="mb-2">
      <v-col cols="4"> </v-col>
      <v-col cols="8" class="d-flex align-center">
        <v-spacer />
        <v-switch
          v-show="switchIsEnabled(['protocol'])"
          v-model="showSplitMenu"
          :label="$t('ProtocolFlowchart.show_split_menu')"
          data-cy="show-split-menu"
          hide-details
          class="mr-4"
          :readonly="loading || toggle.length !== 0"
          :disabled="toggle.length !== 0"
          :loading="loading ? 'warning' : null"
        />
        <v-switch
          v-show="switchIsEnabled(['protocol'])"
          v-model="studiesGeneralStore.soaPreferences.show_epochs"
          :label="$t('ProtocolFlowchart.show_epochs')"
          data-cy="show-epochs"
          hide-details
          class="mr-4"
          :readonly="loading"
          :loading="loading ? 'warning' : null"
          @update:model-value="updateSoaPreferences('show_epochs')"
        />
        <v-switch
          v-show="switchIsEnabled(['protocol'])"
          v-model="studiesGeneralStore.soaPreferences.show_milestones"
          :label="$t('ProtocolFlowchart.show_milestones')"
          data-cy="show-milestones"
          hide-details
          class="mr-4"
          :readonly="loading"
          :loading="loading ? 'warning' : null"
          @update:model-value="updateSoaPreferences('show_milestones')"
        />
        <v-switch
          v-show="switchIsEnabled(['protocol_lab_table'])"
          v-model="studiesGeneralStore.soaPreferences.show_all_visits_lab_table"
          :label="$t('ProtocolFlowchart.show_all_visits_lab_table')"
          data-cy="show-all-visits-lab-table"
          hide-details
          class="mr-4"
          :readonly="loading"
          :loading="loading ? 'warning' : null"
          @update:model-value="
            updateSoaPreferences('show_all_visits_lab_table')
          "
        />
        <ManageFootnotesButton
          v-if="supportsFootnotes"
          ref="manageFootnotes"
          :layout="layout"
          :editable="canEditStudy"
          :footnote-letters="footnoteLetters"
          @footnote-expanded="highlightFootnoteItems"
          @footnotes-changed="refreshFlowchartKeepingSelection"
          @linking-changed="onLinkingChanged"
          @scroll-to-item="scrollToItem"
        />
        <v-menu rounded location="bottom">
          <template #activator="{ props }">
            <v-btn
              class="ml-2"
              icon
              size="small"
              variant="outlined"
              color="nnBaseBlue"
              v-bind="props"
              :loading="loading"
            >
              <v-icon>mdi-download-outline</v-icon>
              <v-tooltip activator="parent" location="top">
                {{ $t('DataTableExportButton.export') }}
              </v-tooltip>
            </v-btn>
          </template>
          <v-list>
            <v-list-item link @click="downloadEXCEL">
              <v-list-item-title>EXCEL</v-list-item-title>
            </v-list-item>
            <v-list-item link @click="downloadCSV">
              <v-list-item-title>CSV</v-list-item-title>
            </v-list-item>
            <v-list-item link @click="downloadDocx">
              <v-list-item-title>DOCX</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
      </v-col>
    </v-row>
    <div v-if="layout === 'protocol' && showSplitMenu">
      <div class="text-center">
        {{ $t('ProtocolFlowchart.split_info_1') }}
      </div>
      <div class="text-center">
        {{ $t('ProtocolFlowchart.split_info_2') }}
      </div>
      <div class="d-flex flex-column align-center pa-2">
        <v-btn-toggle
          v-model="toggle"
          class="btn-toggle"
          variant="outlined"
          divided
          multiple
        >
          <v-slide-group show-arrows>
            <div
              v-for="visit in groupedVisits"
              :key="visit.uid"
              class="slide-div"
            >
              <v-btn
                selected-class="split-class"
                data-cy="split-class"
                variant="outlined"
                rounded="0"
                class="mt-2"
                height="40px"
                elevation="0"
                :value="visit.uid"
                :disabled="!switchIsEnabled(['protocol'])"
                @click="splitSoA(visit.uid)"
              >
                <template #prepend>
                  <v-icon
                    v-if="toggle.includes(visit.uid)"
                    icon="mdi-content-cut"
                    class="horizontal-flip"
                  />
                </template>
                {{ visit.group || visit.name }}
              </v-btn>

              <Transition name="slide-fade">
                <div
                  v-if="toggle.includes(visit.uid)"
                  style="text-align: center"
                >
                  <v-btn
                    variant="outlined"
                    class="mt-n2 go-to-btn"
                    data-cy="go-to-split"
                    elevation="0"
                    :loading="splitLoading"
                    @click="scrollToSplit(visit)"
                  >
                    {{ $t('_global.go_to') }}
                    <template #loader>
                      <v-progress-linear
                        style="width: 75%"
                        rounded
                        indeterminate
                      />
                    </template>
                  </v-btn>
                </div>
              </Transition>
            </div>
          </v-slide-group>
        </v-btn-toggle>
      </div>
    </div>
    <div ref="flowchartWrapper" class="protocol-flowchart-wrapper">
      <div
        id="protocolFlowchart"
        @click="onFlowchartClick"
        v-html="sanitizedFlowchart"
      />
      <ManageCellFootnotesPopover
        v-if="selectedCellRefs"
        ref="manageCellFootnotesPopover"
        :style="panelStyle"
        :cell-refs="selectedCellRefs"
        :layout="layout"
        :footnote-letters="footnoteLetters"
        @close="closeFootnotesPopover"
        @create-footnote="createFootnoteForSelectedCell"
        @footnotes-changed="refreshFlowchartKeepingSelection"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, inject, nextTick, onMounted, ref, watch } from 'vue'
import study from '@/api/study'
import soaDownloads from '@/utils/soaDownloads'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import unitConstants from '@/constants/units'
import footnoteConstants from '@/constants/footnotes'
import units from '@/api/units'
import { useAccessGuard } from '@/composables/accessGuard'
import { sanitizeHTML } from '@/utils/sanitize'
import { referencedItemMatchesRef } from '@/utils/soaFootnotes'
import ManageCellFootnotesPopover from '@/components/studies/ManageCellFootnotesPopover.vue'
import ManageFootnotesButton from '@/components/studies/ManageFootnotesButton.vue'

const props = defineProps({
  update: {
    type: Number,
    default: 0,
  },
  layout: {
    type: String,
    default: 'protocol',
  },
  studyVisits: {
    type: Array,
    default: () => [],
  },
})

const supportsFootnotes = computed(() =>
  footnoteConstants.FOOTNOTE_LAYOUTS.includes(props.layout)
)

const studiesGeneralStore = useStudiesGeneralStore()
const accessGuard = useAccessGuard()
const roles = inject('roles')

// Write requests always target the latest study, so a selected version is read-only.
const canEditStudy = computed(
  () =>
    !studiesGeneralStore.selectedStudyVersion &&
    accessGuard.checkPermission(roles.STUDY_WRITE)
)

const protocolFlowchart = ref('')
const loading = ref(true)
const preferredTimeUnits = ref([])
const toggle = ref([])
const groupedVisits = ref([])
const showSplitMenu = ref(false)
const splitLoading = ref(false)

const OBJECT_UID_ATTR_RE = /^object-uid(-\d+)?$/
const OBJECT_PROPAGATED_ATTR = 'object-propagated'
const OBJECT_ATTR_ALLOW_RE = /^object-(type|uid)(-\d+)?$|^object-propagated$/

const flowchartWrapper = ref(null)
const manageCellFootnotesPopover = ref(null)
const manageFootnotes = ref(null)
const isLinkingFootnote = ref(false)
const LOADING_CELL_CLASS = 'footnote-loading-cell'
// Refs of the cells whose footnote link is being saved, one entry per pending click.
const loadingCellRefs = []
let flowchartRefresh = Promise.resolve()
const selectedCellRefs = ref(null)
const selectedCellEl = ref(null)
const panelStyle = ref({})
const DEFAULT_PANEL_WIDTH = 360

watch(
  () => props.layout,
  (newVal, oldVal) => {
    if (newVal !== oldVal) updateFlowchart()
  }
)
watch(
  () => props.update,
  (newVal, oldVal) => {
    if (newVal !== oldVal) updateFlowchart()
  }
)
watch(
  () => props.studyVisits,
  () => loadVisits()
)
watch(canEditStudy, () => {
  closeFootnotesPopover()
  markClickableCells()
})

onMounted(() => {
  updateFlowchart()
  units
    .getBySubset(unitConstants.TIME_UNIT_SUBSET_STUDY_PREFERRED_TIME_UNIT)
    .then((resp) => {
      preferredTimeUnits.value = resp.data.items
    })
  loadVisits()
  getSoASplits()
})

function scrollToSplit(visit) {
  toggle.value = toggle.value.filter(
    (item) => !(typeof item === 'number' && Number.isInteger(item))
  )
  const uidSet = new Set(toggle.value)
  const index = groupedVisits.value
    .filter((item) => uidSet.has(item.uid))
    .map((item) => item.uid)
    .indexOf(visit.uid)
  const els = document.querySelectorAll('table')
  els[index + 1].scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function loadVisits() {
  try {
    // These visit names are placeholders and should be excluded from split-menu grouping.
    const excludedVisitNames = new Set(['29500', '29999'])

    const visits = (props.studyVisits ?? []).map((v) => ({
      name: v.visit_short_name,
      uid: v.uid,
      show_visit: v.show_visit,
      group: v.consecutive_visit_group ?? null,
    }))

    const result = []
    let lastGroup = null
    let lastVisitInGroup = null

    for (const visit of visits.slice(1)) {
      if (!visit.show_visit) {
        continue
      }

      if (excludedVisitNames.has(`${visit.name}`.trim())) {
        continue
      }

      if (!visit.group) {
        if (lastVisitInGroup) {
          result.push(lastVisitInGroup)
          lastVisitInGroup = null
        }
        result.push(visit)
        lastGroup = null
      } else {
        if (!lastGroup) {
          lastVisitInGroup = visit
        } else if (visit.group === lastGroup) {
          lastVisitInGroup = visit
        } else {
          result.push(lastVisitInGroup)
        }
        lastGroup = visit.group
      }
    }
    groupedVisits.value = result
  } catch (error) {
    console.error('Failed to load visits', error)
  }
}
async function splitSoA(visitUid) {
  splitLoading.value = true
  loading.value = true
  if (toggle.value.includes(visitUid)) {
    const payload = { uid: visitUid }
    await study.splitSoA(studiesGeneralStore.selectedStudy.uid, payload)
    updateFlowchart()
  } else {
    await study.removeSoASplit(studiesGeneralStore.selectedStudy.uid, visitUid)
    updateFlowchart()
  }
}
async function getSoASplits() {
  const resp = await study.getSoASplits(studiesGeneralStore.selectedStudy.uid)
  toggle.value = resp.data.map((item) => item.uid)
  if (toggle.value.length) {
    showSplitMenu.value = true
  }
}
const sanitizedFlowchart = computed(() =>
  sanitizeHTML(protocolFlowchart.value, {
    allowAttrPattern: OBJECT_ATTR_ALLOW_RE,
  })
)
// StudySoAFootnote uid -> the letter the protocol prints for it
const footnoteLetters = computed(() => {
  const letters = {}
  if (!protocolFlowchart.value) {
    return letters
  }
  const doc = new DOMParser().parseFromString(
    protocolFlowchart.value,
    'text/html'
  )
  doc.querySelectorAll('p.footnote[object-uid]').forEach((p) => {
    const letter = p.querySelector('sup')?.textContent?.trim()
    if (letter) {
      letters[p.getAttribute('object-uid')] = letter
    }
  })
  return letters
})
const highlightedFootnoteItems = ref(null)
function applyFootnoteHighlight(items) {
  const wrapperEl = flowchartWrapper.value
  if (!wrapperEl) {
    return
  }
  wrapperEl.querySelectorAll('.highlighted-footnote-cell').forEach((cell) => {
    cell.classList.remove('highlighted-footnote-cell')
  })
  if (!items?.length) {
    return
  }
  wrapperEl.querySelectorAll('td, th').forEach((cell) => {
    if (
      extractRefs(cell).some((ref) =>
        items.some((item) => referencedItemMatchesRef(item, ref))
      )
    ) {
      cell.classList.add('highlighted-footnote-cell')
    }
  })
}
function highlightFootnoteItems(items) {
  highlightedFootnoteItems.value = items
  applyFootnoteHighlight(items)
}
function scrollToItem(item) {
  const wrapperEl = flowchartWrapper.value
  if (!wrapperEl) {
    return
  }
  const cell = Array.from(wrapperEl.querySelectorAll('td, th')).find((el) =>
    extractRefs(el).some((ref) => referencedItemMatchesRef(item, ref))
  )
  if (!cell) {
    return
  }
  cell.scrollIntoView({ behavior: 'smooth', block: 'center' })
  cell.classList.add('flash-highlight-cell')
  setTimeout(() => {
    cell.classList.remove('flash-highlight-cell')
  }, 2000)
}
function findObjectCell(el) {
  if (!supportsFootnotes.value) {
    return null
  }
  let node = el
  while (node && node !== flowchartWrapper.value) {
    if (
      (node.tagName === 'TD' || node.tagName === 'TH') &&
      node.attributes &&
      Array.from(node.attributes).some((attr) =>
        OBJECT_UID_ATTR_RE.test(attr.name)
      )
    ) {
      return node
    }
    node = node.parentElement
  }
  return null
}
function extractRefs(cell) {
  const viaPropagatedCell = cell.hasAttribute(OBJECT_PROPAGATED_ATTR)
  return Array.from(cell.attributes)
    .filter((attr) => OBJECT_UID_ATTR_RE.test(attr.name))
    .map((attr) => {
      const suffix = attr.name.slice('object-uid'.length)
      return {
        uid: attr.value,
        type: cell.getAttribute(`object-type${suffix}`),
        viaPropagatedCell,
      }
    })
}
function findCellByRefs(refs) {
  const wrapperEl = flowchartWrapper.value
  if (!wrapperEl || !refs?.length) {
    return null
  }
  return (
    Array.from(wrapperEl.querySelectorAll('td, th')).find((cell) => {
      const cellRefs = extractRefs(cell)
      return (
        cellRefs.length === refs.length &&
        refs.every((ref) =>
          cellRefs.some(
            (cellRef) =>
              cellRef.uid === ref.uid &&
              cellRef.type === ref.type &&
              cellRef.viaPropagatedCell === ref.viaPropagatedCell
          )
        )
      )
    }) ?? null
  )
}
function positionPanel(cell) {
  const wrapperEl = flowchartWrapper.value
  if (!wrapperEl) {
    return
  }
  const wrapperRect = wrapperEl.getBoundingClientRect()
  const cellRect = cell.getBoundingClientRect()
  const panelWidth =
    manageCellFootnotesPopover.value?.$el?.getBoundingClientRect().width ||
    DEFAULT_PANEL_WIDTH
  let left = cellRect.right - wrapperRect.left + 8
  if (left + panelWidth > wrapperEl.clientWidth) {
    left = Math.max(0, cellRect.left - wrapperRect.left - panelWidth - 8)
  }
  panelStyle.value = {
    top: `${cellRect.top - wrapperRect.top}px`,
    left: `${left}px`,
  }
}
function onLinkingChanged(isLinking) {
  isLinkingFootnote.value = isLinking
  if (isLinking) {
    closeFootnotesPopover()
  }
}
// The flowchart HTML is replaced after every change, so the class is reapplied by refs.
function applyCellLoading() {
  const wrapperEl = flowchartWrapper.value
  if (!wrapperEl) {
    return
  }
  wrapperEl.querySelectorAll(`.${LOADING_CELL_CLASS}`).forEach((cell) => {
    cell.classList.remove(LOADING_CELL_CLASS)
  })
  loadingCellRefs.forEach((refs) => {
    findCellByRefs(refs)?.classList.add(LOADING_CELL_CLASS)
  })
}
async function toggleFootnoteLink(cell) {
  const refs = extractRefs(cell)
  const pending = manageFootnotes.value?.toggleCellRefs(refs)
  // Picking cells for a new footnote is synchronous, there is nothing to wait for.
  if (!pending) {
    return
  }
  loadingCellRefs.push(refs)
  applyCellLoading()
  try {
    await pending
    await flowchartRefresh
  } catch {
    // Failed requests are already reported by the Axios interceptor.
  }
  loadingCellRefs.splice(loadingCellRefs.indexOf(refs), 1)
  applyCellLoading()
}
function onFlowchartClick(event) {
  if (!canEditStudy.value) {
    return
  }
  const cell = findObjectCell(event.target)
  if (isLinkingFootnote.value) {
    if (cell) {
      toggleFootnoteLink(cell)
    }
    return
  }
  if (!cell) {
    closeFootnotesPopover()
    return
  }
  if (selectedCellEl.value === cell) {
    closeFootnotesPopover()
    return
  }
  selectedCellEl.value?.classList.remove('selected-object-cell')
  selectedCellEl.value = cell
  selectedCellEl.value.classList.add('selected-object-cell')
  selectedCellRefs.value = extractRefs(cell)
  nextTick(() => positionPanel(cell))
}
function createFootnoteForSelectedCell() {
  manageFootnotes.value?.openNewFootnote(selectedCellRefs.value ?? [])
}
function closeFootnotesPopover() {
  selectedCellEl.value?.classList.remove('selected-object-cell')
  selectedCellEl.value = null
  selectedCellRefs.value = null
}
function markClickableCells() {
  const wrapperEl = flowchartWrapper.value
  if (!wrapperEl) {
    return
  }
  wrapperEl.querySelectorAll('td, th').forEach((cell) => {
    const hasRef = Array.from(cell.attributes).some((attr) =>
      OBJECT_UID_ATTR_RE.test(attr.name)
    )
    cell.classList.toggle(
      'clickable-object-cell',
      supportsFootnotes.value && canEditStudy.value && hasRef
    )
  })
}
function switchIsEnabled(layouts = []) {
  return canEditStudy.value && (!layouts || layouts.includes(props.layout))
}
function updateSoaPreferences(key) {
  loading.value = true
  studiesGeneralStore
    .setSoaPreferences({ [key]: studiesGeneralStore.soaPreferences[key] })
    .then(() => {
      updateFlowchart()
    })
}
// Fetches can overlap (e.g. one per saved footnote link) and finish out of order,
// so only the newest one may replace the flowchart or clear the loading state.
let flowchartFetchCount = 0
let latestFlowchartFetch = Promise.resolve()

// Resolves to whether this fetch was applied, i.e. was not superseded by a newer one.
function fetchFlowchart() {
  const fetchId = ++flowchartFetchCount
  const isLatest = () => fetchId === flowchartFetchCount
  const request = study
    .getStudyProtocolFlowchartHtml(studiesGeneralStore.selectedStudy.uid, {
      layout: props.layout,
      include_uids: supportsFootnotes.value,
    })
    .then(async (resp) => {
      if (!isLatest()) {
        // Wait for the newer fetch so callers resume once the flowchart is up to date.
        await latestFlowchartFetch.catch(() => {})
        return false
      }
      protocolFlowchart.value = resp.data
      splitLoading.value = false
      await nextTick()
      markClickableCells()
      applyFootnoteHighlight(highlightedFootnoteItems.value)
      applyCellLoading()
      return true
    })
    .finally(() => {
      if (isLatest()) {
        stopLoading()
      }
    })
  latestFlowchartFetch = request
  return request
}
function updateFlowchart() {
  loading.value = true
  closeFootnotesPopover()
  return fetchFlowchart()
}
function refreshFlowchartKeepingSelection() {
  loading.value = true
  flowchartRefresh = fetchFlowchart().then((applied) => {
    const refs = selectedCellRefs.value
    // A newer fetch restores the selection itself.
    if (!applied || !refs) {
      return
    }
    const cell = findCellByRefs(refs)
    if (!cell) {
      closeFootnotesPopover()
      return
    }
    selectedCellEl.value?.classList.remove('selected-object-cell')
    selectedCellEl.value = cell
    selectedCellEl.value.classList.add('selected-object-cell')
    positionPanel(cell)
  })
  return flowchartRefresh
}
async function downloadDocx() {
  loading.value = true
  try {
    await soaDownloads.docxDownload(props.layout)
  } finally {
    stopLoading()
  }
}
async function downloadCSV() {
  loading.value = true
  try {
    await soaDownloads.csvDownload(props.layout)
  } finally {
    stopLoading()
  }
}
async function downloadEXCEL() {
  loading.value = true
  try {
    await soaDownloads.excelDownload(props.layout)
  } finally {
    stopLoading()
  }
}
function stopLoading() {
  loading.value = false
}
</script>

<style lang="scss">
.split-class {
  color: red;
  border-inline-start-style: solid !important;
  border-left-color: red !important;
  border-left-width: medium !important;
  width: -webkit-fill-available;
}
.layoutSelect {
  max-width: 200px;
}
.horizontal-flip {
  transform: rotate(180deg);
}
.btn-toggle {
  overflow-x: auto;
  height: 70px !important;
}
.slide-div {
  display: inline-block;
  vertical-align: top;
}
.go-to-btn {
  width: -webkit-fill-available;
  border-bottom-left-radius: 5px !important;
  border-bottom-right-radius: 5px !important;
}
.protocol-flowchart-wrapper {
  position: relative;
}

#protocolFlowchart {
  padding-bottom: 1em;

  .clickable-object-cell {
    position: relative;
    cursor: pointer;

    &::after {
      content: '';
      position: absolute;
      top: 0;
      right: 0;
      width: 0;
      height: 0;
      border-style: solid;
      border-width: 0 6px 6px 0;
      border-color: transparent rgba(var(--v-theme-nnBaseBlue), 0.55)
        transparent transparent;
    }

    &:hover,
    &.selected-object-cell {
      background-color: rgba(var(--v-theme-nnBaseBlue), 0.15);

      &::after {
        border-color: transparent rgb(var(--v-theme-nnBaseBlue)) transparent
          transparent;
      }
    }
  }

  .footnote-loading-cell {
    position: relative;
    // Hides the cell content so the spinner is not drawn over it.
    color: transparent;

    &::before {
      content: '';
      position: absolute;
      inset: 0;
      margin: auto;
      width: 14px;
      height: 14px;
      box-sizing: border-box;
      border: 2px solid rgba(var(--v-theme-nnBaseBlue), 0.25);
      border-top-color: rgb(var(--v-theme-nnBaseBlue));
      border-radius: 50%;
      animation: footnote-cell-spin 0.8s linear infinite;
    }
  }

  .highlighted-footnote-cell,
  .flash-highlight-cell {
    outline-offset: -2px;
    transition:
      background-color 0.3s ease,
      outline-color 0.3s ease;
  }

  .highlighted-footnote-cell {
    outline: 2px solid rgb(var(--v-theme-warning));
  }

  .flash-highlight-cell {
    outline: 2px solid rgb(var(--v-theme-success));
  }

  // Opaque tint with a selector more specific than the grey group / header rules
  // below, so the highlight replaces their background instead of sitting under it.
  table tr > td,
  table tr > th {
    &.highlighted-footnote-cell {
      background-color: color-mix(
        in srgb,
        rgb(var(--v-theme-warning)) 25%,
        rgb(var(--v-theme-surface))
      );
    }

    &.flash-highlight-cell {
      background-color: color-mix(
        in srgb,
        rgb(var(--v-theme-success)) 35%,
        rgb(var(--v-theme-surface))
      );
    }
  }

  table {
    width: 100%;
    border-collapse: collapse;
    table-layout: auto;
    resize: both;
    margin-bottom: 1em;

    &:not(:first-child) {
      margin-top: 2em;
    }

    &,
    & th,
    & td {
      border: 1px solid black;
      padding: 1px 3px;
    }

    & thead {
      background-color: rgb(var(--v-theme-tableGray));

      & th {
        border-color: black;
      }

      & .header1:nth-child(n + 2) {
        vertical-align: top;
        text-orientation: mixed;
      }

      & th:first-child {
        text-align: left;
      }
    }

    & tbody {
      & th {
        text-align: left;
        font-weight: normal;
      }

      & tr td:nth-child(n + 2) {
        text-align: center;
        vertical-align: middle;
      }

      & .soaGroup {
        background-color: rgb(var(--v-theme-tableGray));
        font-weight: bold;
      }

      & .group {
        background-color: rgb(var(--v-theme-tableGray));
        font-weight: bold;
      }

      & .subGroup {
        background-color: rgb(var(--v-theme-tableGray));
      }

      & .activity:first-child,
      & .activityPlaceholder:first-child,
      & .activityPlaceholderSubmitted:first-child {
        padding-left: 1em;
      }

      & .activityInstance:first-child {
        padding-left: 2em;
        font-style: italic;
      }
    }
  }
}

@keyframes footnote-cell-spin {
  to {
    transform: rotate(360deg);
  }
}

.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}

.slide-fade-enter-from {
  transform: translateY(15px);
}

.slide-fade-leave-active {
  animation: slideOut 0.2s ease-out;
}

@keyframes slideOut {
  0% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-30px);
  }
  100% {
    transform: translateX(150px);
  }
}

.slide-fade-leave-to {
  transform: translateX(150px);
}
</style>
