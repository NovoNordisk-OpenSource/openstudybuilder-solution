<template>
  <div>
    <v-row class="activities-row">
      <v-col cols="12" class="activities-col px-0">
        <div class="table-container">
          <NNTable
            ref="tableRef"
            table-id="library-activity-instances-table"
            :headers="translatedHeaders"
            :items="activitiesList"
            :hide-export-button="false"
            :hide-default-switches="true"
            item-value="item_key"
            :sub-tables="true"
            :disable-filtering="true"
            :hide-search-field="false"
            :modifiable-table="true"
            :no-padding="true"
            elevation="0"
            :loading="loading"
            :expanded="expandedItems"
            :items-length="paginationTotal"
            :no-data-text="t('activityInstancesTable.noInstancesFound')"
            :use-cached-filtering="false"
            :export-config="{
              dataUrlParams: exportDataUrlParams,
              objectLabel: t('activityInstancesTable.exportLabel'),
              dataUrl: exportDataUrl,
            }"
            @filter="handleFilter"
            @update:expanded="updateExpandedItems"
            @update:options="updateTableOptions"
          >
            <template #item="{ item, internalItem, toggleExpand, isExpanded }">
              <tr :class="{ 'expanded-parent-row': isExpanded(internalItem) }">
                <template v-for="header in translatedHeaders" :key="header.key">
                  <td
                    v-if="isColumnVisible(header.key)"
                    :width="header.width || 'auto'"
                    class="data-cell"
                  >
                    <template v-if="header.key === 'name'">
                      <div class="d-flex align-center">
                        <v-btn
                          v-if="item.versions && item.versions.length > 0"
                          :icon="
                            isExpanded(internalItem)
                              ? 'mdi-chevron-down'
                              : 'mdi-chevron-right'
                          "
                          variant="text"
                          class="flex-shrink-0 mr-1"
                          @click="toggleExpand(internalItem)"
                        />
                        <router-link
                          class="text-truncate"
                          :to="{
                            name: 'ActivityInstanceOverview',
                            params: {
                              id: item.uid,
                              version: item.version,
                            },
                          }"
                        >
                          {{ item.name }}
                        </router-link>
                      </div>
                    </template>

                    <template v-else-if="header.key === 'version'">
                      {{ item.version }}
                    </template>
                    <template v-else-if="header.key === 'status'">
                      <StatusChip :status="item.status" />
                    </template>
                    <template
                      v-else-if="header.key === 'activity_instance_class'"
                    >
                      {{
                        item.activity_instance_class &&
                        item.activity_instance_class.name
                          ? item.activity_instance_class.name
                          : ''
                      }}
                    </template>
                    <template v-else-if="header.key === 'topic_code'">
                      {{ item.topic_code || '' }}
                    </template>
                    <template v-else-if="header.key === 'adam_param_code'">
                      {{ item.adam_param_code || '' }}
                    </template>
                  </td>
                </template>
              </tr>
            </template>

            <template #expanded-row="{ item }">
              <tr v-if="item.versions && item.versions.length > 0">
                <td :colspan="getVisibleColumnsCount()" class="pa-0">
                  <v-data-table
                    class="elevation-0"
                    :items="item.versions"
                    item-value="uid"
                    :items-per-page="-1"
                    hide-default-header
                    hide-default-footer
                  >
                    <template #headers />
                    <template #bottom />
                    <template #item="{ item }">
                      <tr class="child-row">
                        <template
                          v-for="header in translatedHeaders"
                          :key="header.key"
                        >
                          <td
                            v-if="isColumnVisible(header.key)"
                            :width="header.width || 'auto'"
                            :class="[
                              header.key === 'name' ? 'pl-10' : '',
                              'data-cell',
                            ]"
                          >
                            <template v-if="header.key === 'name'">
                              <router-link
                                :to="{
                                  name: 'ActivityInstanceOverview',
                                  params: {
                                    id: item.uid,
                                    version: item.version,
                                  },
                                }"
                              >
                                {{ item.name }}
                              </router-link>
                            </template>

                            <template v-else-if="header.key === 'version'">
                              {{ item.version }}
                            </template>
                            <template v-else-if="header.key === 'status'">
                              <StatusChip :status="item.status" />
                            </template>
                            <template
                              v-else-if="
                                header.key === 'activity_instance_class'
                              "
                            >
                              {{
                                item.activity_instance_class
                                  ? item.activity_instance_class.name
                                  : ''
                              }}
                            </template>
                            <template v-else-if="header.key === 'topic_code'">
                              {{ item.topic_code || '' }}
                            </template>
                            <template
                              v-else-if="header.key === 'adam_param_code'"
                            >
                              {{ item.adam_param_code || '' }}
                            </template>
                          </td>
                        </template>
                      </tr>
                    </template>
                  </v-data-table>
                </td>
              </tr>
            </template>
          </NNTable>
        </div>
      </v-col>
    </v-row>

    <!-- Show this only if there are genuinely no items at all, not just no search results -->
    <div v-if="allActivities.length === 0 && !loading" class="py-4 text-center">
      {{ t('activityInstancesTable.noItemsAvailable') }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import activitiesApi from '@/api/activities'
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'

const route = useRoute()
const { t } = useI18n()

const props = defineProps({
  itemData: {
    type: Object,
    default: () => ({}),
  },
  activityId: {
    type: String,
    default: '',
  },
  version: {
    type: String,
    required: false,
    default: '',
  },
})

// This computed property will be used as fallback if we can't get version from other sources
const defaultActivityVersion = computed(() => {
  return t('activityInstancesTable.versionNotAvailable')
})

const tableRef = ref(null)
const allActivities = ref([]) // Stores all activities for filtering
const activitiesList = ref([]) // Activities displayed in the table
const loading = ref(false)
const expandedItems = ref([])
const paginationTotal = ref(0) // Total count for pagination
let sortTimer = null // Timer for delayed sort application
const tableOptions = ref({
  page: 1,
  itemsPerPage: 25,
  sortBy: [{ key: 'name', order: 'asc' }], // Initial sort configuration
})

// Define headers for the activity instances table
const instanceHeaders = [
  {
    title: 'activityInstancesTable.headerName',
    key: 'name',
    sortable: false,
    width: '25%',
  },
  {
    title: 'activityInstancesTable.headerVersion',
    key: 'version',
    sortable: false,
    width: '10%',
  },
  {
    title: 'activityInstancesTable.headerStatus',
    key: 'status',
    sortable: false,
    width: '10%',
  },
  {
    title: 'activityInstancesTable.headerActivityInstanceClass',
    key: 'activity_instance_class',
    sortable: false,
    width: '15%',
  },
  {
    title: 'activityInstancesTable.headerTopicCode',
    key: 'topic_code',
    sortable: false,
    width: '10%',
  },
  {
    title: 'activityInstancesTable.headerAdamParamCode',
    key: 'adam_param_code',
    sortable: false,
    width: '15%',
  },
]

const exportDataUrl = computed(() => {
  if (!props.activityId || !currentVersion.value) return ''
  return `/concepts/activities/activities/${props.activityId}/versions/${currentVersion.value}/instances/export`
})

// Add flatten parameter for exports
const exportDataUrlParams = computed(() => ({
  flatten: true,
}))
// Computed property to translate header titles
const translatedHeaders = computed(() => {
  return instanceHeaders.map((header) => ({
    ...header,
    title: t(header.title), // Translate the title using the key stored in the 'title' field
  }))
})

// Function to get version from props, URL or itemData (just like ActivityGroupings.vue)
function refresh() {
  const activityId = props.activityId || route.params.id
  const version =
    props.version || route.params.version || props.itemData?.activity?.version

  if (activityId && version) {
    fetchActivityInstancesFromApi(version, tableOptions.value)
  } else if (activityId) {
    // Fallback to current version lookup if we still don't have a version
    fetchCurrentActivityVersion()
  }
}

// Helper function to fetch the current activity version
function fetchCurrentActivityVersion() {
  if (props.activityId) {
    activitiesApi
      .getObject('activities', props.activityId)
      .then((response) => {
        if (response.data && response.data.version) {
          fetchActivityInstancesFromApi(
            response.data.version,
            tableOptions.value
          )
        } else {
          fetchActivityInstancesFromApi(
            defaultActivityVersion.value,
            tableOptions.value
          )
        }
      })
      .catch((error) => {
        console.error('Error fetching activity by ID:', error)
        // Fallback to default version
        fetchActivityInstancesFromApi(
          defaultActivityVersion.value,
          tableOptions.value
        )
      })
  } else {
    fetchAllActivityInstances()
  }
}

const versionFromApi = ref('')
const currentVersion = computed(() => {
  return (
    props.version ||
    route.params.version ||
    props.itemData?.activity?.version ||
    versionFromApi.value
  )
})
onMounted(() => {
  if (!currentVersion.value && props.activityId) {
    activitiesApi.getObject('activities', props.activityId).then((response) => {
      versionFromApi.value = response.data.version
    })
  }
  // Call refresh() to handle version resolution and API calls
  refresh()
})

// Watch for changes in the activityId, version, or itemData
watch(
  [
    () => props.activityId,
    () => props.version,
    () => route.params.version,
    () => props.itemData,
  ],
  () => {
    refresh()
  }
)

// Helper function to check if an item matches the search term
function itemMatchesSearch(item, searchTerm) {
  return (
    (item.name && item.name.toLowerCase().includes(searchTerm)) ||
    (item.version && item.version.toLowerCase().includes(searchTerm)) ||
    (item.status && item.status.toLowerCase().includes(searchTerm)) ||
    (item.activity_instance_class &&
      item.activity_instance_class.name &&
      item.activity_instance_class.name.toLowerCase().includes(searchTerm)) ||
    (item.topic_code && item.topic_code.toLowerCase().includes(searchTerm)) ||
    (item.adam_param_code &&
      item.adam_param_code.toLowerCase().includes(searchTerm))
  )
}

// Update expanded items when expansion changes
function updateExpandedItems(items) {
  expandedItems.value = items || []
}

// Handles filtering of activity instances based on search term
function handleFilter(filters, options) {
  loading.value = true

  if (allActivities.value.length === 0 || !filters || !filters.search) {
    activitiesList.value = allActivities.value
    loading.value = false
    return
  }

  const searchTerm = options.search?.toLowerCase()
  const filteredActivities = []

  if (searchTerm) {
    const expandedKeys = new Set(
      expandedItems.value.map((item) => item.item_key)
    )
    allActivities.value.forEach((item) => {
      const mainItemMatches = itemMatchesSearch(item, searchTerm)

      let matchingVersions = []
      if (item.versions && item.versions.length > 0) {
        matchingVersions = item.versions.filter((version) =>
          itemMatchesSearch(version, searchTerm)
        )
      }

      if (mainItemMatches || matchingVersions.length > 0) {
        filteredActivities.push({ ...item, versions: matchingVersions })
      }
    })

    activitiesList.value = filteredActivities

    expandedItems.value = filteredActivities.filter(
      (item) =>
        expandedKeys.has(item.item_key) ||
        (!itemMatchesSearch(item, searchTerm) &&
          item.versions &&
          item.versions.length > 0)
    )
  } else {
    activitiesList.value = allActivities.value
  }

  // Handle sorting changes
  if (options.sortBy && options.sortBy.length > 0) {
    const currentSortKey = tableOptions.value.sortBy?.[0]?.key
    const currentSortOrder = tableOptions.value.sortBy?.[0]?.order
    const newSortKey = options.sortBy[0].key
    const newSortOrder = options.sortBy[0].order

    // Clear any pending sort timers
    if (sortTimer) {
      clearTimeout(sortTimer)
      sortTimer = null
    }

    if (currentSortKey !== newSortKey || currentSortOrder !== newSortOrder) {
      // Update sort options
      tableOptions.value.sortBy = [...options.sortBy]
      applyClientSideSort()
    }
  }

  loading.value = false
}

// Fetches activity instances from API using pagination parameters
function fetchActivityInstancesFromApi(activityVersion, options = {}) {
  loading.value = true

  // Version parameter is kept for backward compatibility but no longer used in the URL

  if (!props.activityId) {
    console.error('No activity ID provided for activity instances fetch')
    loading.value = false
    return
  }

  // Build query parameters with pagination from options or defaults
  const params = {
    page_number: options.page || tableOptions.value.page,
    page_size: options.itemsPerPage || tableOptions.value.itemsPerPage,
    total_count: true, // Request total count for pagination
  }

  // Track if this request includes sorting parameters
  let hasSortParams = false

  // Add sort parameters to API request
  if (options.sortBy && options.sortBy.length > 0) {
    const sortItem = options.sortBy[0]
    params.sort_by = sortItem.key
    params.order = sortItem.order === 'desc' ? 'desc' : 'asc'
  }

  console.log(
    'Fetching instances from API for activity:',
    props.activityId,
    'version:',
    activityVersion
  )

  activitiesApi
    .getVersionInstances(props.activityId, activityVersion, params)
    .then((response) => {
      try {
        const items = response.data?.items || []

        // Process the items with knowledge of whether this is a sort request
        processActivityInstances(items, hasSortParams)

        paginationTotal.value = response.data?.total || items.length
      } catch (e) {
        console.error('Error processing activity instances:', e)
        activitiesList.value = []
        paginationTotal.value = 0
      }
    })
    .catch((error) => {
      console.error('Error fetching activity instances:', error)
      activitiesList.value = []
      paginationTotal.value = 0
    })
    .finally(() => {
      loading.value = false
    })
}

// Fetch all activity instances without filtering by activity
function fetchAllActivityInstances() {
  loading.value = true
  const params = {}
  activitiesApi
    .get(params, 'activity-instances')
    .then((resp) => {
      processActivityInstances(resp.data.items)
      paginationTotal.value = resp.data.total
      loading.value = false
    })
    .catch(() => {
      loading.value = false
    })
}

// Process activity instances from the API and organize them for display
function processActivityInstances(instances) {
  if (!instances || !Array.isArray(instances)) {
    allActivities.value = []
    activitiesList.value = []
    return
  }

  const result = []

  // Process each instance
  instances.forEach((instance) => {
    const resultItem = {
      ...instance,
      versions: instance.children || [],
      item_key: instance.uid + '_' + instance.version,
    }

    delete resultItem.children
    result.push(resultItem)
  })

  // Store both the original and display data
  allActivities.value = [...result]
  activitiesList.value = [...result]

  // Apply current sort if we have any
  if (tableOptions.value.sortBy && tableOptions.value.sortBy.length > 0) {
    applyClientSideSort()
  }
}

// Simple function to apply client-side sorting as a backup to server-side sorting
function applyClientSideSort() {
  if (
    !tableOptions.value.sortBy ||
    !tableOptions.value.sortBy.length ||
    !allActivities.value.length
  ) {
    return
  }

  const { key, order } = tableOptions.value.sortBy[0]

  // Create a sorted copy of the data
  const sortedResult = [...allActivities.value].sort((a, b) => {
    let aValue = a[key]
    let bValue = b[key]

    // Handle nested objects like activity_instance_class
    if (key === 'activity_instance_class') {
      aValue = a.activity_instance_class?.name || ''
      bValue = b.activity_instance_class?.name || ''
    }

    // String comparison
    if (typeof aValue === 'string' && typeof bValue === 'string') {
      aValue = aValue.toLowerCase()
      bValue = bValue.toLowerCase()
    } else {
      aValue = String(aValue || '')
      bValue = String(bValue || '')
    }

    return order === 'desc'
      ? bValue.localeCompare(aValue)
      : aValue.localeCompare(bValue)
  })

  activitiesList.value = sortedResult
}

// Check if a column is visible in the table
function isColumnVisible(key) {
  // If no table ref or no selectedColumns, show all columns
  if (!tableRef.value || !tableRef.value.selectedColumns) return true

  // Check if the column is in the selected columns list
  return tableRef.value.selectedColumns.some((col) => col.key === key)
}

// Count visible columns for the colspan attribute in expanded rows
function getVisibleColumnsCount() {
  // If no selectedColumns available, default to showing all columns
  if (!tableRef.value || !tableRef.value.selectedColumns) return 7 // Default column count

  return tableRef.value.selectedColumns.length
}

// Handle table options changes (pagination and sorting)
function updateTableOptions(options) {
  if (!options) return

  console.log('Table options updated:', JSON.stringify(options))

  // Track if pagination has changed (requiring a data refresh)
  let shouldRefreshFromApi = false

  // Check for pagination changes
  if (
    options.page !== tableOptions.value.page ||
    options.itemsPerPage !== tableOptions.value.itemsPerPage
  ) {
    tableOptions.value.page = options.page
    tableOptions.value.itemsPerPage = options.itemsPerPage
    shouldRefreshFromApi = true
  }

  // Only refresh from API for pagination changes, not for sorting
  if (
    shouldRefreshFromApi &&
    props.activityId &&
    (props.version || route.params.version)
  ) {
    const version = props.version || route.params.version
    fetchActivityInstancesFromApi(version, tableOptions.value)
  }
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
.activities-row {
  margin: 0 !important;
  width: 100%;
}

.activities-col {
  padding: 0 !important;
}

/* Ensure card content takes full width */
.activities-row :deep(.v-card-text) {
  width: 100% !important;
  padding: 0 !important;
}

/* Cell styling */
.data-cell {
  border: 0.5px solid #ddd !important;
}

/* Force table to take full width */
.activities-row :deep(.v-data-table),
.activities-row :deep(.v-table),
.activities-row :deep(table) {
  width: 100% !important;
  table-layout: fixed !important;
}

.text-truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}

.expanded-parent-row {
  background-color: rgb(var(--v-theme-nnTableRowExpanded)) !important;
}

/* Child row styling */
:deep(.child-row) {
  background-color: rgb(var(--v-theme-nnTableRowChild)) !important;
}

:deep(.expanded-parent-row) {
  background-color: rgb(var(--v-theme-nnTableRowExpanded)) !important;
}

/* Table styling overrides that penetrate component boundaries */
.activity-overview-container :deep(.v-table),
.activities-row :deep(.v-table) {
  background: transparent !important;
}

.activity-overview-container :deep(.v-data-table__td),
.activities-row :deep(.v-data-table__td) {
  background-color: white !important;
}

.activity-overview-container :deep(.v-data-table__th),
.activities-row :deep(.v-data-table__th) {
  background-color: rgb(var(--v-theme-nnTrueBlue)) !important;
}

.activity-overview-container :deep(.v-data-table__tbody tr),
.activities-row :deep(.v-data-table__tbody tr) {
  background-color: white !important;
}

.activity-overview-container :deep(.v-card),
.activity-overview-container :deep(.v-sheet),
.activities-row :deep(.v-card),
.activities-row :deep(.v-sheet) {
  background-color: transparent !important;
  box-shadow: none !important;
}

.activities-row :deep(.expanded-parent-row),
.activities-row :deep(.expanded-parent-row td) {
  background-color: rgb(var(--v-theme-nnTableRowExpanded)) !important;
}

.activities-row :deep(.child-row),
.activities-row :deep(.child-row td) {
  background-color: rgb(var(--v-theme-nnTableRowChild)) !important;
}

.activities-row :deep(.expanded-parent-row td),
.activities-row :deep(.child-row td) {
  border: 0.5px solid #ddd !important;
}
</style>
