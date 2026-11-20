<template>
  <div>
    <div class="text-subtitle-2 text-medium-emphasis">
      {{ $t('StandardsImport.col_term') }}
    </div>
    <div class="d-flex align-center flex-wrap">
      <div class="text-h5">
        {{ detail?.preferred_term || conceptId }}
      </div>
      <template v-if="detail">
        <!-- Null for a term the release no longer ships: it has no change of its own,
             only memberships closing - which the alert below says. -->
        <v-chip
          v-if="detail.change_status"
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
        <!-- Placed as on the codelist view, and refused up front for the same reason.
             It does nothing yet: the API keys every review mark on a codelist, and a
             term's state is only inherited from the codelists holding it. -->
        <v-tooltip
          v-if="detail.review?.status !== 'REVIEWED'"
          :disabled="!hasOpenFindings"
          location="top"
          :text="$t('StandardsImport.term_mark_reviewed_blocked')"
        >
          <template #activator="{ props: tooltipProps }">
            <span v-bind="tooltipProps">
              <v-btn
                variant="outlined"
                color="primary"
                rounded="xl"
                prepend-icon="mdi-check-circle-outline"
                :disabled="hasOpenFindings"
                data-cy="standards-import-term-mark-reviewed"
              >
                {{ $t('StandardsImport.codelist_mark_reviewed') }}
              </v-btn>
            </span>
          </template>
        </v-tooltip>
      </template>
    </div>
    <div v-if="detail" class="text-medium-emphasis mt-1">
      {{ detail.concept_id }}
    </div>

    <!-- Which of the term's codelists the membership card and the pair findings are
         about. The term's own findings and attributes do not depend on it. -->
    <template v-if="detail">
      <v-select
        v-if="codelists.length"
        v-model="selectedCodelistId"
        :items="codelists"
        :item-title="codelistTitle"
        item-value="codelist_id"
        :label="$t('StandardsImport.term_codelist')"
        hide-details
        class="codelist-select mt-4"
        data-cy="standards-import-term-codelist"
      />
      <div v-else class="text-medium-emphasis mt-4">
        {{ $t('StandardsImport.term_no_codelists') }}
      </div>
    </template>

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
      <!-- First, as on the codelist view: a finding is what can hold the release back.
           The term's own findings hold wherever it is held, so they stay listed
           whichever codelist is selected; a pair finding only under its codelist. -->
      <v-sheet color="white" rounded="xl" elevation="0" class="pa-4 mt-4">
        <div class="card-title mb-3">
          {{ $t('StandardsImport.codelist_findings') }}
        </div>
        <div v-if="!findings.length" class="text-medium-emphasis">
          {{ $t('StandardsImport.term_no_findings') }}
        </div>
        <v-table
          v-else
          class="review-table"
          density="comfortable"
          data-cy="standards-import-term-findings"
        >
          <thead>
            <tr>
              <th class="actions-column" />
              <th>{{ $t('StandardsImport.type') }}</th>
              <th>{{ $t('StandardsImport.col_codelist') }}</th>
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
                <template v-if="finding.codelist">
                  <div class="font-weight-medium">
                    {{
                      finding.codelist.submission_value ||
                      finding.codelist.codelist_id
                    }}
                  </div>
                  <div class="text-caption text-medium-emphasis">
                    {{ finding.codelist.codelist_id }}
                  </div>
                </template>
                <span v-else class="text-medium-emphasis">
                  {{ $t('StandardsImport.term_findings_every_codelist') }}
                </span>
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

      <!-- The term inside the selected codelist: whether the release opens or closes
           the membership, and its submission value there on either side. -->
      <v-sheet
        v-if="selectedCodelist"
        color="white"
        rounded="xl"
        elevation="0"
        class="pa-4 mt-4"
      >
        <div class="d-flex align-center mb-3">
          <div class="card-title">
            {{ $t('StandardsImport.term_membership') }}
          </div>
          <v-chip
            size="small"
            variant="tonal"
            class="ml-3"
            :color="membershipChangeColor(selectedCodelist.membership_change)"
          >
            {{
              selectedCodelist.membership_change
                ? $t(
                    `StandardsImport.membership_${selectedCodelist.membership_change.toLowerCase()}`
                  )
                : $t('StandardsImport.term_membership_unchanged')
            }}
          </v-chip>
        </div>
        <v-table
          class="review-table"
          density="comfortable"
          data-cy="standards-import-term-membership"
        >
          <thead>
            <tr>
              <th class="attribute-column">
                {{ $t('StandardsImport.codelist_col_attribute') }}
              </th>
              <th>{{ $t('StandardsImport.codelist_col_previous') }}</th>
              <th>{{ $t('StandardsImport.codelist_col_this_release') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td class="font-weight-medium py-2">
                {{ $t(attributeLabelKey('submission_value')) }}
              </td>
              <td class="py-2">
                <AttributeDiff
                  v-if="submissionValues.previous != null"
                  :old-value="submissionValues.previous"
                  :new-value="
                    submissionValues.current ?? submissionValues.previous
                  "
                  side="old"
                />
                <span v-else class="text-medium-emphasis">
                  {{ $t('StandardsImport.term_not_a_member') }}
                </span>
              </td>
              <td class="py-2">
                <AttributeDiff
                  v-if="submissionValues.current != null"
                  :old-value="
                    submissionValues.previous ?? submissionValues.current
                  "
                  :new-value="submissionValues.current"
                  side="new"
                />
                <span v-else class="text-medium-emphasis">
                  {{ $t('StandardsImport.term_not_a_member') }}
                </span>
              </td>
            </tr>
          </tbody>
        </v-table>
      </v-sheet>

      <!-- What is already built on the term: what a change to it, or its leaving a
           codelist, would land on. Read live, and over the whole term - a reference
           goes to the term, not to the codelist it was picked from. -->
      <v-sheet color="white" rounded="xl" elevation="0" class="pa-4 mt-4">
        <div class="d-flex align-center mb-1">
          <div class="card-title">{{ $t('StandardsImport.term_usage') }}</div>
          <v-chip
            v-if="usageTotal"
            size="small"
            variant="tonal"
            color="warning"
            class="ml-3"
          >
            {{ $t('StandardsImport.term_usage_count', usageTotal) }}
          </v-chip>
        </div>
        <div class="text-caption text-medium-emphasis mb-3">
          {{ $t('StandardsImport.term_usage_hint') }}
        </div>
        <div v-if="isNew" class="text-medium-emphasis">
          {{ $t('StandardsImport.term_usage_new') }}
        </div>
        <div v-else-if="!detail.usage.length" class="text-medium-emphasis">
          {{ $t('StandardsImport.term_usage_none') }}
        </div>
        <v-table
          v-else
          class="review-table"
          density="comfortable"
          data-cy="standards-import-term-usage"
        >
          <thead>
            <tr>
              <th>{{ $t('StandardsImport.term_usage_col_consumer') }}</th>
              <th>{{ $t('StandardsImport.term_usage_col_through') }}</th>
              <th>{{ $t('StandardsImport.term_usage_col_relationship') }}</th>
              <th class="text-right">
                {{ $t('StandardsImport.term_usage_col_count') }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(entry, index) in detail.usage" :key="index">
              <td class="font-weight-medium py-2">
                {{ entry.consumer_labels.join(' / ') }}
              </td>
              <td class="py-2">{{ usageThroughLabel(entry.through) }}</td>
              <td class="py-2 text-medium-emphasis">
                {{ entry.relationship }}
              </td>
              <td class="py-2 text-right">{{ entry.count }}</td>
            </tr>
          </tbody>
        </v-table>
      </v-sheet>

      <v-sheet color="white" rounded="xl" elevation="0" class="pa-4 mt-4">
        <div class="card-title mb-3">
          {{ $t('StandardsImport.attributes') }}
        </div>

        <v-alert
          v-if="isNew"
          type="info"
          variant="tonal"
          class="alert-bordered mb-4"
          density="compact"
          :text="$t('StandardsImport.term_new_no_previous')"
        />
        <!-- The release says nothing about the term any more, so what is shown is
             what MDR holds - and the term keeps it, as nothing here deletes a term. -->
        <v-alert
          v-if="isDropped"
          type="info"
          variant="tonal"
          class="alert-bordered mb-4"
          density="compact"
          :text="$t('StandardsImport.term_dropped')"
        />
        <!-- Every attribute the release defines, changed or not. Those it changes carry
             the old and new words in one value, so what moved reads at a glance rather
             than by comparing two columns. A new term has nothing to set its values
             beside, so they are shown as they are. -->
        <v-table
          density="comfortable"
          class="review-table"
          data-cy="standards-import-term-attributes"
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

      <!-- Only once a terminology-changes sheet mentioning the term was uploaded. -->
      <v-sheet
        v-if="detail.changelog?.length"
        color="white"
        rounded="xl"
        elevation="0"
        class="pa-4 mt-4"
        data-cy="standards-import-term-changelog"
      >
        <div class="card-title mb-3">
          {{ $t('StandardsImport.diff_changelog_available') }}
        </div>
        <ChangelogEntryList :entries="detail.changelog" />
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
} from '@/utils/standardsImport'

const { t, te } = useI18n()
const notificationHub = inject('notificationHub')

const props = defineProps({
  effectiveDate: {
    type: String,
    required: true,
  },
  conceptId: {
    type: String,
    required: true,
  },
  // The codelist the term was opened from, selected first. Null from the terms table,
  // which lists a term once for all of its codelists.
  codelistId: {
    type: String,
    default: null,
  },
})
const emit = defineEmits(['resolved'])

const detail = ref(null)
const loading = ref(false)
const error = ref('')
const resolveDialogOpen = ref(false)
const selectedFinding = ref({})
const selectedCodelistId = ref(null)

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
const isDropped = computed(() => !!detail.value && !detail.value.change_status)
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
const codelists = computed(() => detail.value?.codelists || [])
const selectedCodelist = computed(
  () =>
    codelists.value.find(
      (codelist) => codelist.codelist_id === selectedCodelistId.value
    ) || null
)

// The term's own findings, then the selected codelist's pair findings, each carrying
// the codelist it is about (none for the term's own). What still needs someone first.
const findings = computed(() => {
  const termFindings = (detail.value?.findings || []).map((finding) => ({
    ...finding,
    codelist: null,
  }))
  const pairFindings = (selectedCodelist.value?.findings || []).map(
    (finding) => ({ ...finding, codelist: selectedCodelist.value })
  )
  return [...termFindings, ...pairFindings].sort(
    (a, b) =>
      FINDING_STATUSES.indexOf(a.status) - FINDING_STATUSES.indexOf(b.status)
  )
})
// Mirrors `blocks_review` in the API, over every codelist rather than the selected
// one: the term's review is inherited from all of them.
const REVIEW_BLOCKING_STATUSES = ['OPEN', 'INFORMATIONAL']
function blocksReview(finding) {
  return REVIEW_BLOCKING_STATUSES.includes(finding.status)
}
const hasOpenFindings = computed(
  () =>
    (detail.value?.findings || []).some(blocksReview) ||
    codelists.value.some((codelist) => codelist.findings.some(blocksReview))
)

// The term's submission value in the selected codelist, before and after the release;
// null on the side where the term is not a member. A membership the release ends
// carries the value MDR holds, so it belongs on the "before" side only.
const submissionValues = computed(() => {
  const codelist = selectedCodelist.value
  if (!codelist) {
    return { previous: null, current: null }
  }
  switch (codelist.membership_change) {
    case 'ADDED':
      return { previous: null, current: codelist.term_submission_value }
    case 'ENDED':
      return { previous: codelist.term_submission_value, current: null }
    default:
      return {
        previous:
          codelist.previous_submission_value ?? codelist.term_submission_value,
        current: codelist.term_submission_value,
      }
  }
})

const usageTotal = computed(() =>
  (detail.value?.usage || []).reduce((total, entry) => total + entry.count, 0)
)

// The API names the path in words of its own; one it adds later reads as it comes.
function usageThroughLabel(through) {
  const key = `StandardsImport.term_usage_through_${through.replaceAll(' ', '_')}`
  return te(key) ? t(key) : through
}

function codelistTitle(codelist) {
  const label = codelist.submission_value || codelist.codelist_id
  return codelist.name ? `${label} · ${codelist.name}` : label
}

function membershipChangeColor(change) {
  if (!change) {
    return undefined
  }
  return change === 'ADDED' ? 'success' : 'error'
}

// Keeps the reader's choice across a reload; otherwise the codelist the term was
// opened from, or the first one it belongs to.
function selectDefaultCodelist() {
  const ids = codelists.value.map((codelist) => codelist.codelist_id)
  if (ids.includes(selectedCodelistId.value)) {
    return
  }
  selectedCodelistId.value = ids.includes(props.codelistId)
    ? props.codelistId
    : ids[0] || null
}

// `reset` blanks the view first, for a different term. After a decision it stays up
// while the new state loads, so the cards do not vanish and reappear.
function load({ reset = true } = {}) {
  if (reset) {
    detail.value = null
    selectedCodelistId.value = null
  }
  loading.value = true
  error.value = ''
  codelistsApi
    .getTerm(props.effectiveDate, props.conceptId)
    .then((response) => {
      detail.value = response.data
      selectDefaultCodelist()
    })
    .catch((err) => {
      error.value =
        err.response?.data?.message || t('StandardsImport.term_load_error')
    })
    .finally(() => {
      loading.value = false
    })
}

// A decision moves the finding's status, and can move the review state of the
// codelists the term inherits it from, so the whole detail is asked for afresh - and
// whoever holds counts about the release is told.
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

watch(
  () => [props.effectiveDate, props.conceptId],
  () => load(),
  { immediate: true }
)

// The type tooltips read from here; only the releases list loads it otherwise.
// Fetched once per session.
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
.codelist-select {
  max-width: 480px;
}
/* Values run to several lines; the label stays level with their first one. */
td {
  vertical-align: top;
}
</style>
