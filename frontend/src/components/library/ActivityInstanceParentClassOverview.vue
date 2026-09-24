<template>
  <div class="activity-instance-parent-class-overview-container">
    <v-card elevation="0" class="rounded-0">
      <v-card-text>
        <!-- Activity Instance Parent Class Summary -->
        <ActivitySummary
          v-if="itemOverview && itemOverview.parent_activity_instance_class"
          :activity="
            adaptForSummary(itemOverview.parent_activity_instance_class)
          "
          :all-versions="allVersions(itemOverview)"
          :show-data-collection="false"
          :show-library="false"
          :show-abbreviation="false"
          :show-synonyms="false"
          class="activity-summary"
          @version-change="(value) => manualChangeVersion(value)"
        />

        <!-- Activity Instance Classes Table -->
        <div class="activity-section">
          <div class="section-header mb-1">
            <h3 class="text-headline-small font-weight-bold text-primary">
              {{
                $t('ActivityInstanceClassOverview.activity_instance_classes')
              }}
            </h3>
          </div>
          <div>
            <NNTable
              table-id="activity-instance-parent-child-classes"
              :headers="instanceClassHeaders"
              :items="addUniqueKeys(childClasses, 'instance') || []"
              :items-length="childClassesTotal"
              :items-per-page="childClassesItemsPerPage"
              :hide-export-button="false"
              :hide-default-switches="true"
              :disable-filtering="true"
              :hide-search-field="true"
              :modifiable-table="true"
              :no-padding="true"
              elevation="0"
              class="instance-classes-table activity-instance-classes-styled"
              item-value="unique_key"
              :disable-sort="false"
              :loading="childClassesLoading"
              :items-per-page-options="[10, 25, 50, 100]"
              :server-items-length="childClassesTotal"
              :export-config="{
                objectLabel: 'Activity Instance Classes',
                dataUrl: `activity-instance-classes/${$route.params.id}/activity-instance-classes`,
              }"
              @update:options="handleChildClassesOptions"
            >
              <template #[`item.name`]="{ item }">
                <router-link
                  :to="{
                    name: 'ActivityInstanceClassOverview',
                    params: { id: item.uid, version: item.version },
                  }"
                  class="d-block text-primary"
                >
                  {{ item.name }}
                </router-link>
              </template>
              <template #[`item.is_domain_specific`]="{ item }">
                {{ item.is_domain_specific ? 'Yes' : 'No' }}
              </template>
              <template #[`item.definition`]="{ item }">
                {{ item.definition || '' }}
              </template>
              <template #[`item.library_name`]="{ item }">
                {{ item.library_name || '' }}
              </template>
              <template #[`item.modified_date`]="{ item }">
                {{ item.modified_date ? formatDate(item.modified_date) : '' }}
              </template>
              <template #[`item.modified_by`]="{ item }">
                {{ item.modified_by || '' }}
              </template>
              <template #[`item.version`]="{ item }">
                {{ item.version || '' }}
              </template>
              <template #[`item.status`]="{ item }">
                <StatusChip v-if="item.status" :status="item.status" />
                <span v-else></span>
              </template>
            </NNTable>
          </div>
        </div>

        <!-- Activity Item Classes Table -->
        <div class="activity-section">
          <div class="section-header mb-1">
            <h3 class="text-headline-small font-weight-bold text-primary">
              {{ $t('ActivityInstanceClassOverview.activity_item_classes') }}
            </h3>
          </div>
          <div>
            <NNTable
              table-id="activity-instance-parent-item-classes"
              :headers="itemClassHeaders"
              :items="activityItemClasses"
              :items-length="activityItemClasses.length"
              :items-per-page="itemClassesItemsPerPage"
              :hide-export-button="false"
              :hide-default-switches="true"
              :disable-filtering="true"
              :modifiable-table="true"
              :no-padding="true"
              elevation="0"
              class="item-classes-table activity-item-classes-styled"
              item-value="unique_key"
              :disable-sort="false"
              :loading="itemClassesLoading"
              :items-per-page-options="itemsPerPageOptions"
              :server-items-length="itemClassesTotal"
              :use-cached-filtering="false"
              :export-config="{
                objectLabel: 'Activity Item Classes',
                dataUrl: `activity-instance-classes/${$route.params.id}/activity-item-classes`,
              }"
              @update:options="handleItemClassesOptions"
              @filter="handleItemClassFilter"
            >
              <template #[`item.name`]="{ item }">
                <router-link
                  v-if="item.uid"
                  :to="{
                    name: 'ActivityItemClassOverview',
                    params: { id: item.uid, version: item.version },
                  }"
                  class="text-primary"
                >
                  {{ item.name || '' }}
                </router-link>
                <span v-else>{{ item.name || '' }}</span>
              </template>
              <template #[`item.parent_name`]="{ item }">
                <router-link
                  v-if="item.parent_uid"
                  :to="{
                    name: 'ActivityInstanceClassOverview',
                    params: { id: item.parent_uid },
                  }"
                  class="text-primary"
                >
                  {{ item.parent_name || '' }}
                </router-link>
                <span v-else>{{ item.parent_name || '' }}</span>
              </template>
              <template #[`item.definition`]="{ item }">
                {{ item.definition || '' }}
              </template>
              <template #[`item.library_name`]="{ item }">
                {{ item.library_name || '' }}
              </template>
              <template #[`item.modified_date`]="{ item }">
                {{ item.modified_date ? formatDate(item.modified_date) : '' }}
              </template>
              <template #[`item.modified_by`]="{ item }">
                {{ item.modified_by || '' }}
              </template>
              <template #[`item.version`]="{ item }">
                {{ item.version || '' }}
              </template>
              <template #[`item.status`]="{ item }">
                <StatusChip v-if="item.status" :status="item.status" />
                <span v-else></span>
              </template>
            </NNTable>
          </div>
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import ActivitySummary from '@/components/library/ActivitySummary.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import activityInstanceClasses from '@/api/activityInstanceClasses'

const route = useRoute()
const router = useRouter()

const itemOverview = ref(null)
const filteredItemClasses = ref([])
const searchTerm = ref('')

// Paginated data for tables
const childClasses = ref([])
const childClassesTotal = ref(0)
const childClassesLoading = ref(false)
const childClassesPage = ref(1)
const childClassesItemsPerPage = ref(25)

const itemClasses = ref([])
const itemClassesTotal = ref(0)
const itemClassesLoading = ref(false)
const itemClassesPage = ref(1)
const itemClassesItemsPerPage = ref(100)

const itemsPerPageOptions = [10, 25, 50, 100, 500, 1000]

const instanceClassHeaders = [
  { title: 'NAME', key: 'name' },
  { title: 'DEFINITION', key: 'definition' },
  { title: 'DOMAIN SPECIFIC', key: 'is_domain_specific' },
  { title: 'LIBRARY', key: 'library_name' },
  { title: 'MODIFIED', key: 'modified_date' },
  { title: 'MODIFIED BY', key: 'modified_by' },
  { title: 'VERSION', key: 'version' },
  { title: 'STATUS', key: 'status' },
]

const itemClassHeaders = [
  { title: 'NAME', key: 'name' },
  { title: 'ADDITIONAL PARENT INSTANCE CLASS', key: 'parent_name' },
  { title: 'DEFINITION', key: 'definition' },
  { title: 'MODIFIED', key: 'modified_date' },
  { title: 'MODIFIED BY', key: 'modified_by' },
  { title: 'VERSION', key: 'version' },
  { title: 'STATUS', key: 'status' },
]

// Expose itemOverview for parent component
defineExpose({ itemOverview })

const activityItemClasses = computed(() => {
  return searchTerm.value
    ? filteredItemClasses.value
    : addUniqueKeys(itemClasses.value, 'item') || []
})

// Add unique keys to items to avoid duplicate key warnings
function addUniqueKeys(items, prefix = 'item') {
  if (!items) return items
  return items.map((item, index) => ({
    ...item,
    unique_key: `${prefix}_${item.uid || item.name || 'item'}_${index}`,
  }))
}

function adaptForSummary(parentClass) {
  const adapted = {
    name: parentClass.name,
    start_date: parentClass.start_date,
    end_date: parentClass.end_date,
    status: parentClass.status,
    version: route.params.version || parentClass.version,
    definition: parentClass.definition,
    is_domain_specific: parentClass.is_domain_specific,
    domain_specific: parentClass.is_domain_specific ? 'Yes' : 'No',
    hierarchy: parentClass.hierarchy,
    hierarchy_label: parentClass.hierarchy,
    modified_by: parentClass.author_username,
  }
  // Don't include synonyms at all
  delete adapted.synonyms
  return adapted
}

function allVersions(item) {
  if (!item || !item.all_versions) return []
  return [...item.all_versions]
}

function changeVersion(version) {
  router.push({
    name: 'ActivityInstanceParentClassOverview',
    params: { id: route.params.id, version },
  })
}

function manualChangeVersion(version) {
  changeVersion(version)
}

function formatDate(dateString) {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return (
    date.toLocaleDateString() +
    ', ' +
    date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  )
}

// Fetch child classes with pagination
async function fetchChildClasses(page = 1, itemsPerPage = 25, sortBy = []) {
  try {
    childClassesLoading.value = true
    const uid = route.params.id
    const version = route.params.version

    const params = {
      page_number: page,
      page_size: itemsPerPage,
      total_count: true,
    }

    if (version) {
      params.version = version
    }

    // Add sorting if specified
    if (sortBy && sortBy.length > 0) {
      const sortField = sortBy[0].key
      const sortOrder = sortBy[0].order === 'asc'
      params.sort_by = JSON.stringify({ [sortField]: sortOrder })
    }

    const response = await activityInstanceClasses.getChildClasses(uid, params)
    childClasses.value = response.data.items || []
    childClassesTotal.value = response.data.total || 0
  } catch (error) {
    console.error('Error fetching child classes:', error)
    childClasses.value = []
    childClassesTotal.value = 0
  } finally {
    childClassesLoading.value = false
  }
}

// Fetch item classes with pagination
async function fetchItemClasses(page = 1, itemsPerPage = 100, sortBy = []) {
  try {
    itemClassesLoading.value = true
    const uid = route.params.id
    const version = route.params.version

    const params = {
      page_number: page,
      page_size: itemsPerPage,
      total_count: true,
    }

    if (version) {
      params.version = version
    }

    // Add sorting if specified
    if (sortBy && sortBy.length > 0) {
      const sortField = sortBy[0].key
      const sortOrder = sortBy[0].order === 'asc'
      params.sort_by = JSON.stringify({ [sortField]: sortOrder })
    }

    const response = await activityInstanceClasses.getItemClasses(uid, params)
    itemClasses.value = response.data.items || []
    itemClassesTotal.value = response.data.total || 0
  } catch (error) {
    console.error('Error fetching item classes:', error)
    itemClasses.value = []
    itemClassesTotal.value = 0
  } finally {
    itemClassesLoading.value = false
  }
}

// Handle child classes table options
function handleChildClassesOptions(options) {
  if (!options) return

  childClassesPage.value = options.page || 1
  childClassesItemsPerPage.value = options.itemsPerPage || 25

  fetchChildClasses(
    childClassesPage.value,
    childClassesItemsPerPage.value,
    options.sortBy || []
  )
}

// Handle item classes table options
function handleItemClassesOptions(options) {
  if (!options) return

  itemClassesPage.value = options.page || 1
  itemClassesItemsPerPage.value = options.itemsPerPage || 100

  fetchItemClasses(
    itemClassesPage.value,
    itemClassesItemsPerPage.value,
    options.sortBy || []
  )
}

// Handle filter for Activity Item Classes table
function handleItemClassFilter(_filters, options) {
  // Handle both pagination and search
  if (options) {
    // Check for pagination changes
    if (
      options.page !== itemClassesPage.value ||
      options.itemsPerPage !== itemClassesItemsPerPage.value
    ) {
      handleItemClassesOptions(options)
    }

    // Handle search
    if (options.search !== undefined && options.search !== null) {
      searchTerm.value = options.search.toLowerCase()
      if (searchTerm.value) {
        let itemsToFilter = addUniqueKeys(itemClasses.value, 'item') || []
        itemsToFilter = itemsToFilter.filter((item) => {
          const searchableFields = [
            item.name,
            item.parent_name,
            item.definition,
            item.modified_by,
            item.version,
            item.status,
          ]

          const searchableText = searchableFields
            .filter(Boolean)
            .join(' ')
            .toLowerCase()

          return searchableText.includes(searchTerm.value)
        })
        filteredItemClasses.value = itemsToFilter
      } else {
        filteredItemClasses.value = []
      }
    } else {
      searchTerm.value = ''
      filteredItemClasses.value = itemClasses.value
    }
  }
}

// Initialize data on mount
onMounted(() => {
  fetchChildClasses(1, childClassesItemsPerPage.value, [])
  fetchItemClasses(1, itemClassesItemsPerPage.value, [])
})

// Watch for route changes
watch(
  () => [route.params.id, route.params.version],
  () => {
    fetchChildClasses(1, childClassesItemsPerPage.value, [])
    fetchItemClasses(1, itemClassesItemsPerPage.value, [])
  }
)
</script>

<style scoped>
.activity-instance-parent-class-overview-container {
  width: 100%;
  background-color: transparent;
}

.activity-section {
  margin-top: 1rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-header h3 {
  color: rgb(var(--v-theme-primary)) !important;
}

/* Hide empty search area when search is disabled */
.instance-classes-table :deep(.v-card-title) {
  display: none !important;
}

/* Critical styling for white background on tables */
.activity-instance-parent-class-overview-container :deep(.v-table) {
  background: transparent !important;
}

/* Round table corners */
.activity-instance-parent-class-overview-container :deep(.v-data-table) {
  border-radius: 8px !important;
  overflow: visible;
}

.activity-instance-parent-class-overview-container :deep(.v-table__wrapper) {
  border-radius: 8px !important;
  overflow-x: auto;
}

.activity-instance-parent-class-overview-container :deep(.v-data-table__th) {
  background-color: #272e41 !important;
}

.activity-instance-parent-class-overview-container
  :deep(.v-data-table__tbody tr) {
  background-color: white !important;
}

.activity-instance-parent-class-overview-container :deep(.v-card),
.activity-instance-parent-class-overview-container :deep(.v-sheet) {
  background-color: transparent !important;
  box-shadow: none !important;
}

/* Custom styling for Activity tables to match mockup */
:deep(.activity-instance-classes-styled),
:deep(.activity-item-classes-styled) {
  /* Table header styling */
  thead tr {
    background: #272e41 !important;
  }

  thead th {
    background: transparent !important;
    color: white !important;
    font-weight: 600 !important;
    border-bottom: none !important;
  }

  /* Table row styling */
  tbody tr {
    border-bottom: 1px solid #e0e0e0;
  }

  tbody tr:hover {
    background-color: #f5f5f5;
  }

  /* Status chip colors */
  .v-chip.bg-success {
    background-color: #4caf50 !important;
  }
}
</style>
