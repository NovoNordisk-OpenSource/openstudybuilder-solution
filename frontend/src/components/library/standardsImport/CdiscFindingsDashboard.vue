<template>
  <v-sheet color="white" rounded="xl" elevation="0" class="pa-4 h-100">
    <div class="d-flex align-center mb-3">
      <div class="page-title">
        {{ $t('StandardsImport.dashboard_title') }}
      </div>
      <v-spacer />
      <v-btn variant="outlined" rounded="xl" :loading="loading" @click="load">
        {{ $t('StandardsImport.refresh') }}
      </v-btn>
    </div>

    <v-progress-linear v-if="loading" indeterminate class="mb-2" />

    <v-alert
      v-if="error"
      type="error"
      variant="tonal"
      class="alert-bordered"
      density="compact"
      :text="error"
    />

    <!-- Before the first analysis has finished there is nothing to count, which must
         not read as an analysis that found nothing. -->
    <v-alert
      v-else-if="!release?.analyzed_at"
      type="info"
      variant="tonal"
      class="alert-bordered"
      :text="$t('StandardsImport.not_analysed')"
    />

    <v-row v-else-if="!loading" dense>
      <v-col v-for="card in cards" :key="card.type" cols="12">
        <!-- Drawn like the task boxes on the left, and coloured by the same rule as
             the review task: still to do while anything is open, done once nothing
             is. -->
        <v-alert
          :type="card.open ? 'warning' : 'success'"
          variant="tonal"
          class="alert-bordered h-100"
          :data-cy="`standards-import-dashboard-finding-${card.type}`"
        >
          <div class="d-flex align-center font-weight-bold">
            {{ findingTypeLabel(card.type) }}
            <EnumInfoTooltip enum-key="inconsistency_type" :value="card.type" />
            <v-spacer />
            <v-btn
              size="x-small"
              variant="text"
              rounded="xl"
              append-icon="mdi-chevron-right"
              :data-cy="`standards-import-dashboard-finding-${card.type}-see-all`"
              @click="emit('seeAll', card.type)"
            >
              {{ $t('StandardsImport.see_all') }}
            </v-btn>
          </div>

          <div class="d-flex justify-space-between mt-4">
            <div
              v-for="counter in COUNTERS"
              :key="counter.key"
              class="text-center"
            >
              <div class="text-caption">
                {{ $t(`StandardsImport.${counter.key}`) }}
              </div>
              <div class="text-h5 font-weight-bold">
                {{ card[counter.key].toLocaleString() }}
              </div>
            </div>
          </div>
        </v-alert>
      </v-col>
    </v-row>
  </v-sheet>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import EnumInfoTooltip from '@/components/tools/EnumInfoTooltip.vue'
import inconsistenciesApi from '@/api/standardsImport/inconsistencies'
import { findingTypeLabel } from '@/utils/standardsImport'
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
// The finding type whose resolution queue the reader asked for.
const emit = defineEmits(['seeAll'])

// Each key is both the finding's `status` lower-cased (bar `total`) and the i18n key
// of the counter's label.
const COUNTERS = [
  { key: 'total' },
  { key: 'open' },
  { key: 'auto_resolved' },
  { key: 'resolved' },
  { key: 'ignored' },
]

const findings = ref([])
const loading = ref(false)
const error = ref('')

// One card per kind of finding the analysis can raise, found ones or not: the same
// cards on every release, so a zero reads as "none of these" rather than as a card that
// went missing. Cards with open findings come first, as they are the ones still to
// settle; within each group the order is the API's own enum order (the sort is stable).
const cards = computed(() => {
  const byType = new Map(
    Object.keys(resolutionStrategiesStore.raisedBy)
      .filter(
        (type) => resolutionStrategiesStore.getReviewPass(type) === 'ANALYSIS'
      )
      .map((type) => [
        type,
        { type, total: 0, open: 0, auto_resolved: 0, resolved: 0, ignored: 0 },
      ])
  )
  for (const finding of findings.value) {
    const card = byType.get(finding.type)
    if (!card) {
      continue
    }
    card.total += 1
    const counter = finding.status.toLowerCase()
    if (counter in card) {
      card[counter] += 1
    }
  }
  return [...byType.values()].sort(
    (a, b) => Number(b.open > 0) - Number(a.open > 0)
  )
})

async function load() {
  if (!props.effectiveDate || !props.release?.analyzed_at) {
    findings.value = []
    return
  }
  loading.value = true
  error.value = ''
  try {
    const [{ data }] = await Promise.all([
      inconsistenciesApi.getAll({ effective_date: props.effectiveDate }),
      resolutionStrategiesStore.fetchResolutionStrategies(),
    ])
    findings.value = data || []
  } catch (exception) {
    findings.value = []
    error.value =
      exception.response?.data?.message ||
      exception.message ||
      t('StandardsImport.findings_error')
  } finally {
    loading.value = false
  }
}

// A re-analysis replaces the findings, and settling one moves the open count and can
// flip the status — the page refetches the release on both, which is the cue here.
watch(
  () => [
    props.effectiveDate,
    props.release?.analyzed_at,
    props.release?.open_inconsistency_count,
    props.release?.status,
  ],
  load
)
onMounted(load)
</script>
