<template>
  <div class="activity-item-class-overview-container">
    <v-card elevation="0" class="rounded-0">
      <v-card-title class="d-flex">
        <v-spacer />
        <v-btn
          variant="outlined"
          color="nnBaseBlue"
          icon
          size="small"
          @click="closePage"
        >
          <v-icon>mdi-close</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('_global.close') }}
          </v-tooltip>
        </v-btn>
      </v-card-title>
      <v-card-text>
        <!-- Activity Item Class Summary -->
        <ActivitySummary
          v-if="itemOverview && itemOverview.activity_item_class"
          :activity="adaptForSummary(itemOverview.activity_item_class)"
          :all-versions="allVersions(itemOverview)"
          :show-data-collection="false"
          :show-library="false"
          :show-abbreviation="false"
          :show-synonyms="false"
          :show-nci-concept-id="true"
          class="activity-summary"
          @version-change="(value) => manualChangeVersion(value)"
        />

        <!-- Activity Instance Classes Table -->
        <div class="activity-section">
          <div class="section-header mb-1">
            <h3 class="text-headline-small font-weight-bold text-primary">
              {{ $t('ActivityItemClassOverview.activity_instance_classes') }}
            </h3>
          </div>
          <div>
            <NNTable
              key="instancesTable"
              table-id="activity-item-class-instances"
              :headers="instanceClassHeaders"
              :items="searchTerm ? filteredInstanceClasses : instanceClasses"
              :items-length="
                searchTerm
                  ? filteredInstanceClasses.length
                  : instanceClassesTotal
              "
              :items-per-page="instanceClassesItemsPerPage"
              :hide-export-button="false"
              :hide-default-switches="true"
              :disable-filtering="true"
              :hide-search-field="false"
              :modifiable-table="true"
              :no-padding="true"
              elevation="0"
              item-value="uid"
              :disable-sort="false"
              :loading="instanceClassesLoading"
              :items-per-page-options="itemsPerPageOptions"
              :server-items-length="instanceClassesTotal"
              :export-config="{
                objectLabel: 'Activity Instance Classes',
                dataUrl: `activity-item-classes/${$route.params.id}/activity-instance-classes`,
              }"
              @update:options="handleInstanceClassesOptions"
              @filter="handleInstanceClassFilter"
            >
              <template #[`item.instance_name`]="{ item }">
                <router-link
                  :to="{
                    name: item.parent_class
                      ? 'ActivityInstanceClassOverview'
                      : 'ActivityInstanceParentClassOverview',
                    params: { id: item.uid, version: item.version },
                  }"
                  class="d-block text-primary"
                >
                  {{ item.name }}
                </router-link>
              </template>
              <template #[`item.adam_param_specific_enabled`]="{ item }">
                {{ item.adam_param_specific_enabled ? 'Yes' : 'No' }}
              </template>
              <template #[`item.mandatory`]="{ item }">
                {{ item.mandatory ? $t('_global.yes') : $t('_global.no') }}
              </template>
              <template #[`item.modified`]="{ item }">
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
        <div v-if="displayApplicableCodelists" class="activity-section">
          <div class="section-header mb-1">
            <h3 class="text-headline-small font-weight-bold text-primary">
              {{ $t('ActivityItemClassOverview.applicable_codelists') }}
            </h3>
          </div>
          <div>
            <NNTable
              key="codelistsTable"
              table-id="activity-item-class-codelists"
              :headers="codelistHeaders"
              :items="codelists"
              :items-length="totalCodelists"
              hide-default-switches
              hide-export-button
              hide-search-field
              disable-filtering
              no-padding
              item-value="uid"
              :loading="codelistsLoading"
              @filter="fetchCodelists"
            >
              <template #[`item.name.is_ordinal`]="{ item }">
                {{ item.is_ordinal ? $t('_global.yes') : $t('_global.no') }}
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
import { useI18n } from 'vue-i18n'
import ActivitySummary from '@/components/library/ActivitySummary.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import activityItemClasses from '@/api/activityItemClasses'
import filteringParameters from '@/utils/filteringParameters'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const itemOverview = ref(null)

// Paginated data for activity instance classes table
const instanceClasses = ref([])
const instanceClassesTotal = ref(0)
const instanceClassesLoading = ref(false)
const instanceClassesPage = ref(1)
const instanceClassesItemsPerPage = ref(100)
const searchTerm = ref('')
const filteredInstanceClasses = ref([])
const codelists = ref([])
const codelistsLoading = ref(false)
const totalCodelists = ref(0)

const itemsPerPageOptions = [10, 25, 50, 100, 500, 1000]

const instanceClassHeaders = [
  { title: 'NAME', key: 'instance_name' },
  { title: 'ADAM PARAM SPECIFIC ENABLED', key: 'adam_param_specific_enabled' },
  { title: 'MANDATORY', key: 'mandatory' },
  { title: 'MODIFIED', key: 'modified' },
  { title: 'MODIFIED BY', key: 'modified_by' },
  { title: 'VERSION', key: 'version' },
  { title: 'STATUS', key: 'status' },
]

const codelistHeaders = [
  { title: t('_global.name'), key: 'name.name' },
  { title: t('_global.submission_value'), key: 'attributes.submission_value' },
  {
    title: t('CodeListDetail.nci_pref_name'),
    key: 'attributes.nci_preferred_name',
  },
  { title: t('CodeListDetail.is_ordinal'), key: 'name.is_ordinal' },
  { title: t('_global.definition'), key: 'attributes.definition' },
]

const displayApplicableCodelists = computed(
  () =>
    itemOverview.value?.activity_item_class?.name ===
    'categoric_finding_original_result'
)

// Expose itemOverview for parent component
defineExpose({ itemOverview })

function adaptForSummary(activityItemClass) {
  const adapted = {
    name: activityItemClass.name,
    display_name: activityItemClass.display_name,
    start_date: activityItemClass.start_date,
    end_date: activityItemClass.end_date,
    status: activityItemClass.status,
    version: route.params.version || activityItemClass.version,
    definition: activityItemClass.definition,
    nci_concept_id: activityItemClass.nci_code,
    nci_concept_name: activityItemClass.nci_concept_name,
    modified_date: activityItemClass.modified_date,
    modified_by: activityItemClass.author_username,
  }
  return adapted
}

function allVersions(item) {
  if (!item || !item.all_versions) return []
  return [...item.all_versions]
}

function changeVersion(version) {
  router.push({
    name: 'ActivityItemClassOverview',
    params: { id: route.params.id, version },
  })
}

function manualChangeVersion(version) {
  changeVersion(version)
}

async function closePage() {
  let isNsv = Boolean(
    itemOverview.value?.activity_item_class?.non_standard_variable
  )
  if (!isNsv) {
    try {
      const resp = await activityItemClasses.get(route.params.id)
      isNsv = Boolean(resp.data?.non_standard_variable)
    } catch (error) {
      console.error('Error checking NSV status:', error)
    }
  }
  router.push({
    name: 'Activities',
    params: { tab: isNsv ? 'non-standard-variables' : 'activity-item-classes' },
  })
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

// Fetch activity instance classes with pagination
async function fetchInstanceClasses(page = 1, itemsPerPage = 100) {
  try {
    instanceClassesLoading.value = true
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

    const response = await activityItemClasses.getActivityInstanceClasses(
      uid,
      params
    )
    instanceClasses.value = response.data.items || []
    instanceClassesTotal.value = response.data.total || 0
  } catch (error) {
    console.error('Error fetching activity instance classes:', error)
    instanceClasses.value = []
    instanceClassesTotal.value = 0
  } finally {
    instanceClassesLoading.value = false
  }
}

// Handle activity instance classes table options
function handleInstanceClassesOptions(options) {
  if (
    options &&
    (options.page !== instanceClassesPage.value ||
      options.itemsPerPage !== instanceClassesItemsPerPage.value)
  ) {
    instanceClassesPage.value = options.page || 1
    instanceClassesItemsPerPage.value = options.itemsPerPage || 100
    fetchInstanceClasses(
      instanceClassesPage.value,
      instanceClassesItemsPerPage.value
    )
  }
}

// Handle filter for Activity Instance Classes table
function handleInstanceClassFilter(_filters, options) {
  // Handle both pagination and search
  if (options) {
    // Check for pagination changes
    if (
      options.page !== instanceClassesPage.value ||
      options.itemsPerPage !== instanceClassesItemsPerPage.value
    ) {
      handleInstanceClassesOptions(options)
    }

    // Handle search
    if (options.search !== undefined) {
      searchTerm.value = options.search.toLowerCase()
      if (searchTerm.value) {
        let itemsToFilter = instanceClasses.value || []
        itemsToFilter = itemsToFilter.filter((item) => {
          const searchableFields = [
            item.name,
            item.modified_by,
            item.version,
            item.status,
            item.adam_param_specific_enabled ? 'yes' : 'no',
            item.mandatory ? 'yes' : 'no',
          ]

          const searchableText = searchableFields
            .filter(Boolean)
            .join(' ')
            .toLowerCase()

          return searchableText.includes(searchTerm.value)
        })
        filteredInstanceClasses.value = itemsToFilter
      } else {
        filteredInstanceClasses.value = []
      }
    }
  }
}

async function fetchCodelists(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  params.ct_catalogue_name = 'SDTM CT'
  params.valid_codelists_for_item = true
  codelistsLoading.value = true
  try {
    const resp = await activityItemClasses.getDatasetCodelists(
      route.params.id,
      'NA',
      params
    )
    codelists.value = resp.data.items
    totalCodelists.value = resp.data.total
  } finally {
    codelistsLoading.value = false
  }
}

// Initialize data on mount
onMounted(() => {
  fetchInstanceClasses(1, instanceClassesItemsPerPage.value)
})

// Watch for route changes
watch(
  () => [route.params.id, route.params.version],
  () => {
    fetchInstanceClasses(1, instanceClassesItemsPerPage.value)
  }
)
</script>

<style scoped>
.activity-item-class-overview-container {
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

/* Critical styling for white background on tables */
.activity-item-class-overview-container :deep(.v-table) {
  background: transparent !important;
}

/* Round table corners */
.activity-item-class-overview-container :deep(.v-data-table) {
  border-radius: 8px !important;
  overflow: visible;
}

.activity-item-class-overview-container :deep(.v-table__wrapper) {
  border-radius: 8px !important;
  overflow-x: auto;
}

.activity-item-class-overview-container :deep(.v-data-table__th) {
  background-color: #272e41 !important;
}

.activity-item-class-overview-container :deep(.v-data-table__tbody tr) {
  background-color: white !important;
}

.activity-item-class-overview-container :deep(.v-card),
.activity-item-class-overview-container :deep(.v-sheet) {
  background-color: transparent !important;
  box-shadow: none !important;
}
</style>
