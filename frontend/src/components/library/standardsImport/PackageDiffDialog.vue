<template>
  <!-- Shown full screen, so the title and the close button stay put and only the
       bands scroll - a single band runs to thousands of rows. -->
  <v-card color="dfltBackground" class="h-100 d-flex flex-column">
    <v-card-title>
      <div class="d-flex align-center flex-wrap ga-4">
        <div class="page-title">
          {{ dialogTitle }}
        </div>
        <v-select
          :model-value="catalogue"
          :items="catalogues.length ? catalogues : [catalogue]"
          :readonly="catalogues.length < 2"
          density="compact"
          variant="outlined"
          hide-details
          class="catalogue-select"
          data-cy="standards-import-pre-review-diff-catalogue"
          @update:model-value="emit('update:catalogue', $event)"
        />
      </div>
    </v-card-title>
    <v-card-text class="flex-grow-1 overflow-y-auto">
      <v-alert
        v-if="error"
        type="error"
        variant="tonal"
        class="mb-4"
        :text="error"
      />
      <v-progress-linear v-if="loading" indeterminate class="mb-4" />
      <template v-else-if="report">
        <v-alert
          v-if="!report.previous_available"
          type="info"
          variant="tonal"
          :text="$t('StandardsImport.no_previous_release')"
        />
        <template v-else>
          <v-row class="mb-4" dense>
            <v-col
              v-for="stat in summaryCards"
              :key="stat.key"
              cols="12"
              sm="6"
            >
              <v-card variant="outlined">
                <v-card-text>
                  <div class="text-subtitle-1 font-weight-bold mb-2">
                    {{ stat.title }}
                  </div>
                  <div class="d-flex justify-space-between">
                    <span class="text-success">
                      {{ $t('StandardsImport.diff_added') }}: {{ stat.added }}
                    </span>
                    <span class="text-warning">
                      {{ $t('StandardsImport.diff_modified') }}:
                      {{ stat.modified }}
                    </span>
                    <span class="text-error">
                      {{ $t('StandardsImport.diff_removed') }}:
                      {{ stat.removed }}
                    </span>
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
          <section
            v-for="group in bandGroups"
            :key="group.key"
            class="mb-6"
            :data-cy="`standards-import-pre-review-diff-${group.key}`"
          >
            <div
              class="text-h5 font-weight-bold text-primary mb-3 pb-1 group-title"
            >
              {{ group.title }}
            </div>
            <div
              v-if="!group.bands.length"
              class="text-body-2 text-medium-emphasis"
            >
              {{ $t('StandardsImport.diff_group_empty') }}
            </div>
            <v-expansion-panels v-else accordion>
              <v-expansion-panel v-for="band in group.bands" :key="band.level">
                <v-expansion-panel-title>
                  {{ band.label }} ({{ band.rows.length }})
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <v-data-table
                    :headers="headersFor(band)"
                    :items="band.rows"
                    item-value="index"
                    :items-per-page="-1"
                    hide-default-footer
                    density="compact"
                  >
                    <!-- Attribute changes carry a field with a before and an after
                       value. Rendering them as one inline word-level diff keeps
                       the edit readable in place - most of these values are long
                       definitions where only a phrase moved. -->
                    <template #[`item.submissionValue`]="{ item }">
                      <v-chip
                        v-if="item.submissionValue"
                        size="small"
                        variant="tonal"
                        color="primary"
                        class="font-weight-bold"
                        data-cy="standards-import-pre-review-diff-submission-value"
                      >
                        {{ item.submissionValue }}
                      </v-chip>
                    </template>
                    <template #[`item.history`]="{ item }">
                      <v-btn
                        v-if="item.conceptId"
                        size="small"
                        variant="outlined"
                        color="primary"
                        rounded="xl"
                        prepend-icon="mdi-history"
                        data-cy="standards-import-pre-review-diff-history"
                        @click="openHistory(item)"
                      >
                        {{
                          $t(
                            item.conceptType === 'codelist'
                              ? 'StandardsImport.history_see_codelist'
                              : 'StandardsImport.history_see_term'
                          )
                        }}
                      </v-btn>
                    </template>
                    <template #[`item.detail`]="{ item }">
                      <template v-if="item.attributeChanges">
                        <div
                          v-for="(change, index) in item.attributeChanges"
                          :key="`${change.field}-${index}`"
                          class="py-1"
                        >
                          <div class="text-caption text-medium-emphasis">
                            {{ fieldLabel(change.field) }}
                            <template v-if="item.context">
                              — {{ item.context }}
                            </template>
                          </div>
                          <AttributeDiff
                            :old-value="change.old"
                            :new-value="change.new"
                          />
                        </div>
                      </template>
                      <div
                        v-else-if="item.codelistGroups"
                        data-cy="standards-import-pre-review-diff-codelists"
                      >
                        <div
                          v-for="group in item.codelistGroups"
                          :key="group.kind"
                          class="py-1"
                        >
                          <span class="text-caption text-medium-emphasis mr-2">
                            {{
                              $t(`StandardsImport.diff_codelists_${group.kind}`)
                            }}
                          </span>
                          <span>{{ group.codelists.join(', ') }}</span>
                        </div>
                      </div>
                      <span v-else>{{ item.detail }}</span>
                    </template>
                    <!-- CDISC's own note about the change, where its terminology
                       changes sheet mentioned it. Editorial commentary, not part
                       of the diff: a change with nothing said about it is no less
                       real, so an unannotated row says so rather than looking
                       broken. -->
                    <template #[`item.changelog`]="{ item }">
                      <div
                        v-for="(entry, index) in item.changelog"
                        :key="index"
                        class="py-1"
                      >
                        <div class="text-body-2">
                          {{ entry.change_summary }}
                        </div>
                        <div
                          v-if="entry.request_codes?.length"
                          class="d-flex flex-wrap ga-1 mt-1"
                        >
                          <v-chip
                            v-for="code in entry.request_codes"
                            :key="code"
                            size="x-small"
                            variant="tonal"
                          >
                            {{ code }}
                          </v-chip>
                        </div>
                        <div
                          v-if="entry.implementation_instructions"
                          class="text-caption text-medium-emphasis font-italic mt-1"
                        >
                          {{ entry.implementation_instructions }}
                        </div>
                      </div>
                      <span
                        v-if="!item.changelog.length"
                        class="text-caption text-medium-emphasis"
                      >
                        {{ $t('StandardsImport.diff_not_in_changelog') }}
                      </span>
                    </template>
                  </v-data-table>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </section>
        </template>
      </template>
    </v-card-text>
    <v-card-actions class="bg-white border-t-thin py-4 px-6">
      <v-spacer />
      <v-btn
        color="primary"
        variant="flat"
        rounded="xl"
        min-width="120px"
        data-cy="standards-import-diff-close"
        @click="emit('close')"
      >
        {{ $t('_global.close') }}
      </v-btn>
    </v-card-actions>
    <v-dialog
      :model-value="!!historyConcept"
      max-width="1440px"
      scrollable
      persistent
    >
      <ConceptHistoryDialog
        v-if="historyConcept"
        :catalogue="catalogue"
        :effective-date="effectiveDate"
        :concept-type="historyConcept.conceptType"
        :concept-id="historyConcept.conceptId"
        @close="historyConcept = null"
      />
    </v-dialog>
  </v-card>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import AttributeDiff from './AttributeDiff.vue'
import ConceptHistoryDialog from './ConceptHistoryDialog.vue'
import packageDiffApi from '@/api/standardsImport/packageDiff'

const { t, te } = useI18n()

const props = defineProps({
  catalogue: {
    type: String,
    default: '',
  },
  effectiveDate: {
    type: String,
    default: '',
  },
  catalogues: {
    type: Array,
    default: () => [],
  },
})
const emit = defineEmits(['close', 'update:catalogue'])

const report = ref(null)
const loading = ref(false)
const error = ref('')

// Resolved separately from `report`, via a lookup that only follows the
// `HAS_PRIOR_VERSION` link rather than walking both catalogues' codelists and
// terms - so the title can name the previous release right away instead of
// waiting on the full diff.
const previousRelease = ref(null)

// Dates only: the catalogue is the dropdown beside the title, and repeating it here
// would say the same thing twice.
const dialogTitle = computed(() => {
  const info = previousRelease.value || report.value
  if (info?.previous_available) {
    return t('StandardsImport.diff_dialog_title_with_previous', {
      effectiveDate: props.effectiveDate,
      previousDate: info.previous_effective_date,
    })
  }
  return t('StandardsImport.diff_dialog_title', {
    effectiveDate: props.effectiveDate,
  })
})

// Tallies every change across all bands into added/modified/removed counts for
// codelists and terms, so the dialog can lead with a dashboard-style summary
// instead of making the user open each severity band to gauge the impact.
// Membership changes are folded into the term counts: a term entering or
// leaving a codelist, or its submission value there changing, is what a
// reviewer experiences as that term being added, removed, or modified.
const summary = computed(() => {
  const counts = {
    codelist: { added: 0, modified: 0, removed: 0 },
    term: { added: 0, modified: 0, removed: 0 },
  }
  // A concept edited in several fields is one modification, as it is one row below.
  const modifiedCodelists = new Set()
  const modifiedTerms = new Set()
  for (const band of report.value?.bands || []) {
    for (const change of band.changes) {
      switch (change.kind) {
        case 'codelist_added':
          counts.codelist.added += 1
          break
        case 'codelist_removed':
          counts.codelist.removed += 1
          break
        case 'codelist_changed':
          modifiedCodelists.add(change.conceptId)
          break
        case 'term_added':
        case 'membership_added':
          counts.term.added += 1
          break
        case 'term_removed':
        case 'membership_removed':
          counts.term.removed += 1
          break
        case 'term_changed':
          modifiedTerms.add(change.conceptId)
          break
        case 'membership_changed':
        case 'term_moved':
          counts.term.modified += 1
          break
        default:
          break
      }
    }
  }
  counts.codelist.modified += modifiedCodelists.size
  counts.term.modified += modifiedTerms.size
  return counts
})

const summaryCards = computed(() => [
  {
    key: 'codelist',
    title: t('StandardsImport.diff_summary_codelists'),
    ...summary.value.codelist,
  },
  {
    key: 'term',
    title: t('StandardsImport.diff_summary_terms'),
    ...summary.value.term,
  },
])

// The API's severity levels (`ct_diff.SEVERITIES`) that are about a codelist itself:
// removed, new, and renamed or redescribed. Every other level is about terms,
// membership changes (a term entering or leaving a codelist, or its submission value
// there changing) included.
const CODELIST_LEVELS = [1, 8, 11]

const bandGroups = computed(() => {
  const bands = report.value?.bands || []
  return [
    {
      key: 'codelist',
      title: t('StandardsImport.diff_group_codelists'),
      bands: withRows(
        bands.filter((band) => CODELIST_LEVELS.includes(band.level))
      ),
    },
    {
      key: 'term',
      title: t('StandardsImport.diff_group_terms'),
      bands: withRows(
        bands.filter((band) => !CODELIST_LEVELS.includes(band.level))
      ),
    },
  ]
})

// One row per change, except that a codelist or a term whose attributes changed in
// several fields is one row stacking those diffs: the API reports each field as a change
// of its own, but a reviewer reads them as one edit to one concept.
function withRows(bands) {
  return bands.map((band) => ({ ...band, rows: buildRows(band.changes) }))
}

// What makes two changes one row: the same concept edited in several fields, or the
// same term entering or leaving several codelists. Anything else stands alone.
function mergeKey(change) {
  if (['codelist_changed', 'term_changed'].includes(change.kind)) {
    return `${change.kind}:${change.conceptId}`
  }
  if (['membership_added', 'membership_removed'].includes(change.kind)) {
    return `${change.kind}:${change.key[1]}`
  }
  return null
}

function buildRows(changes) {
  const rows = []
  const byConcept = new Map()
  for (const change of changes) {
    const row = describeChange(change)
    const key = mergeKey(change)
    const existing = key && byConcept.get(key)
    if (!key) {
      rows.push(row)
      continue
    }
    if (!existing) {
      byConcept.set(key, row)
      rows.push(row)
      continue
    }
    existing.attributeChanges?.push(...(row.attributeChanges || []))
    for (const group of row.codelistGroups || []) {
      const target = existing.codelistGroups.find((g) => g.kind === group.kind)
      if (target) {
        for (const codelist of group.codelists) {
          if (!target.codelists.includes(codelist)) {
            target.codelists.push(codelist)
          }
        }
      } else {
        existing.codelistGroups.push(group)
      }
    }
    existing.changelog = distinctEntries([
      ...existing.changelog,
      ...row.changelog,
    ])
  }
  return rows
}

// The changelog column only earns its width where a terminology-changes sheet was
// uploaded for the release; without one every row would read "not in changelog".
// The detail column is "Affected codelist(s)" in a band whose rows say which codelists
// a term entered, left or moved between; in the others it is the attribute diff, or
// nothing, and stays "Detail".
const CODELIST_DETAIL_KINDS = [
  'membership_added',
  'membership_removed',
  'term_removed',
  'term_moved',
]

function headersFor(band) {
  const listsCodelists =
    band.changes.some((change) =>
      CODELIST_DETAIL_KINDS.includes(change.kind)
    ) && !band.changes.some((change) => change.field)
  const headers = [
    { title: t('StandardsImport.diff_concept_id'), key: 'conceptId' },
    { title: t('StandardsImport.diff_name'), key: 'name' },
    {
      title: t('StandardsImport.diff_submission_values'),
      key: 'submissionValue',
    },
    {
      title: t(
        listsCodelists
          ? 'StandardsImport.diff_affected_codelists'
          : 'StandardsImport.diff_detail'
      ),
      key: 'detail',
    },
  ]
  if (report.value?.changelog_available) {
    headers.push({
      title: t('StandardsImport.diff_changelog'),
      key: 'changelog',
      sortable: false,
    })
  }
  headers.push({
    title: '',
    key: 'history',
    sortable: false,
    align: 'end',
  })
  return headers
}

// The API sends the raw camelCase snapshot field names; fall back to those for
// any field added on the backend before a label lands here.
function fieldLabel(field) {
  const key = `StandardsImport.diff_field_${field}`
  return te(key) ? t(key) : field
}

// Each change is one of a handful of kinds coming from the API's severity bands
// (codelist/term added/removed/changed, membership added/removed/changed, moved) -
// this turns that loosely-typed shape into a concept string plus either a detail
// string or, for the attribute changes, a before/after pair the table renders as
// a diff.
function describeConcept(change) {
  const termValue = (change.term_submission_values || []).join(', ')
  switch (change.kind) {
    case 'codelist_added':
    case 'codelist_removed':
      return {
        name: change.codelist.name,
        submissionValue: change.codelist.submissionValue,
        detail: '',
      }
    case 'term_added':
      return {
        name: change.term.preferredTerm,
        submissionValue: termValue,
        detail: '',
      }
    case 'term_removed':
      return {
        name: change.term.preferredTerm,
        submissionValue: termValue,
        // The codelists the term left with it, folded into this row by the API.
        codelistGroups: codelistGroups(change, { leaves: change.codelists }),
      }
    case 'codelist_changed':
      return {
        name: change.codelist.name,
        submissionValue: change.codelist.submissionValue,
        attributeChanges: [change],
      }
    case 'term_changed':
      return {
        name: change.term.preferredTerm,
        submissionValue: termValue,
        attributeChanges: [change],
      }
    case 'membership_added':
      return {
        name: change.term_name,
        submissionValue: termValue,
        codelistGroups: codelistGroups(change, {
          enters: [change.key[0]],
          stays: change.stays_in,
        }),
      }
    case 'membership_removed':
      return {
        name: change.term_name,
        submissionValue: termValue,
        codelistGroups: codelistGroups(change, {
          leaves: [change.key[0]],
          stays: change.stays_in,
        }),
      }
    case 'membership_changed':
      return {
        name: change.term_name,
        submissionValue: termValue,
        // A submission value only exists within a codelist, so the diff needs to
        // name which one.
        context: t('StandardsImport.diff_in_codelist', {
          codelist: codelistLabel(change, change.key[0]),
        }),
        attributeChanges: [change],
      }
    case 'term_moved':
      return {
        name: change.term_name,
        submissionValue: termValue,
        codelistGroups: codelistGroups(change, {
          leaves: change.move.left,
          enters: change.move.entered,
          stays: change.stays_in,
        }),
      }
    default:
      return { name: change.kind, detail: '' }
  }
}

// What a term does to the codelists around it, one line each: the ones it leaves, the
// ones it enters and the ones it is in before and after. Lines with nothing to say are
// left out.
const CODELIST_GROUP_ORDER = ['leaves', 'enters', 'stays']

function codelistGroups(change, ids) {
  return CODELIST_GROUP_ORDER.filter((kind) => ids[kind]?.length).map(
    (kind) => ({
      kind,
      codelists: ids[kind].map((id) => codelistLabel(change, id)),
    })
  )
}

// A codelist's concept id followed by its submission value, where the API sent one
// for it: the id alone says little to someone reading the diff.
function codelistLabel(change, codelistId) {
  const value = change.codelist_submission_values?.[codelistId]
  return value ? `${codelistId} (${value})` : codelistId
}

// The API leaves `changelog` off a change its sheet did not mention, rather than
// sending an empty list, so that "CDISC said nothing about this" stays distinct
// from "no sheet was uploaded" - which is `changelog_available` on the report.
// The table only needs the former flattened to an empty list.
function describeChange(change) {
  return {
    ...describeConcept(change),
    ...conceptOf(change),
    changelog: distinctEntries(change.changelog || []),
  }
}

// What the history of a row is of. A membership change or a move is about the term, and
// the term is the same in every codelist it moves between.
function conceptOf(change) {
  if (change.kind.startsWith('codelist_')) {
    return {
      conceptType: 'codelist',
      conceptId: change.conceptId || change.codelist.conceptId,
    }
  }
  const termId =
    change.conceptId ||
    change.term?.conceptId ||
    change.move?.conceptId ||
    change.key?.[1]
  return { conceptType: 'term', conceptId: termId }
}

const historyConcept = ref(null)

function openHistory(item) {
  historyConcept.value = {
    conceptType: item.conceptType,
    conceptId: item.conceptId,
  }
}

// A term sits in several codelists and the sheet reports its change under each, so a
// term-level change is matched by one entry per codelist. They differ only in the
// codelist they name, which this column does not show, so those repeats read as the
// same note twice.
function distinctEntries(entries) {
  const seen = new Set()
  return entries.filter((entry) => {
    const key = JSON.stringify([
      entry.change_summary,
      entry.request_codes || [],
      entry.implementation_instructions || '',
    ])
    if (seen.has(key)) {
      return false
    }
    seen.add(key)
    return true
  })
}

function loadPreviousRelease() {
  if (!props.catalogue || !props.effectiveDate) {
    return
  }
  previousRelease.value = null
  packageDiffApi
    .getPreviousRelease(props.catalogue, props.effectiveDate)
    .then((response) => {
      previousRelease.value = response.data
    })
    .catch(() => {
      // The full diff call below surfaces the same lookup's failure; nothing
      // else to show for this fast, title-only one.
    })
}

function load() {
  if (!props.catalogue || !props.effectiveDate) {
    return
  }
  loading.value = true
  error.value = ''
  report.value = null
  packageDiffApi
    .get(props.catalogue, props.effectiveDate)
    .then((response) => {
      report.value = response.data
    })
    .catch((err) => {
      error.value =
        err.response?.data?.message ||
        err.message ||
        t('StandardsImport.diff_error')
    })
    .finally(() => {
      loading.value = false
    })
}

function loadAll() {
  loadPreviousRelease()
  load()
}

watch(() => [props.catalogue, props.effectiveDate], loadAll)
onMounted(loadAll)
</script>

<style scoped lang="scss">
.catalogue-select {
  min-width: 220px;
}

.group-title {
  border-bottom: 2px solid rgb(var(--v-theme-primary));
}
</style>
