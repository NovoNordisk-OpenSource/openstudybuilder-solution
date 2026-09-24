<template>
  <div>
    <v-row class="activity-items-row">
      <v-col cols="12" class="activity-items-col px-0">
        <div class="section-header mb-1">
          <h3 class="text-headline-small font-weight-bold text-primary">
            {{ $t('ActivityOverview.activity_items') }}
          </h3>
        </div>
        <div class="table-container">
          <NNTable
            ref="tableRef"
            table-id="library-activity-items-table"
            :headers="itemHeaders"
            :items="activityItems"
            :hide-export-button="false"
            :hide-default-switches="true"
            item-value="item_key"
            :disable-filtering="true"
            :hide-search-field="false"
            :modifiable-table="true"
            :no-padding="true"
            elevation="0"
            :loading="loading"
            :items-length="paginationTotal"
            :server-items-length="paginationTotal"
            :no-data-text="t('activityItemsTable.noItemsFound')"
            :use-cached-filtering="false"
            :export-config="{
              objectLabel: t('activityItemsTable.exportLabel'),
              dataUrl: exportDataUrl,
            }"
            @filter="handleFilter"
          >
            <template #[`item.name`]="{ item }">
              <div class="d-block">
                <span v-if="item.ct_terms && item.ct_terms.length > 0">
                  {{
                    [...new Set(item.ct_terms.map((term) => term.name))].join(
                      ', '
                    )
                  }}
                </span>
                <span v-else-if="item.ct_codelist" class="font-italic">
                  {{
                    $t('ActivityInstanceForm.all_terms_in_codelist_named', {
                      name: item.ct_codelist.name,
                    })
                  }}
                </span>
                <span
                  v-else-if="
                    item.unit_definitions && item.unit_definitions.length > 0
                  "
                >
                  {{
                    item.unit_definitions.map((unit) => unit.name).join(', ')
                  }}
                </span>
                <span v-else-if="item.text_value">
                  {{ item.text_value }}
                </span>
                <span v-else>-</span>
              </div>
            </template>
            <template #[`item.item_type`]="{ item }">
              <div class="d-block">
                {{ item.activity_item_class?.data_type_name || '' }}
              </div>
            </template>
            <template #[`item.activity_item_class`]="{ item }">
              <div class="d-block">
                {{ item.activity_item_class?.name || '' }}
              </div>
            </template>
            <template #[`item.submission_value`]="{ item }">
              <div class="d-block">
                <template
                  v-if="
                    (item.activity_item_class?.name === 'test_name' ||
                      item.activity_item_class?.name === 'test_code') &&
                    item.ct_terms?.length > 0
                  "
                >
                  <div v-for="(term, idx) in item.ct_terms" :key="idx">
                    &bull; {{ term.submission_value }}
                  </div>
                </template>
                <span v-else-if="item.ct_terms && item.ct_terms.length > 0">
                  {{
                    item.ct_terms
                      .map((term) => term.submission_value)
                      .join(', ')
                  }}
                </span>
                <span v-else-if="item.ct_codelist" class="font-italic">
                  {{
                    $t('ActivityInstanceForm.all_terms_in_codelist_named', {
                      name: item.ct_codelist.name,
                    })
                  }}
                </span>
                <span v-else>-</span>
              </div>
            </template>
          </NNTable>
        </div>
      </v-col>
    </v-row>

    <!-- Show this only if there are genuinely no items at all, not just no search results -->
    <div v-if="activityItems.length === 0 && !loading" class="py-4 text-center">
      {{ t('activityItemsTable.noItemsAvailable') }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import activitiesApi from '@/api/activities'
import NNTable from '@/components/tools/NNTable.vue'

const route = useRoute()
const { t } = useI18n()

const props = defineProps({
  activityInstanceId: {
    type: String,
    required: true,
  },
  version: {
    type: String,
    required: false,
    default: '',
  },
})

const tableRef = ref(null)
const activityItems = ref([])
const allActivityItems = ref([]) // Store all items for client-side filtering
const loading = ref(false)
const paginationTotal = ref(0)
const currentSearch = ref('') // Track current search term
const currentPage = ref(1)
const itemsPerPage = ref(10)

// Define headers for the activity items table
const itemHeaders = [
  {
    title: t('activityItemsTable.headerActivityItemClass'),
    key: 'activity_item_class',
    sortable: false,
    width: '20%',
  },
  {
    title: t('activityItemsTable.headerDataType'),
    key: 'item_type',
    sortable: false,
    width: '12%',
  },
  {
    title: t('activityItemsTable.headerName'),
    key: 'name',
    sortable: false,
    width: '30%',
  },
  {
    title: t('activityItemsTable.headerSubmissionValue'),
    key: 'submission_value',
    sortable: false,
    width: '38%',
  },
]

const exportDataUrl = computed(() => {
  if (!props.activityInstanceId) return ''
  return `/concepts/activities/activity-instances/${props.activityInstanceId}/activity-items`
})

onMounted(() => {
  refresh()
})

// Watch for changes in the activityInstanceId or version
watch(
  [
    () => props.activityInstanceId,
    () => props.version,
    () => route.params.version,
  ],
  (newValues, oldValues) => {
    // Skip if oldValues is undefined (initial mount)
    if (!oldValues) return

    // Only refresh if the values actually changed
    const hasActualChange = newValues.some(
      (val, index) => val !== oldValues[index]
    )

    if (hasActualChange) {
      refresh()
    }
  }
)

// Initialize the component when mounted or props change
function refresh() {
  const version = props.version || route.params.version

  if (props.activityInstanceId) {
    fetchActivityItems(props.activityInstanceId, version)
  }
}

// Fetches activity items from API
async function fetchActivityItems(activityInstanceId, version) {
  try {
    loading.value = true

    const params = {
      page_number: 1,
      page_size: 1000,
      total_count: true,
    }

    const response = await activitiesApi.getActivityInstanceItems(
      activityInstanceId,
      version,
      params
    )

    // Transform the response data to include item_key
    const items = (response.data || []).map((item, index) => ({
      ...item,
      item_key: `item-${index}`,
    }))

    allActivityItems.value = items

    // Apply initial filter with current pagination
    applySearchFilter(
      currentSearch.value,
      currentPage.value,
      itemsPerPage.value
    )
  } catch (error) {
    console.error('Error fetching activity items:', error)
    activityItems.value = []
    allActivityItems.value = []
    paginationTotal.value = 0
  } finally {
    loading.value = false
  }
}

// Helper function to check if an item matches the search term
function itemMatchesSearch(item, searchTerm) {
  const term = searchTerm.toLowerCase()

  // Search in activity item class name, role, data type
  if (item.activity_item_class?.name?.toLowerCase().includes(term)) return true
  if (item.activity_item_class?.role_name?.toLowerCase().includes(term))
    return true
  if (item.activity_item_class?.data_type_name?.toLowerCase().includes(term))
    return true

  // Search in text_value field
  if (item.text_value?.toLowerCase().includes(term)) return true

  // Search in CT terms (name and submission value)
  if (
    item.ct_terms?.some(
      (ctTerm) =>
        ctTerm.name?.toLowerCase().includes(term) ||
        ctTerm.submission_value?.toLowerCase().includes(term)
    )
  )
    return true

  // Search in unit definitions
  if (
    item.unit_definitions?.some(
      (unit) =>
        unit.name?.toLowerCase().includes(term) ||
        unit.dimension_name?.toLowerCase().includes(term)
    )
  )
    return true

  // Search in ODM forms
  if (
    item.odm_forms?.some(
      (form) =>
        form.name?.toLowerCase().includes(term) ||
        form.oid?.toLowerCase().includes(term)
    )
  )
    return true

  return false
}

// Apply search filter to the items
function applySearchFilter(searchTerm, page = 1, perPage = 10) {
  currentSearch.value = searchTerm || ''

  let itemsToDisplay = allActivityItems.value

  // Apply search filter if needed
  if (searchTerm && searchTerm.trim() !== '') {
    itemsToDisplay = allActivityItems.value.filter((item) =>
      itemMatchesSearch(item, searchTerm)
    )
  }

  // Apply pagination
  if (perPage === -1) {
    // Show all items when "All" is selected
    activityItems.value = itemsToDisplay
  } else {
    const startIndex = (page - 1) * perPage
    const endIndex = startIndex + perPage
    activityItems.value = itemsToDisplay.slice(startIndex, endIndex)
  }

  paginationTotal.value = itemsToDisplay.length
}

// Handles filtering of activity items based on search term
function handleFilter(_, options) {
  if (!options) return

  const searchChanged = options.search !== currentSearch.value
  const nextPerPage = searchChanged
    ? itemsPerPage.value
    : options.itemsPerPage !== undefined
      ? options.itemsPerPage
      : itemsPerPage.value
  const nextPage =
    options.page !== undefined
      ? options.page
      : searchChanged
        ? 1
        : currentPage.value

  itemsPerPage.value = nextPerPage
  currentPage.value = searchChanged ? 1 : nextPage

  applySearchFilter(options.search, currentPage.value, itemsPerPage.value)
}
</script>

<style scoped>
/* Table container styling */
.table-container {
  width: 100%;
  margin-bottom: 24px;
  border-radius: 4px;
  background-color: transparent;
  box-shadow: none;
  overflow: hidden;
}

/* Row container styling */
.activity-items-row {
  margin: 0 !important;
  width: 100%;
}

.activity-items-col {
  padding: 0 !important;
}

/* Adjusts the spacing for section headers */
.section-header {
  margin-top: 16px;
  margin-bottom: 8px;
  padding-left: 0;
}

/* Ensure card content takes full width */
.activity-items-row :deep(.v-card-text) {
  width: 100% !important;
  padding: 0 !important;
}

/* Force table to take full width */
.activity-items-row :deep(.v-data-table),
.activity-items-row :deep(.v-table),
.activity-items-row :deep(table) {
  width: 100% !important;
  table-layout: fixed !important;
}

/* Table styling overrides that penetrate component boundaries */
.activity-items-row :deep(.v-table) {
  background: transparent !important;
}

.activity-items-row :deep(.v-data-table__td) {
  background-color: white !important;
}

.activity-items-row :deep(.v-data-table__th) {
  background-color: rgb(var(--v-theme-nnTrueBlue)) !important;
}

.activity-items-row :deep(.v-data-table__tbody tr) {
  background-color: white !important;
}

.activity-items-row :deep(.v-card),
.activity-items-row :deep(.v-sheet) {
  background-color: transparent !important;
  box-shadow: none !important;
}
</style>
