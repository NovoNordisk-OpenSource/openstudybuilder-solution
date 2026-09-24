<template>
  <div class="group-overview-container">
    <BaseActivityOverview
      ref="overview"
      :source="'activity-groups'"
      :item-uid="itemUid"
      :transform-func="transformItem"
      :navigate-to-version="changeVersion"
      :history-headers="historyHeaders"
      :yaml-version="props.yamlVersion"
      :cosmos-version="props.cosmosVersion"
      v-bind="$attrs"
      @update:subgroups="handleSubgroupsUpdate"
    >
      <template #htmlContent>
        <!-- Group Details using ActivitySummary -->
        <div class="summary-section">
          <v-skeleton-loader
            v-if="!itemOverview?.group"
            type="card"
            class="group-activity-summary"
          />
          <ActivitySummary
            v-else
            :activity="itemOverview.group"
            :all-versions="allVersions(itemOverview)"
            :show-library="true"
            :show-nci-concept-id="true"
            :show-data-collection="false"
            :show-abbreviation="false"
            :show-author="true"
            class="group-activity-summary"
            @version-change="
              (value) => changeVersion(itemOverview.group, value)
            "
          />
        </div>

        <!-- Activity Subgroups using NNTable -->
        <div v-if="loadingSubgroups" class="my-5">
          <div class="section-header mb-1">
            <h3 class="text-headline-small font-weight-bold text-primary">
              {{ $t('ActivityOverview.activity_subgroups') }}
            </h3>
          </div>
          <v-skeleton-loader type="table" />
        </div>
        <div v-else class="my-5">
          <div class="section-header mb-1">
            <h3 class="text-headline-small font-weight-bold text-primary">
              {{ $t('ActivityOverview.activity_subgroups') }}
            </h3>
          </div>
          <NNTable
            table-id="group-overview-subgroups"
            :headers="subgroupsHeaders"
            :items="filteredSubgroups"
            :items-length="subgroupsTotal"
            :items-per-page="tableOptions.itemsPerPage"
            :page="tableOptions.page"
            :hide-export-button="false"
            :hide-default-switches="true"
            disable-filtering
            :hide-search-field="false"
            :modifiable-table="true"
            :no-padding="true"
            elevation="0"
            class="subgroups-table"
            item-value="uid"
            :initial-sort="initialSort"
            :disable-sort="false"
            :loading="false"
            :column-data-resource="'concepts/activities/activity-sub-groups'"
            :filters-modify-function="modifyFilters"
            :initial-column-data="getInitialColumnData()"
            :export-config="{
              dataUrl: `concepts/activities/activity-groups/${route.params.id}/subgroups`,
            }"
            @filter="handleFilter"
            @update:options="updateTableOptions"
            @click:column="handleColumnClick"
          >
            <template #[`item.name`]="{ item }">
              <router-link
                :to="{
                  name: 'SubgroupOverview',
                  params: { id: item.uid, version: item.version },
                }"
              >
                {{ item.name }}
              </router-link>
            </template>
            <template #[`item.status`]="{ item }">
              <StatusChip :status="item.status" />
            </template>
            <template #no-data>
              <div class="text-center py-4">
                <span class="text-body-large text-grey-darken-1">{{
                  $t('ActivityOverview.no_subgroups')
                }}</span>
              </div>
            </template>
          </NNTable>
        </div>
      </template>
      <template #itemForm="{ show, item, close }">
        <v-dialog
          :model-value="show"
          persistent
          max-width="800px"
          content-class="top-dialog"
        >
          <ActivitiesGroupsForm
            ref="groupFormRef"
            :open="show"
            :subgroup="false"
            :edited-group-or-subgroup="item"
            @close="close"
          />
        </v-dialog>
      </template>
    </BaseActivityOverview>
  </div>
</template>

<script setup>
import { onMounted, ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import activities from '@/api/activities'
import columnData from '@/api/columnData'

import BaseActivityOverview from './BaseActivityOverview.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import ActivitySummary from '@/components/library/ActivitySummary.vue'
import NNTable from '@/components/tools/NNTable.vue'
import { defineAsyncComponent } from 'vue'

const ActivitiesGroupsForm = defineAsyncComponent(
  () => import('@/components/library/ActivitiesGroupsForm.vue')
)

const props = defineProps({
  itemOverview: {
    type: Object,
    required: true,
  },
  itemUid: {
    type: String,
    required: true,
  },
  yamlVersion: {
    type: String,
    default: null,
  },
  cosmosVersion: {
    type: String,
    default: null,
  },
})
const emit = defineEmits(['refresh', 'update:itemOverview'])

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const appStore = useAppStore()
const overview = ref()
const groupFormRef = ref()

const filteredSubgroups = ref([])
const subgroupsTotal = ref(0)
const loadingSubgroups = ref(true)
const tableOptions = ref({
  search: '',
  sortBy: [],
  sortDesc: [],
  page: 1,
  itemsPerPage: 10,
})

// Store ALL subgroups for client-side filtering and pagination
const allSubgroups = ref([])

const initialSort = ref([{ key: 'name', order: 'asc' }])
const sortBy = ref([])

const historyHeaders = [
  { title: t('_global.library'), key: 'library_name' },
  { title: t('_global.name'), key: 'name' },
  { title: t('_global.definition'), key: 'definition' },
  { title: t('_global.version'), key: 'version' },
  { title: t('_global.start_date'), key: 'start_date' },
  { title: t('_global.end_date'), key: 'end_date' },
  { title: t('_global.status'), key: 'status' },
]

const subgroupsHeaders = computed(() => [
  { title: t('_global.name'), key: 'name', align: 'start', sortable: true },
  {
    title: t('_global.definition'),
    key: 'definition',
    align: 'start',
    sortable: true,
  },
  {
    title: t('_global.version'),
    key: 'version',
    align: 'start',
    sortable: true,
  },
  { title: t('_global.status'), key: 'status', align: 'start', sortable: true },
])

function allVersions(item) {
  return [...item.all_versions].sort().reverse()
}

async function changeVersion(group, version) {
  await router.push({
    name: 'GroupOverview',
    params: { id: group.uid, version },
  })
  emit('refresh')
}

function transformItem(item) {
  item.item_key = item.uid

  // Map author_username to author field for ActivitySummary component
  if (item.group && item.group.author_username) {
    item.group.author = item.group.author_username
  }
}

function itemMatchesSearch(item, searchTerm) {
  if (!searchTerm || searchTerm === '') return true

  const term = searchTerm.toLowerCase()

  if (item.name?.toLowerCase().includes(term)) return true

  if (item.definition?.toLowerCase().includes(term)) return true

  if (item.version && item.version.toString().toLowerCase().includes(term))
    return true

  if (item.status?.toLowerCase().includes(term)) return true

  return false
}

function handleColumnClick(column) {
  if (!column.sortable) return

  const key = column.key
  const currentSortBy = tableOptions.value.sortBy[0] || ''
  const currentSortDesc = tableOptions.value.sortDesc[0] || false
  const newSortDesc = currentSortBy !== key ? false : !currentSortDesc

  tableOptions.value.sortBy = [key]
  tableOptions.value.sortDesc = [newSortDesc]
  if (props.itemOverview?.subgroups) {
    const sourceItems =
      props.itemOverview.subgroups.items || props.itemOverview.subgroups
    let subgroupsToFilter = [...sourceItems]

    if (tableOptions.value.search) {
      const searchTerm = tableOptions.value.search.toLowerCase()
      subgroupsToFilter = subgroupsToFilter.filter((item) =>
        itemMatchesSearch(item, searchTerm)
      )
    }

    subgroupsToFilter.sort((a, b) => {
      const valA = a[key] || ''
      const valB = b[key] || ''
      if (typeof valA === 'string' && typeof valB === 'string') {
        return newSortDesc ? valB.localeCompare(valA) : valA.localeCompare(valB)
      }
      return newSortDesc ? valB - valA : valA - valB
    })

    filteredSubgroups.value = subgroupsToFilter
    subgroupsTotal.value = subgroupsToFilter.length
  }
}

let savedFilters = ref({})

function applyFiltersAndPagination(searchTerm = '', page = 1, perPage = 10) {
  let itemsToDisplay = [...allSubgroups.value]

  if (searchTerm && searchTerm.trim() !== '') {
    itemsToDisplay = itemsToDisplay.filter((item) =>
      itemMatchesSearch(item, searchTerm)
    )
  }

  const sortKey = tableOptions.value.sortBy[0] || 'name'
  const sortDesc = tableOptions.value.sortDesc[0] || false
  itemsToDisplay.sort((a, b) => {
    const valA = a[sortKey] || ''
    const valB = b[sortKey] || ''
    if (typeof valA === 'string' && typeof valB === 'string') {
      return sortDesc ? valB.localeCompare(valA) : valA.localeCompare(valB)
    }
    return sortDesc ? valB - valA : valA - valB
  })

  subgroupsTotal.value = itemsToDisplay.length

  if (perPage > 0) {
    const startIndex = (page - 1) * perPage
    const endIndex = startIndex + perPage
    filteredSubgroups.value = itemsToDisplay.slice(startIndex, endIndex)
  } else {
    filteredSubgroups.value = itemsToDisplay
  }
}

// Client-side filtering since API doesn't support search
function handleFilter(filters, options) {
  if (filters !== undefined) {
    savedFilters.value = filters
  }

  if (!options) {
    options = tableOptions.value
  }

  if (options.search !== undefined) {
    tableOptions.value.search = options.search
  }
  if (options.page !== undefined) {
    tableOptions.value.page = options.page
  }
  if (options.itemsPerPage !== undefined) {
    tableOptions.value.itemsPerPage = options.itemsPerPage
  }

  applyFiltersAndPagination(
    tableOptions.value.search,
    tableOptions.value.page,
    tableOptions.value.itemsPerPage
  )
}

function updateTableOptions(options) {
  if (!options) return

  if (options.sortBy && options.sortBy.length > 0) {
    const sortItem = options.sortBy[0]
    tableOptions.value.sortBy = [sortItem.key]
    tableOptions.value.sortDesc = [sortItem.order === 'desc']
    sortBy.value = options.sortBy
  }

  if (options.page !== undefined) {
    tableOptions.value.page = options.page
  }
  if (options.itemsPerPage !== undefined) {
    tableOptions.value.itemsPerPage = options.itemsPerPage
  }

  applyFiltersAndPagination(
    tableOptions.value.search,
    tableOptions.value.page,
    tableOptions.value.itemsPerPage
  )
}

function getSubgroupsHeaders() {
  const params = {
    field_name: 'name',
    search_string: '',
    page_size: 50,
  }

  return columnData.getHeaderData(
    params,
    'concepts/activities/activity-sub-groups'
  )
}

function modifyFilters(jsonFilter, params) {
  return {
    jsonFilter,
    params,
  }
}

function getInitialColumnData() {
  if (!props.itemOverview?.subgroups) return {}

  const sourceItems =
    props.itemOverview.subgroups.items || props.itemOverview.subgroups
  if (!Array.isArray(sourceItems) || sourceItems.length === 0) return {}

  const columnData = {}

  subgroupsHeaders.value.forEach((header) => {
    if (header.key === 'actions' || header.noFilter) return

    const uniqueValues = [
      ...new Set(sourceItems.map((item) => item[header.key])),
    ].filter((val) => val !== undefined && val !== null && val !== '')

    if (uniqueValues.length > 0) {
      columnData[header.key] = uniqueValues
    }
  })

  return columnData
}

function handleSubgroupsUpdate(subgroupsData) {
  if (props.itemOverview) {
    emit('update:itemOverview', {
      ...props.itemOverview,
      subgroups: subgroupsData,
    })

    // IMPORTANT: The direct assignment is needed for the search functionality to work
    // eslint-disable-next-line vue/no-mutating-props
    props.itemOverview.subgroups = subgroupsData

    const items = subgroupsData?.items || subgroupsData || []

    allSubgroups.value = Array.isArray(items) ? [...items] : []
    applyFiltersAndPagination(
      tableOptions.value.search,
      tableOptions.value.page,
      tableOptions.value.itemsPerPage
    )

    setTimeout(() => {
      loadingSubgroups.value = false
    }, 0)
  }
}

watch(
  () => props.itemOverview,
  (newItemOverview, oldItemOverview) => {
    if (newItemOverview?.group?.uid !== oldItemOverview?.group?.uid) {
      allSubgroups.value = []
      tableOptions.value.search = ''
      tableOptions.value.page = 1
    }

    if (newItemOverview === null) {
      loadingSubgroups.value = true
      filteredSubgroups.value = []
      subgroupsTotal.value = 0
      return
    }

    if (newItemOverview?.subgroups === null) {
      loadingSubgroups.value = true
      fetchSubgroups()
      return
    }

    loadingSubgroups.value = !newItemOverview?.subgroups

    if (newItemOverview?.subgroups) {
      const sourceItems =
        newItemOverview.subgroups.items || newItemOverview.subgroups
      allSubgroups.value = Array.isArray(sourceItems) ? [...sourceItems] : []
      applyFiltersAndPagination(
        tableOptions.value.search,
        tableOptions.value.page,
        tableOptions.value.itemsPerPage
      )
    }
  },
  { immediate: true }
)

watch(
  () => props.itemOverview?.subgroups,
  (newSubgroups) => {
    if (newSubgroups === null) {
      return
    }

    loadingSubgroups.value = false

    if (newSubgroups) {
      const items = newSubgroups.items || newSubgroups
      allSubgroups.value = Array.isArray(items) ? [...items] : []
      applyFiltersAndPagination(
        tableOptions.value.search,
        tableOptions.value.page,
        tableOptions.value.itemsPerPage
      )
    } else {
      allSubgroups.value = []
      filteredSubgroups.value = []
      subgroupsTotal.value = 0
    }
  },
  { immediate: true }
)

// Fetches all subgroups for client-side filtering (API doesn't support search)
const fetchSubgroups = async () => {
  if (!route.params.id || !route.params.id.trim()) {
    return
  }

  try {
    loadingSubgroups.value = true

    const params = {
      page_size: 0,
      total_count: true,
    }

    const result = await activities.getActivityGroupSubgroups(
      route.params.id,
      route.params.version || '',
      params
    )

    if (result && result.data) {
      const items = result.data.items || result.data
      allSubgroups.value = Array.isArray(items) ? [...items] : []
      applyFiltersAndPagination(
        tableOptions.value.search,
        tableOptions.value.page,
        tableOptions.value.itemsPerPage
      )
    } else {
      allSubgroups.value = []
      filteredSubgroups.value = []
      subgroupsTotal.value = 0
    }
  } catch (error) {
    console.error('Error fetching subgroups:', error)
    allSubgroups.value = []
    filteredSubgroups.value = []
    subgroupsTotal.value = 0
  } finally {
    // Always ensure loading is false when done
    loadingSubgroups.value = false
  }
}

onMounted(() => {
  getSubgroupsHeaders()
    .then(() => {})
    .catch((error) => {
      console.error('Error loading subgroups headers:', error)
    })

  if (props.itemOverview?.subgroups === null) {
    fetchSubgroups()
  }
})

onMounted(() => {
  appStore.addBreadcrumbsLevel(
    t('Sidebar.library.concepts'),
    { name: 'Activities' },
    1,
    false
  )

  appStore.addBreadcrumbsLevel(
    t('Sidebar.library.activities'),
    { name: 'Activities' },
    2,
    true
  )

  appStore.addBreadcrumbsLevel(
    t('Sidebar.library.activities_groups'),
    { name: 'Activities', params: { tab: 'activity-groups' } },
    3,
    true
  )

  const groupName = props.itemOverview?.group?.name || t('_global.loading')

  appStore.addBreadcrumbsLevel(
    groupName,
    {
      name: 'GroupOverview',
      params: { id: route.params.id },
    },
    4,
    true
  )
})
</script>

<style scoped>
/* Group overview container styling */
.group-overview-container {
  width: 100%;
  background-color: transparent;
}

/* Summary section styling */
.summary-section {
  margin-bottom: 24px;
}

/* Subgroups table styling */
.subgroups-table {
  margin-top: 8px;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: none;
  background-color: transparent;
}

/* Table styling */
.subgroups-table :deep(table) {
  border-collapse: collapse;
  width: 100%;
}

.subgroups-table :deep(th) {
  background-color: var(--semantic-system-brand, #001965);
  color: white;
  font-weight: 500;
  padding: 12px 16px;
  text-align: left;
}

.subgroups-table :deep(td) {
  padding: 8px 16px;
  border-bottom: 1px solid #e0e0e0;
  background-color: white !important;
}

.subgroups-table :deep(.v-card-text) {
  width: 100% !important;
  padding: 0 !important;
}

.subgroups-table :deep(.v-table__wrapper) {
  height: auto !important;
}

.subgroups-table :deep(.v-card-title) {
  padding: 8px 16px;
  display: flex;
  flex-direction: row;
  justify-content: flex-start;
  align-items: center;
  background-color: transparent;
}

.subgroups-table :deep(.v-card__title .v-input) {
  max-width: 300px;
  margin-right: auto;
}

.subgroups-table :deep(.v-data-table-footer) {
  border-top: 1px solid #e0e0e0;
  background-color: transparent !important;
}

/* Round table corners */
.group-overview-container :deep(.v-data-table) {
  border-radius: 8px !important;
  overflow: visible;
}

.group-overview-container :deep(.v-table__wrapper) {
  border-radius: 8px !important;
  overflow-x: auto;
}

.group-overview-container :deep(.v-table),
.subgroups-table :deep(.v-table) {
  background: transparent !important;
}

.group-overview-container :deep(.v-data-table__th),
.subgroups-table :deep(.v-data-table__th) {
  background-color: rgb(var(--v-theme-nnTrueBlue)) !important;
}

.group-overview-container :deep(.v-data-table__tbody tr),
.subgroups-table :deep(.v-data-table__tbody tr) {
  background-color: white !important;
}

.group-overview-container :deep(.v-card),
.group-overview-container :deep(.v-sheet),
.subgroups-table :deep(.v-card),
.subgroups-table :deep(.v-sheet) {
  background-color: transparent !important;
  box-shadow: none !important;
}
</style>
