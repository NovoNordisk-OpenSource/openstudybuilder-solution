<template>
  <div>
    <NNTable
      ref="table"
      :headers="headers"
      :items="items"
      :items-length="-1"
      :loading-watcher="loading"
      show-expand
      item-value="uid"
      hide-search-field
      hide-export-button
      hide-default-switches
      :initial-column-data="{ status: STATUSES }"
      :initial-filters="{ status: ['OPEN'] }"
      data-cy="standards-import-review-queue-table"
      @filter="onFilter"
    >
      <template #[`header.status`]="{ column }">
        {{ column.title }}
        <v-tooltip
          location="bottom"
          content-class="bg-white text-black elevation-3"
        >
          <template #activator="{ props }">
            <v-icon v-bind="props" size="14" color="white">
              mdi-information-outline
            </v-icon>
          </template>
          <div
            v-for="status in STATUSES"
            :key="status"
            class="d-flex align-center mb-1"
          >
            <v-chip
              size="small"
              :color="statusColor(status)"
              variant="tonal"
              class="mr-2"
            >
              {{ status }}
            </v-chip>
            {{ statusDescription(status) }}
          </div>
        </v-tooltip>
      </template>
      <template #[`item.candidates`]="{ item }">
        <FindingDetails :finding="item" class="py-1" />
      </template>
      <template #[`item.type`]="{ item }">
        {{ item.type }}
        <EnumInfoTooltip enum-key="inconsistency_type" :value="item.type" />
      </template>
      <template #[`item.status`]="{ item }">
        <v-chip size="small" :color="statusColor(item.status)" variant="tonal">
          {{ item.status }}
        </v-chip>
      </template>
      <template #[`item.actions`]="{ item }">
        <ActionsMenu :actions="actions" :item="item" />
      </template>
      <!-- NNTable fills every column's cell with its raw value, Vuetify's own expand
           column included, so the toggle has to be drawn here. -->
      <template
        #[`item.data-table-expand`]="{ internalItem, isExpanded, toggleExpand }"
      >
        <v-btn
          :icon="
            isExpanded(internalItem) ? 'mdi-chevron-up' : 'mdi-chevron-down'
          "
          variant="text"
          size="small"
          data-cy="standards-import-review-queue-expand"
          @click="toggleExpand(internalItem)"
        />
      </template>
      <!-- The candidates start under the Type column, leaving the actions and expand
           columns empty, so the detail reads as belonging to the finding above it. The
           cell has no padding of its own: the inner cells' padding then matches the
           parent's, and Catalogue lines up with Type. -->
      <template #expanded-row="{ columns, item }">
        <tr>
          <td
            v-if="leadingColumnCount(columns)"
            :colspan="leadingColumnCount(columns)"
          />
          <td
            :colspan="columns.length - leadingColumnCount(columns)"
            class="px-0"
          >
            <v-table density="compact">
              <thead>
                <tr>
                  <th>{{ $t('StandardsImport.catalogue') }}</th>
                  <th>{{ $t('StandardsImport.value') }}</th>
                  <th>{{ $t('StandardsImport.source') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(candidate, index) in item.candidates" :key="index">
                  <td>{{ (candidate.catalogues || []).join(', ') }}</td>
                  <td>{{ candidate.value }}</td>
                  <td>{{ candidate.source }}</td>
                </tr>
              </tbody>
            </v-table>
          </td>
        </tr>
      </template>
    </NNTable>

    <ResolveInconsistencyDialog
      :open="resolveDialogOpen"
      :item="selectedItem"
      @close="resolveDialogOpen = false"
      @resolved="onResolved"
    />
  </div>
</template>

<script setup>
import { inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import NNTable from '@/components/tools/NNTable.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ResolveInconsistencyDialog from './ResolveInconsistencyDialog.vue'
import FindingDetails from './FindingDetails.vue'
import EnumInfoTooltip from '@/components/tools/EnumInfoTooltip.vue'
import inconsistenciesApi from '@/api/standardsImport/inconsistencies'
import {
  canResolveFinding,
  canUndoFinding,
  findingStatusColor,
} from '@/utils/standardsImport'
import { useStandardsImportTypeDescriptionsStore } from '@/stores/standardsImportTypeDescriptions'
import { useStandardsImportResolutionStrategiesStore } from '@/stores/standardsImportResolutionStrategies'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const typeDescriptionsStore = useStandardsImportTypeDescriptionsStore()
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
  // 'ANALYSIS' or 'SPONSOR_IMPACT' to show only what that step raised. Applied here
  // rather than by the API, which filters on one finding type at a time. Empty means
  // both.
  reviewPass: {
    type: String,
    default: '',
  },
  // One InconsistencyType to show alone, as the findings dashboard asks for. Empty
  // means every type.
  type: {
    type: String,
    default: '',
  },
})
const emit = defineEmits(['resolved'])

// InconsistencyStatus in the standards_import API. AUTO_RESOLVED rows were
// settled by the analysis itself and need no action, but stay inspectable.
const STATUSES = ['OPEN', 'AUTO_RESOLVED', 'RESOLVED', 'IGNORED']

// Actions first, then the expand toggle: what can be done with a finding, and the
// way into its candidates, sit at the start of the row where the eye lands.
const headers = [
  { title: '', key: 'actions', sortable: false, noFilter: true },
  {
    title: '',
    key: 'data-table-expand',
    sortable: false,
    noFilter: true,
  },
  { title: t('StandardsImport.type'), key: 'type', noFilter: true },
  {
    title: t('StandardsImport.concept_id'),
    key: 'concept_id',
    noFilter: true,
  },
  {
    title: t('StandardsImport.candidates'),
    key: 'candidates',
    sortable: false,
    noFilter: true,
  },
  { title: t('StandardsImport.status'), key: 'status' },
]

// The columns drawn before Type in the expanded row. Read from the rendered columns
// rather than `headers`, since the reader can hide some; with Type hidden, none.
function leadingColumnCount(columns) {
  return Math.max(
    columns.findIndex((column) => column.key === 'type'),
    0
  )
}

const table = ref(null)
const items = ref([])
const loading = ref(false)
// Kept in sync with NNTable's status filter (see `initial-filters` below),
// so a reload triggered from elsewhere (undo, re-analysis) respects it.
const currentStatus = ref('OPEN')
const resolveDialogOpen = ref(false)
const selectedItem = ref({})

const statusColor = findingStatusColor

function statusDescription(status) {
  return typeDescriptionsStore.getValueDescription(
    'inconsistency_status',
    status
  )
}

const actions = [
  {
    label: t('StandardsImport.resolve'),
    icon: 'mdi-check-decagram',
    condition: canResolveFinding,
    click: (item) => {
      selectedItem.value = item
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

function load() {
  if (!props.effectiveDate) {
    return
  }
  loading.value = true
  const params = { effective_date: props.effectiveDate }
  if (currentStatus.value) {
    params.status = currentStatus.value
  }
  if (props.type) {
    params.type = props.type
  }
  Promise.all([
    inconsistenciesApi.getAll(params),
    props.reviewPass
      ? resolutionStrategiesStore.fetchResolutionStrategies()
      : null,
  ])
    .then(([response]) => {
      items.value = props.reviewPass
        ? response.data.filter(
            (item) =>
              resolutionStrategiesStore.getReviewPass(item.type) ===
              props.reviewPass
          )
        : response.data
    })
    .finally(() => {
      loading.value = false
    })
}

function onFilter(filters) {
  const parsed = filters ? JSON.parse(filters) : {}
  currentStatus.value = parsed.status?.v?.[0] || null
  load()
}

function undoResolution(item) {
  inconsistenciesApi.deleteResolution(item.uid).then(() => {
    notificationHub.add({
      type: 'success',
      msg: t('StandardsImport.undo_success'),
    })
    load()
    emit('resolved')
  })
}

function onResolved() {
  load()
  emit('resolved')
}

watch(() => props.effectiveDate, load)

// Re-analysing in step 3 replaces the review items wholesale. This step cannot
// rely on onMounted to notice: the stepper keeps a visited step mounted (Vuetify
// toggles it with v-show), so it would otherwise show the pre-analysis queue
// until something else forced a reload.
watch(() => props.release?.analyzed_at, load)

// The status filter is how a reviewer moves between what is still open and what was
// already settled, so its bar starts open. NNTable's `show-filter-bar-by-default`
// only picks the filterable columns and leaves the bar shut, hence the exposed ref.
onMounted(() => {
  table.value.showFilterBar = true
})
</script>
