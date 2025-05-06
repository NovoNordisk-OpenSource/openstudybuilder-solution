<template>
  <NNTable
    key="studyActivityInstancesTable"
    ref="tableRef"
    export-object-label="ActivityInstances"
    :headers="headers"
    :items="studyActivitiesInstances"
    :items-length="total"
    item-value="activity_instance.uid"
    :export-data-url="exportDataUrl"
    :column-data-resource="`studies/${studiesGeneralStore.selectedStudy.uid}/study-activity-instances`"
    :history-data-fetcher="fetchStudyActivityInstancesHistory"
    :history-title="$t('StudyActivityTable.global_history_title')"
    :filters-modify-function="modifyFilters"
    :default-filters="defaultFilters"
    @filter="getStudyActivityInstances"
  >
    <template #[`item.actions`]="{ item }">
      <ActionsMenu
        :actions="actions"
        :item="item"
        :badge="actionsMenuBadge(item)"
      />
    </template>
    <template #[`footer.prepend`]>
      <v-chip
        class="instanceAvailable"
        variant="flat"
        :text="$t('StudyActivityInstances.no_action_needed')"
      />
      <v-chip
        class="ml-2 suggestion"
        variant="flat"
        :text="$t('StudyActivityInstances.notification')"
      />
      <v-chip
        class="ml-2 noInstance"
        variant="flat"
        :text="$t('StudyActivityInstances.action_needed')"
      />
      <v-chip
        class="ml-2 na"
        variant="flat"
        :text="$t('StudyActivityInstances.na')"
      />
      <v-spacer />
    </template>
    <template #[`item.activity_instance.name`]="{ item }">
      <div
        :class="getInstanceCssClass(item)"
        @click="
          item.activity_instance
            ? redirectToActivityInstance(item.activity_instance.uid)
            : editRelationship(item)
        "
      >
        {{
          item.activity_instance
            ? item.activity_instance.name
            : item.activity.is_data_collected
              ? $t('StudyActivityInstances.add_instance')
              : $t('StudyActivityInstances.na')
        }}
      </div>
    </template>
    <template #[`item.activity.is_data_collected`]="{ item }">
      {{ $filters.yesno(item.activity.is_data_collected) }}
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
  <ConfirmDialog ref="confirmRef" :text-cols="6" :action-cols="5" />
</template>
<script setup>
import { computed, onMounted, inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudyActivitiesStore } from '@/stores/studies-activities'
import study from '@/api/study'
import filteringParameters from '@/utils/filteringParameters'
import NNTable from '@/components/tools/NNTable.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import StudyActivityInstancesEditForm from './StudyActivityInstancesEditForm.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import statuses from '@/constants/statuses'
import { useRouter } from 'vue-router'

const { t } = useI18n()
const eventBusEmit = inject('eventBusEmit')
const studiesGeneralStore = useStudiesGeneralStore()
const activitiesStore = useStudyActivitiesStore()
const roles = inject('roles')
const tableRef = ref()
const confirmRef = ref()
const router = useRouter()

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
  { title: t('StudyActivityInstances.state_actions'), key: 'state' },
  {
    title: t('StudyActivityInstances.adam_code'),
    key: 'activity_instance.adam_param_code',
  },
]
const defaultFilters = [
  { title: t('StudyActivity.activity'), key: 'activity.name' },
  {
    title: t('StudyActivityInstances.activity_instance'),
    key: 'activity_instance.name',
  },
  { title: t('StudyActivityInstances.state_actions'), key: 'state' },
]
const studyActivitiesInstances = ref([])
const total = ref(0)
const activeActivity = ref({})
const showEditForm = ref(false)
const activityInstanceHistoryItems = ref([])
const showHistory = ref(false)
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
    condition: (item) =>
      !studiesGeneralStore.selectedStudyVersion && item.activity_instance,
    click: deleteRelationship,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('StudyActivityInstances.update_to_new_version'),
    icon: 'mdi-update',
    iconColor: 'primary',
    condition: (item) =>
      !studiesGeneralStore.selectedStudyVersion &&
      item.latest_activity_instance,
    click: updateInstance,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openHistory,
  },
]

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

onMounted(() => {
  getStudyActivityInstances()
})

function getInstanceCssClass(item) {
  if (item.activity_instance) {
    if (item.state === statuses.SUGGESTION) {
      return 'px-1 suggestion row-pointer'
    } else {
      return 'px-1 instanceAvailable row-pointer'
    }
  }
  return !item.activity.is_data_collected
    ? 'px-1 na row-pointer'
    : 'px-1 noInstance row-pointer'
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
  params.studyUid = studiesGeneralStore.selectedStudy.uid
  activitiesStore.fetchStudyActivityInstances(params).then((resp) => {
    studyActivitiesInstances.value = resp.data.items
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

async function redirectToActivityInstance(instanceUid) {
  router.push({
    name: 'ActivityInstanceOverview',
    params: { id: instanceUid },
  })
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

async function deleteRelationship(item) {
  const options = {
    type: 'warning',
    cancelLabel: t('_global.cancel'),
    agreeLabel: t('_global.delete'),
  }
  if (
    await confirmRef.value.open(
      t('StudyActivityInstances.confirm_delete', {
        instance: item.study_activity_instance_uid,
      }),
      options
    )
  ) {
    const data = {
      activity_instance_uid: null,
      study_activity_uid: item.study_activity_uid,
      show_activity_instance_in_protocol_flowchart:
        item.show_activity_instance_in_protocol_flowchart,
    }
    activitiesStore
      .updateStudyActivityInstance(
        studiesGeneralStore.selectedStudy.uid,
        item.study_activity_instance_uid,
        data
      )
      .then(() => {
        eventBusEmit('notification', {
          msg: t('StudyActivityInstances.instance_deleted'),
          type: 'success',
        })
        tableRef.value.filterTable()
      })
  }
}

function updateInstance(item) {
  activitiesStore
    .updateStudyActivityInstanceToLatest(
      studiesGeneralStore.selectedStudy.uid,
      item.study_activity_instance_uid
    )
    .then(() => {
      eventBusEmit('notification', {
        msg: t('StudyActivityInstances.instance_updated'),
        type: 'success',
      })
      tableRef.value.filterTable()
    })
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
  if (item.latest_activity_instance) {
    return {
      color: 'error',
      icon: 'mdi-bell-outline',
    }
  }
  return undefined
}
</script>
<style scoped>
.instanceAvailable {
  background-color: darkseagreen;
  border-radius: 5px;
  color: black;
}
.noInstance {
  background-color: rgb(202, 124, 124);
  border-radius: 5px;
  color: black;
}
.suggestion {
  background-color: rgb(217, 201, 106);
  border-radius: 5px;
  color: black;
}
.na {
  background-color: rgb(179, 179, 179);
  border-radius: 5px;
  color: black;
}
.row-pointer {
  cursor: pointer;
}
</style>
