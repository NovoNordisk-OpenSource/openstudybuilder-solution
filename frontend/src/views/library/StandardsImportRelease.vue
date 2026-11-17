<template>
  <div class="px-4 pb-4">
    <!-- The effective date is the page title, so the header carries no second copy of
         it. What is left is the release's state and the way back out. -->
    <div class="d-flex align-center">
      <div data-cy="page-title" class="page-title d-flex align-center">
        {{ isNewRelease ? $t('StandardsImport.new_release') : effectiveDate }}
        <HelpButton :help-text="$t('StandardsImport.general')" />
      </div>
      <v-chip
        v-if="stage"
        class="ml-3"
        size="small"
        variant="tonal"
        :color="releaseStatusColor(release.status)"
      >
        {{ $t(`StandardsImport.stage_${stage}`) }}
      </v-chip>
      <div v-if="isNewRelease" class="text-caption text-medium-emphasis ml-3">
        {{ $t('StandardsImport.new_release_hint') }}
      </div>
      <v-spacer />
      <!-- bg-white because `outlined` leaves the button transparent, and the page sits
           on the light-blue app background. -->
      <v-btn
        variant="outlined"
        color="primary"
        size="small"
        rounded="xl"
        class="bg-white"
        prepend-icon="mdi-arrow-left"
        :to="{ name: 'StandardsImport' }"
      >
        {{ $t('StandardsImport.back_to_releases') }}
      </v-btn>
    </div>

    <v-alert
      v-if="release?.status === 'IMPORTED'"
      type="info"
      variant="tonal"
      rounded="xl"
      class="alert-bordered mt-4"
      :text="$t('StandardsImport.release_locked')"
    />

    <v-row class="mt-4" align="stretch">
      <v-col cols="12" md="6">
        <ReleaseTasks
          :release="release"
          :mandatory-catalogues="mandatoryCatalogues"
          :open-inconsistencies="openInconsistencies"
          :pending-decisions="pendingDecisions"
          :locked="locked"
          :analysis-running="analysisRunning"
          :assessment-running="assessmentRunning"
          :import-readiness="importReadiness"
          :import-running="importRunning"
          @open="onOpenTask"
        />
      </v-col>
      <!-- The dashboard follows the step the release is at: while the CDISC
           conflicts are being settled, what matters is how they stand, not how much
           changed. The sponsor impact step weighs the changes themselves, so it keeps
           the counts and puts how far its own findings have got above them - and so
           does the approval, which is the last look before they land. -->
      <v-col cols="12" md="6">
        <CdiscFindingsDashboard
          v-if="stage === 'analysis'"
          :effective-date="effectiveDate"
          :release="release"
          @see-all="(type) => openQueue('ANALYSIS', type)"
        />
        <ReleaseChangeDashboard
          v-else
          ref="dashboard"
          :effective-date="effectiveDate"
        >
          <SponsorImpactProgress
            v-if="['assessment', 'importing'].includes(stage)"
            ref="progress"
            :effective-date="effectiveDate"
            :release="release"
          />
        </ReleaseChangeDashboard>
      </v-col>
    </v-row>

    <!-- One dialog for every task: only ever one is open, and the shell around the
         panel - title, scroll region, close - is the same whichever it is. Wide
         enough for the finding queue's columns and the six-column file tables, but
         not fullscreen: the release behind it stays visible, which is the context
         the panel acts on. -->
    <v-dialog
      :model-value="openTask !== null"
      max-width="1440px"
      scrollable
      persistent
    >
      <v-card color="dfltBackground" rounded="xl">
        <v-card-title>
          <div class="page-title">
            {{
              openTask ? $t(`StandardsImport.task_${TASK_TITLE[openTask]}`) : ''
            }}
          </div>
        </v-card-title>
        <v-divider />
        <v-card-text>
          <PackageFilesStep
            v-if="openTask === 'packageFiles'"
            :effective-date="effectiveDate"
            :disabled="locked"
            @effective-date-detected="onEffectiveDateDetected"
            @uploaded="onUploaded"
          />
          <SupportingFilesStep
            v-else-if="openTask === 'changelog'"
            :effective-date="effectiveDate"
            :disabled="locked"
            :sections="['changelog']"
            @uploaded="onUploaded"
          />
          <SupportingFilesStep
            v-else-if="openTask === 'pairingWorkbooks'"
            :effective-date="effectiveDate"
            :disabled="locked"
            :sections="['pairings']"
            @uploaded="onUploaded"
          />
          <!-- The flat finding queue: reached from the CDISC conflicts box, where the
               findings are about catalogues disagreeing and need no more context, and
               from the review tables, where a sponsor impact finding only means
               something once you know which concept it is about. -->
          <ReviewQueueStep
            v-else-if="openTask === 'resolveQueue'"
            :effective-date="effectiveDate"
            :release="release"
            :review-pass="queueReviewPass"
            :type="queueType"
            @resolved="onResolved"
          />
        </v-card-text>
        <v-divider />
        <v-card-actions class="bg-white border-t-thin py-4 px-6">
          <v-spacer />
          <v-btn
            color="primary"
            variant="flat"
            rounded="xl"
            min-width="120px"
            data-cy="standards-import-task-close"
            @click="openTask = null"
          >
            {{ $t('_global.close') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog
      v-model="reviewDialogOpen"
      fullscreen
      persistent
      content-class="fullscreen-dialog"
    >
      <ReleaseReviewDialog
        :effective-date="effectiveDate"
        :entity-type="reviewEntityType"
        @close="onReviewClosed"
        @resolved="onResolved"
      />
    </v-dialog>

    <v-dialog
      v-model="diffDialogOpen"
      fullscreen
      persistent
      content-class="fullscreen-dialog"
    >
      <PackageDiffDialog
        v-if="diffDialogOpen && diffCatalogue"
        :catalogue="diffCatalogue"
        :catalogues="stagedCatalogues"
        :effective-date="effectiveDate"
        @update:catalogue="diffCatalogue = $event"
        @close="diffDialogOpen = false"
      />
    </v-dialog>

    <ConfirmDialog ref="confirm" />
  </div>
</template>

<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import HelpButton from '@/components/tools/HelpButton.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import PackageFilesStep from '@/components/library/standardsImport/PackageFilesStep.vue'
import SupportingFilesStep from '@/components/library/standardsImport/SupportingFilesStep.vue'
import ReleaseTasks from '@/components/library/standardsImport/ReleaseTasks.vue'
import ReleaseChangeDashboard from '@/components/library/standardsImport/ReleaseChangeDashboard.vue'
import CdiscFindingsDashboard from '@/components/library/standardsImport/CdiscFindingsDashboard.vue'
import SponsorImpactProgress from '@/components/library/standardsImport/SponsorImpactProgress.vue'
import ReviewQueueStep from '@/components/library/standardsImport/ReviewQueueStep.vue'
import PackageDiffDialog from '@/components/library/standardsImport/PackageDiffDialog.vue'
import ReleaseReviewDialog from '@/components/library/standardsImport/ReleaseReviewDialog.vue'
import effectiveDatesApi from '@/api/standardsImport/effectiveDates'
import inconsistenciesApi from '@/api/standardsImport/inconsistencies'
import analysisApi from '@/api/standardsImport/analysis'
import sponsorImpactApi from '@/api/standardsImport/sponsorImpact'
import importsApi from '@/api/standardsImport/imports'
import codelistsApi from '@/api/standardsImport/codelists'
import jobsApi from '@/api/standardsImport/jobs'
import configApi from '@/api/standardsImport/config'
import { releaseStage, releaseStatusColor } from '@/utils/standardsImport'
import { useStandardsImportResolutionStrategiesStore } from '@/stores/standardsImportResolutionStrategies'

const { t } = useI18n()
const appStore = useAppStore()
const notificationHub = inject('notificationHub')
const resolutionStrategiesStore = useStandardsImportResolutionStrategiesStore()
const route = useRoute()
const router = useRouter()

// 'new' is the placeholder the dashboard's "Start new release" button routes to.
// The real effective date only becomes known once the first package file is
// uploaded — the API reads it out of the file, it is not client-chosen.
const NEW_RELEASE_PARAM = 'new'

// Task key -> the i18n suffix naming it, so the dialog heading matches the box the
// reader clicked rather than restating it in different words.
const TASK_TITLE = {
  packageFiles: 'packages',
  changelog: 'changelog',
  pairingWorkbooks: 'pairings',
  resolveQueue: 'resolve_queue',
}

// The two sponsor impact review tasks open the full-screen review tables instead of the
// shared dialog: they need the width, and the table they land on is the one the box
// named.
const REVIEW_TASK_ENTITY = {
  reviewCodelists: 'CODELIST',
  reviewTerms: 'TERM',
}

const effectiveDate = ref(
  route.params.effective_date === NEW_RELEASE_PARAM
    ? ''
    : route.params.effective_date
)
const release = ref(null)
const mandatoryCatalogues = ref([])
const openInconsistencies = ref({})
// When each CDISC conflict decision was made.
const cdiscDecisionTimes = ref([])
const openTask = ref(null)
const dashboard = ref(null)
const progress = ref(null)
const reviewDialogOpen = ref(false)
const diffDialogOpen = ref(false)
const diffCatalogue = ref('')
const reviewEntityType = ref('CODELIST')
// Which part of the finding queue the review task, tables or dashboard sent us to.
const queueReviewPass = ref('')
const queueType = ref('')
// An analysis or an assessment started from this page and not finished yet.
const analysisRunning = ref(false)
const assessmentRunning = ref(false)
const importRunning = ref(false)
// `can_import`, `blockers` and `catalogues` of the release dashboard, once the release
// is at a status the approval could be given from.
const importReadiness = ref(null)
const confirm = ref(null)

const stagedCatalogues = computed(() =>
  (release.value?.files || []).map((file) => file.catalogue)
)

const isNewRelease = computed(() => !effectiveDate.value)

// Once imported, the staging service refuses further uploads for the release.
const locked = computed(() =>
  ['IMPORTING', 'IMPORTED'].includes(release.value?.status)
)

function onOpenTask(task) {
  if (task === 'analysis') {
    runAnalysis()
    return
  }
  if (task === 'sponsorImpact') {
    runAssessment()
    return
  }
  if (task === 'approve') {
    runImport()
    return
  }
  if (task === 'packageDiff') {
    if (!stagedCatalogues.value.includes(diffCatalogue.value)) {
      diffCatalogue.value = stagedCatalogues.value[0] || ''
    }
    diffDialogOpen.value = !!diffCatalogue.value
    return
  }
  if (task === 'reviewCdiscConflicts') {
    openQueue('ANALYSIS')
    return
  }
  const entityType = REVIEW_TASK_ENTITY[task]
  if (entityType) {
    reviewEntityType.value = entityType
    reviewDialogOpen.value = true
    return
  }
  openTask.value = task
}

// Both dialogs at once would leave the queue behind a full-screen card, so the tables
// step aside; closing the queue is what brings them back.
function openQueue(reviewPass, type) {
  queueReviewPass.value = reviewPass || ''
  queueType.value = type || ''
  reviewDialogOpen.value = false
  openTask.value = 'resolveQueue'
}

// Decisions made since the last analysis: deciding only records the choice, and it is
// the next analysis that writes it into the staged values. Same test as the API's
// `count_decisions_since_analysis`, which refuses the assessment while any remain.
// Computed rather than counted on fetch, because the release and the findings load
// side by side and either can land first.
const pendingDecisions = computed(() => {
  if (!release.value) {
    return 0
  }
  const analyzedAt = release.value.analyzed_at
  return cdiscDecisionTimes.value.filter(
    (decidedAt) => !analyzedAt || new Date(decidedAt) > new Date(analyzedAt)
  ).length
})

const stage = computed(() =>
  releaseStage(release.value, {
    pendingDecisions: pendingDecisions.value,
    canImport: !!importReadiness.value?.can_import,
  })
)

// The first successful package-file upload tells us which release we are in.
// Swap the placeholder URL for the real one so the page is reloadable and
// shareable, and so the dashboard has a date to call the API with.
function onEffectiveDateDetected(date) {
  if (!date || date === effectiveDate.value) {
    return
  }
  effectiveDate.value = date
  router.replace({
    name: 'StandardsImportRelease',
    params: { effective_date: date },
  })
  loadRelease()
}

// An upload changes both columns: what the tasks say about the release, and what
// there is to diff. The dashboard watches the effective date, which does not move
// on a second upload, so it has to be told.
function onUploaded() {
  loadRelease()
  dashboard.value?.load()
}

// An analysis or an assessment replaces its own review items wholesale, so both the
// release and the queue counts behind the review boxes are stale afterwards.
function onAnalysed() {
  return Promise.all([loadRelease(), loadOpenInconsistencies()])
}

// Analysis and assessment both run as a background job, straight from their section's
// header: there is nothing to choose first. The job poller announces the job as it
// starts; this adds the one toast at the end, either way. The release is reloaded on
// the way in too, so the stage chip and the tasks see ANALYZING / ASSESSING while it
// runs. Resolves, once the release and the queue are reloaded, to whether the job
// succeeded.
function runReleaseJob({ api, jobName, running, successKey, errorKey }) {
  running.value = true

  return api
    .run(effectiveDate.value)
    .then(({ data: job }) => {
      loadRelease()
      return jobsApi.waitForJobCompletion(job.uid, jobName)
    })
    .then(() => {
      notificationHub.add({
        type: 'success',
        msg: t(`StandardsImport.${successKey}`),
      })
      return true
    })
    .catch((error) => {
      notificationHub.add({
        type: 'error',
        msg:
          error.response?.data?.message ||
          error.message ||
          t(`StandardsImport.${errorKey}`),
      })
      return false
    })
    .then((succeeded) => {
      running.value = false
      return onAnalysed().then(() => succeeded)
    })
}

// The same refusals as the API's `guard_assessable`, read off the freshly reloaded
// release and queue: no CDISC conflict left open, no decision the analysis has not
// applied yet.
const assessable = computed(
  () =>
    !!release.value?.analyzed_at &&
    !locked.value &&
    !Object.values(openInconsistencies.value.ANALYSIS || {}).some(Boolean) &&
    !pendingDecisions.value
)

// An analysis that leaves nothing to decide goes straight on to the assessment: the
// assessment needs a current analysis anyway, and that is the only thing between them.
// Anything still open stops the chain, so the reader settles it first.
function runAnalysis() {
  runReleaseJob({
    api: analysisApi,
    jobName: release.value?.analyzed_at
      ? t('StandardsImport.reanalyse')
      : t('StandardsImport.run_analysis'),
    running: analysisRunning,
    successKey: 'analysis_success',
    errorKey: 'analysis_error',
  }).then((analysed) => {
    if (analysed && assessable.value) {
      runAssessment()
    }
  })
}

function runAssessment() {
  runReleaseJob({
    api: sponsorImpactApi,
    jobName: release.value?.assessed_at
      ? t('StandardsImport.reassess_sponsor_impact')
      : t('StandardsImport.run_sponsor_impact'),
    running: assessmentRunning,
    successKey: 'sponsor_impact_success',
    errorKey: 'sponsor_impact_error',
  })
}

// The only step that cannot be taken back - the import only ever appends to the
// library - so it asks first, naming the catalogues it is about to write. The same list
// goes along as `expected_catalogues`: should the release have changed since the
// dashboard was read, the API refuses rather than import something not confirmed here.
async function runImport() {
  const catalogues = importReadiness.value?.catalogues || []
  const confirmed = await confirm.value.open(
    t('StandardsImport.import_confirm', {
      date: effectiveDate.value,
      catalogues: catalogues.join(', '),
    }),
    {
      type: 'warning',
      title: t('StandardsImport.task_approve'),
      agreeLabel: t('StandardsImport.approve'),
      width: 600,
    }
  )
  if (!confirmed) {
    return
  }
  runReleaseJob({
    api: { run: (date) => importsApi.run(date, catalogues) },
    jobName: t('StandardsImport.import_job'),
    running: importRunning,
    successKey: 'import_success',
    errorKey: 'import_error',
  })
}

// Resolving an item moves the count, and can flip the release out of BLOCKED.
function onResolved() {
  loadRelease()
  loadOpenInconsistencies()
  progress.value?.load()
}

// The review tables are where codelists get marked reviewed, which nothing on the
// release records, so the progress has to be told.
function onReviewClosed() {
  reviewDialogOpen.value = false
  progress.value?.load()
}

// One call rather than one per review box: between them the boxes cover the whole
// queue, so tallying it locally - by the step that raised each finding, then by what
// it is about - asks the API for the same rows once. Every status rather than OPEN
// alone, because settled findings are where the decisions not yet applied are.
function loadOpenInconsistencies() {
  if (!effectiveDate.value) {
    openInconsistencies.value = {}
    cdiscDecisionTimes.value = []
    return Promise.resolve()
  }
  return Promise.all([
    inconsistenciesApi.getAll({ effective_date: effectiveDate.value }),
    resolutionStrategiesStore.fetchResolutionStrategies(),
  ])
    .then(([response]) => {
      const counts = {}
      const decisionTimes = []
      for (const finding of response.data || []) {
        const reviewPass = resolutionStrategiesStore.getReviewPass(finding.type)
        if (finding.status === 'OPEN') {
          const byEntity = (counts[reviewPass] ||= {})
          byEntity[finding.entity_type] =
            (byEntity[finding.entity_type] || 0) + 1
        }
        // Analysis types only: analysis never applies a sponsor impact decision, so
        // none of those can be waiting for it.
        if (reviewPass === 'ANALYSIS' && finding.resolution?.decided_at) {
          decisionTimes.push(finding.resolution.decided_at)
        }
      }
      openInconsistencies.value = counts
      cdiscDecisionTimes.value = decisionTimes
    })
    .catch(() => {
      openInconsistencies.value = {}
      cdiscDecisionTimes.value = []
    })
}

function loadRelease() {
  if (!effectiveDate.value) {
    release.value = null
    return Promise.resolve()
  }
  return effectiveDatesApi
    .get(effectiveDate.value)
    .then((response) => {
      release.value = response.data
      loadImportReadiness()
    })
    .catch(() => {
      // A release only exists once its first package file has landed.
      release.value = null
      importReadiness.value = null
    })
}

// Statuses an import may start from. Anywhere else the answer is already known - not
// analysed, busy, or imported - and the dashboard would only say so at greater cost.
const IMPORTABLE_STATUSES = ['ANALYZED', 'BLOCKED', 'READY']

// Chained on the release rather than loaded beside it, since it depends on its status;
// and reloaded with it, since everything that moves the status - a job ending, a
// finding settled - can also change the verdict.
function loadImportReadiness() {
  if (!IMPORTABLE_STATUSES.includes(release.value?.status)) {
    importReadiness.value = null
    return
  }
  codelistsApi
    .getDashboard(effectiveDate.value)
    .then(({ data }) => {
      importReadiness.value = {
        can_import: data.can_import,
        blockers: data.blockers,
        catalogues: data.catalogues,
      }
    })
    .catch(() => {
      importReadiness.value = null
    })
}

// An org-wide setting rather than anything about this release, so it loads once.
// Same source the API's analysis guard reads, which is the point: the tasks column
// must say a release is ready exactly when analysis would accept it.
function loadMandatoryCatalogues() {
  configApi
    .getCataloguePriority()
    .then((response) => {
      mandatoryCatalogues.value = (response.data || [])
        .filter((entry) => entry.mandatory)
        .map((entry) => entry.catalogue_name)
    })
    .catch(() => {
      mandatoryCatalogues.value = []
    })
}

onMounted(() => {
  appStore.addBreadcrumbsLevel(
    t('StandardsImport.title'),
    { name: 'StandardsImport' },
    3,
    true
  )
  appStore.addBreadcrumbsLevel(
    isNewRelease.value ? t('StandardsImport.new_release') : effectiveDate.value,
    {
      name: 'StandardsImportRelease',
      params: { effective_date: route.params.effective_date },
    },
    4,
    true
  )
  loadRelease()
  loadMandatoryCatalogues()
  loadOpenInconsistencies()
})
</script>
