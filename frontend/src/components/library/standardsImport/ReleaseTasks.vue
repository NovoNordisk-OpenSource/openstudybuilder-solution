<template>
  <v-sheet color="white" rounded="xl" elevation="0" class="pa-4 h-100">
    <div class="page-title mb-1">
      {{ $t('StandardsImport.tasks_title') }}
    </div>

    <!-- One panel per step of the import, in the order they are done. A step the
         release cannot have reached yet still opens, so anyone can see what it will
         ask of them, but it is faded and none of its buttons does anything: the whole
         road stays visible without inviting anyone down it early. -->
    <v-expansion-panels
      v-model="openSections"
      multiple
      variant="accordion"
      flat
      data-cy="standards-import-task-sections"
    >
      <v-expansion-panel
        v-for="(section, index) in sections"
        :key="section.key"
        :value="section.key"
        :class="{ 'section-unavailable': !section.available }"
        :data-cy="`standards-import-section-${section.key}`"
      >
        <v-expansion-panel-title>
          <span
            class="font-weight-bold"
            :class="{ 'text-primary': section.key === currentSection }"
          >
            {{ index + 1 }}. {{ section.title }}
          </span>
          <v-chip
            class="ml-3"
            size="small"
            variant="tonal"
            :color="SECTION_STATE_COLOR[sectionState(index)]"
            :data-cy="`standards-import-section-${section.key}-state`"
          >
            {{ $t(`StandardsImport.section_state_${sectionState(index)}`) }}
          </v-chip>
          <!-- Offered whatever the state of the step, and even on a step that is not
               reachable yet: it only reads. `.stop` keeps it from folding the panel. -->
          <v-btn
            v-if="section.extraAction"
            class="ml-3"
            size="small"
            variant="outlined"
            color="primary"
            rounded="xl"
            :disabled="section.extraAction.disabled"
            :data-cy="`standards-import-task-${section.extraAction.key}-open`"
            @click.stop="emit('open', section.extraAction.task)"
          >
            {{ section.extraAction.label }}
          </v-btn>
          <!-- `.stop` so the click runs the action without also folding the panel.
               The tooltip hangs off a wrapper because a disabled button receives no
               hover, and a disabled one is exactly where the reason matters. A
               completed step offers no action: the release has moved past it —
               unless the action says it stays until the release is imported. -->
          <template
            v-if="
              section.action &&
              (sectionState(index) !== 'completed' ||
                (section.action.keepUntilImported && stage !== 'imported'))
            "
          >
            <span
              v-if="section.action.running"
              class="ml-3 d-flex align-center text-body-2 text-info"
              :data-cy="`standards-import-task-${section.action.key}-running`"
            >
              <v-progress-circular
                indeterminate
                size="16"
                width="2"
                class="mr-2"
              />
              {{ section.action.runningLabel }}
            </span>
            <v-tooltip
              v-else
              location="top"
              max-width="400"
              :text="section.action.hint"
            >
              <template #activator="{ props: tooltipProps }">
                <span v-bind="tooltipProps" class="ml-2">
                  <v-btn
                    size="small"
                    variant="outlined"
                    color="primary"
                    rounded="xl"
                    :disabled="section.action.disabled || !section.available"
                    :data-cy="`standards-import-task-${section.action.key}-open`"
                    @click.stop="emit('open', section.action.task)"
                  >
                    {{ section.action.label }}
                  </v-btn>
                </span>
              </template>
            </v-tooltip>
          </template>
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <v-alert
            v-for="(task, taskIndex) in section.tasks"
            :key="task.key"
            :type="task.type"
            variant="tonal"
            class="alert-bordered"
            :class="{ 'mt-3': taskIndex > 0 }"
            :data-cy="`standards-import-task-${task.key}`"
          >
            <div class="font-weight-bold">
              {{ task.title }}
            </div>
            <div class="text-body-2 mt-1">
              {{ task.text }}
            </div>
            <ul v-if="task.details?.length" class="text-body-2 mt-1 pl-5">
              <li v-for="detail in task.details" :key="detail">
                {{ detail }}
              </li>
            </ul>
            <template #append>
              <v-btn
                variant="text"
                rounded="xl"
                :disabled="task.disabled || !section.available"
                :data-cy="`standards-import-task-${task.key}-open`"
                @click="emit('open', task.task)"
              >
                {{ task.action }}
              </v-btn>
            </template>
          </v-alert>
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>
  </v-sheet>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { releaseStage } from '@/utils/standardsImport'

const { t } = useI18n()

const props = defineProps({
  release: {
    type: Object,
    default: null,
  },
  mandatoryCatalogues: {
    type: Array,
    default: () => [],
  },
  locked: {
    type: Boolean,
    default: false,
  },
  // Open review items by the step that raised them, then by `entity_type`, e.g.
  // `{ ANALYSIS: { CODELIST: 2 }, SPONSOR_IMPACT: { TERM: 1 } }`.
  openInconsistencies: {
    type: Object,
    default: () => ({}),
  },
  // An analysis started from this page and still running. The release only says
  // ANALYZING once the job has been accepted, and the page knows sooner than that.
  analysisRunning: {
    type: Boolean,
    default: false,
  },
  // The same as `analysisRunning`, for the sponsor impact assessment.
  assessmentRunning: {
    type: Boolean,
    default: false,
  },
  // CDISC conflict decisions made since the last analysis, so not applied yet.
  pendingDecisions: {
    type: Number,
    default: 0,
  },
  // `can_import` and `blockers` of the release dashboard: the same check
  // `POST /import` makes, so the approval is offered exactly when it would be accepted.
  // Null while not loaded, or while the release cannot be at that step yet.
  importReadiness: {
    type: Object,
    default: null,
  },
  // The same as `analysisRunning`, for the import.
  importRunning: {
    type: Boolean,
    default: false,
  },
})
const emit = defineEmits(['open'])

const BUSY_STATUSES = ['ANALYZING', 'ASSESSING']

const stage = computed(() =>
  releaseStage(props.release, {
    pendingDecisions: props.pendingDecisions,
    canImport: !!props.importReadiness?.can_import,
  })
)

const staged = computed(() =>
  (props.release?.files || []).map((file) => file.catalogue)
)

// Presence-only, mirroring `guard_mandatory_catalogues_present` in the API: extra
// catalogues beyond the mandatory set are fine. Matching it matters — this box is
// what tells someone whether analysis will be accepted, and the two disagreeing
// would be worse than not showing it at all.
const missingCatalogues = computed(() =>
  props.mandatoryCatalogues.filter((name) => !staged.value.includes(name))
)

const packageFilesComplete = computed(
  () => staged.value.length > 0 && !missingCatalogues.value.length
)

const packageFilesText = computed(() => {
  if (!staged.value.length) {
    return t('StandardsImport.packages_task_empty')
  }
  if (missingCatalogues.value.length) {
    return t('StandardsImport.packages_task_missing', {
      catalogues: missingCatalogues.value.join(', '),
    })
  }
  return t('StandardsImport.packages_task_complete', {
    count: staged.value.length,
  })
})

// `changelog_catalogues` counts catalogues rather than files, because that is what a
// re-upload replaces — so it is also the honest thing to report against the number of
// catalogues staged. Done means every staged catalogue is covered: stopping at the
// first sheet would call the task finished with catalogues still unannotated.
const changelogComplete = computed(
  () =>
    staged.value.length > 0 &&
    (props.release?.changelog_catalogues || 0) >= staged.value.length
)

const changelogText = computed(() => {
  if (!props.release) {
    return t('StandardsImport.supporting_files_need_packages')
  }
  return props.release.changelog_catalogues
    ? t('StandardsImport.changelog_task_uploaded', {
        count: props.release.changelog_catalogues,
        total: staged.value.length,
      })
    : t('StandardsImport.changelog_task_none')
})

// A count of files, not of catalogues: `StagedPairingFile` records the workbook and the
// sheets read from it and never which catalogue it belongs to, so one workbook is as far
// as this can be taken — there is nothing to check coverage against.
const pairingsComplete = computed(() => !!props.release?.pairing_files)

const pairingsText = computed(() => {
  if (!props.release) {
    return t('StandardsImport.supporting_files_need_packages')
  }
  return props.release.pairing_files
    ? t('StandardsImport.pairings_task_uploaded', {
        count: props.release.pairing_files,
      })
    : t('StandardsImport.pairings_task_none')
})

// `analyzed_at` rather than the status, which moves on for other reasons: a
// release can be BLOCKED or IMPORTED and still have been analysed. The timestamp is
// only written once the job succeeds, so a first analysis under way is still "not
// analysed" here.
const analysed = computed(() => !!props.release?.analyzed_at)

const analysisInProgress = computed(
  () => props.analysisRunning || props.release?.status === 'ANALYZING'
)

// The API refuses analysis while another background job holds the same release,
// and while a mandatory catalogue is missing.
const analysisRunnable = computed(
  () =>
    packageFilesComplete.value &&
    !props.locked &&
    !analysisInProgress.value &&
    !BUSY_STATUSES.includes(props.release?.status)
)

const analysisText = computed(() => {
  if (BUSY_STATUSES.includes(props.release?.status)) {
    return t('StandardsImport.analysis_task_running')
  }
  if (!packageFilesComplete.value) {
    return t('StandardsImport.analysis_task_blocked')
  }
  return analysed.value
    ? t('StandardsImport.analysis_task_done')
    : t('StandardsImport.analysis_task_ready')
})

function openCount(reviewPass, entityType) {
  const byEntity = props.openInconsistencies[reviewPass] || {}
  return entityType
    ? byEntity[entityType] || 0
    : Object.values(byEntity).reduce((sum, count) => sum + count, 0)
}

const openCdiscConflicts = computed(() => openCount('ANALYSIS'))

// An assessment only describes the release if it is newer than the last analysis —
// the same comparison `releaseStage` makes.
const assessmentCurrent = computed(
  () =>
    !!props.release?.assessed_at &&
    new Date(props.release.assessed_at) > new Date(props.release.analyzed_at)
)

// Every conflict has a decision, but at least one is not in the staged values yet:
// the next analysis applies them, and shows whether they settled everything.
const resolutionsToVerify = computed(
  () =>
    analysed.value && !openCdiscConflicts.value && props.pendingDecisions > 0
)

const assessmentInProgress = computed(
  () => props.assessmentRunning || props.release?.status === 'ASSESSING'
)

const importInProgress = computed(
  () => props.importRunning || props.release?.status === 'IMPORTING'
)

// The same refusals as the API's `guard_assessable`.
const assessmentRunnable = computed(
  () =>
    analysed.value &&
    !openCdiscConflicts.value &&
    !props.pendingDecisions &&
    !props.locked &&
    !assessmentInProgress.value &&
    !importInProgress.value &&
    !BUSY_STATUSES.includes(props.release?.status)
)

const assessmentText = computed(() => {
  if (props.release?.status === 'ASSESSING') {
    return t('StandardsImport.sponsor_impact_task_running')
  }
  if (openCdiscConflicts.value) {
    return t('StandardsImport.sponsor_impact_task_blocked')
  }
  if (props.pendingDecisions) {
    return t('StandardsImport.sponsor_impact_task_needs_verification')
  }
  return assessmentCurrent.value
    ? t('StandardsImport.sponsor_impact_task_done')
    : t('StandardsImport.sponsor_impact_task_ready')
})

// A review is mandatory, so it stays a warning until there is something to review and
// nothing left open in it — not reachable yet is no more done than items still open.
function reviewTask({ key, task, titleKey, count, ready, notReadyKey }) {
  return {
    key,
    task,
    title: t(`StandardsImport.${titleKey}`),
    type: ready && !count ? 'success' : 'warning',
    text: !ready
      ? t(`StandardsImport.${notReadyKey}`)
      : count
        ? t('StandardsImport.review_task_open', { count })
        : t('StandardsImport.review_task_clear'),
    action: t('StandardsImport.review'),
    disabled: !ready,
  }
}

const reviewSection = computed(() => ({
  key: 'review',
  title: t('StandardsImport.section_review'),
  available: true,
  extraAction: {
    key: 'pre-review-diff',
    task: 'packageDiff',
    label: t('StandardsImport.pre_review_diff'),
    disabled: !staged.value.length,
  },
  tasks: [
    {
      key: 'package-files',
      task: 'packageFiles',
      title: t('StandardsImport.task_packages'),
      type: packageFilesComplete.value ? 'success' : 'warning',
      text: packageFilesText.value,
      action: t('StandardsImport.upload'),
      disabled: props.locked,
    },
    // Never warning, even when empty: without it the diffs simply carry no CDISC
    // annotation, and nothing on the import path gates on that. Success once every
    // staged catalogue is covered.
    {
      key: 'changelog',
      task: 'changelog',
      title: t('StandardsImport.task_changelog'),
      type: changelogComplete.value ? 'success' : 'info',
      text: changelogText.value,
      action: t('StandardsImport.upload'),
      disabled: props.locked || !props.release,
    },
    // Never warning either: a release with no pairing workbook imports perfectly
    // well, it simply records no codelist pairings.
    {
      key: 'pairing-workbooks',
      task: 'pairingWorkbooks',
      title: t('StandardsImport.task_pairings'),
      type: pairingsComplete.value ? 'success' : 'info',
      text: pairingsText.value,
      action: t('StandardsImport.upload'),
      disabled: props.locked || !props.release,
    },
  ],
}))

// Only once there is an analysis does the conflict review mean anything: before that
// the queue is empty because nothing has looked, which is not the same as nothing to
// review.
const cdiscSection = computed(() => ({
  key: 'cdisc',
  title: t('StandardsImport.section_cdisc_conflicts'),
  available: !!props.release && (packageFilesComplete.value || analysed.value),
  // Running the analysis is what the section is for rather than one task in it, so it
  // sits in the header, next to the state it moves on.
  action: {
    key: 'analysis',
    task: 'analysis',
    label: analysed.value
      ? t('StandardsImport.reanalyse')
      : t('StandardsImport.run_analysis'),
    hint: analysisText.value,
    disabled: !analysisRunnable.value,
    running: analysisInProgress.value,
    runningLabel: t('StandardsImport.analysis_in_progress'),
  },
  tasks: [
    reviewTask({
      key: 'cdisc-conflicts',
      task: 'reviewCdiscConflicts',
      titleKey: 'task_review_cdisc_conflicts',
      count: openCdiscConflicts.value,
      ready: analysed.value,
      notReadyKey: 'review_task_needs_analysis',
    }),
    // Only while there is something to verify: the analysis that verifies it is
    // also what makes the box go away.
    ...(resolutionsToVerify.value
      ? [
          {
            key: 'verify-resolutions',
            task: 'analysis',
            title: t('StandardsImport.task_verify_resolutions'),
            type: 'warning',
            text: t('StandardsImport.verify_resolutions_text'),
            action: t('StandardsImport.reanalyse'),
            disabled: !analysisRunnable.value,
          },
        ]
      : []),
  ],
}))

// The two review boxes split the sponsor impact findings by their own `entity_type`,
// so between them they account for every one — none is left without a box to answer
// it in.
const assessmentSection = computed(() => ({
  key: 'assessment',
  title: t('StandardsImport.section_sponsor_impact'),
  available:
    analysed.value &&
    ((!openCdiscConflicts.value && !props.pendingDecisions) ||
      !!props.release.assessed_at),
  // In the header like the analysis, and for the same reason. Kept at the import
  // step: sponsor data can change while the release waits for approval.
  action: {
    keepUntilImported: true,
    key: 'sponsor-impact',
    task: 'sponsorImpact',
    label: props.release?.assessed_at
      ? t('StandardsImport.reassess_sponsor_impact')
      : t('StandardsImport.run_sponsor_impact'),
    hint: assessmentText.value,
    disabled: !assessmentRunnable.value,
    running: assessmentInProgress.value,
    runningLabel: t('StandardsImport.sponsor_impact_in_progress'),
  },
  tasks: [
    reviewTask({
      key: 'review-codelists',
      task: 'reviewCodelists',
      titleKey: 'task_review_codelists',
      count: openCount('SPONSOR_IMPACT', 'CODELIST'),
      ready: assessmentCurrent.value,
      notReadyKey: 'review_task_needs_assessment',
    }),
    reviewTask({
      key: 'review-terms',
      task: 'reviewTerms',
      titleKey: 'task_review_terms',
      count: openCount('SPONSOR_IMPACT', 'TERM'),
      ready: assessmentCurrent.value,
      notReadyKey: 'review_task_needs_assessment',
    }),
  ],
}))

// Decided by the API alone: besides what this column can see, it also refuses while
// the MDR head is at or past this release, or while a CDISC term the release retires
// is still in use.
const importRunnable = computed(
  () =>
    !!props.importReadiness?.can_import &&
    !props.locked &&
    !importInProgress.value
)

const approveText = computed(() => {
  if (stage.value === 'imported') {
    return t('StandardsImport.approve_task_done')
  }
  if (importInProgress.value) {
    return t('StandardsImport.approve_task_running')
  }
  if (importRunnable.value) {
    // READY is only ever reached by an import that failed part-way.
    return props.release?.status === 'READY'
      ? t('StandardsImport.approve_task_retry')
      : t('StandardsImport.approve_task_ready')
  }
  return props.importReadiness?.blockers?.length
    ? t('StandardsImport.approve_task_blocked')
    : t('StandardsImport.approve_task_not_ready')
})

// The approval drives `POST /effective-dates/{date}/import`. While the API refuses it,
// its reasons are listed under the box, in its own words.
const importingSection = computed(() => ({
  key: 'importing',
  title: t('StandardsImport.section_importing'),
  available:
    ['importing', 'imported'].includes(stage.value) ||
    (assessmentCurrent.value &&
      !openCdiscConflicts.value &&
      !openCount('SPONSOR_IMPACT')),
  tasks: [
    {
      key: 'approve',
      task: 'approve',
      title: t('StandardsImport.task_approve'),
      type:
        stage.value === 'imported'
          ? 'success'
          : importInProgress.value
            ? 'info'
            : 'warning',
      text: approveText.value,
      details:
        importRunnable.value || importInProgress.value || props.locked
          ? []
          : props.importReadiness?.blockers || [],
      action: t('StandardsImport.approve'),
      disabled: !importRunnable.value,
    },
  ],
}))

const sections = computed(() => [
  reviewSection.value,
  cdiscSection.value,
  assessmentSection.value,
  importingSection.value,
])

// `releaseStage` suffix -> the section doing that step's work.
const SECTION_OF_STAGE = {
  review: 'review',
  analysis: 'cdisc',
  assessment: 'assessment',
  importing: 'importing',
  imported: 'importing',
}

const currentSection = computed(() => SECTION_OF_STAGE[stage.value] || 'review')

const SECTION_STATE_COLOR = {
  in_progress: 'info',
  completed: 'success',
  upcoming: 'grey',
}

// Read off the release's stage alone, like the section that opens by itself: what
// comes before it is done, what comes after it has not started. An imported release
// has finished its last step too.
function sectionState(index) {
  if (stage.value === 'imported') {
    return 'completed'
  }
  const current = sections.value.findIndex(
    (section) => section.key === currentSection.value
  )
  if (index < current) {
    return 'completed'
  }
  return index === current ? 'in_progress' : 'upcoming'
}

// The current step opens by itself, on arrival and whenever the release moves on;
// anything the reader opened or closed by hand is left as it is.
const openSections = ref([])
watch(
  currentSection,
  (section) => {
    if (!openSections.value.includes(section)) {
      openSections.value = [...openSections.value, section]
    }
  },
  { immediate: true }
)
</script>

<style scoped lang="scss">
// Faded grey rather than Vuetify's disabled panel, which is a heavy dark grey and
// cannot be opened at all. Grayscale takes the colour out of the task boxes too, so a
// yellow "still to do" there does not read as something to do now.
.section-unavailable {
  :deep(.v-expansion-panel-title),
  :deep(.v-expansion-panel-text) {
    filter: grayscale(1);
    opacity: 0.55;
  }
}
</style>
