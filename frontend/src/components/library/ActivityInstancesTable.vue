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
            :items-per-page-options="itemsPerPageOptions"
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
import tablesConstants from '@/constants/tables'

// "All" (page_size=0) empties this table server-side; omit it until fixed there.
const itemsPerPageOptions = tablesConstants.ITEMS_PER_PAGE_OPTIONS.filter(
  (option) => option.value !== -1
)

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
const activeSearchTerm = ref('') // Current search term, lowercased, '' when inactive
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
    fetchActivityInstancesFromApi(version)
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
          fetchActivityInstancesFromApi(response.data.version)
        } else {
          fetchActivityInstancesFromApi(defaultActivityVersion.value)
        }
      })
      .catch((error) => {
        console.error('Error fetching activity by ID:', error)
        // Fallback to default version
        fetchActivityInstancesFromApi(defaultActivityVersion.value)
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

// Sorts a list of activities by tableOptions.sortBy; returns a new array
function sortActivities(items, sortBy) {
  if (!sortBy || !sortBy.length) return items

  const { key, order } = sortBy[0]
  return [...items].sort((a, b) => {
    let aValue = a[key]
    let bValue = b[key]

    if (key === 'activity_instance_class') {
      aValue = a.activity_instance_class?.name || ''
      bValue = b.activity_instance_class?.name || ''
    }

    aValue =
      typeof aValue === 'string' ? aValue.toLowerCase() : String(aValue || '')
    bValue =
      typeof bValue === 'string' ? bValue.toLowerCase() : String(bValue || '')

    return order === 'desc'
      ? bValue.localeCompare(aValue)
      : aValue.localeCompare(bValue)
  })
}

// Recomputes activitiesList (the current page's rows) from allActivities by
// applying the active search term, sort, and pagination, in that order.
// allActivities always holds the FULL instance set for the activity/version
// (see fetchActivityInstancesFromApi), so search and pagination never disagree
// about which instances exist - unlike filtering a single fetched server page.
function updateDisplayedActivities() {
  const term = activeSearchTerm.value
  const expandedKeys = new Set(expandedItems.value.map((item) => item.item_key))

  let filtered = allActivities.value
  if (term) {
    filtered = allActivities.value.reduce((acc, item) => {
      const mainItemMatches = itemMatchesSearch(item, term)
      const matchingVersions = (item.versions || []).filter((version) =>
        itemMatchesSearch(version, term)
      )
      if (mainItemMatches || matchingVersions.length > 0) {
        acc.push({ ...item, versions: matchingVersions })
      }
      return acc
    }, [])
  }

  filtered = sortActivities(filtered, tableOptions.value.sortBy)
  paginationTotal.value = filtered.length

  const itemsPerPage = tableOptions.value.itemsPerPage
  const pageCount =
    itemsPerPage > 0
      ? Math.max(1, Math.ceil(filtered.length / itemsPerPage))
      : 1
  if (tableOptions.value.page > pageCount) {
    tableOptions.value.page = pageCount
  }

  const start = (tableOptions.value.page - 1) * itemsPerPage
  activitiesList.value =
    itemsPerPage > 0 ? filtered.slice(start, start + itemsPerPage) : filtered

  if (term) {
    expandedItems.value = activitiesList.value.filter(
      (item) =>
        expandedKeys.has(item.item_key) ||
        (!itemMatchesSearch(item, term) &&
          item.versions &&
          item.versions.length > 0)
    )
  }
}

// Handles filtering/pagination/sort changes emitted by NNTable's @filter
function handleFilter(filters, options) {
  if (!options) return

  const term = (options.search || '').toLowerCase()
  const searchChanged = term !== activeSearchTerm.value
  const itemsPerPageChanged =
    options.itemsPerPage !== tableOptions.value.itemsPerPage

  activeSearchTerm.value = term
  tableOptions.value.itemsPerPage = options.itemsPerPage
  if (options.sortBy && options.sortBy.length > 0) {
    tableOptions.value.sortBy = [...options.sortBy]
  }
  // A new search or page-size resets to page 1; otherwise honor the clicked page
  tableOptions.value.page =
    searchChanged || itemsPerPageChanged ? 1 : options.page

  updateDisplayedActivities()
}

// Fetches the FULL instance set (not one server page) so search/pagination
// in updateDisplayedActivities never miss a match on an unfetched page. A
// second, exact-sized call covers the rare activity beyond the initial page.
const INITIAL_FETCH_PAGE_SIZE = 100

function fetchActivityInstancesFromApi(activityVersion) {
  loading.value = true

  if (!props.activityId) {
    console.error('No activity ID provided for activity instances fetch')
    loading.value = false
    return
  }

  activitiesApi
    .getVersionInstances(props.activityId, activityVersion, {
      page_number: 1,
      page_size: INITIAL_FETCH_PAGE_SIZE,
      total_count: true,
    })
    .then((response) => {
      const items = response.data?.items || []
      const total = response.data?.total ?? items.length

      if (total > items.length) {
        return activitiesApi
          .getVersionInstances(props.activityId, activityVersion, {
            page_number: 1,
            page_size: total,
          })
          .then((fullResponse) => fullResponse.data?.items || [])
      }
      return items
    })
    .then((items) => {
      processActivityInstances(items)
      tableOptions.value.page = 1
      updateDisplayedActivities()
    })
    .catch((error) => {
      console.error('Error fetching activity instances:', error)
      allActivities.value = []
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
  activitiesApi
    .get({}, 'activity-instances')
    .then((resp) => {
      processActivityInstances(resp.data.items)
      tableOptions.value.page = 1
      updateDisplayedActivities()
    })
    .catch((error) => {
      console.error('Error fetching activity instances:', error)
      allActivities.value = []
      activitiesList.value = []
      paginationTotal.value = 0
    })
    .finally(() => {
      loading.value = false
    })
}

// Normalizes raw API instances into allActivities; display state (activitiesList,
// paginationTotal) is derived from it by updateDisplayedActivities.
function processActivityInstances(instances) {
  if (!instances || !Array.isArray(instances)) {
    allActivities.value = []
    return
  }

  allActivities.value = instances.map((instance) => {
    const resultItem = {
      ...instance,
      versions: instance.children || [],
      item_key: instance.uid + '_' + instance.version,
    }
    delete resultItem.children
    return resultItem
  })
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

// Handle table options changes (pagination and sorting); allActivities is
// already fully loaded, so this only needs to re-slice it, never refetch.
function updateTableOptions(options) {
  if (!options) return

  tableOptions.value.page = options.page
  tableOptions.value.itemsPerPage = options.itemsPerPage
  if (options.sortBy && options.sortBy.length > 0) {
    tableOptions.value.sortBy = [...options.sortBy]
  }

  updateDisplayedActivities()
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
