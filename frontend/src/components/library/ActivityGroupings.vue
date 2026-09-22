<template>
  <div>
    <v-row v-if="versionDetail" class="activity-section">
      <v-col cols="12" class="px-0">
        <div class="section-header mb-1">
          <h3 class="text-headline-small font-weight-bold text-primary">
            {{ $t('ActivityOverview.activity_groupings') }}
          </h3>
        </div>
        <div class="table-container">
          <NNTable
            table-id="activity-groupings-table"
            :headers="groupingsHeaders"
            :items="filteredGroupings"
            item-value="item_key"
            :items-length="paginationTotal"
            :hide-export-button="true"
            hide-default-switches
            :show-filter-bar-by-default="false"
            :disable-filtering="true"
            :hide-search-field="false"
            :modifiable-table="true"
            :no-padding="true"
            elevation="0"
            :initial-sort="initialSort"
            :loading="isLoading"
            :use-cached-filtering="false"
            @filter="handleFilter"
            @update:options="updateTableOptions"
          >
            <template #[`item.activity_group`]="{ item }">
              <router-link
                :to="{
                  name: 'GroupOverview',
                  params: {
                    id: item.activity_group.uid,
                    version: item.group_version,
                  },
                }"
                class="d-block"
              >
                {{ item.activity_group.name }}
              </router-link>
              <div class="text-body-small text-grey-darken-1">
                {{ $t('_global.version') }} {{ item.group_version }}
                <span v-if="item.group_status" class="ml-2"
                  >- {{ item.group_status }}</span
                >
              </div>
            </template>
            <template #[`item.activity_subgroup`]="{ item }">
              <router-link
                :to="{
                  name: 'SubgroupOverview',
                  params: {
                    id: item.activity_subgroup.uid,
                    version: item.subgroup_version,
                  },
                }"
                class="d-block"
              >
                {{ item.activity_subgroup.name }}
              </router-link>
              <div class="text-body-small text-grey-darken-1">
                {{ $t('_global.version') }} {{ item.subgroup_version }}
                <span v-if="item.subgroup_status" class="ml-2"
                  >- {{ item.subgroup_status }}</span
                >
              </div>
            </template>
            <template #[`item.activity_instances`]="{ item }">
              <div
                v-if="
                  item.activity_instances && item.activity_instances.length > 0
                "
              >
                <div
                  v-for="instance in item.activity_instances"
                  :key="instance.uid"
                  class="mb-1"
                >
                  <router-link
                    :to="{
                      name: 'ActivityInstanceOverview',
                      params: {
                        id: instance.uid,
                      },
                    }"
                    class="d-block"
                  >
                    {{ instance.name }}
                  </router-link>
                  <div
                    v-if="instance.version"
                    class="text-body-small text-grey-darken-1"
                  >
                    {{ $t('_global.version') }} {{ instance.version }}
                  </div>
                </div>
              </div>
              <div v-else class="text-body-small text-grey-darken-1">
                {{ $t('ActivityOverview.no_instances') }}
              </div>
              <v-tooltip location="bottom">
                <template #activator="{ props: tooltipProps }">
                  <v-btn
                    v-bind="tooltipProps"
                    class="mt-2"
                    size="small"
                    variant="outlined"
                    color="primary"
                    prepend-icon="mdi-plus"
                    @click="createInstance(item)"
                  >
                    {{ $t('ActivityOverview.create_instance') }}
                  </v-btn>
                </template>
                {{ $t('ActivityOverview.create_instance_tooltip') }}
              </v-tooltip>
            </template>
          </NNTable>
        </div>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import activities from '@/api/activities'
import NNTable from '@/components/tools/NNTable.vue'

const { t } = useI18n()
const route = useRoute()

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
    default: '',
  },
})

const emit = defineEmits(['refresh', 'create-instance'])

const versionDetail = ref(null)
const paginationTotal = ref(0)
const isLoading = ref(false)
const tableOptions = ref({
  page: 1,
  itemsPerPage: 25,
  sortBy: [],
  sortDesc: [],
})

const filteredGroupings = ref([])

const initialSort = ref([{ key: 'activity_group', order: 'asc' }])

const groupingsHeaders = [
  {
    title: t('ActivityOverview.activity_group'),
    key: 'activity_group',
    width: '30%',
  },
  {
    title: t('ActivityOverview.activity_subgroup'),
    key: 'activity_subgroup',
    width: '30%',
  },
  {
    title: t('ActivityOverview.instances'),
    key: 'activity_instances',
    width: '40%',
  },
]

// Helper function to check if an item matches search term for activity groupings
function itemMatchesSearch(item, searchTerm) {
  if (!searchTerm || searchTerm === '') return true
  const term = searchTerm.toLowerCase()

  if (item.activity_group?.name?.toLowerCase().includes(term)) return true

  if (item.activity_subgroup?.name?.toLowerCase().includes(term)) return true

  if (
    item.group_version &&
    item.group_version.toString().toLowerCase().includes(term)
  )
    return true

  if (
    item.subgroup_version &&
    item.subgroup_version.toString().toLowerCase().includes(term)
  )
    return true

  if (
    item.activity_instances?.some(
      (instance) =>
        instance.name?.toLowerCase().includes(term) ||
        instance.version?.toLowerCase().includes(term)
    )
  )
    return true

  return false
}

function createInstance(groupingItem) {
  const activityName =
    versionDetail.value?.items?.[0]?.name ||
    props.itemData?.activity?.name ||
    ''
  emit('create-instance', {
    activity_uid: props.activityId || route.params.id,
    activity_name: activityName,
    activity_group_uid: groupingItem.activity_group.uid,
    activity_group_name: groupingItem.activity_group.name,
    activity_subgroup_uid: groupingItem.activity_subgroup.uid,
    activity_subgroup_name: groupingItem.activity_subgroup.name,
  })
}

// Handle filter events from NNTable
function handleFilter(_, options) {
  let groupingsToFilter = [...transformedGroupings.value]

  // Apply search filter if provided
  if (options && options.search) {
    const searchTerm = options.search.toLowerCase()
    groupingsToFilter = groupingsToFilter.filter((item) =>
      itemMatchesSearch(item, searchTerm)
    )
  }

  // Apply sorting if provided
  if (options && options.sortBy && options.sortBy.length > 0) {
    const sortItem = options.sortBy[0]
    const key = sortItem.key
    const order = sortItem.order

    groupingsToFilter.sort((a, b) => {
      let valA, valB

      // Handle nested properties for sorting
      if (key === 'activity_group') {
        valA = a.activity_group?.name?.toLowerCase() || ''
        valB = b.activity_group?.name?.toLowerCase() || ''
      } else if (key === 'activity_subgroup') {
        valA = a.activity_subgroup?.name?.toLowerCase() || ''
        valB = b.activity_subgroup?.name?.toLowerCase() || ''
      } else {
        valA = a[key]
        valB = b[key]
      }

      // Handle undefined values
      valA = valA || ''
      valB = valB || ''

      // Compare based on type
      if (typeof valA === 'string' && typeof valB === 'string') {
        return order === 'asc'
          ? valA.localeCompare(valB)
          : valB.localeCompare(valA)
      } else {
        return order === 'asc' ? valA - valB : valB - valA
      }
    })

    // Update tableOptions with the current sort
    tableOptions.value.sortBy = [...options.sortBy]
    tableOptions.value.sortDesc = [...(options.sortDesc || [])]
  }

  // Update the filtered data
  filteredGroupings.value = groupingsToFilter
}

// Handle table options changes (pagination and sorting)
function updateTableOptions(options) {
  if (!options) return

  // Store sort options separately to prevent losing them
  if (options.sortBy && options.sortBy.length > 0) {
    tableOptions.value.sortBy = [...options.sortBy]
  }

  if (
    options.page !== tableOptions.value.page ||
    options.itemsPerPage !== tableOptions.value.itemsPerPage
  ) {
    tableOptions.value.page = options.page
    tableOptions.value.itemsPerPage = options.itemsPerPage

    const activityId = props.activityId || route.params.id
    const version =
      props.version || route.params.version || props.itemData?.activity?.version

    if (activityId && version) {
      fetchVersionDetail(activityId, version, {
        page: options.page,
        itemsPerPage: options.itemsPerPage,
      })
    }
  }

  // Apply the filter with the updated options
  handleFilter(null, options)
}

// Computed property to transform activity_groupings for the NNTable
const transformedGroupings = computed(() => {
  if (versionDetail.value && versionDetail.value.items) {
    return versionDetail.value.items.map((grouping, index) => {
      return {
        activity_group: {
          uid: grouping.group.uid,
          name: grouping.group.name,
        },
        activity_subgroup: {
          uid: grouping.subgroup.uid,
          name: grouping.subgroup.name,
        },
        group_version: grouping.group.version,
        subgroup_version: grouping.subgroup.version,
        group_status: grouping.group.status,
        subgroup_status: grouping.subgroup.status,
        activity_instances: grouping.activity_instances || [],
        item_key: `grouping-${index}`,
      }
    })
  }

  // Empty array if detail endpoint data is not available
  return []
})

// Watch for changes in transformedGroupings to update filteredGroupings
watch(
  () => transformedGroupings.value,
  (newGroupings) => {
    // Initialize filtered groupings with transformed data
    filteredGroupings.value = [...newGroupings]

    // Apply any existing filters/sorting
    if (tableOptions.value.sortBy && tableOptions.value.sortBy.length > 0) {
      handleFilter(null, {
        search: '',
        sortBy: tableOptions.value.sortBy,
        sortDesc: tableOptions.value.sortDesc,
      })
    }
  },
  { immediate: true }
)

// Fetch activity version detail
async function fetchVersionDetail(activityUid, version, options = {}) {
  try {
    isLoading.value = true
    const params = {
      page_number: options.page || tableOptions.value.page,
      page_size: options.itemsPerPage || tableOptions.value.itemsPerPage,
      total_count: true,
    }

    if (activityUid && version) {
      const response = await activities.getVersionDetail(
        activityUid,
        version,
        params
      )
      versionDetail.value = response.data
      paginationTotal.value = response.data.total || 0
    }
  } catch (error) {
    console.error('Error fetching activity version detail:', error)
  } finally {
    isLoading.value = false
  }
}

// Initialize the component when mounted or props change
function refresh() {
  const activityId = props.activityId || route.params.id
  const version =
    props.version || route.params.version || props.itemData?.activity?.version

  if (activityId && version) {
    fetchVersionDetail(activityId, version, tableOptions.value)
    emit('refresh') // Use the emit to notify parent components
  }
}

onMounted(() => {
  refresh()
})

// Watch for changes in the activityId or version
watch(
  [() => props.activityId, () => props.version, () => props.itemData],
  () => {
    refresh()
  }
)
</script>

<style scoped>
/* Activity section styling */
.activity-section {
  margin: 0 !important;
  width: 100%;
}

/* Adjusts the spacing for section headers */
.section-header {
  margin-top: 16px;
  margin-bottom: 8px;
  padding-left: 0;
}

/* Ensures tables have a clean design */
.table-container {
  width: 100%;
  margin-bottom: 24px;
  border-radius: 4px;
  background-color: transparent;
  box-shadow: none;
  overflow: hidden;
}

/* Set column widths based on header definitions */
:deep(.activity-section th),
:deep(.activity-section td) {
  width: var(--width, 33%) !important;
}

/* Fix table wrapper to auto-height */
:deep(.v-table__wrapper) {
  height: auto !important;
}
</style>
