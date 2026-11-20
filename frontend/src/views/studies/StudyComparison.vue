<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('StudyComparison.title') }} ({{ studyId }})
    </div>

    <v-row class="mt-2" align="center">
      <v-col cols="12" md="6">
        <v-select
          v-model="versionA"
          :items="versionOptions"
          :label="$t('StudyComparison.version_a')"
          :loading="loadingVersions"
          hide-details
          data-cy="comparison-version-a"
        />
      </v-col>
      <v-col cols="12" md="6">
        <v-select
          v-model="versionB"
          :items="versionOptions"
          :label="$t('StudyComparison.version_b')"
          :loading="loadingVersions"
          hide-details
          data-cy="comparison-version-b"
        />
      </v-col>
    </v-row>
    <v-row align="center">
      <v-col cols="12" md="6">
        <v-combobox
          v-model="ignoreFields"
          :items="ignoreFieldSuggestions"
          :label="$t('StudyComparison.ignore_fields')"
          :hint="$t('StudyComparison.ignore_fields_hint')"
          persistent-hint
          multiple
          chips
          closable-chips
          data-cy="comparison-ignore-fields"
        />
      </v-col>
      <v-col cols="12" md="auto" class="d-flex align-center">
        <v-switch
          v-model="showOnlyDifferences"
          :label="$t('StudyComparison.show_only_differences')"
          hide-details
          data-cy="comparison-show-only-differences"
        />
      </v-col>
      <v-col cols="12" md="auto" class="d-flex align-center ga-4">
        <v-btn
          color="nnBaseBlue"
          variant="elevated"
          rounded="xl"
          :disabled="!canCompare"
          :loading="loading"
          data-cy="comparison-compare"
          @click="compare"
        >
          {{ $t('StudyComparison.compare') }}
        </v-btn>
        <v-btn
          color="nnBaseBlue"
          variant="outlined"
          rounded="xl"
          :disabled="!result"
          :loading="downloading"
          data-cy="comparison-download"
          @click="downloadJson"
        >
          {{ $t('StudyComparison.download_json') }}
        </v-btn>
      </v-col>
    </v-row>

    <v-alert
      v-if="!loadingVersions && versionOptions.length < 2"
      type="info"
      variant="tonal"
      class="mt-4"
    >
      {{ $t('StudyComparison.no_versions') }}
    </v-alert>
    <v-alert v-else-if="error" type="error" variant="tonal" class="mt-4">
      {{ $t('StudyComparison.load_error') }}
    </v-alert>
    <v-progress-linear v-else-if="loading" indeterminate class="mt-4" />
    <v-alert
      v-else-if="!result"
      type="info"
      variant="tonal"
      class="mt-4"
      data-cy="comparison-prompt"
    >
      {{ $t('StudyComparison.select_prompt') }}
    </v-alert>
    <template v-else>
      <v-alert
        v-if="!result.has_changes"
        type="success"
        variant="tonal"
        class="mt-4"
        data-cy="comparison-no-differences"
      >
        {{ $t('StudyComparison.no_differences') }}
      </v-alert>
      <div class="d-flex align-center mt-4" data-cy="comparison-summary">
        <span class="mr-4">
          {{
            $t('StudyComparison.summary', {
              a: result.version_a,
              b: result.version_b,
              sections: visibleSections.length,
            })
          }}
        </span>
        <v-chip color="success" size="small" class="mr-2" label>
          {{ $t('StudyComparison.added', { count: totals.added }) }}
        </v-chip>
        <v-chip color="error" size="small" class="mr-2" label>
          {{ $t('StudyComparison.removed', { count: totals.removed }) }}
        </v-chip>
        <v-chip color="warning" size="small" class="mr-2" label>
          {{ $t('StudyComparison.modified', { count: totals.modified }) }}
        </v-chip>
        <v-chip color="info" size="small" class="mr-2" label>
          {{ $t('StudyComparison.recreated', { count: totals.recreated }) }}
        </v-chip>
        <v-chip v-if="!showOnlyDifferences" size="small" class="mr-2" label>
          {{ $t('StudyComparison.unchanged', { count: totals.unchanged }) }}
        </v-chip>
      </div>
      <v-expansion-panels multiple class="mt-4">
        <v-expansion-panel
          v-for="section in visibleSections"
          :key="section.section"
        >
          <v-expansion-panel-title>
            <span class="font-weight-bold mr-4">{{ section.title }}</span>
            <v-chip
              v-if="section.added"
              color="success"
              size="small"
              class="mr-2"
              label
            >
              {{ $t('StudyComparison.added', { count: section.added }) }}
            </v-chip>
            <v-chip
              v-if="section.removed"
              color="error"
              size="small"
              class="mr-2"
              label
            >
              {{ $t('StudyComparison.removed', { count: section.removed }) }}
            </v-chip>
            <v-chip
              v-if="section.modified"
              color="warning"
              size="small"
              class="mr-2"
              label
            >
              {{ $t('StudyComparison.modified', { count: section.modified }) }}
            </v-chip>
            <v-chip
              v-if="section.recreated"
              color="info"
              size="small"
              class="mr-2"
              label
            >
              {{
                $t('StudyComparison.recreated', { count: section.recreated })
              }}
            </v-chip>
            <v-chip v-if="section.unchanged" size="small" class="mr-2" label>
              {{
                $t('StudyComparison.unchanged', { count: section.unchanged })
              }}
            </v-chip>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <div
              v-for="item in section.items"
              :key="item.key"
              class="mb-4"
              data-cy="comparison-item"
            >
              <v-expansion-panels
                v-if="item.change_type === 'UNCHANGED' && item.changes?.length"
                variant="accordion"
              >
                <v-expansion-panel>
                  <v-expansion-panel-title class="py-1">
                    <v-chip size="small" class="mr-3" label>
                      {{ $t('StudyComparison.change_types.UNCHANGED') }}
                    </v-chip>
                    <span>{{ item.label || item.key }}</span>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <ComparisonFields :changes="item.changes" />
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>
              <template v-else>
                <div class="d-flex align-center">
                  <v-chip
                    :color="changeColors[item.change_type]"
                    size="small"
                    class="mr-3"
                    label
                  >
                    {{ $t(`StudyComparison.change_types.${item.change_type}`) }}
                  </v-chip>
                  <span class="font-weight-medium">{{
                    item.label || item.key
                  }}</span>
                </div>
                <ComparisonFields
                  v-if="item.changes?.length"
                  :changes="item.changes"
                  class="mt-2"
                />
              </template>
            </div>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import study from '@/api/study'
import exportLoader from '@/utils/exportLoader'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import ComparisonFields from '@/components/studies/ComparisonFields.vue'

const { t } = useI18n()
const studiesGeneralStore = useStudiesGeneralStore()

const studyId = computed(() => studiesGeneralStore.studyId)
const studyUid = computed(() => studiesGeneralStore.selectedStudy?.uid)

const changeColors = {
  ADDED: 'success',
  REMOVED: 'error',
  MODIFIED: 'warning',
  RECREATED: 'info',
  UNCHANGED: undefined,
}

const versionOptions = ref([])
const versionA = ref(null)
const versionB = ref(null)
const loadingVersions = ref(false)
const loading = ref(false)
const error = ref(false)
const result = ref(null)
const downloading = ref(false)
const showOnlyDifferences = ref(false)
const ignoreFields = ref(['*_date', '*_at'])
const ignoreFieldSuggestions = ['*_date', '*_at', '*_uid', '*_uids']

const canCompare = computed(
  () =>
    !!versionA.value && !!versionB.value && versionA.value !== versionB.value
)
const totals = computed(() =>
  visibleSections.value.reduce(
    (acc, s) => ({
      added: acc.added + s.added,
      removed: acc.removed + s.removed,
      modified: acc.modified + s.modified,
      recreated: acc.recreated + (s.recreated || 0),
      unchanged: acc.unchanged + (s.unchanged || 0),
    }),
    { added: 0, removed: 0, modified: 0, recreated: 0, unchanged: 0 }
  )
)
const visibleSections = computed(() =>
  (result.value?.sections || []).filter((s) => s.items?.length)
)

function formatDate(value) {
  return value ? String(value).substring(0, 10) : ''
}

function isCurrentDraft(row) {
  const statuses = row.study_status || []
  return statuses.length === 1 && statuses[0] === 'DRAFT'
}

function buildOptions(history) {
  const seen = new Set()
  const options = []
  for (const row of history) {
    // Only locked/released versions can be requested by number, the draft by name
    const version = isCurrentDraft(row) ? 'draft' : row.metadata_version
    if (!version || seen.has(version)) {
      continue
    }
    seen.add(version)
    const label = isCurrentDraft(row)
      ? t('StudyComparison.current_draft', { version: row.metadata_version })
      : `${version} (${(row.study_status || []).join(', ')})`
    options.push({
      value: version,
      title: `${label} – ${formatDate(row.modified_date)}`,
      date: row.modified_date || '',
    })
  }
  return options.sort((a, b) => b.date.localeCompare(a.date))
}

async function loadVersions() {
  loadingVersions.value = true
  try {
    const resp = await study.getStudySnapshotHistory(studyUid.value, {
      page_size: 0,
    })
    versionOptions.value = buildOptions(resp.data.items || [])
    versionB.value = versionOptions.value[0]?.value ?? null
    versionA.value = versionOptions.value[1]?.value ?? null
  } catch {
    versionOptions.value = []
  } finally {
    loadingVersions.value = false
  }
}

async function compare() {
  loading.value = true
  error.value = false
  result.value = null
  try {
    const resp = await study.compareVersions(
      studyUid.value,
      versionA.value,
      versionB.value,
      !showOnlyDifferences.value,
      ignoreFields.value
    )
    result.value = resp.data
  } catch {
    error.value = true
  } finally {
    loading.value = false
  }
}

async function downloadJson() {
  downloading.value = true
  try {
    // The export is always complete, regardless of the display toggle
    const data = !showOnlyDifferences.value
      ? result.value
      : (
          await study.compareVersions(
            studyUid.value,
            versionA.value,
            versionB.value,
            true,
            ignoreFields.value
          )
        ).data
    exportLoader.downloadFile(
      JSON.stringify(data, null, 2),
      'application/json',
      `${studyUid.value}_comparison_${versionA.value}_vs_${versionB.value}.json`
    )
  } finally {
    downloading.value = false
  }
}

watch([versionA, versionB, showOnlyDifferences, ignoreFields], () => {
  result.value = null
  error.value = false
})
watch(studyUid, (uid, previous) => {
  if (uid && uid !== previous) {
    result.value = null
    loadVersions()
  }
})
onMounted(loadVersions)
</script>
