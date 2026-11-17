<template>
  <div ref="root" class="pa-4" data-cy="crf-compare">
    <v-btn-toggle
      v-model="mode"
      mandatory
      density="comfortable"
      color="primary"
      variant="outlined"
      divided
      class="mb-4"
      data-cy="crf-compare-mode"
      @update:model-value="resetSelection"
    >
      <v-btn value="form" data-cy="crf-compare-mode-form">
        {{ $t('CRFCompare.mode_forms') }}
      </v-btn>
      <v-btn value="collection" data-cy="crf-compare-mode-collection">
        {{ $t('CRFCompare.mode_collections') }}
      </v-btn>
    </v-btn-toggle>
    <div class="d-flex align-center ga-3 flex-nowrap">
      <CrfCompareSelector
        :key="`left-${mode}`"
        v-model="left"
        :mode="mode"
        :libraries="libraryNames"
        data-cy="crf-compare-left"
      />
      <v-btn
        icon="mdi-swap-horizontal"
        variant="text"
        :title="$t('CRFCompare.swap')"
        data-cy="crf-compare-swap"
        @click="swap"
      />
      <CrfCompareSelector
        :key="`right-${mode}`"
        v-model="right"
        :mode="mode"
        :libraries="libraryNames"
        data-cy="crf-compare-right"
      />
      <v-btn
        color="primary"
        rounded="xl"
        size="large"
        :disabled="!canCompare"
        :loading="loading"
        data-cy="crf-compare-run"
        class="flex-shrink-0"
        @click="runCompare"
      >
        {{ $t('CRFCompare.compare') }}
      </v-btn>
    </div>

    <v-divider class="my-4" />

    <template v-if="comparison">
      <div class="d-flex align-center ga-3 flex-wrap">
        <v-switch
          v-model="onlyDifferences"
          :label="$t('CRFCompare.show_only_differences')"
          data-cy="crf-compare-only-differences"
          hide-details
          inset
        />
        <v-chip-group v-model="selectedFields" multiple filter>
          <v-chip
            v-for="field in OPTIONAL_FIELDS"
            :key="field"
            :value="field"
            :data-cy="`crf-compare-filter-${field}`"
            size="small"
            variant="outlined"
          >
            {{ $t(`CRFCompare.filters.${field}`) }}
          </v-chip>
        </v-chip-group>
        <v-menu :close-on-content-click="false">
          <template #activator="{ props: menuProps }">
            <v-btn
              v-bind="menuProps"
              size="small"
              variant="outlined"
              rounded="xl"
              prepend-icon="mdi-playlist-check"
              data-cy="crf-compare-attributes"
            >
              {{ $t('CRFCompare.more_attributes') }}
              <template v-if="selectedAttributes.length > 0">
                ({{ selectedAttributes.length }})
              </template>
            </v-btn>
          </template>
          <v-card min-width="280" max-height="480" class="overflow-y-auto">
            <v-list density="compact">
              <template v-for="level in ATTRIBUTE_LEVELS" :key="level">
                <v-list-subheader>
                  {{ $t(`CRFCompare.attribute_level.${level}`) }}
                </v-list-subheader>
                <v-list-item v-for="def in ATTRIBUTES[level]" :key="def.name">
                  <v-checkbox
                    v-model="selectedAttributes"
                    :value="attributeKey(level, def.name)"
                    :label="$t(`CRFCompare.attributes.${def.name}`)"
                    :data-cy="`crf-compare-attribute-${attributeKey(level, def.name)}`"
                    density="compact"
                    hide-details
                  />
                </v-list-item>
              </template>
            </v-list>
          </v-card>
        </v-menu>
        <v-select
          v-model="language"
          :items="languages"
          :label="$t('CRFCompare.language')"
          data-cy="crf-compare-language"
          hide-details
          style="max-width: 110px"
        />
        <v-spacer />
      </div>

      <v-alert
        v-if="comparison.differences.length > 0"
        type="warning"
        variant="tonal"
        icon="mdi-information-outline"
        class="my-4"
        data-cy="crf-compare-banner"
      >
        <div class="d-flex align-center">
          <span>{{ $t('CRFCompare.banner_title') }}</span>
          <v-spacer />
          <v-btn
            :icon="bannerOpen ? 'mdi-chevron-up' : 'mdi-chevron-down'"
            size="small"
            variant="text"
            :title="
              bannerOpen ? $t('CRFCompare.collapse') : $t('CRFCompare.expand')
            "
            :aria-expanded="bannerOpen"
            data-cy="crf-compare-banner-toggle"
            @click="bannerOpen = !bannerOpen"
          />
        </div>
        <v-expand-transition>
          <ul v-show="bannerOpen" class="ml-4">
            <li
              v-for="difference in comparison.differences"
              :key="difference.id"
            >
              <a class="difference-link" @click="focusRow(difference.id)">
                {{ difference.name }}
              </a>
              <span v-if="difference.kind !== 'item'" class="text-caption">
                ({{
                  difference.kind === 'form'
                    ? $t('CRFCompare.crf_form')
                    : $t('CRFCompare.item_group')
                }})
              </span>
            </li>
          </ul>
        </v-expand-transition>
      </v-alert>
      <v-alert
        v-else
        type="success"
        variant="tonal"
        class="my-4"
        data-cy="crf-compare-banner"
      >
        {{
          mode === 'collection'
            ? $t('CRFCompare.no_differences_collections')
            : $t('CRFCompare.no_differences')
        }}
      </v-alert>

      <div class="crf-compare-row crf-compare-row--header mb-2">
        <div class="d-flex align-center ga-2">
          <v-icon
            :icon="
              mode === 'collection'
                ? 'mdi-alpha-c-circle'
                : 'mdi-alpha-f-circle'
            "
            color="crfForm"
          />
          <span class="text-h6">{{ leftForm.name }}</span>
          <v-chip size="small" label>{{ leftForm.libraryName }}</v-chip>
          <v-chip size="small" label color="info" variant="tonal">
            {{ $t('CRFCompare.version') }} {{ leftForm.version }}
          </v-chip>
        </div>
        <div />
        <div class="d-flex align-center ga-2">
          <v-icon
            :icon="
              mode === 'collection'
                ? 'mdi-alpha-c-circle'
                : 'mdi-alpha-f-circle'
            "
            color="crfForm"
          />
          <span class="text-h6">{{ rightForm.name }}</span>
          <v-chip size="small" label>{{ rightForm.libraryName }}</v-chip>
          <v-chip size="small" label color="info" variant="tonal">
            {{ $t('CRFCompare.version') }} {{ rightForm.version }}
          </v-chip>
        </div>
      </div>

      <div v-if="visibleRows.length === 0" class="text-medium-emphasis">
        {{ $t('CRFCompare.no_items') }}
      </div>
      <div
        v-for="(row, index) in visibleRows"
        :key="row.id"
        class="crf-compare-row"
        :class="{ 'is-focused': row.id === focusedId }"
        :data-row-id="row.id"
        data-cy="crf-compare-row"
        @click="focusDifference(row)"
      >
        <CrfCompareCell
          side="left"
          :row="row"
          :enabled-fields="enabledFields"
          :language="language"
          :collapsed="collapsedGroups.includes(row.id)"
          :last-in-group="isLastInGroup(index)"
          @toggle="toggleGroup(row.id)"
        />
        <div class="gutter">
          <template
            v-if="
              row.id === focusedId && row.kind === 'item' && applicable(row)
            "
          >
            <v-btn
              icon="mdi-arrow-left"
              size="small"
              variant="outlined"
              color="info"
              class="bg-white"
              :title="applyTitle('toLeft')"
              :disabled="!canApply('toLeft')"
              data-cy="crf-compare-apply-left"
              @click.stop="applyFocused('toLeft')"
            />
            <v-btn
              icon="mdi-arrow-right"
              size="small"
              variant="outlined"
              color="info"
              class="bg-white mt-2"
              :title="applyTitle('toRight')"
              :disabled="!canApply('toRight')"
              data-cy="crf-compare-apply-right"
              @click.stop="applyFocused('toRight')"
            />
          </template>
        </div>
        <CrfCompareCell
          side="right"
          :row="row"
          :enabled-fields="enabledFields"
          :language="language"
          :collapsed="collapsedGroups.includes(row.id)"
          :last-in-group="isLastInGroup(index)"
          @toggle="toggleGroup(row.id)"
        />
      </div>
    </template>
    <div v-else class="text-medium-emphasis py-8 text-center">
      {{ $t('CRFCompare.empty_prompt') }}
    </div>
    <ConfirmDialog ref="confirm" />
  </div>
</template>

<script setup>
import {
  computed,
  inject,
  nextTick,
  onMounted,
  ref,
  shallowRef,
  watch,
} from 'vue'
import { useI18n } from 'vue-i18n'
import librariesApi from '@/api/libraries'
import { useCrfCompare } from '@/composables/crfCompare'
import {
  ATTRIBUTES,
  OPTIONAL_FIELDS,
  attributeKey,
  collectLanguages,
  compareCollections,
  compareForms,
  filterRows,
} from '@/utils/crfCompare'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import { describeApply, isApplicable } from '@/utils/crfCompareApply'
import CrfCompareCell from '@/components/library/crfs/crfCompare/CrfCompareCell.vue'
import CrfCompareSelector from '@/components/library/crfs/crfCompare/CrfCompareSelector.vue'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const { loadForm, loadCollection, fileAsCollection, checkApply, applyItemRow } =
  useCrfCompare()

const emptySelection = () => ({
  library: null,
  uid: null,
  version: null,
  source: 'db',
  file: null,
})
const root = ref(null)
const confirm = ref(null)
const applying = ref(false)
const mode = ref('form')
const libraries = ref([])
const left = ref(emptySelection())
const right = ref(emptySelection())
const leftForm = shallowRef(null)
const rightForm = shallowRef(null)
const loading = ref(false)

const onlyDifferences = ref(false)
const selectedFields = ref([])
const selectedAttributes = ref([])
const ATTRIBUTE_LEVELS = Object.keys(ATTRIBUTES)
const language = ref('en')
const collapsedGroups = ref([])
const focusedId = ref(null)
const bannerOpen = ref(true)

const libraryNames = computed(() => libraries.value.map((lib) => lib.name))
const enabledFields = computed(
  () => new Set([...selectedFields.value, ...selectedAttributes.value])
)
const isComplete = (selection) => !!(selection.uid && selection.version)
const canCompare = computed(
  () => isComplete(left.value) && isComplete(right.value)
)

const comparison = computed(() => {
  if (!leftForm.value || !rightForm.value) return null
  const compare =
    mode.value === 'collection' ? compareCollections : compareForms
  return compare(leftForm.value, rightForm.value, {
    enabledFields: enabledFields.value,
    language: language.value,
  })
})

const languages = computed(() => {
  const found = new Set([
    ...collectLanguages(leftForm.value),
    ...collectLanguages(rightForm.value),
  ])
  found.add('en')
  return [...found].sort()
})

const visibleRows = computed(() => {
  if (!comparison.value) return []
  return filterRows(comparison.value.rows, onlyDifferences.value).filter(
    (row) =>
      row.kind === 'group' || !collapsedGroups.value.includes(row.groupId)
  )
})

watch(
  () => comparison.value?.stops,
  (stops) => {
    if (!stops?.length) {
      focusedId.value = null
    } else if (!stops.includes(focusedId.value)) {
      focusedId.value = stops[0]
    }
  }
)

onMounted(async () => {
  const resp = await librariesApi.get()
  libraries.value = resp.data
})

function isLastInGroup(index) {
  const next = visibleRows.value[index + 1]
  return visibleRows.value[index].kind === 'item' && next?.kind !== 'item'
}

function toggleGroup(groupRowId) {
  collapsedGroups.value = collapsedGroups.value.includes(groupRowId)
    ? collapsedGroups.value.filter((id) => id !== groupRowId)
    : [...collapsedGroups.value, groupRowId]
}

function resetSelection() {
  left.value = emptySelection()
  right.value = emptySelection()
  leftForm.value = null
  rightForm.value = null
  collapsedGroups.value = []
}

// A file selection was parsed in the selector already, so nothing is fetched.
function loadSide(selection) {
  if (selection.source === 'file') {
    const { file, uid } = selection
    return mode.value === 'collection'
      ? fileAsCollection(file.xml, file.forms)
      : file.forms.find((form) => form.uid === uid)
  }
  const load = mode.value === 'collection' ? loadCollection : loadForm
  return load(selection.uid, selection.version)
}

async function loadBoth() {
  const [leftResult, rightResult] = await Promise.all([
    loadSide(left.value),
    loadSide(right.value),
  ])
  leftForm.value = leftResult
  rightForm.value = rightResult
}

async function runCompare() {
  loading.value = true
  try {
    await loadBoth()
    collapsedGroups.value = []
    if (!languages.value.includes(language.value)) {
      language.value = languages.value[0]
    }
  } finally {
    loading.value = false
  }
}

function swap() {
  ;[left.value, right.value] = [right.value, left.value]
  ;[leftForm.value, rightForm.value] = [rightForm.value, leftForm.value]
}

async function focusRow(id) {
  const row = comparison.value.rows.find((candidate) => candidate.id === id)
  if (row.kind === 'item') {
    collapsedGroups.value = collapsedGroups.value.filter(
      (groupId) => groupId !== row.groupId
    )
  }
  if (comparison.value.stops.includes(id)) {
    focusedId.value = id
  }
  await nextTick()
  root.value
    ?.querySelector(`[data-row-id="${id}"]`)
    ?.scrollIntoView({ block: 'center', behavior: 'smooth' })
}

const focusedRow = computed(() =>
  comparison.value?.rows.find((row) => row.id === focusedId.value)
)

function focusDifference(row) {
  if (comparison.value.stops.includes(row.id)) {
    focusedId.value = row.id
  }
}

// The form an apply lands on: the compared form itself, or in a collection
// comparison the form the focused row sits in.
function targetForm(direction) {
  const side = direction === 'toRight' ? 'right' : 'left'
  if (mode.value === 'collection') return focusedRow.value?.forms?.[side]
  return side === 'right' ? rightForm.value : leftForm.value
}

const sources = computed(() => ({
  left: left.value.source,
  right: right.value.source,
}))

// File elements have no DB uids, so applying to or from one is never possible.
function fileReason(direction) {
  const [from, to] =
    direction === 'toRight' ? ['left', 'right'] : ['right', 'left']
  if (sources.value[from] === 'file') return 'source_is_file'
  if (sources.value[to] === 'file') return 'target_is_file'
  return null
}

// Copying onto a form needs a library that can be edited and no other apply in
// flight.
function canApply(direction) {
  if (applying.value || fileReason(direction)) return false
  return libraries.value.find(
    (library) => library.name === targetForm(direction)?.libraryName
  )?.is_editable
}

// A difference in position alone cannot be copied, so it offers no apply.
function applicable(row) {
  return isApplicable(row, 'toRight')
}

function applyTitle(direction) {
  const reason = fileReason(direction)
  if (reason) return t(`CRFCompare.cannot_apply.${reason}`)
  return canApply(direction) || applying.value
    ? t(`CRFCompare.apply_${direction}`)
    : t('CRFCompare.library_not_editable')
}

function applyMessage(row, direction, desc) {
  const [from, to] =
    direction === 'toRight' ? ['left', 'right'] : ['right', 'left']
  const form = targetForm(direction)
  const params = {
    item: (row[from] || row[to]).name,
    form: `${form.name} (${form.libraryName})`,
  }
  if (desc.kind === 'add') return t('CRFCompare.confirm_add', params)
  if (desc.kind === 'remove') return t('CRFCompare.confirm_remove', params)
  const fields = [...desc.itemFields, ...desc.refFields]
    .map((field) => `• ${t(`CRFCompare.field.${field}`)}`)
    .join('\n')
  return `${t('CRFCompare.confirm_update', params)}\n${fields}`
}

async function applyFocused(direction) {
  const row = focusedRow.value
  const groupRow = comparison.value.rows.find(
    (candidate) => candidate.id === row.groupId
  )
  applying.value = true
  try {
    const reason = await checkApply(row, groupRow, direction, sources.value)
    if (reason) {
      notificationHub.add({
        msg: t(`CRFCompare.cannot_apply.${reason}`),
        type: 'warning',
      })
      return
    }
    const desc = describeApply(row, direction)
    const source =
      mode.value === 'collection'
        ? row.forms[direction === 'toRight' ? 'left' : 'right']
        : direction === 'toRight'
          ? leftForm.value
          : rightForm.value
    const agreed = await confirm.value.open(
      applyMessage(row, direction, desc),
      {
        title: t('CRFCompare.confirm_title'),
        type: desc.kind === 'remove' ? 'error' : 'warning',
        agreeLabel: t('CRFCompare.apply'),
        width: 520,
      }
    )
    if (!agreed) return
    await applyItemRow(row, groupRow, direction, {
      language: language.value,
      changeDescription: t('CRFCompare.change_description', {
        form: source.name,
        version: source.version,
      }),
    })
    notificationHub.add({ msg: t('CRFCompare.applied') })
    await loadBoth()
  } finally {
    applying.value = false
  }
}
</script>

<style scoped>
.crf-compare-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 56px minmax(0, 1fr);
}
.gutter {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.is-focused :deep(.cell--item),
.is-focused :deep(.cell--group) {
  outline: 2px solid rgb(var(--v-theme-info));
  outline-offset: -2px;
}
.difference-link {
  cursor: pointer;
  text-decoration: underline;
}
</style>
