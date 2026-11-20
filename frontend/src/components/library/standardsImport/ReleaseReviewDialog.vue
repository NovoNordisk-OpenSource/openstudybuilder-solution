<template>
  <!-- Full screen: a release runs to thousands of codelists and
       tens of thousands of terms, and the point of this view is to work through them -
       the release page behind it adds nothing while that is happening. -->
  <v-card color="dfltBackground" class="h-100 d-flex flex-column">
    <v-card-title>
      <div class="d-flex align-center flex-wrap">
        <div class="page-title">
          {{ $t('StandardsImport.review_dialog_title') }}
        </div>
        <v-chip v-if="effectiveDate" size="small" variant="tonal" class="ml-3">
          {{ effectiveDate }}
        </v-chip>
      </div>
    </v-card-title>
    <v-divider />
    <v-card-text class="flex-grow-1 overflow-y-auto">
      <!-- A codelist opens in place of the tables rather than on a page of its own:
           the review is a pass through many of them, and coming back has to land on
           the same page of the same filtered table. -->
      <!-- A term opens the same way, from a codelist's terms or from the terms table,
           one level further in. -->
      <TermReviewDetail
        v-if="openTerm"
        :effective-date="effectiveDate"
        :concept-id="openTerm.conceptId"
        :codelist-id="openTerm.codelistId"
        @resolved="onTermResolved"
      />
      <!-- Kept mounted behind an open term, so its terms card keeps its filters. -->
      <CodelistReviewDetail
        v-if="openCodelistId"
        v-show="!openTerm"
        ref="codelistDetail"
        :effective-date="effectiveDate"
        :codelist-id="openCodelistId"
        @resolved="onCodelistResolved"
        @open-term="openTermOfCodelist"
      />
      <!-- v-show rather than v-if, so the table keeps its page while a codelist or a
           term is open. -->
      <div v-show="!openCodelistId && !openTerm">
        <!-- The two tables answer the same question about different things, so they are
           one view with a switch rather than two tabs of separate state. Same control
           as the status selector on the activities tables. -->
        <div class="d-flex justify-center bg-white py-4">
          <v-btn-toggle
            v-model="entity"
            mandatory
            divided
            variant="outlined"
            density="compact"
            color="nnBaseBlue"
            class="layoutSelector"
          >
            <v-btn
              value="CODELIST"
              data-cy="standards-import-review-select-codelists"
            >
              {{ $t('StandardsImport.dashboard_codelists') }}
            </v-btn>
            <v-btn value="TERM" data-cy="standards-import-review-select-terms">
              {{ $t('StandardsImport.dashboard_terms') }}
            </v-btn>
          </v-btn-toggle>
        </div>

        <!-- One table, keyed on the entity: the two differ in their columns and in the
           endpoint behind them, but not in their shell, and remounting is what makes the
           new side ask for its own first page. -->
        <NNTable
          :key="entity"
          :headers="headers"
          :items="items"
          :items-length="total"
          :loading="loading"
          :item-value="isCodelists ? 'codelist_id' : 'concept_id'"
          :table-id="`standards-import-review-${isCodelists ? 'codelists' : 'terms'}`"
          hide-export-button
          hide-default-switches
          disable-filtering
          :modifiable-table="false"
          table-height="max(400px, calc(100vh - 420px))"
          :extra-item-class="() => 'cursor-pointer'"
          data-cy="standards-import-review-table"
          @filter="fetchPage"
          @click:row="onRowClick"
        >
          <template #afterSwitches>
            <!-- One state at a time, unlike the switches after it, which combine. A
               codelist is never removed (it is new, changed or left alone), so that
               choice is offered on the terms alone. -->
            <v-btn-toggle
              v-model="changeFilter"
              mandatory
              divided
              variant="outlined"
              density="compact"
              color="nnBaseBlue"
              class="layoutSelector ml-4"
              data-cy="standards-import-review-change-filter"
            >
              <v-btn value="NEW">{{ $t('StandardsImport.change_new') }}</v-btn>
              <v-btn value="CHANGED">
                {{ $t('StandardsImport.change_changed') }}
              </v-btn>
              <v-btn v-if="!isCodelists" value="REMOVED">
                {{ $t('StandardsImport.dashboard_removed') }}
              </v-btn>
              <v-btn value="ALL">{{
                $t('StandardsImport.review_filter_all')
              }}</v-btn>
            </v-btn-toggle>
            <!-- Buttons that act as switches: the state is read from the filled icon and
               the colour, so the label stays put whichever way it is set. -->
            <v-btn
              variant="outlined"
              rounded="xl"
              :color="openOnly ? 'nnBaseBlue' : undefined"
              :active="openOnly"
              :aria-pressed="openOnly"
              :prepend-icon="toggleIcon(openOnly)"
              class="filter-toggle ml-4 mr-2"
              data-cy="standards-import-review-only-issues"
              @click="openOnly = !openOnly"
            >
              {{ $t('StandardsImport.review_only_issues') }}
            </v-btn>
            <v-btn
              variant="outlined"
              rounded="xl"
              :color="notReviewedOnly ? 'nnBaseBlue' : undefined"
              :active="notReviewedOnly"
              :aria-pressed="notReviewedOnly"
              :prepend-icon="toggleIcon(notReviewedOnly)"
              class="filter-toggle"
              data-cy="standards-import-review-only-not-reviewed"
              @click="notReviewedOnly = !notReviewedOnly"
            >
              {{ $t('StandardsImport.review_only_not_reviewed') }}
            </v-btn>
          </template>
          <template #[`item.submission_value`]="{ item }">
            <div class="font-weight-medium">
              {{ item.submission_value || item.codelist_id }}
            </div>
            <div v-if="item.name" class="text-caption text-medium-emphasis">
              {{ item.name }}
            </div>
          </template>
          <template #[`item.term_changes`]="{ item }">
            <ReviewCountChips :counts="termChangeCounts(item)" />
          </template>
          <template #[`item.preferred_term`]="{ item }">
            <div class="font-weight-medium">
              {{ item.preferred_term || item.concept_id }}
            </div>
            <div class="text-caption text-medium-emphasis">
              {{ item.concept_id }}
            </div>
          </template>
          <template #[`item.change_status`]="{ item }">
            <v-chip
              size="small"
              variant="tonal"
              :color="changeStatusColor(item.change_status)"
            >
              {{ changeLabel(item.change_status) }}
            </v-chip>
          </template>
          <!-- What the change touched. `changes` carries the before/after for the
             properties, so the old value rides along as a tooltip rather than as two
             more columns. -->
          <template #[`item.impacted`]="{ item }">
            <span v-if="!item.impacted.length" class="text-medium-emphasis">
              &mdash;
            </span>
            <v-chip
              v-for="property in item.impacted"
              :key="property"
              size="small"
              variant="tonal"
              class="mr-1 my-1"
            >
              {{ propertyLabel(property) }}
              <v-tooltip v-if="changeFor(item, property)" location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="12" class="ml-1">
                    mdi-information-outline
                  </v-icon>
                </template>
                {{ changeFor(item, property).old_value || '—' }} →
                {{ changeFor(item, property).new_value || '—' }}
              </v-tooltip>
            </v-chip>
          </template>
          <!-- How many codelists hold the term once this release lands - the API leaves
             out memberships the release ends, so a DELETED term reads 0. -->
          <template #[`item.codelist_count`]="{ item }">
            {{
              $t('StandardsImport.review_codelist_count', item.codelist_count)
            }}
          </template>
          <template #[`item.findings`]="{ item }">
            <FindingIssuesChip
              :open="item.findings.open"
              :informational="item.findings.informational"
            />
          </template>
          <template #[`item.review`]="{ item }">
            <ReviewStateChip :review="item.review" />
          </template>
        </NNTable>
      </div>
    </v-card-text>
    <!-- Bottom action bar, styled like the one the stepper forms carry: white with a
         thin top border. It is the card's last flex child rather than `.fixed-actions`,
         so the table's own pagination footer cannot end up underneath it. -->
    <v-card-actions class="bg-white border-t-thin py-4 px-6">
      <!-- One step back each time: from a term to the codelist it was opened from, or
           to the tables; from an open codelist to the tables. On the tables there is
           nothing to step back to - Close leaves the dialog. -->
      <v-btn
        v-if="openTerm || openCodelistId"
        class="secondary-btn"
        variant="outlined"
        min-width="120px"
        rounded="xl"
        :data-cy="
          openTerm
            ? 'standards-import-term-back'
            : 'standards-import-codelist-back'
        "
        @click="goBack"
      >
        {{
          openTerm && openCodelistId
            ? $t('StandardsImport.back_to_codelist')
            : $t('StandardsImport.back_to_review')
        }}
      </v-btn>
      <v-spacer />
      <v-btn
        color="primary"
        variant="flat"
        rounded="xl"
        min-width="120px"
        data-cy="standards-import-review-close"
        @click="emit('close')"
      >
        {{ $t('_global.close') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import NNTable from '@/components/tools/NNTable.vue'
import ReviewCountChips from './ReviewCountChips.vue'
import FindingIssuesChip from './FindingIssuesChip.vue'
import ReviewStateChip from './ReviewStateChip.vue'
import CodelistReviewDetail from './CodelistReviewDetail.vue'
import TermReviewDetail from './TermReviewDetail.vue'
import codelistsApi from '@/api/standardsImport/codelists'
import {
  attributeLabelKey,
  changeStatusColor,
  toggleIcon,
} from '@/utils/standardsImport'

const { t } = useI18n()

const props = defineProps({
  effectiveDate: {
    type: String,
    default: '',
  },
  // Which table to land on: the review box the reader clicked decides it.
  entityType: {
    type: String,
    default: 'CODELIST',
  },
})
const emit = defineEmits(['close', 'resolved'])

const codelistHeaders = [
  {
    title: t('StandardsImport.col_codelist'),
    key: 'submission_value',
    sortable: false,
    noFilter: true,
  },
  {
    title: t('StandardsImport.col_term_changes'),
    key: 'term_changes',
    sortable: false,
    noFilter: true,
  },
  { title: t('StandardsImport.col_change_type'), key: 'change_status' },
  {
    title: t('StandardsImport.status'),
    key: 'findings',
    sortable: false,
    noFilter: true,
  },
  { title: t('StandardsImport.col_review_state'), key: 'review' },
]

const termHeaders = [
  {
    title: t('StandardsImport.col_term'),
    key: 'preferred_term',
    sortable: false,
    noFilter: true,
  },
  { title: t('StandardsImport.col_change_type'), key: 'change_status' },
  {
    title: t('StandardsImport.col_impacted'),
    key: 'impacted',
    sortable: false,
    noFilter: true,
  },
  {
    title: t('StandardsImport.col_membership'),
    key: 'codelist_count',
    sortable: false,
    noFilter: true,
  },
  {
    title: t('StandardsImport.status'),
    key: 'findings',
    sortable: false,
    noFilter: true,
  },
  { title: t('StandardsImport.col_review_state'), key: 'review' },
]

const entity = ref(props.entityType || 'CODELIST')
// One table serves both halves, keyed on `entity` so switching remounts it: the two share
// three of their columns and all of their paging, and only the header set and the endpoint
// differ.
const isCodelists = computed(() => entity.value === 'CODELIST')
const headers = computed(() =>
  isCodelists.value ? codelistHeaders : termHeaders
)
const items = ref([])
const total = ref(0)
const loading = ref(false)
// Codelists are asked for in full (`show=all`), unchanged ones included; terms come back
// narrowed to the ones the release changes. The two toggles narrow either further, and
// "only issues" starts on so the review opens on what blocks the import.
const openOnly = ref(true)
const notReviewedOnly = ref(false)
// One of NEW, CHANGED, REMOVED or ALL. What each means to the API depends on the side:
// the two sides name their states differently, and only a term can be removed.
const changeFilter = ref('ALL')
const CHANGE_STATUS_PARAM = {
  CODELIST: { NEW: 'NEW', CHANGED: 'UPDATED' },
  TERM: { NEW: 'NEW', CHANGED: 'CHANGED', REMOVED: 'DELETED' },
}
// The codelist shown in place of the tables, if any.
const openCodelistId = ref(null)
const codelistDetail = ref(null)
// The term shown in place of either, if any: `{ conceptId, codelistId }`, the codelist
// being the one it was opened from - null from the terms table.
const openTerm = ref(null)
// Set once a finding is settled from the open codelist or term: the row counts behind
// it no longer hold, so the table re-asks on the way back.
let tableStale = false
// The same, for the codelist behind an open term.
let codelistStale = false

// NNTable drives the fetch, so the toggles in its header have no options of their own to
// pass. Keeping the last call's arguments is what lets them re-ask with the same page
// size.
let lastArgs = null

function pageParams(options) {
  const size = options?.itemsPerPage
  return {
    page_number: options?.page || 1,
    // NNTable says "all" with a non-positive size; the API spells that `page_size=0`.
    page_size: size > 0 ? size : 0,
  }
}

// NNTable's column filters are disabled, so nothing from `filters` reaches the API: the
// toggles and the search field are the only filters. `disable-filtering` leaves the
// search field in place, and the API matches it against the id and the names.
function buildParams(options, filtersUpdated) {
  if (filtersUpdated && options) {
    options.page = 1
  }
  const params = pageParams(options)
  const search = options?.search?.trim()
  if (search) {
    params.search = search
  }
  if (openOnly.value) {
    params.has_open_findings = true
  }
  if (notReviewedOnly.value) {
    params.review_status = 'NOT_REVIEWED'
  }
  const changeStatus = CHANGE_STATUS_PARAM[entity.value][changeFilter.value]
  if (changeStatus) {
    params.change_status = changeStatus
  }
  return params
}

function fetchPage(filters, options, filtersUpdated) {
  if (!props.effectiveDate) {
    return
  }
  lastArgs = [filters, options, filtersUpdated]
  loading.value = true
  const params = buildParams(options, filtersUpdated)
  const request = isCodelists.value
    ? codelistsApi.getCodelists(props.effectiveDate, { ...params, show: 'all' })
    : codelistsApi.getTerms(props.effectiveDate, params)
  request
    .then((response) => {
      items.value = response.data.items
      total.value = response.data.total
    })
    .finally(() => {
      loading.value = false
    })
}

// A term row lists the term once for all of its codelists, so none is picked for it:
// its detail view starts on the first.
function onRowClick(_event, { item }) {
  if (isCodelists.value) {
    openCodelistId.value = item.codelist_id
  } else {
    openTerm.value = { conceptId: item.concept_id, codelistId: null }
  }
}

function openTermOfCodelist(conceptId) {
  openTerm.value = { conceptId, codelistId: openCodelistId.value }
}

function onCodelistResolved() {
  tableStale = true
  emit('resolved')
}

function onTermResolved() {
  tableStale = true
  codelistStale = !!openCodelistId.value
  emit('resolved')
}

// Same page, same filters: only the rows are asked for again, and only if a decision
// was made while a codelist or a term was open.
function refreshTableIfStale() {
  if (tableStale && lastArgs) {
    const [filters, options] = lastArgs
    fetchPage(filters, options, false)
  }
  tableStale = false
}

function closeCodelist() {
  openCodelistId.value = null
  refreshTableIfStale()
}

// Back to the codelist the term was opened from, if any - refreshed in place if a
// decision was made on the term - or else to the tables.
function closeTerm() {
  openTerm.value = null
  if (openCodelistId.value) {
    if (codelistStale) {
      codelistDetail.value?.reload()
    }
    codelistStale = false
  } else {
    refreshTableIfStale()
  }
}

function goBack() {
  if (openTerm.value) {
    closeTerm()
  } else {
    closeCodelist()
  }
}

function termChangeCounts(item) {
  // A term never leaves the MDR, so "removed" here is a membership this release closes,
  // not a deletion - which is also why the two figures come from `memberships` and only
  // the middle one from the term diff.
  return [
    {
      label: t('StandardsImport.dashboard_added'),
      value: item.memberships.added,
      color: 'success',
    },
    {
      label: t('StandardsImport.dashboard_changed'),
      value: item.term_changes.updated,
      color: 'warning',
    },
    {
      label: t('StandardsImport.dashboard_removed'),
      value: item.memberships.ended,
      color: 'error',
    },
  ]
}

function changeLabel(status) {
  return t(`StandardsImport.change_${status.toLowerCase()}`)
}

function propertyLabel(property) {
  if (property === 'membership') {
    return t('StandardsImport.impacted_membership')
  }
  return t(attributeLabelKey(property))
}

function changeFor(item, property) {
  return item.changes.find((change) => change.field === property)
}

// Switching either scope toggle re-asks with the same page size.
// Page 1, because the row that was on page 4 of the filtered set is not on page 4 of a
// wider one.
watch([openOnly, notReviewedOnly, changeFilter], () => {
  if (!lastArgs) {
    return
  }
  const [filters, options] = lastArgs
  if (options) {
    options.page = 1
  }
  fetchPage(filters, options, false)
})

// `:key="entity"` remounts the table, and the fresh one asks for its own first page - so
// nothing to fetch here, only the other side's rows to forget so a stale page cannot
// flash on the way back.
watch(entity, () => {
  lastArgs = null
  items.value = []
  total.value = 0
  changeFilter.value = 'ALL'
})
</script>

<style scoped>
.layoutSelector {
  border-color: rgb(var(--v-theme-nnBaseBlue));
}
.layoutSelector :deep(.v-btn) {
  text-transform: none;
}
/* Grey border at rest and when on, as the detail view's filters: an outlined button
   would otherwise draw it in the text colour. */
.filter-toggle {
  border-color: rgba(var(--v-border-color), var(--v-border-opacity));
}
</style>
