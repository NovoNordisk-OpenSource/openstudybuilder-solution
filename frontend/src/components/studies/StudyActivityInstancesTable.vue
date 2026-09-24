<template>
  <NNTable
    :key="`studyActivityInstancesTable-${editMode}`"
    ref="tableRef"
    table-id="studies-activity-instances-table"
    :headers="headers"
    :items="studyActivitiesInstances"
    :items-length="total"
    item-value="activity_instance.uid"
    :column-data-resource="`studies/${studiesGeneralStore.selectedStudy.uid}/study-activity-instances`"
    :filters-modify-function="modifyFilters"
    :default-filters="defaultFilters"
    :history-config="{
      dataFetcher: fetchStudyActivityInstancesHistory,
      title: $t('StudyActivityTable.global_history_title'),
    }"
    :export-config="{
      objectLabel: 'ActivityInstances',
      dataUrl: exportDataUrl,
    }"
    @filter="getStudyActivityInstances"
  >
    <template #headerCenter="">
      <v-btn-toggle
        v-if="!editMode"
        v-model="selectedStatusTab"
        mandatory
        density="compact"
        color="nnBaseBlue"
        divided
        variant="outlined"
        class="layoutSelector"
        @update:model-value="onStatusTabChange"
      >
        <v-btn v-for="tab in statusTabs" :key="tab.value" :value="tab.value">
          <v-icon v-if="tab.icon" :color="tab.color">{{ tab.icon }}</v-icon>
          {{ tab.label }}
        </v-btn>
      </v-btn-toggle>
      <v-btn
        v-if="editMode"
        variant="outlined"
        color="nnBaseBlue"
        prepend-icon="mdi-content-save-outline"
        :loading="savingAll"
        :disabled="savingAll"
        class="mr-2"
        @click="saveAllAndClose()"
      >
        {{ $t('_global.save_and_close') }}
      </v-btn>
      <v-btn
        v-if="editMode"
        variant="outlined"
        color="error"
        prepend-icon="mdi-close"
        :disabled="savingAll"
        @click="discardChanges()"
      >
        {{ $t('_global.cancel') }}
      </v-btn>
    </template>
    <template #actions="">
      <v-btn
        v-if="!editMode"
        class="mr-2"
        rounded
        variant="outlined"
        color="nnBaseBlue"
        :disabled="
          !accessGuard.checkPermission($roles.STUDY_WRITE) ||
          studiesGeneralStore.selectedStudyVersion !== null
        "
        @click="openBatchUpdateForm()"
      >
        <v-icon>mdi-exclamation</v-icon>
        <span class="label">{{
          $t('StudyActivityTable.review_instances')
        }}</span>
      </v-btn>
      <v-btn
        v-if="!editMode"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        :disabled="
          !accessGuard.checkPermission($roles.STUDY_WRITE) ||
          studiesGeneralStore.selectedStudyVersion !== null
        "
        @click="openEditMode()"
      >
        <v-icon>mdi-pencil-outline</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ $t('_global.edit_in_table') }}
        </v-tooltip>
      </v-btn>
    </template>
    <template #[`item.actions`]="{ item }">
      <ActionsMenu
        :actions="actions"
        :item="item"
        :badge="actionsMenuBadge(item)"
      />
    </template>
    <template #[`item.activity_instance.name`]="{ item }">
      <template v-if="item.activity_instance">
        <router-link
          :to="{
            name: 'ActivityInstanceOverview',
            params: { id: item.activity_instance.uid },
          }"
        >
          {{ item.activity_instance?.name }}
        </router-link>
      </template>
    </template>
    <template #[`item.activity.is_data_collected`]="{ item }">
      {{ $filters.yesno(item.activity.is_data_collected) }}
    </template>
    <template #[`item.state`]="{ item }">
      <div
        :class="getInstanceCssClass(item)"
        @click="
          [instancesActions.REVIEW_NEEDED, instancesActions.ADD].indexOf(
            item.state
          ) !== -1
            ? editRelationship(item)
            : ''
        "
      >
        {{ item.state }}
      </div>
    </template>
    <template #[`item.is_reviewed`]="{ item }">
      <v-checkbox
        v-model="item.is_reviewed"
        class="mt-2 mb-n4"
        :disabled="
          [
            instancesActions.ADD,
            instancesActions.NA,
            instancesActions.REMOVE,
          ].indexOf(item.state) !== -1 ||
          (item.is_activity_instance_updated && !item.keep_old_version)
        "
        @update:model-value="updateReviewedState(item)"
      />
    </template>
    <template #[`item.is_important`]="{ item }">
      <template v-if="editMode">
        <v-checkbox
          v-model="item.is_important"
          class="mt-2 mb-n4"
          :disabled="
            !item.study_activity_instance_uid ||
            !item.activity?.is_data_collected
          "
          @update:model-value="markItemModified(item)"
        />
      </template>
      <template v-else>
        {{ item.is_important ? $t('_global.yes') : '' }}
      </template>
    </template>
    <template #[`item.baseline_visits`]="{ item }">
      <template v-if="editMode">
        <v-select
          v-model="item.baseline_visit_uids"
          class="cellWidthWide"
          :items="item._availableBaselineVisits || []"
          item-title="visit_name"
          item-value="uid"
          multiple
          chips
          closable-chips
          clearable
          :loading="item._loadingBaselineVisits"
          :disabled="!item.study_activity_instance_uid"
          @click="loadBaselineVisitsForItem(item)"
          @update:model-value="markItemModified(item)"
        >
          <template #chip="{ internalItem: chipItem, props: chipProps }">
            <v-tooltip
              :text="chipItem.title"
              location="top"
              :disabled="!isChipTextTruncated(chipItem.title)"
            >
              <template #activator="{ props: tooltipProps }">
                <v-chip
                  v-bind="{ ...chipProps, ...tooltipProps }"
                  closable
                  size="small"
                >
                  {{ chipItem.title }}
                </v-chip>
              </template>
            </v-tooltip>
          </template>
        </v-select>
      </template>
      <template v-else>
        {{ displayVisits(item.baseline_visits) }}
      </template>
    </template>
    <template #[`item.study_data_supplier_name`]="{ item }">
      <template v-if="editMode">
        <v-select
          v-model="item.study_data_supplier_uid"
          class="cellWidthWide"
          :items="studyDataSuppliers"
          item-title="name"
          item-value="study_data_supplier_uid"
          clearable
          :disabled="!item.study_activity_instance_uid"
          @update:model-value="onSupplierChange(item, $event)"
        >
          <template #selection="{ internalItem: selectedItem }">
            <v-tooltip
              :text="selectedItem.title"
              location="top"
              :disabled="!isTextTruncated(selectedItem.title)"
            >
              <template #activator="{ props }">
                <div v-bind="props" class="selection-tooltip-wrapper">
                  {{ selectedItem.title }}
                </div>
              </template>
            </v-tooltip>
          </template>
        </v-select>
      </template>
      <template v-else>
        {{ item.study_data_supplier_name }}
      </template>
    </template>
    <template #[`item.origin_type.term_name`]="{ item }">
      <template v-if="editMode">
        <v-select
          v-model="item.origin_type_uid"
          class="cellWidthWide"
          :items="originTypes"
          item-title="sponsor_preferred_name"
          item-value="term_uid"
          clearable
          :disabled="!item.study_activity_instance_uid"
          @update:model-value="markItemModified(item)"
        >
          <template #selection="{ internalItem: selectedItem }">
            <v-tooltip
              :text="selectedItem.title"
              location="top"
              :disabled="!isTextTruncated(selectedItem.title)"
            >
              <template #activator="{ props }">
                <div v-bind="props" class="selection-tooltip-wrapper">
                  {{ selectedItem.title }}
                </div>
              </template>
            </v-tooltip>
          </template>
        </v-select>
      </template>
      <template v-else>
        {{ item.origin_type?.term_name }}
      </template>
    </template>
    <template #[`item.origin_source.term_name`]="{ item }">
      <template v-if="editMode">
        <v-select
          v-model="item.origin_source_uid"
          class="cellWidthWide"
          :items="originSources"
          item-title="sponsor_preferred_name"
          item-value="term_uid"
          clearable
          :disabled="!item.study_activity_instance_uid"
          @update:model-value="markItemModified(item)"
        >
          <template #selection="{ internalItem: selectedItem }">
            <v-tooltip
              :text="selectedItem.title"
              location="top"
              :disabled="!isTextTruncated(selectedItem.title)"
            >
              <template #activator="{ props }">
                <div v-bind="props" class="selection-tooltip-wrapper">
                  {{ selectedItem.title }}
                </div>
              </template>
            </v-tooltip>
          </template>
        </v-select>
      </template>
      <template v-else>
        {{ item.origin_source?.term_name }}
      </template>
    </template>
  </NNTable>
  <StudyActivityInstancesEditForm
    :open="showEditForm"
    :edited-activity="activeActivity"
    @close="closeEditForm"
  />
  <v-dialog
    v-model="showHistory"
    persistent
    :fullscreen="$globals.historyDialogFullscreen"
    @keydown.esc="closeHistory"
  >
    <HistoryTable
      :title="activityInstanceHistoryTitle"
      :headers="headers"
      :items="activityInstanceHistoryItems"
      @close="closeHistory"
    />
  </v-dialog>
  <UpdateActivityInstanceForm
    :activity="activeActivity"
    :open="showUpdateForm"
    @close="closeUpdateForm"
  />
  <v-dialog v-model="showBatchUpdateForm">
    <BatchUpdateActivityInstanceForm @close="closeBatchUpdateForm" />
  </v-dialog>
  <ConfirmDialog ref="confirmRef" :text-cols="6" :action-cols="5" />
</template>
<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudyActivitiesStore } from '@/stores/studies-activities'
import study from '@/api/study'
import dataSuppliers from '@/api/dataSuppliers'
import terms from '@/api/controlledTerminology/terms'
import filteringParameters from '@/utils/filteringParameters'
import { escapeHTML } from '@/utils/sanitize'
import NNTable from '@/components/tools/NNTable.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import StudyActivityInstancesEditForm from './StudyActivityInstancesEditForm.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import UpdateActivityInstanceForm from './UpdateActivityInstanceForm.vue'
import BatchUpdateActivityInstanceForm from './BatchUpdateActivityInstanceForm.vue'
import instancesActions from '@/constants/instancesActions'
import { useAccessGuard } from '@/composables/accessGuard'
import _isEmpty from 'lodash/isEmpty'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const studiesGeneralStore = useStudiesGeneralStore()
const activitiesStore = useStudyActivitiesStore()
const accessGuard = useAccessGuard()
const roles = inject('roles')
const tableRef = ref()
const confirmRef = ref()

// Edit mode state
const editMode = ref(false)
const itemsDisabled = ref(false)
const savingAll = ref(false)
const studyDataSuppliers = ref([])
const libraryDataSuppliers = ref([])
const originTypes = ref([])
const originSources = ref([])

const allHeaders = [
  { title: '', key: 'actions', width: '1%' },
  { title: t('StudyActivityInstances.state_actions'), key: 'state' },
  { title: t('StudyActivityInstances.reviewed'), key: 'is_reviewed' },
  { title: t('_global.library'), key: 'activity.library_name' },
  {
    title: t('StudyActivity.flowchart_group'),
    key: 'study_soa_group.soa_group_term_name',
  },
  {
    title: t('StudyActivity.activity_group'),
    key: 'study_activity_group.activity_group_name',
  },
  {
    title: t('StudyActivity.activity_sub_group'),
    key: 'study_activity_subgroup.activity_subgroup_name',
  },
  { title: t('StudyActivity.activity'), key: 'activity.name' },
  {
    title: t('StudyActivity.data_collection'),
    key: 'activity.is_data_collected',
  },
  {
    title: t('StudyActivityInstances.activity_instance'),
    key: 'activity_instance.name',
  },
  {
    title: t('StudyActivityInstances.topic_code'),
    key: 'activity_instance.topic_code',
  },
  {
    title: t('StudyActivityInstances.test_name_code'),
    key: 'activity_instance.test_name_code',
  },
  {
    title: t('StudyActivityInstances.specimen'),
    key: 'activity_instance.specimen',
  },
  {
    title: t('StudyActivityInstances.standard_unit'),
    key: 'activity_instance.standard_unit',
  },
  {
    title: t('StudyActivityInstances.adam_code'),
    key: 'activity_instance.adam_param_code',
  },
  {
    title: t('StudyActivityInstances.important'),
    key: 'is_important',
  },
  {
    title: t('StudyActivityInstances.baseline_visits'),
    key: 'baseline_visits',
  },
  {
    title: t('StudyActivityInstances.data_supplier'),
    key: 'study_data_supplier_name',
  },
  {
    title: t('StudyActivityInstances.origin_type'),
    key: 'origin_type.term_name',
  },
  {
    title: t('StudyActivityInstances.origin_source'),
    key: 'origin_source.term_name',
  },
]

// Columns to hide in edit mode
const editModeHiddenKeys = [
  'actions',
  'state',
  'is_reviewed',
  'activity_instance.topic_code',
  'activity_instance.test_name_code',
  'activity_instance.specimen',
  'activity_instance.standard_unit',
  'activity_instance.adam_param_code',
]

const headers = computed(() => {
  if (editMode.value) {
    return allHeaders.filter((h) => !editModeHiddenKeys.includes(h.key))
  }
  return allHeaders
})
const studyActivitiesInstances = ref([])
const total = ref(0)
const activeActivity = ref({})
const showEditForm = ref(false)
const activityInstanceHistoryItems = ref([])
const showHistory = ref(false)
const showUpdateForm = ref(false)
const showBatchUpdateForm = ref(false)
const actions = [
  {
    label: t('StudyActivityInstances.edit_relationship'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    click: editRelationship,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('StudyActivityInstances.delete_relationship'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    click: deleteRelationship,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('StudyActivityInstances.update_to_new_version'),
    icon: 'mdi-update',
    iconColor: 'primary',
    condition: (item) =>
      !studiesGeneralStore.selectedStudyVersion &&
      item.is_activity_instance_updated,
    click: openUpdateForm,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openHistory,
  },
]
const selectedStatusTab = ref('all')
const statusTabs = [
  { value: 'all', label: t('_global.all') },
  { value: 'updated', icon: 'mdi-alert-circle-outline', color: 'error' },
  { value: 'reviewed', icon: 'mdi-alert-outline', color: 'warning' },
]
const defaultFilters = computed(() => {
  // Use the current headers (already filtered by editMode) and exclude actions
  return headers.value.filter((a) => a.key !== 'actions')
})
const exportDataUrl = computed(() => {
  return `studies/${studiesGeneralStore.selectedStudy.uid}/study-activity-instances`
})
const activityInstanceHistoryTitle = computed(() => {
  if (activeActivity.value) {
    return t('StudyActivityInstances.study_activity_instance_history_title', {
      studyActivityInstanceUid:
        activeActivity.value.study_activity_instance_uid,
    })
  }
  return ''
})

function getInstanceCssClass(item) {
  if (
    [instancesActions.REVIEWED, instancesActions.REVIEW_NOT_NEEDED].indexOf(
      item.state
    ) !== -1
  )
    return 'reviewed'
  if (item.state === instancesActions.REMOVE) return 'needed'
  if (item.state === instancesActions.REVIEW_NEEDED) return 'needed row-pointer'
  if (item.state === instancesActions.ADD) return 'add row-pointer'
  return 'na'
}

function mapInstanceItem(item) {
  return {
    ...item,
    study_data_supplier_uid: item.study_data_supplier_uid || null,
    origin_type_uid: item.origin_type?.term_uid || null,
    origin_source_uid: item.origin_source?.term_uid || null,
    baseline_visit_uids: item.baseline_visits?.map((v) => v.uid) || [],
    _modified: false,
    _saving: false,
    _availableBaselineVisits: item.baseline_visits || [],
    _loadingBaselineVisits: false,
  }
}

function updateReviewedState(instance) {
  study
    .updateStudyActivityInstance(
      studiesGeneralStore.selectedStudy.uid,
      instance.study_activity_instance_uid,
      { is_reviewed: instance.is_reviewed }
    )
    .then((resp) => {
      const index = studyActivitiesInstances.value.findIndex(
        (item) =>
          item.study_activity_instance_uid ===
          instance.study_activity_instance_uid
      )
      if (index !== -1) {
        studyActivitiesInstances.value[index] = mapInstanceItem(resp.data)
      }
    })
}

function getStudyActivityInstances(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  if (params.filters) {
    const filtersObj = JSON.parse(params.filters)
    if (filtersObj['activity_group.name']) {
      params.activity_group_names = []
      filtersObj['activity_group.name'].v.forEach((value) => {
        params.activity_group_names.push(value)
      })
      delete filtersObj['activity_group.name']
    }
    if (filtersObj['activity_subgroup.name']) {
      params.activity_subgroup_names = []
      filtersObj['activity_subgroup.name'].v.forEach((value) => {
        params.activity_subgroup_names.push(value)
      })
      delete filtersObj['activity_subgroup.name']
    }
    if (filtersObj['activity.name']) {
      params.activity_names = []
      filtersObj['activity.name'].v.forEach((value) => {
        params.activity_names.push(value)
      })
      delete filtersObj['activity.name']
    }
    if (Object.keys(filtersObj).length !== 0) {
      params.filters = JSON.stringify(filtersObj)
    } else {
      delete params.filters
    }
  }
  let statusFilter = {}
  if (selectedStatusTab.value === 'reviewed') {
    statusFilter = { keep_old_version: { v: [true] } }
  } else if (selectedStatusTab.value === 'updated') {
    statusFilter = {
      is_activity_instance_updated: { v: [true] },
      keep_old_version: { v: [false] },
    }
  }

  if (selectedStatusTab.value !== 'all') {
    if (_isEmpty(params.filters)) {
      params.filters = statusFilter
    } else {
      const filtersObj =
        typeof params.filters === 'string'
          ? JSON.parse(params.filters)
          : params.filters
      Object.assign(filtersObj, statusFilter)
      params.filters = filtersObj
    }
  }
  params.studyUid = studiesGeneralStore.selectedStudy.uid
  // In edit mode, only show rows with linked activity instances
  if (editMode.value) {
    params.has_activity_instance = true
  }
  activitiesStore.fetchStudyActivityInstances(params).then((resp) => {
    // Initialize uid fields for edit mode dropdowns
    const items = resp.data.items.map(mapInstanceItem)
    studyActivitiesInstances.value = items
    total.value = resp.data.total
  })
}

function modifyFilters(jsonFilter, params) {
  if (jsonFilter['activity_group.name']) {
    params.activity_group_names = []
    jsonFilter['activity_group.name'].v.forEach((value) => {
      params.activity_group_names.push(value)
    })
    delete jsonFilter['activity_group.name']
  }
  if (jsonFilter.activity_groups) {
    params.activity_group_names = []
    jsonFilter.activity_groups.v.forEach((value) => {
      params.activity_group_names.push(value)
    })
    delete jsonFilter.activity_groups
  }
  if (jsonFilter['activity_subgroup.name']) {
    params.activity_subgroup_names = []
    jsonFilter['activity_subgroup.name'].v.forEach((value) => {
      params.activity_subgroup_names.push(value)
    })
    delete jsonFilter['activity_subgroup.name']
  }
  if (jsonFilter.name) {
    params.activity_names = []
    jsonFilter.name.v.forEach((value) => {
      params.activity_names.push(value)
    })
    delete jsonFilter.name
  }
  if (jsonFilter['activity.name']) {
    params.activity_names = []
    jsonFilter['activity.name'].v.forEach((value) => {
      params.activity_names.push(value)
    })
    delete jsonFilter['activity.name']
  }
  return {
    jsonFilter: jsonFilter,
    params: params,
  }
}

function editRelationship(item) {
  activeActivity.value = item
  showEditForm.value = true
}

function closeEditForm() {
  activeActivity.value = {}
  showEditForm.value = false
  tableRef.value.filterTable()
}

function displayVisits(visits) {
  if (!visits) {
    return ''
  }
  return visits.map((v) => v.visit_name).join(', ')
}

async function deleteRelationship(item) {
  const options = {
    width: 600,
    type: 'warning',
    cancelLabel: t('_global.cancel'),
    agreeLabel: t('_global.delete'),
  }
  if (
    await confirmRef.value.openHtml(
      t('StudyActivityInstances.confirm_delete', {
        instance: escapeHTML(
          item.activity_instance?.name || item.activity_instance?.uid
        ),
        activity: escapeHTML(item.activity?.name || item.activity?.uid),
      }),
      options
    )
  ) {
    activitiesStore
      .deleteStudyActivityInstance(
        studiesGeneralStore.selectedStudy.uid,
        item.study_activity_instance_uid
      )
      .then(() => {
        notificationHub.add({
          msg: t('StudyActivityInstances.instance_deleted'),
          type: 'success',
        })
        tableRef.value.filterTable()
      })
  }
}

async function fetchStudyActivityInstancesHistory() {
  const resp = await study.getStudyActivityInstancesAuditTrail(
    studiesGeneralStore.selectedStudy.uid
  )
  return resp.data
}

async function openHistory(item) {
  activeActivity.value = item
  const resp = await study.getStudyActivityInstanceAuditTrail(
    studiesGeneralStore.selectedStudy.uid,
    item.study_activity_instance_uid
  )
  activityInstanceHistoryItems.value = resp.data
  showHistory.value = true
}

function closeHistory() {
  activeActivity.value = {}
  showHistory.value = false
}

function actionsMenuBadge(item) {
  if (item.is_activity_instance_updated) {
    return {
      color: item.keep_old_version ? 'warning' : 'error',
      icon: item.keep_old_version
        ? 'mdi-alert-outline'
        : 'mdi-alert-circle-outline',
    }
  }
  return undefined
}

function openUpdateForm(item) {
  activeActivity.value = item
  showUpdateForm.value = true
}

function closeUpdateForm() {
  activeActivity.value = null
  showUpdateForm.value = false
  tableRef.value.filterTable()
}

function openBatchUpdateForm() {
  showBatchUpdateForm.value = true
}

function closeBatchUpdateForm() {
  showBatchUpdateForm.value = false
  tableRef.value.filterTable()
}

function onStatusTabChange() {
  if (tableRef.value) {
    tableRef.value.filterTable()
  }
}
// Edit mode functions
function openEditMode() {
  editMode.value = true
}

function closeEditMode() {
  editMode.value = false
  itemsDisabled.value = false
  tableRef.value.filterTable()
}

function discardChanges() {
  // Simply close edit mode - filterTable() will reload original data from API
  closeEditMode()
}

function markItemModified(item) {
  item._modified = true
}

function onSupplierChange(item, supplierUid) {
  item._modified = true

  // Default to clearing origin type and source - will be set below if supplier has defaults
  let newOriginTypeUid = null
  let newOriginSourceUid = null

  if (supplierUid) {
    // Find the selected Study Data Supplier
    const selectedStudySupplier = studyDataSuppliers.value.find(
      (s) => s.study_data_supplier_uid === supplierUid
    )

    if (selectedStudySupplier) {
      // Find the linked Library Data Supplier to get defaults
      // Study Data Supplier has data_supplier_uid that links to Library Data Supplier
      const librarySupplier = libraryDataSuppliers.value.find(
        (s) => s.uid === selectedStudySupplier.data_supplier_uid
      )

      if (librarySupplier) {
        // Auto-populate origin type from library supplier defaults
        // Check both term_uid (CT term) and uid (generic) field names
        newOriginTypeUid =
          librarySupplier.origin_type?.term_uid ||
          librarySupplier.origin_type?.uid ||
          null

        // Auto-populate origin source from library supplier defaults
        // Check both term_uid (CT term) and uid (generic) field names
        newOriginSourceUid =
          librarySupplier.origin_source?.term_uid ||
          librarySupplier.origin_source?.uid ||
          null
      }
    }
  }

  // Always update the origin fields (either with new defaults or null to clear)
  item.origin_type_uid = newOriginTypeUid
  item.origin_source_uid = newOriginSourceUid
}

async function saveItem(item) {
  const data = {
    study_data_supplier_uid: item.study_data_supplier_uid || null,
    origin_type_uid: item.origin_type_uid || null,
    origin_source_uid: item.origin_source_uid || null,
    baseline_visit_uids: item.baseline_visit_uids || [],
  }
  // Only include is_important if activity collects data
  if (item.activity?.is_data_collected) {
    data.is_important = item.is_important || false
  }

  await study.updateStudyActivityInstance(
    studiesGeneralStore.selectedStudy.uid,
    item.study_activity_instance_uid,
    data
  )
  item._modified = false
}

async function saveAllAndClose() {
  const modifiedItems = studyActivitiesInstances.value.filter(
    (item) => item._modified && item.study_activity_instance_uid
  )

  if (modifiedItems.length === 0) {
    closeEditMode()
    return
  }

  savingAll.value = true
  try {
    await Promise.all(modifiedItems.map((item) => saveItem(item)))
    notificationHub.add({
      msg: t('StudyActivityInstances.instances_updated', {
        count: modifiedItems.length,
      }),
      type: 'success',
    })
    closeEditMode()
  } catch (error) {
    console.error('Failed to save items:', error)
    notificationHub.add({
      msg: t('StudyActivityInstances.instances_update_failed'),
      type: 'error',
    })
  } finally {
    savingAll.value = false
  }
}

// Check if text would be truncated in a 220px cell (approx 18 chars visible)
function isTextTruncated(text) {
  return text && text.length > 18
}

// Check if chip text would be truncated (chips are smaller, approx 12 chars)
function isChipTextTruncated(text) {
  return text && text.length > 12
}

async function loadBaselineVisitsForItem(item) {
  if (
    !item.study_activity_instance_uid ||
    item._availableBaselineVisits?.length > 0
  ) {
    return
  }
  item._loadingBaselineVisits = true
  try {
    const resp = await study.getBaselineVisitsForStudyActivityInstance(
      studiesGeneralStore.selectedStudy.uid,
      item.study_activity_instance_uid
    )
    item._availableBaselineVisits = resp.data || []
  } catch (error) {
    console.error('Failed to load baseline visits:', error)
    item._availableBaselineVisits = []
  }
  item._loadingBaselineVisits = false
}

// Load dropdown data
onMounted(() => {
  // Load study data suppliers for current study
  study
    .getStudyDataSuppliers(studiesGeneralStore.selectedStudy.uid, {
      page_size: 0,
    })
    .then((resp) => {
      studyDataSuppliers.value = resp.data.items || []
    })

  // Load library data suppliers (for default origin values)
  dataSuppliers.get({ params: { page_size: 1000 } }).then((resp) => {
    libraryDataSuppliers.value = resp.data.items || []
  })

  // Load origin type CT terms
  terms.getTermsByCodelist('originType').then((resp) => {
    originTypes.value = resp.data.items || []
  })

  // Load origin source CT terms
  terms.getTermsByCodelist('originSource').then((resp) => {
    originSources.value = resp.data.items || []
  })
})
</script>
<style scoped>
.cellWidth {
  min-width: 180px;
}
.cellWidthWide {
  min-width: 220px;
}
.selection-tooltip-wrapper {
  width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
}
.reviewed {
  background-color: darkseagreen;
  border-radius: 5px;
  padding-inline: 5px;
  color: black;
}
.add {
  background-color: rgb(202, 124, 124);
  border-radius: 5px;
  padding-inline: 5px;
  color: black;
}
.needed {
  background-color: rgb(217, 201, 106);
  border-radius: 5px;
  padding-inline: 5px;
  color: black;
}
.na {
  background-color: rgb(179, 179, 179);
  border-radius: 5px;
  padding-inline: 5px;
  color: black;
}
.row-pointer {
  cursor: pointer;
}
.layoutSelector {
  border-color: rgb(var(--v-theme-nnBaseBlue));
}
.layoutSelector :deep(.v-btn) {
  text-transform: none;
}
</style>
