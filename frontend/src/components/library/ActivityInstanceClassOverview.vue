<template>
  <div class="activity-instance-class-overview-container">
    <v-card elevation="0" class="rounded-0">
      <v-card-text>
        <!-- Activity Instance Class Summary -->
        <ActivitySummary
          v-if="itemOverview && itemOverview.activity_instance_class"
          :activity="adaptForSummary(itemOverview.activity_instance_class)"
          :all-versions="allVersions(itemOverview)"
          :show-data-collection="false"
          :show-library="false"
          :show-abbreviation="false"
          :show-synonyms="false"
          class="activity-summary"
          @version-change="(value) => manualChangeVersion(value)"
        />

        <!-- Activity Item Classes Table -->
        <div v-if="itemOverview" class="activity-section">
          <div class="section-header mb-1">
            <h3 class="text-headline-small font-weight-bold text-primary">
              {{ $t('ActivityInstanceClassOverview.activity_item_classes') }}
            </h3>
          </div>
          <div>
            <NNTable
              table-id="activity-instance-class-overview-item-classes"
              :headers="itemClassHeaders"
              :items="searchTerm ? filteredItemClasses : itemClasses"
              :items-length="
                searchTerm ? filteredItemClasses.length : itemClassesTotal
              "
              :items-per-page="itemClassesItemsPerPage"
              :hide-export-button="false"
              :hide-default-switches="true"
              :disable-filtering="true"
              :hide-search-field="false"
              :modifiable-table="true"
              :no-padding="true"
              elevation="0"
              class="item-classes-table activity-item-classes-styled"
              item-value="uid"
              :disable-sort="false"
              :loading="itemClassesLoading"
              :items-per-page-options="itemsPerPageOptions"
              :server-items-length="itemClassesTotal"
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
import { ref, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
// import { useI18n } from 'vue-i18n'
import ActivitySummary from '@/components/library/ActivitySummary.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import activityInstanceClasses from '@/api/activityInstanceClasses'

// const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const itemOverview = ref(null)

// Paginated data for item classes table
const itemClasses = ref([])
const itemClassesTotal = ref(0)
const itemClassesLoading = ref(false)
const itemClassesPage = ref(1)
const itemClassesItemsPerPage = ref(100)
const searchTerm = ref('')
const filteredItemClasses = ref([])

const itemsPerPageOptions = [10, 25, 50, 100, 500, 1000]

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

function adaptForSummary(activityInstanceClass) {
  const adapted = {
    name: activityInstanceClass.name,
    start_date: activityInstanceClass.start_date,
    end_date: activityInstanceClass.end_date,
    status: activityInstanceClass.status,
    version: route.params.version || activityInstanceClass.version,
    definition: activityInstanceClass.definition,
    is_domain_specific: activityInstanceClass.is_domain_specific,
    domain_specific: activityInstanceClass.is_domain_specific ? 'Yes' : 'No',
    hierarchy: activityInstanceClass.hierarchy,
    hierarchy_label: activityInstanceClass.hierarchy,
    modified_by: activityInstanceClass.author_username,
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
    name: 'ActivityInstanceClassOverview',
    params: { id: route.params.id, version },
  })
}

function manualChangeVersion(version) {
  changeVersion(version)
}

function formatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return (
    date.toLocaleDateString() +
    ', ' +
    date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  )
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

    // Add version to params if it exists
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
    if (options.search !== undefined) {
      searchTerm.value = options.search.toLowerCase()
      if (searchTerm.value) {
        let itemsToFilter = itemClasses.value || []
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
    }
  }
}

// Initialize data on mount
onMounted(() => {
  fetchItemClasses(1, itemClassesItemsPerPage.value, [])
})

// Watch for route changes
watch(
  () => [route.params.id, route.params.version],
  () => {
    fetchItemClasses(1, itemClassesItemsPerPage.value, [])
  }
)
</script>

<style scoped>
.activity-instance-class-overview-container {
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

/* Critical styling for white background on tables */
.activity-instance-class-overview-container :deep(.v-table) {
  background: transparent !important;
}

/* Round table corners */
.activity-instance-class-overview-container :deep(.v-data-table) {
  border-radius: 8px !important;
  overflow: visible;
}

.activity-instance-class-overview-container :deep(.v-table__wrapper) {
  border-radius: 8px !important;
  overflow-x: auto;
}

.activity-instance-class-overview-container :deep(.v-data-table__th) {
  background-color: #272e41 !important;
}

.activity-instance-class-overview-container :deep(.v-data-table__tbody tr) {
  background-color: white !important;
}

.activity-instance-class-overview-container :deep(.v-card),
.activity-instance-class-overview-container :deep(.v-sheet) {
  background-color: transparent !important;
  box-shadow: none !important;
}

/* Custom styling for Activity Item Classes table to match mockup */
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
