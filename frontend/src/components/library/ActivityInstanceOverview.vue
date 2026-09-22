<template>
  <div class="activity-instance-overview-container">
    <BaseActivityOverview
      ref="overview"
      :transform-func="transformItem"
      :navigate-to-version="changeVersion"
      :history-headers="historyHeaders"
      :action-subitem-map="actionSubitemMap"
      :hidden-actions="['approve', 'edit', 'new_version', 'history']"
      v-bind="$attrs"
      @refresh="refreshData"
    >
      <template #htmlContent="{ itemOverview }">
        <div v-if="itemOverview">
          <!-- Summary section -->
          <ActivityInstanceSummary
            :activity-instance="itemOverview.activity_instance"
            :groupings-version="selectedGroupingsVersion"
            :groupings-data="groupingsSummaryData"
          />

          <div class="activity-instance-attributes-section">
            <div class="section-header section-header--with-actions mb-1">
              <h3 class="text-h6 font-weight-bold text-primary">
                {{
                  $t('ActivityInstanceOverview.activity_instance_attributes')
                }}
              </h3>
              <div class="groupings-action-buttons">
                <template v-for="action in attributesActions" :key="action.key">
                  <v-btn
                    v-if="isAttributesActionVisible(action)"
                    variant="outlined"
                    class="ml-2"
                    :color="action.iconColor"
                    icon
                    size="small"
                    @click="onAttributesActionClick(action.key)"
                  >
                    <v-icon left>{{ action.icon }}</v-icon>
                    <v-tooltip activator="parent" location="top">
                      {{ action.label }}
                    </v-tooltip>
                  </v-btn>
                </template>
              </div>
            </div>

            <!-- Activity Instance Summary -->
            <ActivitySummary
              v-if="itemOverview.activity_instance"
              :activity="
                adaptActivityInstanceForSummary(
                  itemOverview.activity_instance,
                  activityGroupings
                )
              "
              :all-versions="allVersions(itemOverview)"
              :activity-groupings="activityGroupings"
              :show-data-collection="false"
              :show-author="true"
              class="activity-summary"
              @version-change="(value) => manualChangeVersion(value)"
            >
              <template #content>
                <ActivityItemsTable
                  :activity-instance-id="route.params.id"
                  :version="route.params.version"
                />
              </template>
            </ActivitySummary>
          </div>

          <!-- Activity Groupings section -->
          <div class="activity-section">
            <div class="section-header section-header--with-actions mb-1">
              <h3 class="text-headline-small font-weight-bold text-primary">
                {{ $t('ActivityInstanceOverview.activity_groupings') }}
              </h3>
              <div class="groupings-action-buttons">
                <template v-for="action in groupingsActions" :key="action.key">
                  <v-btn
                    v-if="isGroupingActionVisible(action)"
                    variant="outlined"
                    class="ml-2"
                    :color="action.iconColor"
                    icon
                    size="small"
                    @click="onGroupingActionClick(action.key)"
                  >
                    <v-icon left>{{ action.icon }}</v-icon>
                    <v-tooltip activator="parent" location="top">
                      {{ action.label }}
                    </v-tooltip>
                  </v-btn>
                </template>
              </div>
            </div>
            <ActivityGroupingsSummary
              v-model="selectedGroupingsVersion"
              :label="$t('ActivityInstanceOverview.groupings_version')"
              :all-groupings-versions="groupingsVersionChoices"
              :summary-data="groupingsSummaryData"
            >
              <template #content>
                <NNTable
                  table-id="activity-instance-overview-groupings"
                  :headers="groupingsHeaders"
                  :items="displayedGroupings"
                  :items-length="displayedGroupings.length"
                  :items-per-page="10"
                  :hide-export-button="false"
                  :hide-default-switches="true"
                  :disable-filtering="true"
                  :hide-search-field="false"
                  :modifiable-table="true"
                  :no-padding="true"
                  elevation="0"
                  class="groupings-table"
                  item-value="uid"
                  :disable-sort="false"
                  :loading="loadingGroupings"
                  :items-per-page-options="[10, 25, 50, 100]"
                  :server-items-length="displayedGroupings.length"
                  :export-config="{
                    objectLabel: 'Activity Groupings',
                    dataUrl: groupingsExportDataUrl,
                  }"
                  @filter="handleGroupingsFilter"
                  @update:options="handleGroupingsFilter"
                >
                  <template #[`item.activity_group_name`]="{ item }">
                    <router-link
                      v-if="item.activity_group_id"
                      :to="{
                        name: 'GroupOverview',
                        params: {
                          id: item.activity_group_id,
                          version: item.activity_group_version,
                        },
                      }"
                      class="d-block"
                    >
                      {{ item.activity_group_name }}
                    </router-link>
                    <div class="text-body-small text-grey-darken-1">
                      {{ $t('_global.version') }}
                      {{ item.activity_group_version }}
                      <span v-if="item.activity_group_status" class="ml-2"
                        >- {{ item.activity_group_status }}</span
                      >
                    </div>
                  </template>
                  <template #[`item.activity_subgroup_name`]="{ item }">
                    <router-link
                      v-if="item.activity_subgroup_id"
                      :to="{
                        name: 'SubgroupOverview',
                        params: {
                          id: item.activity_subgroup_id,
                          version: item.activity_subgroup_version,
                        },
                      }"
                      class="d-block"
                    >
                      {{ item.activity_subgroup_name }}
                    </router-link>
                    <div class="text-body-small text-grey-darken-1">
                      {{ $t('_global.version') }}
                      {{ item.activity_subgroup_version }}
                      <span v-if="item.activity_subgroup_status" class="ml-2"
                        >- {{ item.activity_subgroup_status }}</span
                      >
                    </div>
                  </template>
                  <template #[`item.activity_name`]="{ item }">
                    <router-link
                      v-if="item.activity_id"
                      :to="{
                        name: 'ActivityOverview',
                        params: {
                          id: item.activity_id,
                          version: item.activity_version,
                        },
                      }"
                      class="d-block"
                    >
                      {{ item.activity_name }}
                    </router-link>
                    <div class="text-body-small text-grey-darken-1">
                      {{ $t('_global.version') }} {{ item.activity_version }}
                      <span v-if="item.activity_status" class="ml-2"
                        >- {{ item.activity_status }}</span
                      >
                    </div>
                  </template>
                </NNTable>
              </template>
            </ActivityGroupingsSummary>
          </div>
        </div>
        <div v-else class="d-flex justify-center align-center pa-8">
          <v-progress-circular
            indeterminate
            color="primary"
          ></v-progress-circular>
        </div>
      </template>
      <template #itemForm="{ show, item, actionSubitem, close }">
        <v-dialog
          :model-value="show"
          persistent
          fullscreen
          content-class="fullscreen-dialog"
        >
          <FeatureDisabledDialog
            v-if="
              (!item?.uid && !newWizardStepper) ||
              (item?.uid && !newWizardStepperEditMode)
            "
            @close="close"
          />
          <Suspense v-else>
            <ActivityInstanceForm
              :activity-instance-uid="item?.uid"
              :edit-mode="item?.uid ? actionSubitem || 'attributes' : 'create'"
              @close="close"
            />
            <template #fallback>
              <v-skeleton-loader
                class="fullscreen-dialog"
                type="card"
              ></v-skeleton-loader>
            </template>
          </Suspense>
        </v-dialog>
      </template>
    </BaseActivityOverview>

    <!-- Groupings edit dialog (separate from BaseActivityOverview form) -->
    <v-dialog
      v-model="showGroupingsForm"
      persistent
      fullscreen
      content-class="fullscreen-dialog"
    >
      <FeatureDisabledDialog
        v-if="showGroupingsForm && !newWizardStepperEditMode"
        @close="closeGroupingsForm"
      />
      <Suspense v-else-if="showGroupingsForm">
        <ActivityInstanceForm
          :activity-instance-uid="route.params.id"
          edit-mode="groupings"
          @close="closeGroupingsForm"
        />
        <template #fallback>
          <v-skeleton-loader
            class="fullscreen-dialog"
            type="card"
          ></v-skeleton-loader>
        </template>
      </Suspense>
    </v-dialog>

    <!-- Groupings history dialog (separate from BaseActivityOverview history) -->
    <v-dialog
      v-model="showGroupingsHistory"
      persistent
      :max-width="$globals.historyDialogMaxWidth"
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeGroupingsHistory"
    >
      <HistoryTable
        :title="groupingsHistoryTitle"
        :headers="groupingsHistoryHeaders"
        :items="groupingsHistoryItems"
        :items-total="groupingsHistoryItems.length"
        :show-change-type="false"
        @close="closeGroupingsHistory"
      />
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed, inject } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import { useFeatureFlagsStore } from '@/stores/feature-flags'
import BaseActivityOverview from './BaseActivityOverview.vue'
import ActivitySummary from './ActivitySummary.vue'
import ActivityGroupingsSummary from './ActivityGroupingsSummary.vue'
import NNTable from '@/components/tools/NNTable.vue'
import ActivityInstanceForm from './ActivityInstanceForm.vue'
import FeatureDisabledDialog from '@/components/tools/FeatureDisabledDialog.vue'
import ActivityItemsTable from './ActivityItemsTable.vue'
import ActivityInstanceSummary from './ActivityInstanceSummary.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import activities from '@/api/activities'

const { t } = useI18n()
const appStore = useAppStore()
const featureFlagsStore = useFeatureFlagsStore()
const route = useRoute()
const router = useRouter()
const notificationHub = inject('notificationHub')

const overview = ref(null)
// Separate data sources for the new endpoints
const activityGroupings = ref([])
const loadingGroupings = ref(false)
const selectedGroupingsVersion = ref(null)
const groupingsSummaryData = ref({})
const showGroupingsForm = ref(false)
const pendingGroupingsVersionSwitch = ref(false)
const showGroupingsHistory = ref(false)
const groupingsHistoryItems = ref([])

const GROUPINGS_SOURCE = 'activity-instances'
const GROUPINGS_SUBITEM = 'groupings'

const actionSubitemMap = {
  edit: 'attributes',
  approve: 'attributes',
  newVersion: 'attributes',
  history: 'attributes',
}

const emit = defineEmits(['refresh'])

// Table headers
const groupingsHeaders = [
  {
    title: 'Activity group',
    key: 'activity_group_name',
    sortable: true,
    width: '40%',
  },
  {
    title: 'Activity subgroup',
    key: 'activity_subgroup_name',
    sortable: true,
    width: '40%',
  },
  {
    title: 'Activity',
    key: 'activity_name',
    sortable: true,
    width: '20%',
  },
]

const groupingsActions = computed(() => {
  return [
    {
      key: 'approve',
      label: t('_global.approve'),
      icon: 'mdi-check-decagram',
      iconColor: 'success',
    },
    {
      key: 'edit',
      label: t('_global.edit'),
      icon: 'mdi-pencil-outline',
      iconColor: 'nnBaseBlue',
    },
    {
      key: 'new_version',
      label: t('_global.new_version'),
      icon: 'mdi-plus-circle-outline',
      iconColor: 'nnBaseBlue',
    },
    {
      key: 'history',
      label: t('_global.history'),
      icon: 'mdi-history',
      iconColor: 'nnBaseBlue',
    },
  ]
})

const attributesActions = computed(() => {
  return [
    {
      key: 'approve',
      label: t('_global.approve'),
      icon: 'mdi-check-decagram',
      iconColor: 'success',
    },
    {
      key: 'edit',
      label: t('_global.edit'),
      icon: 'mdi-pencil-outline',
      iconColor: 'nnBaseBlue',
    },
    {
      key: 'new_version',
      label: t('_global.new_version'),
      icon: 'mdi-plus-circle-outline',
      iconColor: 'nnBaseBlue',
    },
    {
      key: 'history',
      label: t('_global.history'),
      icon: 'mdi-history',
      iconColor: 'nnBaseBlue',
    },
  ]
})

const attributesPossibleActions = computed(() => {
  return overview.value?.item?.possible_actions || []
})

function isAttributesActionVisible(action) {
  if (!action || !action.key) return false
  if (action.key === 'history') return true
  return attributesPossibleActions.value.includes(action.key)
}

function onAttributesActionClick(actionKey) {
  if (!overview.value) return
  if (actionKey === 'approve') return overview.value.approveItem()
  if (actionKey === 'edit') return overview.value.editItem()
  if (actionKey === 'new_version') return overview.value.newItemVersion()
  if (actionKey === 'history') return overview.value.openHistory()
}

const groupingPossibleActions = computed(() => {
  return groupingsSummaryData.value?.possible_actions || []
})

const isGroupingDraft = computed(() => {
  return groupingsSummaryData.value?.status === 'Draft'
})

function isGroupingActionVisible(action) {
  if (!action || !action.key) return false

  if (action.key === 'history') {
    return true
  }

  if (action.key === 'approve') {
    return (
      isGroupingDraft.value && groupingPossibleActions.value.includes('approve')
    )
  }

  return groupingPossibleActions.value.includes(action.key)
}

async function refreshAfterGroupingMutation({
  switchToLatestVersion = false,
} = {}) {
  if (switchToLatestVersion) {
    pendingGroupingsVersionSwitch.value = true
  }

  if (overview.value?.fetchItem) {
    await overview.value.fetchItem()
    return
  }

  if (switchToLatestVersion) {
    initializeSelectedGroupingsVersion()
  }
  await fetchActivityGroupings()
}

async function openGroupingsHistory() {
  const activityInstanceId = route.params.id
  if (!activityInstanceId) return

  try {
    const response = await activities.getVersions(
      GROUPINGS_SOURCE,
      activityInstanceId,
      GROUPINGS_SUBITEM
    )
    groupingsHistoryItems.value = (response.data || []).map(
      transformGroupingsHistoryItem
    )
    showGroupingsHistory.value = true
  } catch (error) {
    console.error('Error loading activity groupings history:', error)
  }
}

function closeGroupingsHistory() {
  showGroupingsHistory.value = false
}

// Flatten a groupings version record so the history table can render the
// activity group / subgroup / activity columns. Mirrors the transform used
// for the main attributes history in transformItem().
function transformGroupingsHistoryItem(item) {
  const copy = { ...item }
  const groupings = Array.isArray(item.activity_groupings)
    ? item.activity_groupings
    : []
  const groups = []
  const subgroups = []
  const activityNames = []
  for (const grouping of groupings) {
    if (grouping?.activity_group?.name) {
      groups.push(grouping.activity_group.name)
    }
    if (grouping?.activity_subgroup?.name) {
      subgroups.push(grouping.activity_subgroup.name)
    }
    if (grouping?.activity?.name) {
      activityNames.push(grouping.activity.name)
    }
  }
  copy.activity_group = { name: groups }
  copy.activity_subgroup = { name: subgroups }
  copy.activity_name =
    copy.activity_name ?? (activityNames.length ? activityNames.join(', ') : '')
  return copy
}

async function onGroupingActionClick(actionKey) {
  const activityInstanceId = route.params.id

  if (actionKey === 'edit') {
    showGroupingsForm.value = true
    return
  }

  if (!activityInstanceId) {
    return
  }

  try {
    if (actionKey === 'approve') {
      await activities.approve(
        activityInstanceId,
        GROUPINGS_SOURCE,
        {},
        GROUPINGS_SUBITEM
      )
      notificationHub?.add({
        msg: t('ActivitiesTable.approve_activity-instances_success'),
        type: 'success',
      })
      await refreshAfterGroupingMutation({ switchToLatestVersion: true })
      return
    }

    if (actionKey === 'new_version') {
      await activities.newVersion(
        activityInstanceId,
        GROUPINGS_SOURCE,
        GROUPINGS_SUBITEM
      )
      notificationHub?.add({
        msg: t('_global.new_version_success'),
        type: 'success',
      })
      await refreshAfterGroupingMutation({ switchToLatestVersion: true })
      return
    }

    if (actionKey === 'history') {
      await openGroupingsHistory()
    }
  } catch (error) {
    console.error(`Error performing grouping action "${actionKey}":`, error)
  }
}

async function closeGroupingsForm() {
  showGroupingsForm.value = false
  // Signal that we need to switch to the latest groupings version
  // once the overview data refreshes (the prop update is async)
  pendingGroupingsVersionSwitch.value = true
  // Also refresh the main overview data
  if (overview.value) {
    await overview.value.fetchItem()
  }
}

// Methods for ActivitySummary component
function refreshData() {
  // Skip the groupings fetch when a version switch is pending – the
  // itemOverview watcher will trigger a fresh fetch with the correct version
  // once the parent View finishes re-fetching the overview data.
  if (!pendingGroupingsVersionSwitch.value) {
    fetchActivityGroupings()
  }
  emit('refresh')
}

// Fetch activity groupings from new endpoint
async function fetchActivityGroupings() {
  try {
    loadingGroupings.value = true
    const activityInstanceId = route.params.id
    const version = selectedGroupingsVersion.value

    // Don't fetch if we don't have a valid groupings version yet —
    // the itemOverview watcher will trigger a fetch once versions are known.
    if (!activityInstanceId || !version) {
      loadingGroupings.value = false
      return
    }

    // If known versions are available, validate the selected one
    const knownVersions = groupingsVersionChoices.value
    if (knownVersions.length && !knownVersions.includes(version)) {
      loadingGroupings.value = false
      selectedGroupingsVersion.value = knownVersions[0]
      return // version watcher will re-trigger the fetch
    }

    if (activityInstanceId) {
      const response = await activities.getActivityInstanceGroupings(
        activityInstanceId,
        version
      )
      groupingsSummaryData.value = {
        start_date: response.data.start_date,
        end_date: response.data.end_date,
        status: response.data.status,
        change_description: response.data.change_description,
        author_username: response.data.author_username,
        possible_actions: response.data.possible_actions || [],
      }
      activityGroupings.value = response.data.activity_groupings || []
      // Initialize filtered groupings
      filteredGroupings.value = convertActivityGroupingsToTableItems(
        activityGroupings.value
      )
    }
  } catch (error) {
    console.error('Error fetching activity groupings:', error)
    groupingsSummaryData.value = {}
    activityGroupings.value = []
    filteredGroupings.value = []
  } finally {
    loadingGroupings.value = false
  }
}

function initializeSelectedGroupingsVersion() {
  const versions = groupingsVersionChoices.value
  if (!versions.length) {
    selectedGroupingsVersion.value = null
    return false
  }

  if (
    !selectedGroupingsVersion.value ||
    !versions.includes(selectedGroupingsVersion.value)
  ) {
    const routeVersion = route.params.version
      ? String(route.params.version)
      : null
    selectedGroupingsVersion.value =
      routeVersion && versions.includes(routeVersion)
        ? routeVersion
        : versions[0]
    return true
  }

  return false
}

// Convert activity instance to format expected by ActivitySummary
function adaptActivityInstanceForSummary(
  activityInstance,
  activityGroupings = []
) {
  if (!activityInstance) return {}

  // Extract activity name from activity groupings
  let activityName = activityInstance.activity_name
  if (!activityName && activityGroupings && activityGroupings.length > 0) {
    activityName = activityGroupings[0]?.activity?.name
  }

  return {
    name: activityInstance.name,
    name_sentence_case: activityInstance.name_sentence_case,
    version: activityInstance.version,
    start_date: activityInstance.start_date,
    end_date: activityInstance.end_date,
    status: activityInstance.status,
    definition: activityInstance.definition,
    abbreviation: activityInstance.abbreviation,
    library_name: activityInstance.library_name,
    nci_concept_id: activityInstance.nci_concept_id,
    nci_concept_name: activityInstance.nci_concept_name,
    adam_param_code: activityInstance.adam_param_code,
    activity_instance_class:
      activityInstance.activity_instance_class?.name ||
      activityInstance.activity_instance_class,
    is_required_for_activity: activityInstance.is_required_for_activity,
    is_default_selected_for_activity:
      activityInstance.is_default_selected_for_activity,
    is_data_sharing: activityInstance.is_data_sharing,
    is_legacy_usage: activityInstance.is_legacy_usage,
    topic_code: activityInstance.topic_code,
    molecular_weight: activityInstance.molecular_weight,
    activity_name: activityName,
    author_username:
      activityInstance.author_username || activityInstance.author_id,
  }
}

// Get all versions for the version selector
function allVersions(item) {
  if (!item || !item.all_versions) return []
  return item.all_versions
}

// Handle manual version changes
async function manualChangeVersion(version) {
  if (!version || !overview.value || !overview.value.itemOverview) return

  try {
    const activityInstance = overview.value.itemOverview.activity_instance
    await router.push({
      name: 'ActivityInstanceOverview',
      params: { id: activityInstance.uid, version: version },
    })
    emit('refresh')
  } catch (error) {
    console.error('Error navigating to new version:', error)
  }
}

// Change version function used by BaseActivityOverview
async function changeVersion(activityInstance, version) {
  if (!activityInstance || !activityInstance.uid) return

  try {
    await router.push({
      name: 'ActivityInstanceOverview',
      params: { id: activityInstance.uid, version },
    })
    emit('refresh')
  } catch (error) {
    console.error('Error navigating to new version:', error)
  }
}

// Add ref for filtered groupings
const searchTerm = ref('')
const filteredGroupings = ref([])

// Convert activity groupings for NNTable
function convertActivityGroupingsToTableItems(groupings) {
  if (!groupings || !groupings.length) return []

  return groupings.map((grouping) => ({
    activity_group_name: grouping.activity_group.name,
    activity_group_id: grouping.activity_group.uid,
    activity_group_version: grouping.activity_group.version,
    activity_group_status: grouping.activity_group.status,
    activity_subgroup_name: grouping.activity_subgroup.name,
    activity_subgroup_id: grouping.activity_subgroup.uid,
    activity_subgroup_version: grouping.activity_subgroup.version,
    activity_subgroup_status: grouping.activity_subgroup.status,
    activity_name: grouping.activity.name,
    activity_id: grouping.activity.uid,
    activity_version: grouping.activity.version,
    activity_status: grouping.activity.status,
    uid: `${grouping.activity_group.uid}-${grouping.activity_subgroup.uid}-${grouping.activity.uid}`, // Add unique key
  }))
}

// Handle filtering for activity groupings
function handleGroupingsFilter(filters, options) {
  // Handle both @filter and @update:options events. Vuetify can fire
  // @update:options early in mount with a non-string `.search` (null,
  // undefined, or an object on some versions), so coerce defensively
  // before calling toLowerCase — that crash was caught by the demo smoke
  // suite on CI but didn't reproduce on macOS Chromium.
  const rawSearch = options?.search ?? filters?.search ?? ''
  const searchValue = typeof rawSearch === 'string' ? rawSearch : ''

  if (searchValue) {
    searchTerm.value = searchValue.toLowerCase()
    const items = convertActivityGroupingsToTableItems(activityGroupings.value)

    filteredGroupings.value = items.filter((item) => {
      // Create searchable text from all fields including the displayed format
      const searchableFields = [
        item.activity_group_name,
        item.activity_subgroup_name,
        item.activity_name,
        item.activity_group_status,
        item.activity_subgroup_status,
        item.activity_status,
        item.activity_group_version,
        item.activity_subgroup_version,
        item.activity_version,
        // Add the displayed format "Version X.X - Status"
        item.activity_group_version && item.activity_group_status
          ? `Version ${item.activity_group_version} - ${item.activity_group_status}`
          : '',
        item.activity_subgroup_version && item.activity_subgroup_status
          ? `Version ${item.activity_subgroup_version} - ${item.activity_subgroup_status}`
          : '',
        item.activity_version && item.activity_status
          ? `Version ${item.activity_version} - ${item.activity_status}`
          : '',
      ]

      const searchableText = searchableFields
        .filter(Boolean)
        .join(' ')
        .toLowerCase()

      return searchableText.includes(searchTerm.value)
    })
  } else {
    searchTerm.value = ''
    filteredGroupings.value = convertActivityGroupingsToTableItems(
      activityGroupings.value
    )
  }
}

// Computed property for displayed items
const displayedGroupings = computed(() => {
  return searchTerm.value
    ? filteredGroupings.value
    : convertActivityGroupingsToTableItems(activityGroupings.value)
})

const groupingsVersionChoices = computed(() => {
  const versions = overview.value?.itemOverview?.activity_groupings_versions
  if (!Array.isArray(versions)) {
    return []
  }
  return versions.map(String)
})

const groupingsExportDataUrl = computed(() => {
  const baseUrl = `concepts/activities/activity-instances/${route.params.id}/activity-groupings`
  if (!selectedGroupingsVersion.value) return baseUrl
  return `${baseUrl}?version=${encodeURIComponent(selectedGroupingsVersion.value)}`
})

const newWizardStepper = computed(() => {
  return featureFlagsStore.getFeatureFlag(
    'new_activity_instance_wizard_stepper'
  )
})

const newWizardStepperEditMode = computed(() => {
  return featureFlagsStore.getFeatureFlag(
    'activity_instance_wizard_stepper_edit_mode'
  )
})

// Transform item for BaseActivityOverview
function transformItem(item) {
  if (!item) return

  if (item.activity_groupings && item.activity_groupings.length > 0) {
    const groups = []
    const subgroups = []
    item.activities = [item.activity_groupings[0].activity]
    item.activity = { name: item.activity_groupings[0].activity.name }

    for (const grouping of item.activity_groupings) {
      groups.push(grouping.activity_group.name)
      subgroups.push(grouping.activity_subgroup.name)
    }

    item.activity_group = { name: groups }
    item.activity_subgroup = { name: subgroups }
  } else {
    item.activity_group = { name: [] }
    item.activity_subgroup = { name: [] }
    item.activity = { name: '' }
  }

  item.item_key = item.uid
}

// History headers for BaseActivityOverview
const historyHeaders = [
  { title: t('_global.library'), key: 'library_name' },
  { title: t('_global.name'), key: 'name' },
  { title: t('_global.abbreviation'), key: 'abbreviation' },
  { title: t('_global.type'), key: 'activity_instance_class_name' },
  { title: t('_global.definition'), key: 'definition' },
  {
    title: t('ActivityInstanceOverview.nci_concept_id'),
    key: 'nci_concept_id',
  },
  {
    title: t('ActivityInstanceOverview.nci_concept_name'),
    key: 'nci_concept_name',
  },
  {
    title: t('ActivityInstanceOverview.is_research_lab'),
    key: 'is_research_lab',
  },
  { title: t('ActivityInstanceOverview.topic_code'), key: 'topic_code' },
  { title: t('ActivityInstanceOverview.adam_code'), key: 'adam_param_code' },
  {
    title: t('ActivityInstanceOverview.is_required_for_activity'),
    key: 'is_required_for_activity',
  },
  {
    title: t('ActivityInstanceOverview.is_default_selected_for_activity'),
    key: 'is_default_selected_for_activity',
  },
  {
    title: t('ActivityInstanceOverview.is_data_sharing'),
    key: 'is_data_sharing',
  },
  {
    title: t('ActivityInstanceOverview.is_legacy_usage'),
    key: 'is_legacy_usage',
  },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.status'), key: 'status' },
  { title: t('_global.version'), key: 'version' },
]

// History headers for the activity groupings history dialog. Keys match the
// payload returned by `GET /activity-instances/{uid}/groupings/versions` after
// being flattened by transformGroupingsHistoryItem().
const groupingsHistoryHeaders = [
  {
    title: t('ActivityTable.activity_group'),
    key: 'activity_group.name',
  },
  {
    title: t('ActivityTable.activity_subgroup'),
    key: 'activity_subgroup.name',
  },
  {
    title: t('ActivityTable.activity_name'),
    key: 'activity_name',
  },
  {
    title: t('_global.change_description'),
    key: 'change_description',
  },
  { title: t('_global.status'), key: 'status' },
  { title: t('_global.version'), key: 'version' },
]

const groupingsHistoryTitle = computed(() =>
  t('ActivityInstanceOverview.groupings_history_title', {
    uid: route.params.id || '',
  })
)

// Watch for route parameter changes to refetch data
watch(
  () => [route.params.id, route.params.version],
  () => {
    const didUpdateSelectedVersion = initializeSelectedGroupingsVersion()
    if (!didUpdateSelectedVersion) {
      fetchActivityGroupings()
    }
  },
  { immediate: true }
)

watch(
  () => overview.value?.itemOverview,
  () => {
    if (pendingGroupingsVersionSwitch.value) {
      pendingGroupingsVersionSwitch.value = false
      const versions = groupingsVersionChoices.value
      const latestVersion = versions[0] ?? null
      if (latestVersion) {
        selectedGroupingsVersion.value = latestVersion
      }
      // Always fetch with the (now correct) version
      fetchActivityGroupings()
    } else {
      initializeSelectedGroupingsVersion()
    }
  },
  { immediate: true }
)

watch(selectedGroupingsVersion, (newVersion, oldVersion) => {
  if (newVersion && newVersion !== oldVersion) {
    fetchActivityGroupings()
  }
})

// Setup on mount
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
    t('Sidebar.library.activities_instances'),
    { name: 'Activities', params: { tab: 'activity-instances' } },
    3,
    true
  )

  // Add instance name when available
  if (overview.value?.itemOverview?.activity_instance?.name) {
    appStore.addBreadcrumbsLevel(
      overview.value.itemOverview.activity_instance.name,
      { name: 'ActivityInstanceOverview', params: route.params },
      4,
      true
    )
  }
})
</script>

<style scoped>
/* Activity Instance overview container styling */
.activity-instance-overview-container {
  width: 100%;
  background-color: transparent;
}

/* Activity section styling */
.activity-section {
  margin-top: 24px;
}

/* Summary section styling */
.activity-summary {
  margin-bottom: 24px;
}

/* Section header styling */
.section-header {
  margin-top: 16px;
  margin-bottom: 8px;
  padding-left: 0;
}

.section-header--with-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.activity-instance-attributes-section {
  margin-bottom: 8px;
}

.groupings-action-buttons {
  display: flex;
  align-items: center;
}

/* Tables styling */
.groupings-table {
  margin-top: 8px;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: none;
  background-color: transparent;
}

/* Table content styling */
.groupings-table :deep(table) {
  border-collapse: collapse;
  width: 100%;
}

.groupings-table :deep(th) {
  background-color: var(--semantic-system-brand, #001965);
  color: white;
  font-weight: 500;
  padding: 12px 16px;
  text-align: left;
}

.groupings-table :deep(td) {
  padding: 8px 16px;
  border-bottom: 1px solid #e0e0e0;
  background-color: white !important;
}

.groupings-table :deep(.v-card-text) {
  width: 100% !important;
  padding: 0 !important;
}

.groupings-table :deep(.v-table__wrapper) {
  height: auto !important;
}

.groupings-table :deep(.v-card-title) {
  padding: 8px 16px;
  display: flex;
  flex-direction: row;
  justify-content: flex-start;
  align-items: center;
  background-color: transparent;
}

.groupings-table :deep(.v-card__title .v-input) {
  max-width: 300px;
  margin-right: auto;
}

.groupings-table :deep(.v-data-table-footer) {
  border-top: 1px solid #e0e0e0;
  background-color: transparent !important;
}

/* Round table corners */
.activity-instance-overview-container :deep(.v-data-table) {
  border-radius: 8px !important;
  overflow: visible;
}

.activity-instance-overview-container :deep(.v-table__wrapper) {
  border-radius: 8px !important;
  overflow-x: auto;
}

.activity-instance-overview-container :deep(.v-table),
.groupings-table :deep(.v-table) {
  background: transparent !important;
}

.activity-instance-overview-container :deep(.v-data-table__th),
.groupings-table :deep(.v-data-table__th) {
  background-color: rgb(var(--v-theme-nnTrueBlue)) !important;
}

.activity-instance-overview-container :deep(.v-data-table__tbody tr),
.groupings-table :deep(.v-data-table__tbody tr) {
  background-color: white !important;
}

.activity-instance-overview-container :deep(.v-card),
.activity-instance-overview-container :deep(.v-sheet),
.groupings-table :deep(.v-card),
.groupings-table :deep(.v-sheet) {
  background-color: transparent !important;
  box-shadow: none !important;
}
</style>
