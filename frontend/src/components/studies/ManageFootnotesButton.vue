<template>
  <v-menu
    v-model="open"
    persistent
    :close-on-content-click="false"
    max-height="800px"
    max-width="550px"
    location="bottom"
    no-click-animation
  >
    <template #activator="{ props: menuProps }">
      <v-btn
        data-cy="manage-footnotes-button"
        v-bind="menuProps"
        variant="outlined"
        color="nnBaseBlue"
      >
        {{ $t('ProtocolFlowchart.manage_footnotes') }}
      </v-btn>
    </template>
    <v-card
      rounded="xl"
      width="550px"
      max-width="100%"
      class="d-flex flex-column"
    >
      <v-card-title
        class="dialog-title d-flex align-center justify-space-between ga-2 w-100 cursor-grab"
      >
        <span class="text-wrap" style="min-width: 0">
          {{ $t('ProtocolFlowchart.manage_footnotes') }}
        </span>
        <v-btn
          class="mx-0 px-0"
          color="secondary"
          data-cy="close-footnotes-button"
          :aria-label="$t('_global.close')"
          icon="mdi-close"
          variant="text"
          @click="open = false"
        />
      </v-card-title>
      <div
        v-if="
          editable && !creatingFootnote && !editedFootnote && !linkingFootnote
        "
        class="px-4 pt-2 pb-6"
      >
        <v-btn
          data-cy="create-footnotes-button"
          color="nnBaseBlue"
          prepend-icon="mdi-plus"
          variant="outlined"
          rounded="xl"
          class="text-body-medium"
          :disabled="Boolean(editedFootnote || linkingFootnote)"
          @click="creatingFootnote = true"
        >
          {{ $t('ProtocolFlowchart.create_footnote') }}
        </v-btn>
      </div>
      <v-divider />
      <div class="footnotes-body">
        <v-alert
          v-if="creatingFootnote"
          variant="tonal"
          data-cy="new-footnote-alert"
          color="nnBaseBlue"
          density="compact"
          icon="mdi-cursor-default-click-outline"
          class="ma-3"
        >
          <div>{{ $t('ProtocolFlowchart.new_footnote_cells_hint') }}</div>
          <div class="mt-1 font-weight-medium">
            {{
              $t('ProtocolFlowchart.new_footnote_cells_selected', {
                count: newFootnoteCells.length,
              })
            }}
          </div>
        </v-alert>
        <div v-if="creatingFootnote && !createFootnoteOption">
          <div class="d-flex align-center pa-2">
            <v-btn
              icon="mdi-arrow-left"
              data-cy="back-footnotes-button"
              color="secondary"
              size="small"
              variant="text"
              @click="creatingFootnote = false"
            />
            <span class="font-weight-medium ml-1">
              {{ $t('ProtocolFlowchart.new_footnote') }}
            </span>
          </div>
          <v-divider />
          <v-list class="pa-0">
            <v-list-item
              v-for="option in createFootnoteOptions"
              :key="option.key"
              :data-cy="`create-footnote-option-${option.key}`"
              tag="button"
              type="button"
              min-height="52"
              class="create-footnote-option text-start w-100"
              @click="createFootnoteOption = option.key"
            >
              <template #prepend>
                <v-icon :icon="option.icon" variant="text" size="small" />
              </template>
              <v-list-item-title
                class="create-footnote-option-title text-high-emphasis"
              >
                {{ $t(option.labelKey) }}
              </v-list-item-title>
              <template #append>
                <v-icon
                  icon="mdi-chevron-right"
                  size="x-small"
                  class="text-medium-emphasis"
                />
              </template>
            </v-list-item>
          </v-list>
        </div>
        <StudyFootnoteStandardsForm
          v-else-if="createFootnoteOption === 'standards'"
          :existing-names="existingFootnoteNames"
          :referenced-items="newFootnoteItems"
          :layout="layout"
          data-cy="standards-footnote-form"
          @cancel="createFootnoteOption = null"
          @created="onFootnoteCreated"
        />
        <StudyFootnoteStudiesForm
          v-else-if="createFootnoteOption === 'studies'"
          :existing-names="existingFootnoteNames"
          :referenced-items="newFootnoteItems"
          :layout="layout"
          data-cy="studies-footnote-form"
          @cancel="createFootnoteOption = null"
          @created="onFootnoteCreated"
          @partially-created="onFootnotesPartiallyCreated"
        />
        <StudyFootnoteEditorForm
          v-else-if="createFootnoteOption === 'scratch'"
          :referenced-items="newFootnoteItems"
          :layout="layout"
          data-cy="scratch-footnote-form"
          @cancel="createFootnoteOption = null"
          @created="onFootnoteCreated"
        />
        <StudyFootnoteEditorForm
          v-else-if="editedFootnote"
          :study-footnote="editedFootnote"
          @cancel="editedFootnote = null"
          @updated="onFootnoteUpdated"
        />
        <div v-else-if="linkingFootnote">
          <div class="d-flex align-center pa-2">
            <v-btn
              icon="mdi-arrow-left"
              color="secondary"
              size="small"
              variant="text"
              @click="linkingFootnote = null"
            />
            <span class="font-weight-medium ml-1">
              {{ $t('ProtocolFlowchart.link_footnote') }}
            </span>
          </div>
          <v-divider />
          <div class="pa-4">
            <v-alert
              variant="tonal"
              color="nnBaseBlue"
              icon="mdi-cursor-default-click-outline"
            >
              <i18n-t
                keypath="ProtocolFlowchart.link_footnote_hint"
                tag="div"
                class="text-break"
              >
                <template #name>
                  <strong>{{ linkingFootnote.name }}</strong>
                </template>
              </i18n-t>
              <div class="mt-1 text-medium-emphasis">
                {{ $t('ProtocolFlowchart.link_footnote_remove_hint') }}
              </div>
            </v-alert>
          </div>
        </div>
        <v-list v-else-if="!footnotes.length">
          <v-list-item>
            <v-list-item-title>
              {{ $t('ProtocolFlowchart.no_footnotes') }}
            </v-list-item-title>
          </v-list-item>
        </v-list>
        <v-expansion-panels v-else v-model="expandedFootnoteUid">
          <div
            v-for="footnote in footnotes"
            :key="footnote.uid"
            :ref="(el) => setRowElement(footnote.uid, el)"
            class="footnote-row"
            :class="{
              'hover-link':
                hoveredAction.uid === footnote.uid &&
                hoveredAction.action === 'link',
              'hover-edit':
                hoveredAction.uid === footnote.uid &&
                hoveredAction.action === 'edit',
              'hover-delete':
                hoveredAction.uid === footnote.uid &&
                hoveredAction.action === 'delete',
              'hide-text': textHiddenUids.has(footnote.uid),
            }"
          >
            <v-expansion-panel :value="footnote.uid">
              <v-expansion-panel-title
                v-slot="{ expanded }"
                class="footnote-title"
                :style="
                  lockedTitleHeights[footnote.uid]
                    ? { minHeight: `${lockedTitleHeights[footnote.uid]}px` }
                    : undefined
                "
                hide-actions
              >
                <span class="footnote-title-text">
                  <span class="font-weight-bold mr-2">{{
                    footnote.letter
                  }}</span>
                  <span
                    class="footnote-name"
                    @mouseenter="checkNameTruncated($event, footnote.uid)"
                  >
                    {{ footnote.name }}
                    <v-tooltip
                      activator="parent"
                      data-cy="footnote-name-tooltip"
                      location="top"
                      max-width="400"
                      open-delay="300"
                      :disabled="truncatedNameUid !== footnote.uid"
                    >
                      {{ footnote.name }}
                    </v-tooltip>
                  </span>
                  <span
                    v-if="footnote.isUnlinked || footnote.hasUnfilledParameters"
                    class="footnote-unlinked-icon ml-2"
                  >
                    <v-icon
                      color="error"
                      icon="mdi-alert-circle-outline"
                      size="large"
                    />
                    <v-tooltip activator="parent" location="top">
                      <div v-if="footnote.hasUnfilledParameters">
                        {{
                          $t('ProtocolFlowchart.footnote_parameters_not_set')
                        }}
                      </div>
                      <div v-if="footnote.isUnlinked">
                        {{ $t('ProtocolFlowchart.no_footnote_items') }}
                      </div>
                    </v-tooltip>
                  </span>
                </span>
                <v-icon
                  class="footnote-chevron mx-2"
                  :icon="expanded ? '$collapse' : '$expand'"
                />
                <template v-if="editable">
                  <span
                    class="footnote-action-panel footnote-link-panel"
                    @mouseenter="setHoveredAction(footnote.uid, 'link')"
                    @mouseleave="setHoveredAction(null, null)"
                    @click.stop="linkFootnoteItems(footnote)"
                  >
                    <v-icon class="footnote-action-icon"
                      >mdi-link-variant-plus</v-icon
                    >
                    <span class="footnote-action-label">
                      {{ $t('ProtocolFlowchart.link_footnote') }}
                    </span>
                  </span>
                  <span
                    class="footnote-action-panel footnote-edit-panel"
                    @mouseenter="setHoveredAction(footnote.uid, 'edit')"
                    @mouseleave="setHoveredAction(null, null)"
                    @click.stop="editFootnote(footnote)"
                  >
                    <v-icon class="footnote-action-icon">
                      mdi-pencil-outline
                    </v-icon>
                    <span class="footnote-action-label">
                      {{ $t('ProtocolFlowchart.edit_footnote') }}
                    </span>
                  </span>
                  <span
                    class="footnote-action-panel footnote-delete-panel"
                    @mouseenter="setHoveredAction(footnote.uid, 'delete')"
                    @mouseleave="setHoveredAction(null, null)"
                    @click.stop="deleteFootnote(footnote)"
                  >
                    <v-icon class="footnote-action-icon">
                      mdi-delete-outline
                    </v-icon>
                    <span class="footnote-action-label">
                      {{ $t('ProtocolFlowchart.remove_footnote') }}
                    </span>
                  </span>
                </template>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <div v-if="!footnote.referencedItems.length">
                  {{ $t('ProtocolFlowchart.no_footnote_items') }}
                </div>
                <div v-else class="d-flex flex-wrap ga-1">
                  <v-chip
                    v-for="{ item, label } in footnote.referencedItemChips"
                    :key="`${item.item_uid}-${Boolean(item.via_propagated_cell)}`"
                    size="small"
                    color="nnBaseBlue"
                    :closable="editable"
                    @click="scrollToItem(item)"
                    @click:close="removeFootnoteItem(footnote, item)"
                  >
                    <span>
                      {{ truncateChipLabel(label) }}
                      <v-tooltip
                        v-if="label.length > CHIP_LABEL_MAX_LENGTH"
                        activator="parent"
                        location="top"
                        max-width="400"
                        open-delay="300"
                      >
                        {{ label }}
                      </v-tooltip>
                    </span>
                  </v-chip>
                </div>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </div>
        </v-expansion-panels>
      </div>
    </v-card>
  </v-menu>
  <ConfirmDialog ref="confirm" />
</template>

<script setup>
import { computed, inject, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useFootnotesStore } from '@/stores/studies-footnotes'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import {
  addReferencedItems,
  assignFootnoteLetters,
  enqueueFootnoteTask,
  getFootnoteNamePlain,
  isReferenceableRef,
  isSameReferencedItem,
  normalizeFootnoteText,
  referencedItemMatchesRef,
  toReferencedItem,
} from '@/utils/soaFootnotes'
import study from '@/api/study'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import StudyFootnoteEditorForm from '@/components/studies/StudyFootnoteEditorForm.vue'
import StudyFootnoteStandardsForm from '@/components/studies/StudyFootnoteStandardsForm.vue'
import StudyFootnoteStudiesForm from '@/components/studies/StudyFootnoteStudiesForm.vue'

const props = defineProps({
  // SoA layout whose footnotes are managed; new footnotes are bound to it.
  layout: {
    type: String,
    required: true,
  },
  footnoteLetters: {
    type: Object,
    default: () => ({}),
  },
  // Without it the footnotes can only be inspected: no create, edit, link or delete.
  editable: {
    type: Boolean,
    required: true,
  },
})
const emit = defineEmits([
  'footnote-expanded',
  'footnotes-changed',
  'linking-changed',
  'scroll-to-item',
])

const footnotesStore = useFootnotesStore()
const studiesGeneralStore = useStudiesGeneralStore()
const { t } = useI18n()
const notificationHub = inject('notificationHub')

const open = ref(false)
const expandedFootnoteUid = ref(null)
const creatingFootnote = ref(false)
const createFootnoteOption = ref(null)
// One entry per protocol cell picked for the new footnote, each a list of referenced items.
const newFootnoteCells = ref([])
const newFootnoteItems = computed(() => newFootnoteCells.value.flat())
const confirm = ref()
const editedFootnote = ref(null)
const linkingFootnote = ref(null)
const hoveredAction = ref({ uid: null, action: null })
let hoverDebounceTimer = null
const textHiddenUids = ref(new Set())
const textRevealTimers = new Map()

// Keeps a row's title hidden until its action panel has collapsed (matches the
// flex-basis transition in the styles), tracked per row so the height does not jump.
const ACTION_COLLAPSE_MS = 300

// While the text is hidden, the title keeps the height it had with the full
// (possibly multi-line) name, so the row does not shrink on hover.
const lockedTitleHeights = ref({})
const rowElements = new Map()

function setRowElement(uid, element) {
  if (element) {
    rowElements.set(uid, element)
  } else {
    rowElements.delete(uid)
  }
}

watch(
  () => hoveredAction.value.uid,
  (uid, previousUid) => {
    if (uid) {
      clearTimeout(textRevealTimers.get(uid))
      if (!textHiddenUids.value.has(uid)) {
        const title = rowElements.get(uid)?.querySelector('.footnote-title')
        if (title) {
          lockedTitleHeights.value[uid] = title.offsetHeight
        }
      }
      textHiddenUids.value.add(uid)
    }
    if (previousUid) {
      textRevealTimers.set(
        previousUid,
        setTimeout(() => {
          textHiddenUids.value.delete(previousUid)
          delete lockedTitleHeights.value[previousUid]
        }, ACTION_COLLAPSE_MS)
      )
    }
  }
)

onBeforeUnmount(() => {
  clearTimeout(hoverDebounceTimer)
  textRevealTimers.forEach((timer) => clearTimeout(timer))
})

const createFootnoteOptions = [
  {
    key: 'standards',
    labelKey: 'ProtocolFlowchart.select_from_standards',
    icon: 'mdi-bookshelf',
  },
  {
    key: 'studies',
    labelKey: 'ProtocolFlowchart.select_from_studies',
    icon: 'mdi-stethoscope',
  },
  {
    key: 'scratch',
    labelKey: 'ProtocolFlowchart.create_from_scratch',
    icon: 'mdi-pencil-plus-outline',
  },
]

const truncatedNameUid = ref(null)

function checkNameTruncated(event, uid) {
  const { scrollHeight, clientHeight } = event.currentTarget
  truncatedNameUid.value = scrollHeight > clientHeight ? uid : null
}

function setHoveredAction(uid, action) {
  clearTimeout(hoverDebounceTimer)
  hoverDebounceTimer = setTimeout(() => {
    hoveredAction.value = { uid, action }
  }, 100)
}

// Letters run "a" to "y", then "z1", "z2", ... (dataFormating.footnoteSymbol
// and the backend's enumerate_letters), so shorter letters come first to keep
// "z2" before "z10". Footnotes without a letter go last.
function compareFootnoteLetters(letterA, letterB) {
  if (!letterA || !letterB) {
    return Number(!letterA) - Number(!letterB)
  }
  return letterA.length - letterB.length || letterA.localeCompare(letterB)
}

const CHIP_LABEL_MAX_LENGTH = 30

function truncateChipLabel(label) {
  return label.length > CHIP_LABEL_MAX_LENGTH
    ? `${label.slice(0, CHIP_LABEL_MAX_LENGTH)}…`
    : label
}

function getReferencedItemChips(referencedItems) {
  return referencedItems.map((item) => {
    if (item.item_type === 'StudyActivitySchedule') {
      return {
        item,
        label: t('ProtocolFlowchart.schedule_label', {
          name: item.item_name,
        }),
      }
    }
    return { item, label: item.item_name || item.item_uid }
  })
}

// Sorted here, not after a fetch, so the order also holds when the letters are
// recomputed. `map` returns a new array, so sorting leaves the store untouched.
const footnotes = computed(() => {
  const letters = assignFootnoteLetters(
    footnotesStore.studyFootnotes,
    props.footnoteLetters
  )
  return footnotesStore.studyFootnotes
    .map((footnote) => {
      const referencedItems = footnote.referenced_items ?? []
      return {
        uid: footnote.uid,
        letter: letters.get(footnote.uid),
        name: getFootnoteNamePlain(footnote),
        referencedItems,
        referencedItemChips: getReferencedItemChips(referencedItems),
        isUnlinked: !referencedItems.length,
        // A template without a footnote instance has no parameter values chosen
        hasUnfilledParameters:
          !footnote.footnote && footnote.template?.parameters?.length > 0,
      }
    })
    .sort((a, b) => compareFootnoteLetters(a.letter, b.letter))
})

const existingFootnoteNames = computed(
  () =>
    new Set(
      footnotes.value.map((footnote) => normalizeFootnoteText(footnote.name))
    )
)

function resetFootnoteFlow() {
  creatingFootnote.value = false
  createFootnoteOption.value = null
  editedFootnote.value = null
  linkingFootnote.value = null
}

watch(open, (isOpen) => {
  if (isOpen) {
    fetchFootnotes()
  } else {
    expandedFootnoteUid.value = null
    resetFootnoteFlow()
  }
})

// A create, edit or link flow must not outlive the right to edit (e.g. a version gets selected).
watch(
  () => props.editable,
  (editable) => {
    if (!editable) {
      resetFootnoteFlow()
    }
  }
)

watch(
  () => props.layout,
  () => {
    open.value = false
  }
)

watch(creatingFootnote, (creating) => {
  if (!creating) {
    newFootnoteCells.value = []
  }
})

// While either is active, clicks on protocol cells pick the cells to link.
const isPickingCells = computed(() =>
  Boolean(linkingFootnote.value || creatingFootnote.value)
)
watch(isPickingCells, (picking) => {
  emit('linking-changed', picking)
})

// What the protocol highlights: the cells picked for a new footnote, otherwise
// the cells of the expanded footnote.
const highlightedItems = computed(() => {
  if (creatingFootnote.value) {
    return newFootnoteItems.value
  }
  if (!expandedFootnoteUid.value) {
    return null
  }
  return (
    footnotes.value.find((item) => item.uid === expandedFootnoteUid.value)
      ?.referencedItems ?? []
  )
})
watch(highlightedItems, (items) => {
  emit('footnote-expanded', items)
})

function fetchFootnotes() {
  return footnotesStore.fetchStudyFootnotes({
    studyUid: studiesGeneralStore.selectedStudy.uid,
    page_size: 0,
    layout: props.layout,
  })
}

function removeFootnoteItem(footnote, item) {
  if (!props.editable) {
    return
  }
  return enqueueFootnoteTask(async () => {
    // Read from the store once the task runs, so it includes earlier queued changes.
    const current = footnotesStore.studyFootnotes.find(
      (existing) => existing.uid === footnote.uid
    )
    if (!current) {
      return
    }
    await study.updateStudyFootnote(
      studiesGeneralStore.selectedStudy.uid,
      footnote.uid,
      {
        referenced_items: current.referenced_items.filter(
          (existing) => !isSameReferencedItem(existing, item)
        ),
      }
    )
    await fetchFootnotes()
    emit('footnotes-changed')
    // Failed requests are already reported by the Axios interceptor.
  }).catch(() => {})
}

function scrollToItem(item) {
  emit('scroll-to-item', item)
}

// The list unmounts under the cursor, so its mouseleave never resets the hover.
function resetHoveredAction() {
  clearTimeout(hoverDebounceTimer)
  hoveredAction.value = { uid: null, action: null }
}

function linkFootnoteItems(footnote) {
  resetHoveredAction()
  // Expanding the footnote highlights the cells it is already linked to.
  expandedFootnoteUid.value = footnote.uid
  linkingFootnote.value = { uid: footnote.uid, name: footnote.name }
}

// Clicks come in faster than the requests finish, and each request builds its
// list of referenced items from the store, so they have to run one at a time.
function toggleCellRefs(cellRefs) {
  if (!props.editable) {
    return
  }
  if (creatingFootnote.value) {
    toggleNewFootnoteCell(cellRefs)
    return
  }
  return (
    enqueueFootnoteTask(() => toggleCellRefsOnLinkingFootnote(cellRefs))
      // Failed requests are already reported by the Axios interceptor.
      .catch(() => {})
  )
}

// A cell the footnote is already linked to is unlinked, any other one is linked.
async function toggleCellRefsOnLinkingFootnote(cellRefs) {
  const footnote = footnotesStore.studyFootnotes.find(
    (item) => item.uid === linkingFootnote.value?.uid
  )
  if (!footnote) {
    return
  }
  const isLinkedToCell = (item) =>
    cellRefs.some((cellRef) => referencedItemMatchesRef(item, cellRef))
  let referencedItems
  if (footnote.referenced_items.some(isLinkedToCell)) {
    referencedItems = footnote.referenced_items.filter(
      (item) => !isLinkedToCell(item)
    )
  } else {
    const newItems = cellRefs.filter(isReferenceableRef).map(toReferencedItem)
    if (!newItems.length) {
      return
    }
    referencedItems = addReferencedItems(footnote.referenced_items, newItems)
  }
  await study.updateStudyFootnote(
    studiesGeneralStore.selectedStudy.uid,
    footnote.uid,
    { referenced_items: referencedItems }
  )
  await fetchFootnotes()
  emit('footnotes-changed')
}

// A cell that is already picked is dropped, any other one is picked.
function toggleNewFootnoteCell(cellRefs) {
  const isPickedCell = (items) =>
    items.some((item) =>
      cellRefs.some((cellRef) => referencedItemMatchesRef(item, cellRef))
    )
  if (newFootnoteCells.value.some(isPickedCell)) {
    newFootnoteCells.value = newFootnoteCells.value.filter(
      (items) => !isPickedCell(items)
    )
    return
  }
  const items = cellRefs.filter(isReferenceableRef).map(toReferencedItem)
  if (items.length) {
    newFootnoteCells.value = [...newFootnoteCells.value, items]
  }
}

function openNewFootnote(cellRefs = []) {
  if (!props.editable) {
    return
  }
  resetHoveredAction()
  editedFootnote.value = null
  linkingFootnote.value = null
  expandedFootnoteUid.value = null
  const items = cellRefs.filter(isReferenceableRef).map(toReferencedItem)
  newFootnoteCells.value = items.length ? [items] : []
  creatingFootnote.value = true
  open.value = true
}

defineExpose({ toggleCellRefs, openNewFootnote })

function editFootnote(footnote) {
  resetHoveredAction()
  editedFootnote.value = footnotesStore.studyFootnotes.find(
    (item) => item.uid === footnote.uid
  )
}

async function onFootnoteUpdated() {
  editedFootnote.value = null
  notificationHub.add({ msg: t('StudyFootnoteEditForm.update_success') })
  await fetchFootnotes()
  emit('footnotes-changed')
}

async function deleteFootnote(footnote) {
  const options = {
    type: 'warning',
    agreeLabel: t('StudyFootnoteTable.remove'),
    cancelLabel: t('StudyFootnoteTable.keep'),
    title: t('StudyFootnoteTable.remove'),
  }
  if (
    await confirm.value.openHtml(
      t('StudyFootnoteTable.confirm_delete', { footnote: footnote.name }),
      options
    )
  ) {
    await footnotesStore.deleteStudyFootnote(
      studiesGeneralStore.selectedStudy.uid,
      footnote.uid
    )
    await fetchFootnotes()
    notificationHub.add({
      msg: t('StudyFootnoteTable.delete_footnote_success'),
    })
    emit('footnotes-changed')
  }
}

async function onFootnoteCreated() {
  creatingFootnote.value = false
  createFootnoteOption.value = null
  notificationHub.add({ msg: t('StudyFootnoteForm.footnote_added') })
  await fetchFootnotes()
  emit('footnotes-changed')
}

// Keeps the form open: the refreshed names mark the copied footnotes as added.
async function onFootnotesPartiallyCreated() {
  await fetchFootnotes()
  emit('footnotes-changed')
}
</script>

<style scoped lang="scss">
// Only the body scrolls, so the draggable title stays in place.
.footnotes-body {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
}

.footnote-row {
  flex: 1 0 100%;
  max-width: 100%;

  & + & {
    margin-top: 4px;
  }
}

// The action buttons live in the title, so they keep the collapsed title's
// height when the panel expands.
.footnote-title {
  padding: 0 0 0 24px;
  overflow: hidden;
}

// position: relative keeps the text above the title's absolutely positioned
// overlay, which would otherwise swallow hover events (needed for the tooltip).
.footnote-title-text {
  position: relative;
  display: flex;
  flex: 1 1 0;
  align-items: center;
  min-width: 0;
  padding-block: 0.8rem;
}

.footnote-name {
  display: -webkit-box;
  min-width: 0;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  line-clamp: 3;
}

.footnote-chevron {
  flex: none;
}

.footnote-unlinked-icon {
  display: inline-flex;
  flex: none;
  align-items: center;
}

.footnote-action-panel {
  position: relative;
  display: flex;
  flex: 0 0 12%;
  align-self: stretch;
  align-items: center;
  overflow: hidden;
  color: rgb(var(--v-theme-nnWhite));
  cursor: pointer;
  transition: flex-basis 0.3s ease;
}

// Auto margins centre the icon + label without pushing the icon off the start
// edge while the panel is still expanding (justify-content: center would).
.footnote-action-icon {
  flex: none;
  margin-left: auto;
}

.footnote-action-label {
  max-width: 0;
  margin-right: auto;
  overflow: hidden;
  white-space: nowrap;
  opacity: 0;
  transition:
    max-width 0.3s ease,
    margin-left 0.3s ease,
    opacity 0.2s ease 0.1s;
}

.footnote-link-panel {
  background-color: rgb(var(--v-theme-green));
}

.footnote-edit-panel {
  background-color: rgb(var(--v-theme-nnBaseBlue));
}

.footnote-delete-panel {
  background-color: rgb(var(--v-theme-error));
}

.footnote-row.hide-text {
  // Vuetify animates the title's min-height; the locked height must apply at once.
  .footnote-title {
    transition: none;
  }

  .footnote-name,
  .footnote-unlinked-icon,
  .footnote-chevron {
    display: none;
  }
}

.footnote-row.hover-link .footnote-link-panel,
.footnote-row.hover-edit .footnote-edit-panel,
.footnote-row.hover-delete .footnote-delete-panel {
  flex-basis: 60%;

  .footnote-action-label {
    max-width: 12rem;
    margin-left: 8px;
    opacity: 1;
  }
}

.create-footnote-option {
  transition: background-color 0.15s ease;

  &:not(:last-child) {
    border-bottom: 1px solid
      rgba(var(--v-border-color), var(--v-border-opacity));
  }

  &:hover,
  &:focus-visible {
    background-color: rgba(var(--v-theme-nnBaseBlue), 0.06);
  }

  &:focus-visible {
    outline: 2px solid rgb(var(--v-theme-nnBaseBlue));
    outline-offset: -2px;
  }
}

.create-footnote-option-title {
  font-size: 1rem !important;
  white-space: normal;
  overflow-wrap: anywhere;
}
</style>
