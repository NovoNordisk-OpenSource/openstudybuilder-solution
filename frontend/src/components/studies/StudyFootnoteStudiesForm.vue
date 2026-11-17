<template>
  <div>
    <div class="d-flex align-center pa-2">
      <v-btn
        icon="mdi-arrow-left"
        data-cy="footnote-studies-back"
        color="secondary"
        size="small"
        variant="text"
        :disabled="adding"
        @click="emit('cancel')"
      />
      <span class="font-weight-medium ml-1">
        {{ $t('ProtocolFlowchart.select_from_studies') }}
      </span>
    </div>
    <v-divider />
    <div class="px-4 pt-3">
      <StudySelectorField
        v-model="sourceStudy"
        data-cy="footnote-studies-source-study"
        :data="studies"
        :loading="studiesLoading"
      />
    </div>
    <SelectMenuSearch
      v-if="sourceStudy"
      v-model="search"
      :placeholder="$t('_global.search')"
      data-cy="footnote-studies-search"
      class="px-4"
    />
    <template v-if="!loading && selectableRows.length">
      <v-list density="compact" class="py-0 px-4">
        <v-list-item
          :disabled="adding"
          data-cy="footnote-studies-select-all"
          @click="toggleAll"
        >
          <template #prepend>
            <v-list-item-action start>
              <v-checkbox-btn
                :model-value="allSelected"
                :indeterminate="someSelected"
                readonly
                tabindex="-1"
              />
            </v-list-item-action>
          </template>
          <v-list-item-title class="font-weight-medium">
            {{ $t('_global.select_all') }}
          </v-list-item-title>
        </v-list-item>
      </v-list>
      <v-divider />
    </template>
    <div class="studies-list px-4">
      <v-progress-linear v-if="loading" indeterminate color="nnBaseBlue" />
      <v-list
        v-else-if="rows.length"
        density="compact"
        data-cy="footnote-studies-list"
      >
        <v-list-item
          v-for="{ item, added } in rows"
          :key="item.footnote.uid"
          :disabled="added || adding"
          @click="toggle(item)"
        >
          <template #prepend>
            <v-list-item-action start>
              <v-checkbox-btn
                :model-value="added || selectedUids.has(item.footnote.uid)"
                readonly
                tabindex="-1"
              />
            </v-list-item-action>
          </template>
          <NNParameterHighlighter
            :name="item.footnote.name"
            :show-prefix-and-postfix="false"
            :tooltip="false"
          />
          <template v-if="added" #append>
            <span class="text-body-small ml-2">
              {{ $t('ProtocolFlowchart.standard_footnote_added') }}
            </span>
          </template>
        </v-list-item>
      </v-list>
      <div v-else class="studies-empty text-center text-medium-emphasis pa-4">
        {{ emptyMessage }}
      </div>
    </div>
    <v-divider />
    <div class="d-flex justify-end ga-2 pa-3">
      <v-btn
        variant="outlined"
        :disabled="adding"
        data-cy="cancel-footnote-studies"
        @click="emit('cancel')"
      >
        {{ $t('_global.cancel') }}
      </v-btn>
      <v-btn
        color="secondary"
        variant="flat"
        data-cy="submit-footnote-studies"
        :disabled="!chosenFootnotes.length"
        :loading="adding"
        @click="submit"
      >
        {{
          chosenFootnotes.length
            ? $t('ProtocolFlowchart.add_selected_footnotes', {
                count: chosenFootnotes.length,
              })
            : $t('_global.add')
        }}
      </v-btn>
    </div>
  </div>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useFootnotesStore } from '@/stores/studies-footnotes'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import study from '@/api/study'
import statuses from '@/constants/statuses'
import { normalizeFootnoteText } from '@/utils/soaFootnotes'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter.vue'
import SelectMenuSearch from '@/components/tools/SelectMenuSearch.vue'
import StudySelectorField from '@/components/studies/StudySelectorField.vue'

const props = defineProps({
  existingNames: {
    type: Set,
    required: true,
  },
  // Items the copied footnotes are assigned to, in the layout given by `layout`.
  referencedItems: {
    type: Array,
    default: () => [],
  },
  layout: {
    type: String,
    default: null,
  },
})
const emit = defineEmits(['cancel', 'created', 'partially-created'])

const { t } = useI18n()
const footnotesStore = useFootnotesStore()
const studiesGeneralStore = useStudiesGeneralStore()
const notificationHub = inject('notificationHub')

const studies = ref([])
const studiesLoading = ref(true)
const sourceStudy = ref(null)
const search = ref('')
const studyFootnotes = ref([])
const selectedUids = ref(new Set())
const loading = ref(false)
const adding = ref(false)
let latestRequest = 0

study
  .getSelectableStudies({ has_study_footnote: true })
  .then((resp) => {
    studies.value = resp.data.filter(
      (item) => item.uid !== studiesGeneralStore.selectedStudy.uid
    )
  })
  .finally(() => {
    studiesLoading.value = false
  })

function htmlToPlainText(value) {
  if (!value) return ''
  const doc = new DOMParser().parseFromString(value, 'text/html')
  return doc.body.textContent ?? ''
}

function plainText(item) {
  return item.footnote.name_plain ?? htmlToPlainText(item.footnote.name)
}

function isAdded(item) {
  return props.existingNames.has(normalizeFootnoteText(plainText(item)))
}

// Footnotes already in the study stay listed (so a search explains their absence)
// but sink below the ones that can still be picked.
const rows = computed(() => {
  const words = (search.value ?? '').toLowerCase().split(/\s+/).filter(Boolean)
  return studyFootnotes.value
    .filter((item) => {
      const text = plainText(item).replace(/[[\]]/g, '').toLowerCase()
      return words.every((word) => text.includes(word))
    })
    .map((item) => ({ item, added: isAdded(item) }))
    .sort((a, b) => a.added - b.added)
})

// "Select all" acts on what is currently listed, so it follows the search filter.
const selectableRows = computed(() => rows.value.filter(({ added }) => !added))

const selectedVisibleCount = computed(
  () =>
    selectableRows.value.filter(({ item }) =>
      selectedUids.value.has(item.footnote.uid)
    ).length
)

const allSelected = computed(
  () =>
    selectableRows.value.length > 0 &&
    selectedVisibleCount.value === selectableRows.value.length
)

const someSelected = computed(
  () => selectedVisibleCount.value > 0 && !allSelected.value
)

const chosenFootnotes = computed(() =>
  studyFootnotes.value.filter(
    (item) => selectedUids.value.has(item.footnote.uid) && !isAdded(item)
  )
)

const emptyMessage = computed(() => {
  if (!sourceStudy.value) {
    return t('ProtocolFlowchart.select_study_for_footnotes')
  }
  return studyFootnotes.value.length
    ? t('ProtocolFlowchart.no_matching_study_footnotes')
    : t('ProtocolFlowchart.no_study_footnotes')
})

async function fetchStudyFootnotes(selected) {
  const request = ++latestRequest
  studyFootnotes.value = []
  selectedUids.value = new Set()
  search.value = ''
  if (!selected) {
    loading.value = false
    return
  }
  loading.value = true
  try {
    const resp = await study.getAllStudyFootnotes({
      page_size: 0,
      ...(props.layout ? { layout: props.layout } : {}),
      filters: {
        footnote_template: { v: [] },
        'footnote.status': { v: [statuses.FINAL] },
        study_uid: { v: [selected.uid] },
      },
    })
    if (request === latestRequest) {
      studyFootnotes.value = resp.data.items.filter((item) => item.footnote)
    }
  } finally {
    if (request === latestRequest) {
      loading.value = false
    }
  }
}

watch(sourceStudy, fetchStudyFootnotes)

function toggle(item) {
  const selected = new Set(selectedUids.value)
  if (selected.has(item.footnote.uid)) {
    selected.delete(item.footnote.uid)
  } else {
    selected.add(item.footnote.uid)
  }
  selectedUids.value = selected
}

function toggleAll() {
  const selected = new Set(selectedUids.value)
  const select = !allSelected.value
  for (const { item } of selectableRows.value) {
    if (select) {
      selected.add(item.footnote.uid)
    } else {
      selected.delete(item.footnote.uid)
    }
  }
  selectedUids.value = selected
}

// Copied one by one: the backend numbers new study footnotes sequentially.
async function submit() {
  if (adding.value || !chosenFootnotes.value.length) {
    return
  }
  const chosen = chosenFootnotes.value
  const copiedUids = new Set()
  notificationHub.clearErrors()
  adding.value = true
  try {
    for (const item of chosen) {
      await footnotesStore.selectFromStudyFootnote({
        studyUid: studiesGeneralStore.selectedStudy.uid,
        footnoteUid: item.footnote.uid,
        referencedItems: props.referencedItems,
        layout: props.layout,
      })
      copiedUids.add(item.footnote.uid)
    }
    emit('created')
  } catch {
    // Already reported by the Axios interceptor; the form stays open so the rest can be retried.
    if (copiedUids.size) {
      selectedUids.value = new Set(
        [...selectedUids.value].filter((uid) => !copiedUids.has(uid))
      )
      emit('partially-created')
    }
  } finally {
    adding.value = false
  }
}
</script>

<style scoped lang="scss">
.studies-list {
  display: flex;
  flex-direction: column;
  min-height: 160px;
  max-height: 360px;
  overflow-y: auto;
}

.studies-empty {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
}
</style>
