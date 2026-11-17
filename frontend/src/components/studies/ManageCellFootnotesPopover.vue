<template>
  <v-card
    class="manage-cell-footnotes-popover"
    data-draggable-card
    elevation="4"
  >
    <div
      class="panel-header d-flex justify-space-between align-center cursor-grab"
      data-drag-handle
    >
      <span class="text-subtitle-2 font-weight-bold">
        {{ $t('ProtocolFlowchart.manage_footnotes') }}
      </span>
      <v-btn
        icon
        size="x-small"
        variant="text"
        density="compact"
        data-cy="close-footnotes-button"
        @click="$emit('close')"
      >
        <v-icon size="16">mdi-close</v-icon>
      </v-btn>
    </div>
    <div class="panel-body px-4 py-5">
      <div v-if="selectedFootnotes.length" class="d-flex flex-wrap ga-1 mb-6">
        <v-chip
          v-for="footnote in selectedFootnotes"
          :key="footnote.uid"
          size="small"
          color="nnBaseBlue"
          data-cy="footnote-chip"
          closable
          @click:close="removeFootnoteFromElement(footnote.uid)"
        >
          <span class="font-weight-bold mr-1">{{ footnote.letter }}</span>
          <span
            class="chip-name"
            @mouseenter="checkChipNameTruncated($event, footnote.uid)"
          >
            {{ footnote.name }}
            <v-tooltip
              activator="parent"
              location="top"
              max-width="400"
              open-delay="300"
              :disabled="truncatedChipUid !== footnote.uid"
            >
              {{ footnote.name }}
            </v-tooltip>
          </span>
        </v-chip>
      </div>
      <v-autocomplete
        v-model="selectedFootnoteUid"
        v-model:search="footnoteSearch"
        data-cy="footnote-autocomplete"
        :items="footnoteOptions"
        :item-title="(item) => `${item.letter}. ${item.name}`"
        item-value="uid"
        :label="$t('ProtocolFlowchart.footnote_add')"
        hide-details
      >
        <template #prepend-item>
          <v-list-item
            data-cy="create-footnote-dropdown-option"
            link
            @click="$emit('create-footnote')"
          >
            <v-list-item-title class="text-nnBaseBlue font-weight-bold">
              {{ $t('ProtocolFlowchart.create_new_footnote') }}
            </v-list-item-title>
          </v-list-item>
          <v-divider class="mt-1" />
        </template>
        <template #item="{ internalItem: item, props: itemProps }">
          <v-list-item v-bind="itemProps">
            <template #title>
              <NNParameterHighlighter
                data-cy="footnote-name-tooltip"
                :name="item.raw.name"
                :show-prefix-and-postfix="false"
                :tooltip="
                  getVisibleLength(item.raw.name) > FOOTNOTE_NAME_MAX_LENGTH
                "
                :tooltip-length="FOOTNOTE_NAME_MAX_LENGTH"
              />
            </template>
          </v-list-item>
        </template>
      </v-autocomplete>
    </div>
  </v-card>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useFootnotesStore } from '@/stores/studies-footnotes'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import study from '@/api/study'
import {
  addReferencedItems,
  assignFootnoteLetters,
  enqueueFootnoteTask,
  getFootnoteNamePlain,
  isReferenceableRef,
  referencedItemMatchesRef,
  toReferencedItem,
} from '@/utils/soaFootnotes'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter.vue'

const props = defineProps({
  cellRefs: {
    type: Array,
    required: true,
  },
  layout: {
    type: String,
    required: true,
  },
  footnoteLetters: {
    type: Object,
    default: () => ({}),
  },
})
const emit = defineEmits(['close', 'create-footnote', 'footnotes-changed'])

const footnotesStore = useFootnotesStore()
const studiesGeneralStore = useStudiesGeneralStore()

const selectedFootnoteUid = ref(null)
const footnoteSearch = ref('')

const FOOTNOTE_NAME_MAX_LENGTH = 60

const truncatedChipUid = ref(null)

function checkChipNameTruncated(event, uid) {
  const { scrollWidth, clientWidth } = event.currentTarget
  truncatedChipUid.value = scrollWidth > clientWidth ? uid : null
}

// Length of what the highlighter shows: no HTML tags and no parameter brackets.
function getVisibleLength(name) {
  return name.replace(/[<>]/g, '').replace(/[[\]]/g, '').length
}

function referencesAnyOf(cellRefs) {
  return (item) =>
    cellRefs.some((cellRef) => referencedItemMatchesRef(item, cellRef))
}

const selectedFootnoteUids = computed(
  () =>
    new Set(
      footnotesStore.studyFootnotes
        .filter((footnote) =>
          footnote.referenced_items.some(referencesAnyOf(props.cellRefs))
        )
        .map((footnote) => footnote.uid)
    )
)

const letterByUid = computed(() =>
  assignFootnoteLetters(footnotesStore.studyFootnotes, props.footnoteLetters)
)

function toFootnoteItem(footnote, name) {
  return {
    uid: footnote.uid,
    letter: letterByUid.value.get(footnote.uid),
    name,
  }
}

const footnoteOptions = computed(() =>
  footnotesStore.studyFootnotes
    .filter((footnote) => !selectedFootnoteUids.value.has(footnote.uid))
    .map((footnote) =>
      toFootnoteItem(
        footnote,
        footnote.template?.name ?? footnote.footnote?.name ?? ''
      )
    )
)

const selectedFootnotes = computed(() =>
  footnotesStore.studyFootnotes
    .filter((footnote) => selectedFootnoteUids.value.has(footnote.uid))
    .map((footnote) => toFootnoteItem(footnote, getFootnoteNamePlain(footnote)))
)

// The cell, layout and study are read when the user acts: by the time a queued request
// runs, the panel may show another cell or be gone. The footnote itself is looked up
// only inside the queued task, so it already includes the previous request's result.
function getActionContext() {
  return {
    cellRefs: props.cellRefs,
    layout: props.layout,
    studyUid: studiesGeneralStore.selectedStudy.uid,
  }
}

watch(selectedFootnoteUid, async (footnoteUid) => {
  if (!footnoteUid) {
    return
  }
  const { cellRefs, layout, studyUid } = getActionContext()
  const newItems = cellRefs.filter(isReferenceableRef).map(toReferencedItem)
  selectedFootnoteUid.value = null
  footnoteSearch.value = ''
  await enqueueFootnoteTask(async () => {
    const footnote = footnotesStore.studyFootnotes.find(
      (item) => item.uid === footnoteUid
    )
    if (!footnote) {
      return
    }
    await study.updateStudyFootnote(studyUid, footnoteUid, {
      referenced_items: addReferencedItems(footnote.referenced_items, newItems),
    })
    await fetchFootnotes(studyUid, layout)
    emit('footnotes-changed')
    // Failed requests are already reported by the Axios interceptor.
  }).catch(() => {})
})

async function removeFootnoteFromElement(footnoteUid) {
  const { cellRefs, layout, studyUid } = getActionContext()
  await enqueueFootnoteTask(async () => {
    const footnote = footnotesStore.studyFootnotes.find(
      (item) => item.uid === footnoteUid
    )
    if (!footnote) {
      return
    }
    // Only detach from this cell: a propagated checkmark keeps the hidden activities' own footnotes.
    // A via_propagated_cell reference is one reference shown on both the propagated checkmark and
    // the item's own cell, so unlinking it from either cell removes it from both.
    const isLinkedToCell = referencesAnyOf(cellRefs)
    const remainingItems = footnote.referenced_items.filter(
      (item) => !isLinkedToCell(item)
    )
    if (remainingItems.length === footnote.referenced_items.length) {
      return
    }
    await study.updateStudyFootnote(studyUid, footnoteUid, {
      referenced_items: remainingItems,
    })
    await fetchFootnotes(studyUid, layout)
    emit('footnotes-changed')
  }).catch(() => {})
}

function fetchFootnotes(
  studyUid = studiesGeneralStore.selectedStudy.uid,
  layout = props.layout
) {
  return footnotesStore.fetchStudyFootnotes({
    studyUid,
    page_size: 0,
    layout,
  })
}

// Queued so that it cannot overwrite the store with data from before a save still running.
onMounted(() => {
  enqueueFootnoteTask(() => fetchFootnotes()).catch(() => {})
})
</script>

<style scoped lang="scss">
.manage-cell-footnotes-popover {
  position: absolute;
  z-index: 10;
  width: max-content;
  min-width: 360px;
  max-width: min(560px, calc(100vw - 32px));
  border-radius: 8px;
  overflow: hidden;
}

.panel-header {
  padding: 10px 16px;
  background-color: rgba(var(--v-theme-nnBaseBlue), 0.08);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.12);
}

.panel-body {
  :deep(.v-chip__content) {
    min-width: 0;
  }
}

.chip-name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
