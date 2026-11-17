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

    <!-- Whatever the step the release is at wants said ahead of how much changed. -->
    <slot />

    <v-progress-linear v-if="loading" indeterminate class="mb-2" />

    <v-alert
      v-if="error"
      type="error"
      variant="tonal"
      class="alert-bordered"
      density="compact"
      :text="error"
    />

    <v-alert
      v-else-if="!loading && !summaries.length"
      type="info"
      variant="tonal"
      class="alert-bordered"
      :text="$t('StandardsImport.no_packages_to_review')"
    />

    <template v-else-if="!loading">
      <v-row dense>
        <v-col v-for="card in cards" :key="card.key" cols="12" sm="6">
          <v-card
            rounded="xl"
            variant="flat"
            class="h-100 change-card"
            :data-cy="`standards-import-dashboard-${card.key}`"
          >
            <v-card-title
              class="text-title-medium font-weight-bold text-primary"
            >
              {{ card.title }}
            </v-card-title>

            <v-card-text class="text-primary">
              <div class="d-flex justify-space-between">
                <div
                  v-for="counter in card.counters"
                  :key="counter.key"
                  class="text-center"
                >
                  <div class="text-caption">
                    {{ counter.label }}
                  </div>
                  <div class="text-h5 font-weight-bold">
                    {{ counter.count.toLocaleString() }}
                  </div>
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Catalogues overlap, so a concept that changed in both SDTM CT and SEND CT
           is counted under each. Say so rather than let the totals read as a count
           of distinct concepts. -->
      <div
        v-if="comparedCatalogues.length"
        class="text-caption text-medium-emphasis mt-3"
      >
        {{
          $t('StandardsImport.dashboard_summed_note', {
            catalogues: comparedCatalogues.join(', '),
          })
        }}
      </div>

      <!-- A catalogue with no staged predecessor contributes nothing, which is not
           an error — but leaving it unsaid makes a zero look like "nothing changed". -->
      <div
        v-if="unComparedCatalogues.length"
        class="text-caption text-medium-emphasis mt-1"
        data-cy="standards-import-dashboard-no-previous"
      >
        {{
          $t('StandardsImport.dashboard_no_previous_catalogues', {
            catalogues: unComparedCatalogues.join(', '),
          })
        }}
      </div>
    </template>
  </v-sheet>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import packageDiffApi from '@/api/standardsImport/packageDiff'

const { t } = useI18n()

const props = defineProps({
  effectiveDate: {
    type: String,
    default: '',
  },
})

// The API's severity bands (`ct_diff.SEVERITIES`) split cleanly by what they are
// about: three of them concern codelists, the other nine terms. That split is what
// makes the two cards possible from the one summaries call — nothing here re-derives
// anything, it only adds up the levels the API already counted.
const CARDS = [
  {
    key: 'codelists',
    title: 'dashboard_codelists',
    added: [8],
    removed: [1],
    changed: [11],
  },
  {
    key: 'terms',
    title: 'dashboard_terms',
    added: [5, 7, 9, 10],
    removed: [2, 3],
    changed: [4, 6, 12],
  },
]

// No per-counter colour: green/red would read as good/bad news, and a release that
// removes a lot of terms is not thereby a worse release. The whole card is the one
// blue of its title.
const COUNTERS = [
  { key: 'added', label: 'dashboard_added' },
  { key: 'removed', label: 'dashboard_removed' },
  { key: 'changed', label: 'dashboard_changed' },
]

const summaries = ref([])
const loading = ref(false)
const error = ref('')

const comparedCatalogues = computed(() =>
  summaries.value
    .filter((summary) => summary.previous_available)
    .map((summary) => summary.catalogue)
)

const unComparedCatalogues = computed(() =>
  summaries.value
    .filter((summary) => !summary.previous_available)
    .map((summary) => summary.catalogue)
)

// Level -> total count across every compared catalogue of the release.
const countsByLevel = computed(() => {
  const totals = {}
  for (const summary of summaries.value) {
    for (const band of summary.bands || []) {
      totals[band.level] = (totals[band.level] || 0) + band.count
    }
  }
  return totals
})

const cards = computed(() =>
  CARDS.map((card) => ({
    key: card.key,
    title: t(`StandardsImport.${card.title}`),
    counters: COUNTERS.map((counter) => ({
      key: counter.key,
      label: t(`StandardsImport.${counter.label}`),
      count: card[counter.key].reduce(
        (sum, level) => sum + (countsByLevel.value[level] || 0),
        0
      ),
    })),
  }))
)

async function load() {
  // A brand-new release has no date yet, so there is nothing to diff against.
  if (!props.effectiveDate) {
    summaries.value = []
    return
  }
  loading.value = true
  error.value = ''
  try {
    const { data } = await packageDiffApi.getSummaries(props.effectiveDate)
    summaries.value = data || []
  } catch (exception) {
    summaries.value = []
    error.value =
      exception.response?.data?.message ||
      exception.message ||
      t('StandardsImport.diff_error')
  } finally {
    loading.value = false
  }
}

watch(() => props.effectiveDate, load)
onMounted(load)

defineExpose({ load })
</script>

<style scoped lang="scss">
// Grey rather than any of the status colours, deliberately: these cards report how
// much changed, which is not itself good or bad news. Set here rather than through
// the card's own props because `variant="outlined"` would tint the border with the
// `color`, and Vuetify emits no border-<theme-colour> utility to pair with a
// background one.
.change-card {
  background-color: rgb(var(--v-theme-nnBaseLight));
  border: thin solid rgb(var(--v-theme-nnGray300));
}
</style>
