<template>
  <div class="d-flex flex-column align-center mb-4 mt-4">
    <v-btn-toggle
      v-model="selectedStatusTab"
      mandatory
      density="compact"
      color="nnBaseBlue"
      divided
      variant="outlined"
      class="layoutSelector justify-center mr-12 text-body-medium flex-shrink-0"
      @update:model-value="onStatusTabChange"
    >
      <v-btn v-for="tab in statusTabs" :key="tab.value" :value="tab.value">
        <v-icon v-if="tab.icon" :color="tab.color">{{ tab.icon }}</v-icon>
        {{ tab.label }}
      </v-btn>
    </v-btn-toggle>
  </div>
  <NNTable
    key="studyActivityTable"
    ref="table"
    table-id="studies-activities-table"
    :headers="headers"
    :items="studyActivities"
    :items-length="total"
    item-value="study_activity_uid"
    :column-data-resource="`studies/${studiesGeneralStore.selectedStudy.uid}/study-activities`"
    :extra-item-class="getItemRowClass"
    :filters-modify-function="modifyFilters"
    :initial-sort-by="[{ key: 'activity.name', order: 'asc' }]"
    :history-config="{
      dataFetcher: fetchActivitiesHistory,
      title: $t('StudyActivityTable.global_history_title'),
    }"
    :export-config="{ objectLabel: 'StudyActivities', dataUrl: exportDataUrl }"
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
        variant="outlined"
        rounded="xl"
        prepend-icon="mdi-exclamation"
        color="nnBaseBlue"
        class="text-body-medium"
        :disabled="
          !accessGuard.checkPermission($roles.STUDY_WRITE) ||
          studiesGeneralStore.selectedStudyVersion !== null
        "
        @click="openBatchUpdateForm()"
      >
        {{ $t('StudyActivityTable.review_activities') }}
      </v-btn>
      <v-btn
        v-if="slot.showSelectBoxes"
        color="primary"
        class="ml-2"
        icon
        size="small"
        :disabled="
          !accessGuard.checkPermission($roles.STUDY_WRITE) ||
          studiesGeneralStore.selectedStudyVersion !== null
        "
        @click="openBatchEditForm(slot.selected)"
      >
        <v-icon>mdi-pencil-box-multiple-outline</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ $t('StudyActivityTable.edit_activity_selection') }}
        </v-tooltip>
      </v-btn>
      <v-btn
        class="ml-2"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        data-cy="add-study-activity"
        :disabled="
          !accessGuard.checkPermission($roles.STUDY_WRITE) ||
          studiesGeneralStore.selectedStudyVersion !== null
        "
        @click.stop="showActivityForm = true"
      >
        <v-icon>mdi-plus</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ $t('StudyActivityForm.add_title') }}
        </v-tooltip>
      </v-btn>
    </template>
    <template #[`item.actions`]="{ item }">
      <div class="d-flex align-center">
        <ActionsMenu
          :actions="getActionsForItem(item)"
          :item="item"
          :badge="actionsMenuBadge(item)"
        />
        <template
          v-for="(comment, idx) in [getActivityComment(item)]"
          :key="idx"
        >
          <span v-if="comment">
            <v-icon
              size="small"
              :color="comment.active ? 'blue' : 'green'"
              style="cursor: pointer"
              @click="showCommentsForActivity(item)"
              >{{
                comment.active
                  ? 'mdi-comment-text-outline'
                  : 'mdi-comment-check-outline'
              }}</v-icon
            >
            <v-tooltip activator="parent" location="top">
              {{
                comment.active
                  ? $t('Comments.active_comments')
                  : $t('Comments.no_active_comments')
              }}
            </v-tooltip>
          </span>
        </template>
      </div>
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
      <v-tooltip location="top">
        <template #activator="{ props }">
          <span v-bind="props">{{
            $filters.dateRelative(item.start_date)
          }}</span>
        </template>
        {{ $filters.date(item.start_date) }}
      </v-tooltip>
    </template>
  </NNTable>
  <v-dialog
    v-model="showActivityForm"
    persistent
    fullscreen
    content-class="fullscreen-dialog"
  >
    <StudyActivityForm
      :exchange-mode="exchangeActivityMode"
      :exchange-activity-uid="selectedStudyActivity?.study_activity_uid"
      @close="closeForm"
      @added="onStudyActivitiesUpdated"
    />
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
  <UpdateActivityRequestForm
    :activity="selectedStudyActivity"
    :open="showRequestUpdateForm"
    @close="closeUpdateForm"
  />
  <UpdateActivityForm
    :activity="selectedStudyActivity"
    :open="showUpdateForm"
    @close="closeUpdateForm"
  />
  <v-dialog
    v-model="showBatchUpdateForm"
    fullscreen
    content-class="fullscreen-dialog"
  >
    <BatchUpdateActivityForm @close="closeBatchUpdateForm" />
  </v-dialog>
  <v-dialog v-model="showComments" max-width="1000px">
    <CommentThreadDialog
      :title="selectedStudyActivity.activity.name"
      :item-type="t('StudyActivityTable.study_activity')"
      :topic-path="`studies/${studiesGeneralStore.selectedStudy.uid}/study-activities/${selectedStudyActivity.study_activity_uid}`"
      @close="closeCommentsDialog()"
    />
  </v-dialog>
</template>

<script setup>
import study from '@/api/study'
import activities from '@/api/activities'
import comments from '@/api/comments'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import filteringParameters from '@/utils/filteringParameters'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StudyActivityBatchEditForm from './StudyActivityBatchEditForm.vue'
import StudyActivityEditForm from './StudyActivityEditForm.vue'
import StudyDraftedActivityEditForm from './StudyDraftedActivityEditForm.vue'
import StudyActivityForm from './StudyActivityForm.vue'
import UpdateActivityRequestForm from './UpdateActivityRequestForm.vue'
import UpdateActivityForm from './UpdateActivityForm.vue'
import BatchUpdateActivityForm from './BatchUpdateActivityForm.vue'
import CommentThreadDialog from '@/components/tools/CommentThreadDialog.vue'
import libConstants from '@/constants/libraries'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudyActivitiesStore } from '@/stores/studies-activities'
import { computed, inject, ref, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { escapeHTML } from '@/utils/sanitize'
import _isEmpty from 'lodash/isEmpty'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
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
      item.is_activity_updated &&
      !item.latest_activity.is_request_rejected &&
      !item.activity.replaced_by_activity,
    click: openUpdateForm,
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
    label: t('DetailedFlowchart.exchange_activity'),
    icon: 'mdi-autorenew',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    click: exchangeStudyActivity,
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
  {
    label: t('_global.comments'),
    icon: 'mdi-comment-text-outline',
    click: showCommentsForActivity,
  },
]
const activityHistoryItems = ref([])
const currentSelection = ref([])
const selectedStudyActivity = ref(null)
const showActivityEditForm = ref(false)
const showDraftedActivityEditForm = ref(false)
const showActivityForm = ref(false)
const showBatchEditForm = ref(false)
const showRequestUpdateForm = ref(false)
const showUpdateForm = ref(false)
const showBatchUpdateForm = ref(false)
const showHistory = ref(false)
const selectedStatusTab = ref('all')
const statusTabs = [
  { value: 'all', label: t('_global.all') },
  { value: 'updated', icon: 'mdi-alert-circle-outline', color: 'error' },
  { value: 'reviewed', icon: 'mdi-alert-outline', color: 'warning' },
  { value: 'commented', icon: 'mdi-comment-text-outline', color: 'blue' },
]
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
const exchangeActivityMode = ref(false)
const showComments = ref(false)
const commentedActivityUids = ref([])

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

const props = defineProps({
  update: {
    type: Number,
    default: null,
  },
})

watch(
  () => props.update,
  () => {
    checkIfFormOpen()
  }
)

onMounted(() => {
  checkIfFormOpen()
  getCommentedActivities()
})

function showCommentsForActivity(item) {
  selectedStudyActivity.value = item
  showComments.value = true
}

function closeCommentsDialog() {
  selectedStudyActivity.value = null
  showComments.value = false
  getCommentedActivities()
}

function getActivityComment(item) {
  return commentedActivityUids.value.find(
    (c) => c.uid === item.study_activity_uid
  )
}

async function getCommentedActivities() {
  await comments
    .getTopics(
      `studies/${studiesGeneralStore.selectedStudy.uid}/study-activities`
    )
    .then((resp) => {
      const topics = resp
      commentedActivityUids.value = topics.map((topic) => {
        const parts = topic.topic_path.split('/')
        return {
          uid: parts[parts.length - 1],
          active: topic.threads_active_count > 0,
        }
      })
    })
}

function onStatusTabChange() {
  if (table.value) {
    table.value.filterTable()
  }
}

function checkIfFormOpen() {
  if (localStorage.getItem('open-form')) {
    showActivityForm.value = true
    localStorage.removeItem('open-form')
  }
}

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
  const messageHtml = `${t('StudyActivityTable.rejected_activity_info_part_1')}
    <p style="color:orange;"><b>${escapeHTML(item.latest_activity.name)}</b></p> ${t('StudyActivityTable.rejected_activity_info_part_2')}
    <p style="color:orange;"><b>${escapeHTML(item.latest_activity.reason_for_rejecting)}.</b></p>${t('StudyActivityTable.rejected_activity_info_part_3')}
    <b style="color:orange;">${escapeHTML(item.latest_activity.contact_person.toUpperCase())}</b>${t('StudyActivityTable.rejected_activity_info_part_4')}`
  if (await confirm.value.openHtml(messageHtml, options)) {
    study
      .deleteStudyActivity(
        studiesGeneralStore.selectedStudy.uid,
        item.study_activity_uid
      )
      .then(() => {
        table.value.filterTable()
        notificationHub.add({
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
      iconColor: item.keep_old_version ? 'green' : 'red',
      click: updateActivityRequest,
    })
  }
  return result
}

function exchangeStudyActivity(item) {
  exchangeActivityMode.value = true
  selectedStudyActivity.value = item
  showActivityForm.value = true
}

function openUpdateForm(item) {
  selectedStudyActivity.value = item
  if (item.activity.library_name === 'Sponsor') {
    showUpdateForm.value = true
  } else {
    showRequestUpdateForm.value = true
  }
}

function closeUpdateForm() {
  selectedStudyActivity.value = null
  showRequestUpdateForm.value = false
  showUpdateForm.value = false
  table.value.filterTable()
}

function openBatchUpdateForm() {
  showBatchUpdateForm.value = true
}

function closeBatchUpdateForm() {
  showBatchUpdateForm.value = false
  table.value.filterTable()
}

function actionsMenuBadge(item) {
  if (
    item.activity.replaced_by_activity ||
    item.is_activity_updated ||
    item.latest_activity?.is_request_rejected
  ) {
    return {
      color: item.keep_old_version ? 'warning' : 'error',
      icon: item.keep_old_version
        ? 'mdi-alert-outline'
        : 'mdi-alert-circle-outline',
    }
  }
  return undefined
}

function closeForm() {
  showActivityForm.value = false
  exchangeActivityMode.value = false
  selectedStudyActivity.value = null
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
        notificationHub.add({
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
  activities
    .getObject('activities', sa.activity.replaced_by_activity)
    .then((resp) => {
      sa.latest_activity = resp.data
      selectedStudyActivity.value = sa
      showRequestUpdateForm.value = true
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
  let statusFilter = {}
  if (selectedStatusTab.value === 'reviewed') {
    statusFilter = { keep_old_version: { v: [true] } }
  } else if (selectedStatusTab.value === 'updated') {
    statusFilter = {
      is_activity_updated: { v: [true] },
      keep_old_version: { v: [false] },
    }
  }

  if (selectedStatusTab.value === 'commented') {
    statusFilter = {
      study_activity_uid: { v: commentedActivityUids.value.map((c) => c.uid) },
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
    notificationHub.add({
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

defineExpose({
  onStudyActivitiesUpdated,
})
</script>

<style scoped>
tbody tr td {
  border-left-style: outset;
  border-bottom-style: outset;
  border-width: 1px !important;
  border-color: rgb(var(--v-theme-nnFadedBlue200)) !important;
}

.layoutSelector {
  border-color: rgb(var(--v-theme-nnBaseBlue));
}

.layoutSelector :deep(.v-btn) {
  text-transform: none;
}
</style>
