<template>
  <div>
    <div class="text-subtitle-2 text-medium-emphasis">
      {{ $t('StandardsImport.col_codelist') }}
    </div>
    <div class="d-flex align-center flex-wrap">
      <div class="text-h5">
        {{ detail?.submission_value || codelistId }}
      </div>
      <template v-if="detail">
        <v-chip
          size="small"
          variant="tonal"
          class="ml-3"
          :color="changeStatusColor(detail.change_status)"
        >
          {{
            $t(`StandardsImport.change_${detail.change_status.toLowerCase()}`)
          }}
        </v-chip>
        <ReviewStateChip :review="detail.review" class="ml-2" />
        <v-spacer />
        <!-- Offered again on a stale review, which needs marking anew once the
             reopened finding is settled. The API refuses while a finding on the
             codelist or its terms is open or unacknowledged, so the button says so up
             front; the wrapper carries the tooltip because a disabled button takes no
             hover. -->
        <v-tooltip
          v-if="detail.review?.status !== 'REVIEWED'"
          :disabled="!hasOpenFindings"
          location="top"
          :text="$t('StandardsImport.codelist_mark_reviewed_blocked')"
        >
          <template #activator="{ props: tooltipProps }">
            <span v-bind="tooltipProps">
              <v-btn
                variant="outlined"
                color="primary"
                rounded="xl"
                prepend-icon="mdi-check-circle-outline"
                :disabled="hasOpenFindings"
                :loading="markingReviewed"
                data-cy="standards-import-codelist-mark-reviewed"
                @click="markReviewed"
              >
                {{ $t('StandardsImport.codelist_mark_reviewed') }}
              </v-btn>
            </span>
          </template>
        </v-tooltip>
      </template>
    </div>
    <div v-if="detail" class="text-medium-emphasis mt-1">
      {{ detail.name }} &middot; {{ detail.codelist_id }}
    </div>

    <v-progress-linear v-if="loading" indeterminate class="mt-4" />

    <v-alert
      v-if="error"
      type="error"
      variant="tonal"
      class="alert-bordered mt-4"
      density="compact"
      :text="error"
    />

    <template v-else-if="detail">
      <!-- First, because a finding is what can hold the release back; the attributes
           below are what it is about. Each one can be settled here, with the same
           actions and dialog as the finding queue. -->
      <v-sheet color="white" rounded="xl" elevation="0" class="pa-4 mt-4">
        <div class="card-title mb-3">
          {{ $t('StandardsImport.codelist_findings') }}
        </div>
        <div v-if="!findings.length" class="text-medium-emphasis">
          {{ $t('StandardsImport.codelist_no_findings') }}
        </div>
        <v-table
          v-else
          class="review-table"
          density="comfortable"
          data-cy="standards-import-codelist-findings"
        >
          <thead>
            <tr>
              <th class="actions-column" />
              <th>{{ $t('StandardsImport.type') }}</th>
              <th>{{ $t('StandardsImport.col_term') }}</th>
              <th>{{ $t('StandardsImport.candidates') }}</th>
              <th>{{ $t('StandardsImport.status') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="finding in findings" :key="finding.uid">
              <td class="py-2">
                <ActionsMenu :actions="actions" :item="finding" />
              </td>
              <td class="py-2">
                {{ findingTypeLabel(finding.type) }}
                <EnumInfoTooltip
                  enum-key="inconsistency_type"
                  :value="finding.type"
                />
              </td>
              <td class="py-2">
                <template v-if="finding.term">
                  <div class="font-weight-medium">
                    {{ finding.term.preferred_term || finding.term.concept_id }}
                  </div>
                  <div class="text-caption text-medium-emphasis">
                    {{ finding.term.concept_id }}
                  </div>
                </template>
                <span v-else class="text-medium-emphasis">&mdash;</span>
              </td>
              <td class="py-2">
                <FindingDetails :finding="finding" />
              </td>
              <td class="py-2">
                <v-chip
                  size="small"
                  variant="tonal"
                  :color="findingStatusColor(finding.status)"
                >
                  {{ $t(`StandardsImport.${finding.status.toLowerCase()}`) }}
                </v-chip>
              </td>
            </tr>
          </tbody>
        </v-table>
      </v-sheet>

      <v-sheet color="white" rounded="xl" elevation="0" class="pa-4 mt-4">
        <div class="card-title mb-3">
          {{ $t('StandardsImport.attributes') }}
        </div>

        <!-- MDR holds no earlier version, so every attribute is what this release
             brings, and there is nothing to set it beside. -->
        <v-alert
          v-if="isNew"
          type="info"
          variant="tonal"
          class="alert-bordered mb-4"
          density="compact"
          :text="$t('StandardsImport.codelist_new_no_previous')"
        />
        <!-- Every attribute the release defines, changed or not. Those it changes carry
             the old and new words in one value, so what moved reads at a glance rather
             than by comparing two columns. A new codelist has nothing to set its values
             beside, so they are shown as they are. -->
        <v-table
          density="comfortable"
          class="review-table"
          data-cy="standards-import-codelist-attributes"
        >
          <thead>
            <tr>
              <th class="attribute-column">
                {{ $t('StandardsImport.codelist_col_attribute') }}
              </th>
              <th>{{ $t('StandardsImport.value') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="attribute in detail.attributes" :key="attribute.field">
              <td class="font-weight-medium py-2">
                {{ $t(attributeLabelKey(attribute.field)) }}
              </td>
              <td class="py-2">
                <AttributeDiff
                  :old-value="previousValue(attribute)"
                  :new-value="currentValue(attribute)"
                  side="inline"
                />
              </td>
            </tr>
          </tbody>
        </v-table>
      </v-sheet>

      <!-- Only once a terminology-changes sheet mentioning the codelist was uploaded.
           Its terms' entries are on each term's own view. -->
      <v-sheet
        v-if="detail.changelog?.length"
        color="white"
        rounded="xl"
        elevation="0"
        class="pa-4 mt-4"
        data-cy="standards-import-codelist-changelog"
      >
        <div class="card-title mb-3">
          {{ $t('StandardsImport.diff_changelog_available') }}
        </div>
        <ChangelogEntryList
          :entries="detail.changelog"
          :codelist-id="detail.codelist_id"
        />
      </v-sheet>

      <!-- Every term the codelist holds, plus the ones this release takes out of it. A
           term's own findings are counted here rather than listed with the codelist's:
           they are about the term, wherever else it is held. -->
      <v-sheet color="white" rounded="xl" elevation="0" class="pa-4 mt-4">
        <div class="d-flex align-center flex-wrap ga-2 mb-3">
          <div class="card-title">
            {{ $t('StandardsImport.codelist_terms') }}
          </div>
          <v-spacer />
          <!-- Same toggles as the review tables'. The filters combine: each one only
               narrows what the others leave. -->
          <template v-if="terms.length">
            <v-btn
              variant="outlined"
              rounded="xl"
              :color="changedTermsOnly ? 'nnBaseBlue' : undefined"
              :active="changedTermsOnly"
              :aria-pressed="changedTermsOnly"
              :prepend-icon="toggleIcon(changedTermsOnly)"
              class="filter-toggle"
              data-cy="standards-import-codelist-terms-only-changed"
              @click="changedTermsOnly = !changedTermsOnly"
            >
              {{ $t('StandardsImport.codelist_terms_only_changed') }}
            </v-btn>
            <!-- One membership change at most, so a radio; not `mandatory`, so
                 clicking the selected one again lifts the filter. Compact, so the group
                 is as tall as a single button rather than 48px. -->
            <v-btn-toggle
              v-model="membershipFilter"
              divided
              density="compact"
              variant="outlined"
              rounded="xl"
              color="nnBaseBlue"
              data-cy="standards-import-codelist-terms-membership"
            >
              <v-btn
                v-for="change in MEMBERSHIP_CHANGES"
                :key="change"
                :value="change"
                :prepend-icon="toggleIcon(membershipFilter === change)"
                :data-cy="`standards-import-codelist-terms-membership-${change.toLowerCase()}`"
              >
                {{ $t(`StandardsImport.membership_${change.toLowerCase()}`) }}
              </v-btn>
            </v-btn-toggle>
            <v-btn
              variant="outlined"
              rounded="xl"
              :color="termsWithFindingsOnly ? 'nnBaseBlue' : undefined"
              :active="termsWithFindingsOnly"
              :aria-pressed="termsWithFindingsOnly"
              :prepend-icon="toggleIcon(termsWithFindingsOnly)"
              class="filter-toggle"
              data-cy="standards-import-codelist-terms-only-findings"
              @click="termsWithFindingsOnly = !termsWithFindingsOnly"
            >
              {{ $t('StandardsImport.codelist_terms_only_findings') }}
            </v-btn>
          </template>
        </div>
        <div v-if="!terms.length" class="text-medium-emphasis">
          {{ $t('StandardsImport.codelist_no_terms') }}
        </div>
        <v-data-table
          v-else
          class="review-table"
          :headers="termHeaders"
          :items="shownTerms"
          :no-data-text="$t('StandardsImport.codelist_no_matching_terms')"
          item-value="concept_id"
          density="comfortable"
          :row-props="{ class: 'cursor-pointer' }"
          data-cy="standards-import-codelist-terms"
          @click:row="(_event, { item }) => emit('open-term', item.concept_id)"
        >
          <template #[`item.term`]="{ item }">
            <div class="font-weight-medium">
              {{ item.submission_value || item.concept_id }}
            </div>
            <div v-if="item.preferred_term">
              {{ item.preferred_term }}
            </div>
            <div class="text-caption text-medium-emphasis">
              {{ item.concept_id }}
            </div>
          </template>
          <!-- Null for a term whose membership just ended: the release does not define
               it, so there is no change of its own to report. -->
          <template #[`item.change_status`]="{ item }">
            <v-chip
              v-if="item.change_status"
              size="small"
              variant="tonal"
              :color="changeStatusColor(item.change_status)"
            >
              {{
                $t(`StandardsImport.change_${item.change_status.toLowerCase()}`)
              }}
            </v-chip>
            <span v-else class="text-medium-emphasis">&mdash;</span>
          </template>
          <template #[`item.membership_change`]="{ item }">
            <v-chip
              v-if="item.membership_change"
              size="small"
              variant="tonal"
              :color="membershipChangeColor(item.membership_change)"
            >
              {{
                $t(
                  `StandardsImport.membership_${item.membership_change.toLowerCase()}`
                )
              }}
            </v-chip>
            <span v-else class="text-medium-emphasis">&mdash;</span>
          </template>
          <template #[`item.findings`]="{ item }">
            <FindingIssuesChip
              :open="countFindings(item, 'OPEN')"
              :informational="countFindings(item, 'INFORMATIONAL')"
            />
          </template>
        </v-data-table>
      </v-sheet>
    </template>

    <ResolveInconsistencyDialog
      :open="resolveDialogOpen"
      :item="selectedFinding"
      @close="resolveDialogOpen = false"
      @resolved="onResolved"
    />
  </div>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import AttributeDiff from './AttributeDiff.vue'
import ChangelogEntryList from './ChangelogEntryList.vue'
import FindingIssuesChip from './FindingIssuesChip.vue'
import ReviewStateChip from './ReviewStateChip.vue'
import ResolveInconsistencyDialog from './ResolveInconsistencyDialog.vue'
import FindingDetails from './FindingDetails.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import EnumInfoTooltip from '@/components/tools/EnumInfoTooltip.vue'
import { useStandardsImportTypeDescriptionsStore } from '@/stores/standardsImportTypeDescriptions'
import codelistsApi from '@/api/standardsImport/codelists'
import inconsistenciesApi from '@/api/standardsImport/inconsistencies'
import {
  FINDING_STATUSES,
  attributeLabelKey,
  canResolveFinding,
  canUndoFinding,
  changeStatusColor,
  findingStatusColor,
  findingTypeLabel,
  toggleIcon,
} from '@/utils/standardsImport'

const { t } = useI18n()
const notificationHub = inject('notificationHub')

const props = defineProps({
  effectiveDate: {
    type: String,
    required: true,
  },
  codelistId: {
    type: String,
    required: true,
  },
})
// `open-term`: a term row was clicked; the dialog holding this view opens it in place.
const emit = defineEmits(['resolved', 'open-term'])

const detail = ref(null)
const loading = ref(false)
const error = ref('')
const resolveDialogOpen = ref(false)
const selectedFinding = ref({})
const markingReviewed = ref(false)

// The same two actions the finding queue offers, under the same conditions.
const actions = [
  {
    label: t('StandardsImport.resolve'),
    icon: 'mdi-check-decagram',
    condition: canResolveFinding,
    click: (finding) => {
      selectedFinding.value = finding
      resolveDialogOpen.value = true
    },
  },
  {
    label: t('StandardsImport.undo_resolution'),
    icon: 'mdi-undo',
    condition: canUndoFinding,
    click: undoResolution,
  },
]

const isNew = computed(() => detail.value?.change_status === 'NEW')
const changesByField = computed(
  () => new Map((detail.value?.changes || []).map((c) => [c.field, c]))
)

// What an attribute held before this release, where it changes it; otherwise the
// value as it stands, so an unchanged row diffs against itself and shows plain.
function previousValue(attribute) {
  const change = changesByField.value.get(attribute.field)
  return change && !isNew.value ? change.old_value : attribute.value
}

function currentValue(attribute) {
  const change = changesByField.value.get(attribute.field)
  return change ? change.new_value : attribute.value
}
const terms = computed(() => detail.value?.terms || [])
// The codelist's own findings only; its terms' are counted in the terms card. Each
// carries the term a membership finding (a duplicate, a changed submission value) is
// about, from `related_concept_id` - by code alone if the term is not listed.
// What still needs someone first, settled findings after.
const findings = computed(() => {
  const termsById = new Map(terms.value.map((term) => [term.concept_id, term]))
  return (detail.value?.findings || [])
    .map((finding) => ({
      ...finding,
      term: finding.related_concept_id
        ? termsById.get(finding.related_concept_id) || {
            concept_id: finding.related_concept_id,
          }
        : null,
    }))
    .sort(
      (a, b) =>
        FINDING_STATUSES.indexOf(a.status) - FINDING_STATUSES.indexOf(b.status)
    )
})
// Mirrors `blocks_review` in the API: a review means someone looked at everything on
// the codelist and its terms, so an unacknowledged INFORMATIONAL finding holds it up
// too - including the term ones this view only counts.
const REVIEW_BLOCKING_STATUSES = ['OPEN', 'INFORMATIONAL']
function blocksReview(finding) {
  return REVIEW_BLOCKING_STATUSES.includes(finding.status)
}
const hasOpenFindings = computed(
  () =>
    findings.value.some(blocksReview) ||
    terms.value.some((term) => (term.findings || []).some(blocksReview))
)

// The terms card's filters. "Changed" is the term's own change - NEW or UPDATED; a
// membership opening or closing is the membership filter's business.
const MEMBERSHIP_CHANGES = ['ADDED', 'ENDED']
const CHANGED_TERM_STATUSES = ['NEW', 'UPDATED']
const changedTermsOnly = ref(false)
const membershipFilter = ref(null)
const termsWithFindingsOnly = ref(false)
const shownTerms = computed(() =>
  terms.value.filter(
    (term) =>
      (!changedTermsOnly.value ||
        CHANGED_TERM_STATUSES.includes(term.change_status)) &&
      (!membershipFilter.value ||
        term.membership_change === membershipFilter.value) &&
      (!termsWithFindingsOnly.value || term.findings?.length)
  )
)

const termHeaders = [
  { title: t('StandardsImport.col_term'), key: 'term', sortable: false },
  { title: t('StandardsImport.col_change_type'), key: 'change_status' },
  {
    title: t('StandardsImport.codelist_col_membership'),
    key: 'membership_change',
  },
  {
    title: t('StandardsImport.codelist_col_findings'),
    key: 'findings',
    sortable: false,
  },
]

function membershipChangeColor(change) {
  return change === 'ADDED' ? 'success' : 'error'
}

function countFindings(term, status) {
  return (term.findings || []).filter((finding) => finding.status === status)
    .length
}

// `reset` blanks the view first, for a different codelist. After a decision it stays
// up while the new state loads, so the cards do not vanish and reappear.
function load({ reset = true } = {}) {
  if (reset) {
    detail.value = null
  }
  loading.value = true
  error.value = ''
  // `show=all`: the terms card lists the whole codelist, not only what changed.
  codelistsApi
    .getCodelist(props.effectiveDate, props.codelistId, { show: 'all' })
    .then((response) => {
      detail.value = response.data
    })
    .catch((err) => {
      error.value =
        err.response?.data?.message || t('StandardsImport.codelist_load_error')
    })
    .finally(() => {
      loading.value = false
    })
}

// A decision moves the finding's status, and can move the codelist's review state with
// it (a reviewed codelist with a finding reopened is stale again), so the whole detail
// is asked for afresh - and whoever holds counts about the release is told.
function onResolved() {
  load({ reset: false })
  emit('resolved')
}

function undoResolution(finding) {
  inconsistenciesApi.deleteResolution(finding.uid).then(() => {
    notificationHub.add({
      type: 'success',
      msg: t('StandardsImport.undo_success'),
    })
    onResolved()
  })
}

// The review state moves the release's progress counts and the table row behind this
// view, so it is reported the same way a settled finding is.
function markReviewed() {
  markingReviewed.value = true
  codelistsApi
    .markReviewed(props.effectiveDate, props.codelistId)
    .then(() => {
      notificationHub.add({
        type: 'success',
        msg: t('StandardsImport.codelist_mark_reviewed_success'),
      })
      onResolved()
    })
    .finally(() => {
      markingReviewed.value = false
    })
}

watch(
  () => [props.effectiveDate, props.codelistId],
  () => load(),
  { immediate: true }
)

// For the dialog, once a finding was settled from a term opened off this codelist:
// this view stays mounted behind the term, so it would otherwise show what it held
// before. In place, so the terms card keeps its filters.
defineExpose({ reload: () => load({ reset: false }) })

// The type tooltips read from here; only the releases list loads it otherwise, and a
// release page can be opened straight from its URL. Fetched once per session.
useStandardsImportTypeDescriptionsStore()
  .fetchTypeDescriptions()
  .catch(() => {})
</script>

<style scoped>
.card-title {
  color: rgb(var(--v-theme-nnTrueBlue));
  font-size: 1.375rem;
  font-weight: 700;
  line-height: 1.75rem;
}
.attribute-column {
  width: 180px;
}
.actions-column {
  width: 56px;
}
/* Values run to several lines; the label stays level with their first one. */
td {
  vertical-align: top;
}
/* An outlined button draws its border in the text colour, black at rest and blue when
   on; the button group beside these keeps the theme's grey border either way. */
.filter-toggle {
  border-color: rgba(var(--v-border-color), var(--v-border-opacity));
}
</style>
