<template>
  <div id="visjs" class="pa-6">
    <div v-if="loading" class="mt-4">
      <v-progress-linear indeterminate />
    </div>
    <div v-else-if="timelineEpochs.length > 0" class="visit-timeline-container">
      <v-btn
        v-if="isOverflowing"
        icon="mdi-chevron-left"
        variant="outlined"
        color="nnBaseBlue"
        size="small"
        class="timeline-nav"
        data-cy="timeline-scroll-left"
        :disabled="!canScrollLeft"
        @click="scrollTimeline(-1)"
      />
      <div
        ref="timelineScroll"
        class="visit-timeline-scroll"
        @scroll="updateScrollState"
      >
        <table ref="timelineTable" class="visit-timeline">
          <tbody>
            <tr class="epoch-row">
              <th class="row-label" />
              <th
                v-for="(group, gi) in timelineEpochs"
                :key="`epoch-${group.uid}`"
                class="epoch-cell"
                :class="{ 'epoch-divider': gi > 0 }"
                :colspan="group.visits.length"
              >
                <span class="epoch-name" :style="{ color: group.color }">
                  {{ group.name }}
                </span>
                <span
                  class="epoch-underline"
                  :style="{ backgroundColor: group.color }"
                />
              </th>
            </tr>
            <tr class="type-row">
              <th class="row-label">
                {{ $t('StudyVisitForm.visit_type') }}
              </th>
              <th
                v-for="group in timelineTypeGroups"
                :key="`type-${group.key}`"
                class="type-group-cell"
                :class="{ 'epoch-divider': group.firstInEpoch }"
                :colspan="group.count"
              >
                <span class="type-name">{{ group.name }}</span>
                <span class="type-underline" />
              </th>
            </tr>
            <tr ref="nameRowParent" class="name-row">
              <th class="row-label" />
              <td
                v-for="visit in timelineVisits"
                :key="`name-${visit.uid}`"
                class="visit-cell"
                :data-visit-uid="visit.uid"
                :class="{
                  'epoch-divider': visit.firstInEpoch,
                  'group-cell': visit.inGroup,
                  'group-start': visit.groupStart,
                  'group-end': visit.groupEnd,
                  reorderable: canReorderVisits,
                }"
                :style="
                  visit.inGroup ? { '--group-color': visit.groupColor } : null
                "
              >
                <span
                  class="visit-box"
                  :class="{
                    active: showForm && selectedVisit?.uid === visit.uid,
                    highlighted: highlightedVisitUid === visit.uid,
                  }"
                  role="button"
                  tabindex="0"
                  data-cy="visit-box"
                  @click="toggleVisitForm(visit)"
                  @contextmenu.prevent="openContextMenu($event, visit)"
                >
                  <v-icon
                    v-if="canReorderVisits"
                    class="mr-1"
                    size="small"
                    :title="$t('StudyVisitTable.drag_to_reorder')"
                  >
                    mdi-drag-vertical
                  </v-icon>
                  {{ visit.visit_short_name || visit.visit_name }}
                </span>
              </td>
            </tr>
            <tr class="value-row">
              <th class="row-label">
                {{ $t('StudyVisitTable.study_day') }}
              </th>
              <td
                v-for="visit in timelineVisits"
                :key="`day-${visit.uid}`"
                :class="{ 'epoch-divider': visit.firstInEpoch }"
              >
                {{ getStudyDay(visit) }}
              </td>
            </tr>
            <tr class="value-row">
              <th class="row-label">
                {{ $t('StudyVisitTable.study_week') }}
              </th>
              <td
                v-for="visit in timelineVisits"
                :key="`week-${visit.uid}`"
                :class="{ 'epoch-divider': visit.firstInEpoch }"
              >
                {{ getStudyWeek(visit) }}
              </td>
            </tr>
            <tr class="value-row">
              <th class="row-label">
                {{ $t('StudyVisitForm.visit_window') }}
              </th>
              <td
                v-for="visit in timelineVisits"
                :key="`window-${visit.uid}`"
                :class="{ 'epoch-divider': visit.firstInEpoch }"
              >
                {{ getVisitWindowLabel(visit) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <v-btn
        v-if="isOverflowing"
        icon="mdi-chevron-right"
        variant="outlined"
        color="nnBaseBlue"
        size="small"
        class="timeline-nav"
        data-cy="timeline-scroll-right"
        :disabled="!canScrollRight"
        @click="scrollTimeline(1)"
      />
    </div>
    <v-empty-state
      v-else-if="!showForm"
      class="empty-state bg-nnBaseLight mt-3"
    >
      <template #media>
        <div class="d-flex justify-center">
          <img :src="emptyStateImageUrl" alt="" class="empty-state-image" />
        </div>
      </template>
      <template #title>
        <div class="text-label-large mt-8">
          {{ $t('StudyVisitForm.no_visits_title') }}
        </div>
      </template>
      <template #text>
        <div class="text-body-small">
          {{ $t('StudyVisitForm.no_visits_text') }}
        </div>
      </template>
      <template #actions>
        <v-btn
          class="secondary-btn"
          variant="outlined"
          rounded="xl"
          data-cy="add-visit-empty-state"
          :disabled="
            !accessGuard.checkPermission(roles.STUDY_WRITE) ||
            studiesGeneralStore.selectedStudyVersion !== null
          "
          :text="$t('StudyVisitTable.add_visit')"
          @click="openVisitForm(null)"
        />
      </template>
    </v-empty-state>
    <StudyVisitTimelineForm
      v-if="showForm"
      ref="visitFormRef"
      :study-visit="selectedVisit"
      class="mt-6"
      @close="closeVisitForm"
      @refresh="getTimeLineVisits"
    />
    <v-menu v-model="contextMenu.show" :target="contextMenu.target">
      <v-list density="compact">
        <v-list-item
          v-if="canDuplicateVisit(contextVisit)"
          data-cy="context-menu-duplicate-visit"
          prepend-icon="mdi-plus-box-multiple-outline"
          :title="$t('StudyVisitTable.duplicate')"
          @click="handleDuplicateFromContextMenu"
        />
        <v-list-item
          data-cy="context-menu-remove-visit"
          prepend-icon="mdi-delete-outline"
          :title="$t('_global.remove')"
          @click="handleRemoveFromContextMenu"
        />
      </v-list>
    </v-menu>
  </div>
</template>

<script setup>
import {
  ref,
  computed,
  watch,
  onMounted,
  onBeforeUnmount,
  nextTick,
  inject,
  toRef,
} from 'vue'
import { useDragAndDrop } from '@formkit/drag-and-drop/vue'
import studyEpochsApi from '@/api/studyEpochs'
import StudyVisitTimelineForm from './StudyVisitTimelineForm.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useEpochsStore } from '@/stores/studies-epochs'
import { useAccessGuard } from '@/composables/accessGuard'
import { useVisitTypeTerms } from '@/composables/visitTypeTerms'
import visitConstants from '@/constants/visits'

const props = defineProps({
  visitTypes: {
    type: Array,
    default: () => [],
  },
})
const emit = defineEmits(['duplicate-request', 'delete-request'])
const { canDuplicateVisit, fixedWindowVisitTypeUids } = useVisitTypeTerms(
  toRef(props, 'visitTypes')
)
const studiesGeneralStore = useStudiesGeneralStore()
const epochsStore = useEpochsStore()
const accessGuard = useAccessGuard()
const roles = inject('roles')

const loading = ref(true)

function visitDragConfig(disabled) {
  return {
    draggable: (child) => child.classList.contains('visit-cell'),
    disabled,
    onDragend: handleVisitDragend,
  }
}
const [nameRowParent, timeLineVisits, updateVisitDragConfig] = useDragAndDrop(
  [],
  visitDragConfig(true)
)
const timelineScroll = ref()
const timelineTable = ref()
const canScrollLeft = ref(false)
const canScrollRight = ref(false)
const isOverflowing = ref(false)
const visitFormRef = ref()
const selectedVisit = ref(null)
const contextVisit = ref(null)
const showForm = ref(false)
const highlightedVisitUid = ref(null)
const contextMenu = ref({ show: false, target: [0, 0] })
let timelineResizeObserver = null
let highlightTimeout = null

const emptyStateImageUrl = new URL(
  '../../../assets/soa_empty_state.png',
  import.meta.url
).href

const studyEpochs = computed(() => epochsStore.studyEpochs)

// Same write gate as the toolbar buttons in StudyVisitTable
const canEditVisits = computed(
  () =>
    accessGuard.checkPermission(roles.STUDY_WRITE) &&
    studiesGeneralStore.selectedStudyVersion === null &&
    epochsStore.visitModeKnown
)

// Gated on visit_subclass: Early discontinuation also sets visit_sublabel_reference
function getVisitGroup(visit) {
  if (!visit) {
    return null
  }
  if (
    visit.visit_subclass ===
    visitConstants.SUBCLASS_ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV
  ) {
    return visit.visit_sublabel_reference
  }
  if (
    visit.visit_subclass ===
    visitConstants.SUBCLASS_ANCHOR_VISIT_IN_GROUP_OF_SUBV
  ) {
    return visit.uid
  }
  return null
}

// Deterministic hash keeps each group's color stable across re-renders.
function hashString(value) {
  let hash = 0
  for (let i = 0; i < value.length; i++) {
    hash = (hash * 31 + value.charCodeAt(i)) | 0
  }
  return Math.abs(hash)
}

function getGroupColor(group) {
  const hue = hashString(group) % 360
  return `hsl(${hue}, 70%, 88%)`
}

const timelineVisits = computed(() => {
  const visits = timeLineVisits.value
  // Grouping is assisted-mode only; ignore stale refs left from before a switch.
  const manualMode = epochsStore.manualVisitMode
  return visits.map((visit, index) => {
    const firstInEpoch =
      index !== 0 && visit.study_epoch_uid !== visits[index - 1].study_epoch_uid
    const group = manualMode ? null : getVisitGroup(visit)
    const inGroup = Boolean(group)
    const groupStart =
      inGroup && (index === 0 || getVisitGroup(visits[index - 1]) !== group)
    const groupEnd =
      inGroup &&
      (index === visits.length - 1 ||
        getVisitGroup(visits[index + 1]) !== group)
    const groupColor = inGroup ? getGroupColor(group) : null
    return { ...visit, firstInEpoch, inGroup, groupStart, groupEnd, groupColor }
  })
})
const timelineEpochs = computed(() => {
  const groups = []
  let current = null
  for (const visit of timeLineVisits.value) {
    const epochUid = visit.study_epoch_uid
    if (!current || current.uid !== epochUid) {
      const epoch = studyEpochs.value.find((item) => item.uid === epochUid)
      current = {
        uid: epochUid,
        name:
          visit.study_epoch?.sponsor_preferred_name ||
          (epoch ? epoch.epoch_name : ''),
        color: epoch?.color_hash || '#e0e0e0',
        visits: [],
      }
      groups.push(current)
    }
    current.visits.push(visit)
  }
  return groups
})
const timelineTypeGroups = computed(() => {
  const groups = []
  let current = null
  timeLineVisits.value.forEach((visit, index) => {
    const typeName = visit.visit_type?.sponsor_preferred_name || ''
    const typeUid = visit.visit_type?.term_uid || typeName
    const firstInEpoch =
      index !== 0 &&
      visit.study_epoch_uid !== timeLineVisits.value[index - 1].study_epoch_uid
    if (!current || current.typeUid !== typeUid) {
      current = {
        key: `${typeUid}-${index}`,
        typeUid,
        name: typeName,
        count: 0,
        firstInEpoch,
      }
      groups.push(current)
    }
    current.count += 1
  })
  return groups
})

function getUnitName(unitUid) {
  const unit = epochsStore.studyTimeUnits.find((item) => item.uid === unitUid)
  if (unit) {
    return unit.name
  }
  return ''
}

// Fixed-window types (unscheduled, non-visit, early discontinuation) have no meaningful window
function getVisitWindowLabel(visit) {
  if (
    fixedWindowVisitTypeUids.value.includes(visit.visit_type?.term_uid) ||
    visit.min_visit_window_value === null ||
    visit.min_visit_window_value === undefined ||
    visit.max_visit_window_value === null ||
    visit.max_visit_window_value === undefined
  ) {
    return ''
  }
  const unitName = getUnitName(visit.visit_window_unit_uid)
  const unitAbbr = unitName ? unitName.charAt(0).toUpperCase() : ''
  const min = visit.min_visit_window_value
  const max = visit.max_visit_window_value
  if (min === -max) {
    return `±${max}${unitAbbr}`
  }
  return `${min}/+${max}${unitAbbr}`
}

// With baseline as time 0, days/weeks are durations from it
function getStudyDay(visit) {
  return studiesGeneralStore.soaPreferences?.baseline_as_time_zero
    ? visit.study_duration_days
    : visit.study_day_number
}

function getStudyWeek(visit) {
  return studiesGeneralStore.soaPreferences?.baseline_as_time_zero
    ? visit.study_duration_weeks
    : visit.study_week_number
}

function scrollTimeline(direction) {
  if (!timelineScroll.value) {
    return
  }
  timelineScroll.value.scrollBy({
    left: direction * 1000,
    behavior: 'smooth',
  })
}

// Hand on the API visit itself, so view-only layout fields never reach a request payload
function getApiVisit(visit) {
  if (!visit) {
    return null
  }
  return timeLineVisits.value.find((item) => item.uid === visit.uid) ?? visit
}

// Resolves true when the open form, if any, may be left; offerSave adds a save option
function confirmDiscardChanges(offerSave = false) {
  if (!visitFormRef.value) {
    return Promise.resolve(true)
  }
  return offerSave
    ? visitFormRef.value.confirmUnsavedChanges()
    : visitFormRef.value.confirmDiscardChanges()
}

// The form is edit-only, so users without write access keep the read-only timeline
async function openVisitForm(visit, { offerSave = false } = {}) {
  if (!canEditVisits.value) {
    return
  }
  const apiVisit = getApiVisit(visit)
  if (showForm.value) {
    // Already open on that visit: rebuilding it would drop pending edits.
    if (apiVisit?.uid === selectedVisit.value?.uid) {
      return
    }
    if (!(await confirmDiscardChanges(offerSave))) {
      return
    }
  }
  selectedVisit.value = apiVisit
  showForm.value = true
}

// Clicking the selected visit again deselects it
async function toggleVisitForm(visit) {
  if (showForm.value && selectedVisit.value?.uid === visit.uid) {
    if (await confirmDiscardChanges()) {
      closeVisitForm()
    }
    return
  }
  openVisitForm(visit)
}

// The form confirms before emitting close (and closes after create), so no check here
function closeVisitForm() {
  showForm.value = false
  selectedVisit.value = null
}

// Every entry in the menu is a write (duplicate, remove).
function openContextMenu(event, visit) {
  if (!canEditVisits.value) {
    return
  }
  contextMenu.value.show = false
  contextVisit.value = getApiVisit(visit)
  contextMenu.value.target = [event.clientX, event.clientY]
  nextTick(() => {
    contextMenu.value.show = true
  })
}

function handleDuplicateFromContextMenu() {
  contextMenu.value.show = false
  emit('duplicate-request', contextVisit.value)
}

function handleRemoveFromContextMenu() {
  contextMenu.value.show = false
  emit('delete-request', contextVisit.value)
}

const canReorderVisits = computed(
  () => epochsStore.manualVisitMode && canEditVisits.value
)

// Wait for the <tr> ref and a post-render flush, or dragging can silently break
watch(
  [canReorderVisits, nameRowParent],
  ([value, parentEl]) => {
    if (!parentEl) {
      return
    }
    updateVisitDragConfig(visitDragConfig(!value))
  },
  { immediate: true, flush: 'post' }
)

function highlightVisit(uid) {
  clearTimeout(highlightTimeout)
  highlightedVisitUid.value = uid
  highlightTimeout = setTimeout(() => {
    highlightedVisitUid.value = null
  }, 1500)
}

// event.values is the drag lib's already-reordered array.
function handleVisitDragend(event) {
  if (event.state.targetIndex === event.state.initialIndex) {
    return
  }
  const draggedUid = event.draggedNode.data.value.uid
  const visitUids = event.values.map((visit) => visit.uid)
  studyEpochsApi
    .reorderStudyVisits(studiesGeneralStore.selectedStudy.uid, visitUids)
    .then(() => {
      getTimeLineVisits()
      highlightVisit(draggedUid)
    })
    .catch(getTimeLineVisits)
}

function deleteVisit(visit) {
  const uid = visit?.uid
  if (!uid) {
    return Promise.resolve()
  }
  return epochsStore
    .deleteStudyVisit({
      studyUid: studiesGeneralStore.selectedStudy.uid,
      studyVisitUid: uid,
    })
    .then(() => {
      if (selectedVisit.value?.uid === uid) {
        closeVisitForm()
      }
      getTimeLineVisits()
    })
}

// Current record from the reloaded list for the toolbar; the form's ref must keep its identity
defineExpose({
  showForm,
  selectedVisit: computed(() => getApiVisit(selectedVisit.value)),
  openNewVisitForm: () => openVisitForm(null, { offerSave: true }),
  confirmDiscardChanges,
  deleteVisit,
  refreshVisits: getTimeLineVisits,
})

function updateScrollState() {
  const el = timelineScroll.value
  if (!el) {
    isOverflowing.value = false
    canScrollLeft.value = false
    canScrollRight.value = false
    return
  }
  const overflowing = el.scrollWidth > el.clientWidth + 1
  isOverflowing.value = overflowing
  canScrollLeft.value = overflowing && el.scrollLeft > 0
  canScrollRight.value =
    overflowing && el.scrollLeft + el.clientWidth < el.scrollWidth - 1
}

function observeTimeline() {
  if (!timelineResizeObserver) {
    return
  }
  timelineResizeObserver.disconnect()
  if (timelineScroll.value) {
    timelineResizeObserver.observe(timelineScroll.value)
  }
  // Table width grows as data renders, unlike the scroll container's.
  if (timelineTable.value) {
    timelineResizeObserver.observe(timelineTable.value)
  }
}

// Brings the visit's column into view, clear of the sticky row labels
function scrollToVisit(uid) {
  const container = timelineScroll.value
  const cell = container?.querySelector(`[data-visit-uid="${uid}"]`)
  if (!cell) {
    return
  }
  const bounds = container.getBoundingClientRect()
  const cellBounds = cell.getBoundingClientRect()
  const labelWidth = container.querySelector('.row-label')?.offsetWidth ?? 0
  if (cellBounds.right > bounds.right) {
    container.scrollBy({
      left: cellBounds.right - bounds.right,
      behavior: 'smooth',
    })
  } else if (cellBounds.left < bounds.left + labelWidth) {
    container.scrollBy({
      left: cellBounds.left - bounds.left - labelWidth,
      behavior: 'smooth',
    })
  }
}

// Don't reset loading to true here: it unmounts the table and the drag lib loses its <tr> ref
function getTimeLineVisits() {
  const params = { page_size: 0 }
  studyEpochsApi
    .getStudyVisits(studiesGeneralStore.selectedStudy.uid, params)
    .then(async (resp) => {
      const knownUids = new Set(timeLineVisits.value.map((visit) => visit.uid))
      const newVisit = knownUids.size
        ? resp.data.items.find((visit) => !knownUids.has(visit.uid))
        : null
      timeLineVisits.value = resp.data.items
      if (newVisit) {
        await nextTick()
        scrollToVisit(newVisit.uid)
        highlightVisit(newVisit.uid)
      }
    })
    .finally(() => {
      loading.value = false
    })
}

// Epoch names can load late and widen cells, so re-measure on both.
watch([timelineVisits, studyEpochs], async () => {
  await nextTick()
  observeTimeline()
  requestAnimationFrame(updateScrollState)
})

onMounted(() => {
  timelineResizeObserver = new ResizeObserver(() => updateScrollState())
  window.addEventListener('resize', updateScrollState)
  getTimeLineVisits()
  if (epochsStore.studyEpochs.length === 0) {
    epochsStore.fetchStudyEpochs({
      studyUid: studiesGeneralStore.selectedStudy.uid,
    })
  }
  if (epochsStore.studyTimeUnits.length === 0) {
    epochsStore.fetchStudyTimeUnits()
  }
  nextTick(() => {
    observeTimeline()
    requestAnimationFrame(updateScrollState)
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateScrollState)
  if (timelineResizeObserver) {
    timelineResizeObserver.disconnect()
    timelineResizeObserver = null
  }
  clearTimeout(highlightTimeout)
})
</script>

<style scoped>
.empty-state {
  border-radius: 8px;
}
.empty-state-image {
  max-width: 240px;
  height: auto;
}
.visit-timeline-container {
  display: flex;
  align-items: stretch;
  gap: 8px;
}
.timeline-nav {
  align-self: center;
  flex: 0 0 auto;
}
.visit-timeline-scroll {
  display: flex;
  align-items: stretch;
  flex: 1 1 auto;
  min-width: 0;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: none;
}
.visit-timeline-scroll::-webkit-scrollbar {
  display: none;
}
.visit-timeline-scroll > .visit-timeline {
  flex: 0 0 auto;
}
.visit-timeline {
  border-collapse: collapse;
  white-space: nowrap;
}
.visit-timeline .row-label {
  position: sticky;
  left: 0;
  z-index: 2;
  background-color: rgb(var(--v-theme-nnWhite, 255, 255, 255));
  text-align: left;
  font-weight: 400;
  color: rgba(0, 0, 0, 0.6);
  padding: 6px 24px 6px 8px;
  vertical-align: middle;
  border-right: 1px solid rgba(0, 0, 0, 0.12);
}
.visit-timeline td,
.visit-timeline th {
  padding: 6px 12px;
  text-align: center;
  vertical-align: middle;
}
.visit-timeline .epoch-divider {
  border-left: 1px solid rgba(0, 0, 0, 0.2);
}
.visit-timeline .epoch-cell {
  text-align: left;
  padding-bottom: 4px;
}
.visit-timeline .epoch-name {
  font-weight: 700;
  font-size: 0.95rem;
}
.visit-timeline .epoch-underline {
  display: block;
  height: 2px;
  margin-top: 4px;
  border-radius: 2px;
}
.visit-timeline .type-group-cell {
  text-align: left;
  padding-bottom: 4px;
}
.visit-timeline .type-name {
  color: rgba(0, 0, 0, 0.6);
  font-size: 0.85rem;
}
.visit-timeline .type-underline {
  display: block;
  height: 2px;
  margin-top: 4px;
  border-radius: 2px;
  background-color: rgba(0, 0, 0, 0.3);
}
.visit-timeline .visit-box {
  display: inline-block;
  min-width: 44px;
  padding: 6px 10px;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition:
    background-color 0.4s ease-in-out,
    border-color 0.4s ease-in-out;
}
.visit-timeline .visit-box:hover {
  border-color: rgb(var(--v-theme-nnBaseBlue));
  background-color: rgba(var(--v-theme-nnBaseBlue), 0.08);
}
.visit-timeline .visit-box.active {
  border-color: rgb(var(--v-theme-nnBaseBlue));
  background-color: rgba(var(--v-theme-nnBaseBlue), 0.08);
}
.visit-timeline .visit-box.highlighted {
  border-color: #00c853;
  background-color: rgba(0, 200, 83, 0.25);
}
.visit-timeline .name-row td.reorderable .visit-box {
  cursor: grab;
  user-select: none;
  -webkit-user-drag: element;
}
.visit-timeline .name-row td.reorderable .visit-box:active {
  cursor: grabbing;
}
.visit-timeline .name-row td.group-cell {
  position: relative;
}
.visit-timeline .name-row td.group-cell::before {
  content: '';
  position: absolute;
  inset: 2px 0;
  background-color: var(--group-color, rgba(0, 0, 0, 0.06));
}
/* Inset the bar at group edges to leave a gap between adjacent groups. */
.visit-timeline .name-row td.group-start::before {
  left: 4px;
  border-top-left-radius: 8px;
  border-bottom-left-radius: 8px;
}
.visit-timeline .name-row td.group-end::before {
  right: 4px;
  border-top-right-radius: 8px;
  border-bottom-right-radius: 8px;
}
.visit-timeline .name-row td.group-cell .visit-box {
  position: relative;
}
.visit-timeline .value-row td,
.visit-timeline .value-row .row-label {
  font-size: 0.85rem;
}
</style>
