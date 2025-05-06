<template>
  <NNTable
    key="studyActivityTable"
    ref="table"
    :headers="headers"
    :items="studyActivities"
    :items-length="total"
    item-value="study_activity_uid"
    export-object-label="StudyActivities"
    :export-data-url="exportDataUrl"
    :column-data-resource="`studies/${studiesGeneralStore.selectedStudy.uid}/study-activities`"
    :history-data-fetcher="fetchActivitiesHistory"
    :history-title="$t('StudyActivityTable.global_history_title')"
    :extra-item-class="getItemRowClass"
    :filters-modify-function="modifyFilters"
    :initial-sort-by="[{ key: 'activity.name', order: 'asc' }]"
    @filter="getStudyActivities"
  >
    <template #[`footer.prepend`]>
      <v-chip color="yellow" variant="flat">
        {{ $t('StudyActivityTable.submitted') }}
      </v-chip>
      <v-chip class="ml-2" color="warning" variant="flat">
        {{ $t('StudyActivityTable.not_submitted') }}
      </v-chip>
      <v-spacer />
    </template>
    <template #actions="slot">
      <v-btn
        v-if="slot.showSelectBoxes"
        size="small"
        color="primary"
        :title="$t('StudyActivityTable.edit_activity_selection')"
        :disabled="
          !accessGuard.checkPermission($roles.STUDY_WRITE) ||
          studiesGeneralStore.selectedStudyVersion !== null
        "
        icon="mdi-pencil-box-multiple-outline"
        @click="openBatchEditForm(slot.selected)"
      />
      <v-btn
        class="ml-2"
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        data-cy="add-study-activity"
        :title="$t('StudyActivityForm.add_title')"
        :disabled="
          !accessGuard.checkPermission($roles.STUDY_WRITE) ||
          studiesGeneralStore.selectedStudyVersion !== null
        "
        icon="mdi-plus"
        @click.stop="showActivityForm = true"
      />
    </template>
    <template #[`item.actions`]="{ item }">
      <ActionsMenu
        :actions="getActionsForItem(item)"
        :item="item"
        :badge="actionsMenuBadge(item)"
      />
    </template>
    <template #[`item.activity.name`]="{ item }">
      <router-link
        :to="{
          name: 'StudyActivityOverview',
          params: {
            study_id: studiesGeneralStore.selectedStudy.uid,
            id: item.study_activity_uid,
          },
        }"
      >
        {{ item.activity.name }}
      </router-link>
    </template>
    <template #[`item.activity.is_data_collected`]="{ item }">
      {{ $filters.yesno(item.activity.is_data_collected) }}
    </template>
    <template #[`item.start_date`]="{ item }">
      {{ $filters.date(item.start_date) }}
    </template>
  </NNTable>
  <v-dialog
    v-model="showActivityForm"
    persistent
    fullscreen
    content-class="fullscreen-dialog"
  >
    <StudyActivityForm @close="closeForm" @added="onStudyActivitiesUpdated" />
  </v-dialog>
  <v-dialog v-model="showActivityEditForm" max-width="800px">
    <StudyActivityEditForm
      :study-activity="selectedStudyActivity"
      @close="closeEditForm"
      @updated="onStudyActivitiesUpdated"
    />
  </v-dialog>
  <v-dialog v-model="showDraftedActivityEditForm" max-width="800px">
    <StudyDraftedActivityEditForm
      :study-activity="selectedStudyActivity"
      @close="closeEditForm"
      @updated="onStudyActivitiesUpdated"
    />
  </v-dialog>
  <v-dialog
    v-model="showHistory"
    persistent
    :fullscreen="$globals.historyDialogFullscreen"
    @keydown.esc="closeHistory"
  >
    <HistoryTable
      :title="activityHistoryTitle"
      :headers="headers"
      :items="activityHistoryItems"
      :items-total="activityHistoryItems.length"
      @close="closeHistory"
    />
  </v-dialog>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  <StudyActivityBatchEditForm
    :open="showBatchEditForm"
    :selection="currentSelection"
    @updated="onStudyActivitiesUpdated"
    @close="closeBatchEditForm"
    @remove="unselectItem"
  />
</template>

<script setup>
import study from '@/api/study'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import filteringParameters from '@/utils/filteringParameters'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StudyActivityBatchEditForm from './StudyActivityBatchEditForm.vue'
import StudyActivityEditForm from './StudyActivityEditForm.vue'
import StudyDraftedActivityEditForm from './StudyDraftedActivityEditForm.vue'
import StudyActivityForm from './StudyActivityForm.vue'
import libConstants from '@/constants/libraries'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudyActivitiesStore } from '@/stores/studies-activities'
import { computed, inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const eventBusEmit = inject('eventBusEmit')
const roles = inject('roles')
const studiesGeneralStore = useStudiesGeneralStore()
const activitiesStore = useStudyActivitiesStore()
const accessGuard = useAccessGuard()
const table = ref()
const confirm = ref()
const studyActivities = ref([])
const actions = [
  {
    label: t('StudyActivityTable.remove_and_info'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: (item) =>
      !studiesGeneralStore.selectedStudyVersion && checkIfRejected(item),
    click: showRejectingInfo,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('StudyActivityTable.update_activity_version'),
    icon: 'mdi-update',
    condition: (item) =>
      item.latest_activity && !item.latest_activity.is_request_rejected,
    click: updateToLatest,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: (item) =>
      !studiesGeneralStore.selectedStudyVersion &&
      !checkIfRejected(item) &&
      checkIfActivityRequestIsEditable(item),
    click: editStudyActivity,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: (item) =>
      !studiesGeneralStore.selectedStudyVersion &&
      !checkIfRejected(item) &&
      !checkIfActivityRequestIsEditable(item),
    click: editStudyDraftedActivity,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('StudyActivityTable.remove_activity'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    click: deleteStudyActivity,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openHistory,
  },
]
const activityHistoryItems = ref([])
const currentSelection = ref([])
const selectedStudyActivity = ref(null)
const showActivityEditForm = ref(false)
const showDraftedActivityEditForm = ref(false)
const showActivityForm = ref(false)
const showBatchEditForm = ref(false)
const showHistory = ref(false)
const headers = [
  { title: '', key: 'actions', width: '1%' },
  { title: t('_global.library'), key: 'activity.library_name' },
  {
    title: t('StudyActivity.flowchart_group'),
    key: 'study_soa_group.soa_group_term_name',
  },
  {
    title: t('StudyActivity.activity_group'),
    key: 'study_activity_group.activity_group_name',
    exludeFromHeader: ['activity.is_data_collected'],
  },
  {
    title: t('StudyActivity.activity_sub_group'),
    key: 'study_activity_subgroup.activity_subgroup_name',
    exludeFromHeader: ['activity.is_data_collected'],
  },
  { title: t('StudyActivity.activity'), key: 'activity.name' },
  {
    title: t('StudyActivity.data_collection'),
    key: 'activity.is_data_collected',
  },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.modified_by'), key: 'author_username' },
]
const total = ref(0)

const exportDataUrl = computed(() => {
  return `studies/${studiesGeneralStore.selectedStudy.uid}/study-activities`
})
const activityHistoryTitle = computed(() => {
  if (selectedStudyActivity.value) {
    return t('StudyActivityTable.study_activity_history_title', {
      studyActivityUid: selectedStudyActivity.value.study_activity_uid,
    })
  }
  return ''
})

function checkIfActivityRequestIsEditable(activity) {
  if (activity.activity.library_name === 'Requested') {
    return activity.activity.is_request_final
  }
  return true
}

function checkIfRejected(activity) {
  if (
    activity.latest_activity &&
    activity.latest_activity.is_request_rejected
  ) {
    return true
  }
  return false
}

async function showRejectingInfo(item) {
  const options = {
    type: 'info',
    width: 600,
    agreeLabel: t('_global.accept'),
  }
  const msg = `${t('StudyActivityTable.rejected_activity_info_part_1')}
    <p style="color:orange;"><b>${item.latest_activity.name}</b></p> ${t('StudyActivityTable.rejected_activity_info_part_2')}
    <p style="color:orange;"><b>${item.latest_activity.reason_for_rejecting}.</b></p>${t('StudyActivityTable.rejected_activity_info_part_3')}
    <b style="color:orange;">${item.latest_activity.contact_person.toUpperCase()}</b>${t('StudyActivityTable.rejected_activity_info_part_4')}`
  if (await confirm.value.open(msg, options)) {
    study
      .deleteStudyActivity(
        studiesGeneralStore.selectedStudy.uid,
        item.study_activity_uid
      )
      .then(() => {
        table.value.filterTable()
        eventBusEmit('notification', {
          type: 'success',
          msg: t('StudyActivityTable.delete_success'),
        })
      })
  }
}

function getActionsForItem(item) {
  const result = [...actions]
  if (item.activity.replaced_by_activity) {
    result.unshift({
      label: t('StudyActivityTable.update_activity_request'),
      icon: 'mdi-bell-outline',
      iconColor: 'red',
      click: updateActivityRequest,
    })
  }
  return result
}

function updateToLatest(item) {
  study
    .updateToLatestActivityVersion(
      studiesGeneralStore.selectedStudy.uid,
      item.study_activity_uid
    )
    .then(() => {
      eventBusEmit('notification', {
        type: 'success',
        msg: t('StudyActivityTable.update_success'),
      })
      table.value.filterTable()
    })
}

function actionsMenuBadge(item) {
  if (item.activity.replaced_by_activity || item.latest_activity) {
    return {
      color: 'error',
      icon: 'mdi-exclamation',
    }
  }
  return undefined
}

function closeForm() {
  showActivityForm.value = false
}

function closeEditForm() {
  showActivityEditForm.value = false
  showDraftedActivityEditForm.value = false
  selectedStudyActivity.value = null
}

async function deleteStudyActivity(sa) {
  const options = { type: 'warning' }
  const activity = sa.activity.name
  const msg =
    !sa.show_activity_group_in_protocol_flowchart ||
    !sa.show_activity_subgroup_in_protocol_flowchart
      ? t('StudyActivityTable.confirm_delete_side_effect')
      : t('StudyActivityTable.confirm_delete', { activity })
  if (await confirm.value.open(msg, options)) {
    study
      .deleteStudyActivity(
        studiesGeneralStore.selectedStudy.uid,
        sa.study_activity_uid
      )
      .then(() => {
        table.value.filterTable()
        eventBusEmit('notification', {
          type: 'success',
          msg: t('StudyActivityTable.delete_success'),
        })
      })
  }
}

function editStudyActivity(sa) {
  selectedStudyActivity.value = sa
  showActivityEditForm.value = true
}

function editStudyDraftedActivity(sa) {
  selectedStudyActivity.value = sa
  showDraftedActivityEditForm.value = true
}

function updateActivityRequest(sa) {
  study
    .updateToApprovedActivity(
      studiesGeneralStore.selectedStudy.uid,
      sa.study_activity_uid
    )
    .then(() => {
      eventBusEmit('notification', {
        type: 'success',
        msg: t('StudyActivityTable.update_success'),
      })
      table.value.filterTable()
    })
}

async function openHistory(sa) {
  selectedStudyActivity.value = sa
  const resp = await study.getStudyActivityAuditTrail(
    studiesGeneralStore.selectedStudy.uid,
    sa.study_activity_uid
  )
  activityHistoryItems.value = resp.data
  showHistory.value = true
}

function closeHistory() {
  selectedStudyActivity.value = null
  showHistory.value = false
}

async function getStudyActivities(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  if (filters && filters !== undefined && filters !== '{}') {
    const filtersObj = JSON.parse(filters)
    if (filtersObj['study_activity_group.activity_group_name']) {
      params.activity_group_names = []
      filtersObj['study_activity_group.activity_group_name'].v.forEach(
        (value) => {
          params.activity_group_names.push(value)
        }
      )
      delete filtersObj['study_activity_group.activity_group_name']
    }
    if (filtersObj['study_activity_subgroup.activity_subgroup_name']) {
      params.activity_subgroup_names = []
      filtersObj['study_activity_subgroup.activity_subgroup_name'].v.forEach(
        (value) => {
          params.activity_subgroup_names.push(value)
        }
      )
      delete filtersObj['study_activity_subgroup.activity_subgroup_name']
    }
    if (filtersObj.name) {
      params.activity_names = []
      filtersObj.name.v.forEach((value) => {
        params.activity_names.push(value)
      })
      delete filtersObj.name
    }
    if (Object.keys(filtersObj).length) {
      params.filters = JSON.stringify(filtersObj)
    } else {
      delete params.filters
    }
  }
  params.studyUid = studiesGeneralStore.selectedStudy.uid
  const resp = await activitiesStore.fetchStudyActivities(params)
  studyActivities.value = resp.data.items
  total.value = resp.data.total
}

function modifyFilters(jsonFilter, params) {
  if (jsonFilter['study_activity_group.activity_group_name']) {
    params.activity_group_names = []
    jsonFilter['study_activity_group.activity_group_name'].v.forEach(
      (value) => {
        params.activity_group_names.push(value)
      }
    )
    delete jsonFilter['study_activity_group.activity_group_name']
  }
  if (jsonFilter['study_activity_subgroup.activity_subgroup_name']) {
    params.activity_subgroup_names = []
    jsonFilter['study_activity_subgroup.activity_subgroup_name'].v.forEach(
      (value) => {
        params.activity_subgroup_names.push(value)
      }
    )
    delete jsonFilter['study_activity_subgroup.activity_subgroup_name']
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

function openBatchEditForm(selection) {
  if (!selection.length) {
    eventBusEmit('notification', {
      type: 'warning',
      msg: t('StudyActivityTable.batch_edit_no_selection'),
    })
    return
  }
  currentSelection.value = selection
  showBatchEditForm.value = true
}

function closeBatchEditForm() {
  currentSelection.value = []
  showBatchEditForm.value = false
}

function onStudyActivitiesUpdated() {
  table.value.filterTable()
}

function unselectItem(item) {
  currentSelection.value = currentSelection.value.filter(
    (sa) => sa.study_activity_uid !== item.study_activity_uid
  )
}

async function fetchActivitiesHistory() {
  const resp = await study.getStudyActivitiesAuditTrail(
    studiesGeneralStore.selectedStudy.uid
  )
  return resp.data
}

function getItemRowClass(item) {
  return item.activity.library_name === libConstants.LIBRARY_REQUESTED
    ? item.activity.is_request_final
      ? 'yellow'
      : 'bg-warning'
    : ''
}
</script>

<style scoped>
tbody tr td {
  border-left-style: outset;
  border-bottom-style: outset;
  border-width: 1px !important;
  border-color: rgb(var(--v-theme-nnFadedBlue200)) !important;
}
</style>
