<template>
  <div class="subgroup-overview-container">
    <BaseActivityOverview
      ref="overview"
      :source="'activity-sub-groups'"
      :item-uid="props.itemUid"
      :transform-func="transformItem"
      :navigate-to-version="changeVersion"
      :history-headers="historyHeaders"
      :yaml-version="props.yamlVersion"
      :cosmos-version="props.cosmosVersion"
      v-bind="$attrs"
    >
      <template #htmlContent>
        <!-- Subgroup Details using ActivitySummary -->
        <div class="summary-section">
          <v-skeleton-loader
            v-if="!props.itemOverview?.activity_subgroup"
            type="card"
            class="subgroup-activity-summary"
          />
          <ActivitySummary
            v-else
            :activity="props.itemOverview.activity_subgroup"
            :all-versions="allVersions(props.itemOverview)"
            :show-library="true"
            :show-nci-concept-id="true"
            :show-data-collection="false"
            :show-abbreviation="false"
            :show-author="true"
            class="subgroup-activity-summary"
            @version-change="
              (value) =>
                changeVersion(props.itemOverview.activity_subgroup, value)
            "
          />
        </div>

        <!-- Activity Groups Section -->
        <div class="my-5">
          <div class="section-header mb-1">
            <h3 class="text-headline-small font-weight-bold text-primary">
              {{ $t('ActivityOverview.activity_group') }}
            </h3>
          </div>
          <NNTable
            key="groupsTable"
            table-id="subgroup-overview-groups"
            :headers="groupsHeaders"
            :items="groups"
            :items-length="groupsTotal"
            :items-per-page="groupsTableOptions.itemsPerPage"
            :page="groupsTableOptions.page"
            :hide-export-button="false"
            :hide-default-switches="true"
            :disable-filtering="true"
            :hide-search-field="true"
            :modifiable-table="true"
            :no-padding="true"
            elevation="0"
            class="groups-table"
            item-value="uid"
            :initial-sort="initialSort"
            :disable-sort="true"
            :loading="false"
            :export-config="{
              objectLabel: 'Activity Groups',
              dataUrl: `concepts/activities/activity-sub-groups/${props.itemUid}/activity-groups`,
            }"
            @filter="
              (filters, options) => handleFilter(filters, options, 'groups')
            "
            @update:options="updateGroupsTableOptions"
          >
            <template #[`item.name`]="{ item }">
              <router-link
                :to="{
                  name: 'GroupOverview',
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
                <span class="text-body-large text-grey-darken-1">
                  {{ $t('SubgroupOverview.noItemsAvailable') }}
                </span>
              </div>
            </template>
          </NNTable>
        </div>

        <!-- Activities Section -->
        <div class="my-5">
          <div class="section-header mb-1">
            <h3 class="text-headline-small font-weight-bold text-primary">
              {{ $t('ActivityOverview.activities') }}
            </h3>
          </div>
          <NNTable
            ref="activitiesTableRef"
            key="activitiesTable"
            table-id="subgroup-overview-activities"
            :headers="activitiesHeaders"
            :items="activities"
            :items-length="activitiesTotal"
            :items-per-page="activitiesTableOptions.itemsPerPage"
            :page="activitiesTableOptions.page"
            :hide-export-button="false"
            :hide-default-switches="true"
            :disable-filtering="true"
            :hide-search-field="false"
            :modifiable-table="true"
            :no-padding="true"
            elevation="0"
            class="activities-table"
            item-value="uid"
            :initial-sort="initialSort"
            :disable-sort="true"
            :loading="isLoadingActivities"
            :export-config="{
              objectLabel: 'Activities',
              dataUrl: `concepts/activities/activity-sub-groups/${props.itemUid}/activities`,
            }"
            @filter="
              (filters, options) => handleFilter(filters, options, 'activities')
            "
            @update:options="updateActivitiesTableOptions"
          >
            <template #[`item.name`]="{ item }">
              <router-link
                :to="{
                  name: 'ActivityOverview',
                  params: { id: item.uid, version: item.version },
                }"
              >
                {{ item.name }}
              </router-link>
            </template>
            <template #[`item.requested`]="{ item }">
              {{
                $filters.yesno(
                  item.library_name === libraryConstants.LIBRARY_REQUESTED
                )
              }}
            </template>
            <template #[`item.status`]="{ item }">
              <StatusChip :status="item.status" />
            </template>
            <template #no-data>
              <div class="text-center py-4">
                <span class="text-body-large text-grey-darken-1">
                  {{ $t('SubgroupOverview.noItemsAvailable') }}
                </span>
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
            :subgroup="true"
            :edited-group-or-subgroup="item"
            @close="close"
          />
        </v-dialog>
      </template>
    </BaseActivityOverview>
  </div>
</template>

<script setup>
import { onMounted, ref, defineAsyncComponent, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import activitiesApi from '@/api/activities'
import libraryConstants from '@/constants/libraries'

import BaseActivityOverview from './BaseActivityOverview.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import ActivitySummary from '@/components/library/ActivitySummary.vue'
import NNTable from '@/components/tools/NNTable.vue'

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
const emit = defineEmits(['refresh'])

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const appStore = useAppStore()

// Table data and loading states
const activities = ref([])
const activitiesTotal = ref(0)
const isLoadingActivities = ref(true)
const groups = ref([])
const groupsTotal = ref(0)
const isLoadingGroups = ref(true)

// Separate setting just for activities pagination
const activitiesTableOptions = ref({
  page: 1,
  itemsPerPage: 10,
  searchString: '',
})
const groupsTableOptions = ref({
  page: 1,
  itemsPerPage: 10,
})

// Initial sort order for tables
const initialSort = ref([{ key: 'name', order: 'asc' }])

const historyHeaders = [
  { title: t('_global.library'), key: 'library_name' },
  { title: t('_global.name'), key: 'name' },
  { title: t('_global.definition'), key: 'definition' },
  { title: t('_global.version'), key: 'version' },
  { title: t('_global.start_date'), key: 'start_date' },
  { title: t('_global.end_date'), key: 'end_date' },
  { title: t('_global.status'), key: 'status' },
]

// Headers for groups table
const groupsHeaders = [
  { title: t('_global.name'), key: 'name', align: 'start', sortable: true },
  {
    title: t('_global.version'),
    key: 'version',
    align: 'start',
    sortable: true,
  },
  { title: t('_global.status'), key: 'status', align: 'start', sortable: true },
]

// Headers for activities table
const activitiesHeaders = [
  { title: t('_global.name'), key: 'name', align: 'start', sortable: true },
  { title: t('SubgroupOverview.requested'), key: 'requested', sortable: true },
  {
    title: t('_global.version'),
    key: 'version',
    align: 'start',
    sortable: true,
  },
  { title: t('_global.status'), key: 'status', align: 'start', sortable: true },
]

function transformItem(item) {
  item.item_key = item.uid
}

async function changeVersion(subgroup, version) {
  await router.push({
    name: 'SubgroupOverview',
    params: {
      id: subgroup.uid,
      version,
    },
  })
  emit('refresh')
}

function handleFilter(filters, options, targetTable) {
  const searchTerm =
    options && options.search && typeof options.search === 'string'
      ? options.search.toLowerCase()
      : filters && filters.search && typeof filters.search === 'string'
        ? filters.search.toLowerCase()
        : ''

  if (targetTable === 'groups') {
    isLoadingGroups.value = true
    groupsTableOptions.value.page = options.page
    groupsTableOptions.value.itemsPerPage = options.itemsPerPage
    fetchGroups()
  } else if (targetTable === 'activities') {
    isLoadingActivities.value = true
    activitiesTableOptions.value.searchString = searchTerm
    activitiesTableOptions.value.page = options.page
    activitiesTableOptions.value.itemsPerPage = options.itemsPerPage
    fetchActivities()
  }
}

// Handles pagination for groups table
function updateGroupsTableOptions(options) {
  if (!options) return

  // Store sort options separately to prevent losing them
  if (options.sortBy && options.sortBy.length > 0) {
    groupsTableOptions.value.sortBy = [...options.sortBy]
  }

  // Update page and items per page
  groupsTableOptions.value.page = options.page
  groupsTableOptions.value.itemsPerPage = options.itemsPerPage
}

// Handles pagination for activities table
function updateActivitiesTableOptions(options) {
  if (!options) return

  // Store sort options separately to prevent losing them
  if (options.sortBy && options.sortBy.length > 0) {
    activitiesTableOptions.value.sortBy = [...options.sortBy]
  }

  // Just update pagination values for display
  activitiesTableOptions.value.page = options.page
  activitiesTableOptions.value.itemsPerPage = options.itemsPerPage
}

async function fetchActivities() {
  const params = {
    version: props.itemOverview?.activity_subgroup?.version,
    total_count: true,
    search_string: activitiesTableOptions.value.searchString,
    page_number: activitiesTableOptions.value.page,
    page_size: activitiesTableOptions.value.itemsPerPage,
  }
  activitiesApi.getSubgroupActivities(props.itemUid, params).then((resp) => {
    activities.value = resp.data.items
    activitiesTotal.value = resp.data.total
    isLoadingActivities.value = false
  })
}

async function fetchGroups() {
  const params = {
    version: props.itemOverview?.activity_subgroup?.version,
    total_count: true,
    page_number: groupsTableOptions.value.page,
    page_size: groupsTableOptions.value.itemsPerPage,
  }
  activitiesApi.getSubgroupGroups(props.itemUid, params).then((resp) => {
    groups.value = resp.data.items
    groupsTotal.value = resp.data.total
    isLoadingGroups.value = false
  })
}

function allVersions(item) {
  return [...item.all_versions].sort().reverse()
}

let lastFetchedVersion = null

watch(
  () => props.itemOverview?.activity_subgroup,
  (newSubgroup) => {
    if (newSubgroup) {
      const currentVersion = newSubgroup.version
      if (lastFetchedVersion !== currentVersion) {
        lastFetchedVersion = currentVersion
        // Reset to page 1 when version changes
        activitiesTableOptions.value.page = 1
        groupsTableOptions.value.page = 1
        isLoadingActivities.value = true
        isLoadingGroups.value = true
        fetchActivities()
        fetchGroups()
      }
    } else {
      groups.value = []
      groupsTotal.value = 0
    }
  },
  { immediate: true }
)

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
    t('Sidebar.library.activities_subgroups'),
    { name: 'Activities', params: { tab: 'activity-subgroups' } },
    3,
    true
  )

  const subgroupName =
    props.itemOverview?.activity_subgroup?.name || t('_global.loading')

  appStore.addBreadcrumbsLevel(
    subgroupName,
    {
      name: 'SubgroupOverview',
      params: { id: route.params.id },
    },
    4,
    true
  )
})
</script>

<style scoped>
/* Subgroup overview container styling */
.subgroup-overview-container {
  width: 100%;
  background-color: transparent;
}

/* Summary section styling */
.summary-section {
  margin-bottom: 24px;
}

/* Section header styling */
.section-header {
  margin-top: 16px;
  margin-bottom: 8px;
  padding-left: 0;
}

/* Tables styling */
.groups-table,
.activities-table {
  margin-top: 8px;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: none;
  background-color: transparent;
}

/* Table content styling */
.groups-table :deep(table),
.activities-table :deep(table) {
  border-collapse: collapse;
  width: 100%;
}

.groups-table :deep(th),
.activities-table :deep(th) {
  background-color: var(--semantic-system-brand, #001965);
  color: white;
  font-weight: 500;
  padding: 12px 16px;
  text-align: left;
}

.groups-table :deep(td),
.activities-table :deep(td) {
  padding: 8px 16px;
  border-bottom: 1px solid #e0e0e0;
  background-color: white !important;
}

.groups-table :deep(.v-card-text),
.activities-table :deep(.v-card-text) {
  width: 100% !important;
  padding: 0 !important;
}

.groups-table :deep(.v-table__wrapper),
.activities-table :deep(.v-table__wrapper) {
  height: auto !important;
}

.groups-table :deep(.v-card-title),
.activities-table :deep(.v-card-title) {
  padding: 8px 16px;
  display: flex;
  flex-direction: row;
  justify-content: flex-start;
  align-items: center;
  background-color: transparent;
}

.groups-table :deep(.v-card__title .v-input),
.activities-table :deep(.v-card__title .v-input) {
  max-width: 300px;
  margin-right: auto;
}

.groups-table :deep(.v-data-table-footer),
.activities-table :deep(.v-data-table-footer) {
  border-top: 1px solid #e0e0e0;
  background-color: transparent !important;
}

/* Round table corners */
.subgroup-overview-container :deep(.v-data-table) {
  border-radius: 8px !important;
  overflow: visible;
}

.subgroup-overview-container :deep(.v-table__wrapper) {
  border-radius: 8px !important;
  overflow-x: auto;
}

.subgroup-overview-container :deep(.v-table),
.groups-table :deep(.v-table),
.activities-table :deep(.v-table) {
  background: transparent !important;
}

.subgroup-overview-container :deep(.v-data-table__th),
.groups-table :deep(.v-data-table__th),
.activities-table :deep(.v-data-table__th) {
  background-color: rgb(var(--v-theme-nnTrueBlue)) !important;
}

.subgroup-overview-container :deep(.v-data-table__tbody tr),
.groups-table :deep(.v-data-table__tbody tr),
.activities-table :deep(.v-data-table__tbody tr) {
  background-color: white !important;
}

.subgroup-overview-container :deep(.v-card),
.subgroup-overview-container :deep(.v-sheet),
.groups-table :deep(.v-card),
.groups-table :deep(.v-sheet),
.activities-table :deep(.v-card),
.activities-table :deep(.v-sheet) {
  background-color: transparent !important;
  box-shadow: none !important;
}
</style>
