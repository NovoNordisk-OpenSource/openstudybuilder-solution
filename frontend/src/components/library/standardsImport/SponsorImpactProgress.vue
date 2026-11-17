<template>
  <v-alert
    v-if="error"
    type="error"
    variant="tonal"
    class="alert-bordered mb-3"
    density="compact"
    :text="error"
  />

  <!-- Before the assessment has run against the current analysis there is nothing to
       count, which must not read as an assessment that found nothing. -->
  <v-alert
    v-else-if="!assessmentCurrent"
    type="info"
    variant="tonal"
    class="alert-bordered mb-3"
    :text="$t('StandardsImport.not_assessed')"
  />

  <!-- One card per bar, grey like the change cards below them: the colours are in
       the bars, one per status, so the cards themselves do not have to say good or
       bad. -->
  <template v-else>
    <v-card
      v-for="bar in bars"
      :key="bar.key"
      rounded="xl"
      variant="flat"
      class="progress-card mb-3"
      :data-cy="`standards-import-dashboard-progress-${bar.key}`"
    >
      <v-card-title
        class="d-flex align-center text-title-medium font-weight-bold text-primary"
      >
        {{ $t(`StandardsImport.${bar.key}_progress`) }}
        <v-spacer />
        <span v-if="!loading && bar.total">{{ bar.percent }}%</span>
      </v-card-title>

      <v-card-text class="text-primary">
        <v-progress-linear v-if="loading" indeterminate height="10" rounded />
        <!-- One segment per status, in the legend's order, each as wide as its
             share; the grey track only shows through when there is nothing at
             all. -->
        <div v-else class="stacked-bar">
          <div
            v-for="segment in bar.segments"
            :key="segment.key"
            :class="`bg-${segment.color}`"
            :style="{ width: `${(segment.count / bar.total) * 100}%` }"
          />
        </div>

        <div v-if="!loading" class="text-caption mt-2">
          <template v-if="bar.total">
            <span
              v-for="segment in bar.segments"
              :key="segment.key"
              class="d-inline-flex align-center mr-4"
            >
              <span class="legend-dot mr-1" :class="`bg-${segment.color}`" />
              {{ $t(`StandardsImport.${segment.label}`) }}
              <span class="font-weight-bold ml-1">
                {{ segment.count.toLocaleString() }}
              </span>
            </span>
          </template>
          <template v-else>
            {{ $t(`StandardsImport.${bar.key}_progress_none`) }}
          </template>
        </div>
      </v-card-text>
    </v-card>
  </template>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import inconsistenciesApi from '@/api/standardsImport/inconsistencies'
import codelistsApi from '@/api/standardsImport/codelists'
import { useStandardsImportResolutionStrategiesStore } from '@/stores/standardsImportResolutionStrategies'

const { t } = useI18n()
const resolutionStrategiesStore = useStandardsImportResolutionStrategiesStore()

const props = defineProps({
  effectiveDate: {
    type: String,
    default: '',
  },
  release: {
    type: Object,
    default: null,
  },
})

const findings = ref([])
const review = ref({})
const loading = ref(false)
const error = ref('')

// An assessment older than the last analysis describes values that have since
// changed — the same comparison `releaseStage` makes.
const assessmentCurrent = computed(
  () =>
    !!props.release?.assessed_at &&
    new Date(props.release.assessed_at) > new Date(props.release.analyzed_at)
)

// Done segments come first so the bars fill from the left; the percentage counts
// only the segments marked `done`.
const DONE = 'success'
const TO_DO = 'warning'

// Both kinds of finding on one bar: one that needs a decision is done once resolved
// (green) — or set aside once ignored (grey) — and one that only informs once
// acknowledged (blue). AUTO_RESOLVED is left out — nobody was asked anything.
// Segment keys are finding statuses, labels i18n keys.
const FINDINGS_BAR = {
  key: 'findings',
  segments: [
    { key: 'RESOLVED', label: 'resolved', color: DONE, done: true },
    { key: 'ACKNOWLEDGED', label: 'acknowledged', color: 'info', done: true },
    { key: 'INFORMATIONAL', label: 'informational', color: 'orange' },
    { key: 'OPEN', label: 'open', color: 'error' },
    { key: 'IGNORED', label: 'ignored', color: 'nnBaseGray' },
  ],
}

// The codelist walkthrough, over the codelists worth a look. A stale review was done
// once and then reopened by a later analysis, so it is neither done nor untouched.
// Segment keys are the API's `ReleaseReviewStats` fields.
const REVIEW_BAR = {
  key: 'review',
  segments: [
    { key: 'reviewed', label: 'review_reviewed', color: DONE, done: true },
    { key: 'stale', label: 'review_reviewed_stale', color: 'error' },
    { key: 'not_reviewed', label: 'review_not_reviewed', color: TO_DO },
  ],
}

function toBar(bar, countOf) {
  const segments = bar.segments.map((segment) => ({
    ...segment,
    count: countOf(segment.key),
  }))
  const sum = (list) => list.reduce((acc, segment) => acc + segment.count, 0)
  const total = sum(segments)
  const done = sum(segments.filter((segment) => segment.done))
  return {
    key: bar.key,
    segments,
    total,
    percent: total ? Math.floor((done / total) * 100) : 100,
  }
}

const bars = computed(() => {
  const counts = {}
  for (const finding of findings.value) {
    if (
      resolutionStrategiesStore.getReviewPass(finding.type) === 'SPONSOR_IMPACT'
    ) {
      counts[finding.status] = (counts[finding.status] || 0) + 1
    }
  }
  return [
    toBar(FINDINGS_BAR, (status) => counts[status] || 0),
    toBar(REVIEW_BAR, (field) => review.value[field] || 0),
  ]
})

async function load() {
  if (!props.effectiveDate || !assessmentCurrent.value) {
    findings.value = []
    review.value = {}
    return
  }
  loading.value = true
  error.value = ''
  try {
    // The findings rather than the dashboard's own counts, so that which bar a
    // finding lands on follows the same `getReviewPass` as the review boxes.
    const [{ data }, { data: dashboard }] = await Promise.all([
      inconsistenciesApi.getAll({ effective_date: props.effectiveDate }),
      codelistsApi.getDashboard(props.effectiveDate),
      resolutionStrategiesStore.fetchResolutionStrategies(),
    ])
    findings.value = data || []
    review.value = dashboard?.review || {}
  } catch (exception) {
    findings.value = []
    review.value = {}
    error.value =
      exception.response?.data?.message ||
      exception.message ||
      t('StandardsImport.review_progress_error')
  } finally {
    loading.value = false
  }
}

// A new assessment or analysis replaces the findings. Settling one, or marking a
// codelist reviewed, moves none of these, so the page calls `load` itself then.
watch(
  () => [
    props.effectiveDate,
    props.release?.assessed_at,
    props.release?.analyzed_at,
  ],
  load
)
onMounted(load)

defineExpose({ load })
</script>

<style scoped lang="scss">
// The same grey as the change cards, for the same reason: see
// `ReleaseChangeDashboard.vue`.
.progress-card {
  background-color: rgb(var(--v-theme-nnBaseLight));
  border: thin solid rgb(var(--v-theme-nnGray300));
}

.stacked-bar {
  display: flex;
  height: 10px;
  border-radius: 5px;
  overflow: hidden;
  background-color: rgb(var(--v-theme-nnGray300));
}

.legend-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
</style>
