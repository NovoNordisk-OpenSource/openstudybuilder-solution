<template>
  <div>
    <NNTable
      ref="table"
      table-id="studies-arms-table"
      :headers="headers"
      item-value="arm_uid"
      :items-length="total"
      :items="arms"
      :column-data-resource="`studies/${studiesGeneralStore.selectedStudy.uid}/study-arms`"
      disable-filtering
      :hide-default-body="sortMode && arms.length > 0"
      :loading="loading"
      :history-config="{
        dataFetcher: fetchArmsHistory,
        title: $t('StudyArmsTable.global_history_title'),
      }"
      :export-config="{ objectLabel: 'StudyArms', dataUrl: exportDataUrl }"
      @filter="fetchStudyArms"
    >
      <template #afterSwitches>
        <div :title="$t('NNTableTooltips.reorder_content')">
          <v-switch
            v-model="sortMode"
            :label="$t('NNTable.reorder_content')"
            hide-details
            class="mr-6"
            :disabled="!accessGuard.checkPermission($roles.STUDY_WRITE)"
          />
        </div>
      </template>
      <template #tbody>
        <tbody v-show="sortMode" ref="parent">
          <tr v-for="arm in arms" :key="arm.arm_uid">
            <td>
              <v-icon size="small"> mdi-sort </v-icon>
            </td>
            <td>{{ arm.order }}</td>
            <td>{{ arm.arm_type?.term_name }}</td>
            <td>{{ arm.name }}</td>
            <td>{{ arm.short_name }}</td>
            <td>{{ arm.number_of_subjects }}</td>
            <td>{{ arm.randomization_group }}</td>
            <td>{{ arm.code }}</td>
            <td>{{ arm.arm_connected_branch_arms?.length }}</td>
            <td>{{ arm.description }}</td>
            <td>{{ $filters.date(arm.start_date) }}</td>
            <td>{{ arm.author_username }}</td>
          </tr>
        </tbody>
      </template>
      <template #[`item.name`]="{ item }">
        <router-link
          :to="{
            name: 'StudyArmOverview',
            params: {
              study_id: studiesGeneralStore.selectedStudy.uid,
              id: item.arm_uid,
            },
          }"
        >
          {{ item.name }}
        </router-link>
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
      <template #[`item.arm_connected_branch_arms`]="{ item }">
        {{ item.arm_connected_branch_arms?.length }}
      </template>
      <template #[`item.arm_type.term_name`]="{ item }">
        <CTCodelistTermDisplay :term="item.arm_type" />
      </template>
      <template #[`item.actions`]="{ item }">
        <ActionsMenu :actions="actions" :item="item" />
      </template>
      <template #actions="">
        <v-btn
          class="ml-2"
          icon
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          :disabled="
            !accessGuard.checkPermission($roles.STUDY_WRITE) ||
            studiesGeneralStore.selectedStudyVersion !== null
          "
          @click.stop="showCohortsStepper = true"
          @close="showCohortsStepper = false"
        >
          <v-icon left>{{
            editStepper ? 'mdi-pencil-outline' : 'mdi-plus'
          }}</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('StudyArmsTable.create_arm') }}
          </v-tooltip>
        </v-btn>
      </template>
    </NNTable>
    <v-dialog
      v-model="showCohortsStepper"
      persistent
      fullscreen
      content-class="fullscreen-dialog"
    >
      <CohortsStepper
        :design-class="designClass"
        :initial-step="cohortsStepperInitialStep"
        @close="closeCohortStepper"
      />
    </v-dialog>
    <StudyArmsForm
      :open="showArmsForm"
      :edited-arm="armToEdit"
      @close="closeForm"
    />
    <v-dialog
      v-model="showArmHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeArmHistory"
    >
      <HistoryTable
        :title="studyArmHistoryTitle"
        :headers="headers"
        :items="armHistoryItems"
        :items-total="armHistoryItems.length"
        @close="closeArmHistory"
      />
    </v-dialog>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  </div>
</template>

<script setup>
import NNTable from '@/components/tools/NNTable.vue'
import armsApi from '@/api/arms'
import CTCodelistTermDisplay from '../tools/CTCodelistTermDisplay.vue'
import cohortsApi from '@/api/cohorts'
import StudyArmsForm from '@/components/studies/StudyArmsForm.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import filteringParameters from '@/utils/filteringParameters'
import studyEpochs from '@/api/studyEpochs'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import CohortsStepper from './CohortsStepper.vue'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { computed, inject, ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDragAndDrop } from '@formkit/drag-and-drop/vue'
import cohortConstants from '@/constants/cohorts'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const roles = inject('roles')
const studiesGeneralStore = useStudiesGeneralStore()
const accessGuard = useAccessGuard()
const table = ref()
const confirm = ref()

const [parent, arms] = useDragAndDrop([], {
  onDragend: (event) => {
    const newOrder =
      event.draggedNode.data.value.order -
      (event.state.initialIndex - event.state.targetIndex)
    changeOrder(event.draggedNode.data.value.arm_uid, newOrder)
  },
})

onMounted(() => {
  cohortsApi
    .checkDesignClassEditable(studiesGeneralStore.selectedStudy.uid)
    .then((resp) => {
      editStepper.value = !resp.data
    })
  cohortsApi
    .getStudyDesignClass(studiesGeneralStore.selectedStudy.uid)
    .then((resp) => {
      designClass.value = resp.data.value
    })
    .catch((error) => {
      if (error.response.status === 404) {
        console.error(error)
      }
    })
})

const headers = [
  { title: '', key: 'actions', width: '1%' },
  { title: '#', key: 'order', width: '5%' },
  {
    title: t('StudyArmsTable.type'),
    key: 'arm_type.term_name',
    width: '7%',
  },
  { title: t('StudyArmsTable.name'), key: 'name' },
  { title: t('StudyArmsTable.label'), key: 'label' },
  { title: t('StudyArmsTable.short_name'), key: 'short_name' },
  {
    title: t('StudyArmsTable.number_of_participants'),
    key: 'number_of_subjects',
  },
  {
    title: t('StudyArmsTable.randomisation_group'),
    key: 'randomization_group',
  },
  { title: t('StudyArmsTable.code'), key: 'code' },
  {
    title: t('StudyArmsTable.connected_branches'),
    key: 'arm_connected_branch_arms',
  },
  { title: t('StudyArmsTable.description'), key: 'description' },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.modified_by'), key: 'author_username' },
]
const actions = [
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    click: editArm,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    click: deleteArm,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openArmHistory,
  },
]
const total = ref(0)
const showArmsForm = ref(false)
const armToEdit = ref({})
const showArmHistory = ref(false)
const armHistoryItems = ref([])
const selectedArm = ref(null)
const sortMode = ref(false)
const showCohortsStepper = ref(false)
const loading = ref(false)
const designClass = ref('')
const editStepper = ref(false)

const exportDataUrl = computed(() => {
  return `studies/${studiesGeneralStore.selectedStudy.uid}/study-arms`
})

const studyArmHistoryTitle = computed(() => {
  if (selectedArm.value) {
    return t('StudyArmsTable.study_arm_history_title', {
      armUid: selectedArm.value.arm_uid,
    })
  }
  return ''
})

// The creation-mode step (incl. "copy from another study") stays reachable
// once arms already exist as long as the design class is still MANUAL,
// since that mode only ever appends more arms without touching cohorts.
// Once the design is FULL, jump straight past it to avoid re-exposing a
// path that would try to downgrade a cohorts-bearing study to MANUAL.
const cohortsStepperInitialStep = computed(() => {
  if (!editStepper.value || designClass.value === cohortConstants.MANUAL) {
    return 1
  }
  return 2
})

async function fetchArmsHistory() {
  const resp = await studyEpochs.getStudyArmsVersions(
    studiesGeneralStore.selectedStudy.uid
  )
  return resp.data
}

function fetchStudyArms(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  params.study_uid = studiesGeneralStore.selectedStudy.uid
  armsApi
    .getAllForStudy(studiesGeneralStore.selectedStudy.uid, { params })
    .then((resp) => {
      arms.value = resp.data.items
      total.value = resp.data.total
    })
}

function closeCohortStepper() {
  showCohortsStepper.value = false
  cohortsApi
    .checkDesignClassEditable(studiesGeneralStore.selectedStudy.uid)
    .then((resp) => {
      editStepper.value = !resp.data
    })
  cohortsApi
    .getStudyDesignClass(studiesGeneralStore.selectedStudy.uid)
    .then((resp) => {
      designClass.value = resp.data.value
    })
    .catch((error) => {
      if (error.response.status === 404) {
        console.error(error)
      }
    })
  table.value.filterTable()
}

function closeForm() {
  armToEdit.value = {}
  showArmsForm.value = false
  table.value.filterTable()
}

function editArm(item) {
  if (designClass.value === cohortConstants.MANUAL) {
    armToEdit.value = item
    showArmsForm.value = true
  } else {
    showCohortsStepper.value = true
  }
}

async function openArmHistory(arm) {
  selectedArm.value = arm
  const resp = await studyEpochs.getStudyArmVersions(
    studiesGeneralStore.selectedStudy.uid,
    arm.arm_uid
  )
  armHistoryItems.value = resp.data
  showArmHistory.value = true
}

function closeArmHistory() {
  showArmHistory.value = false
  selectedArm.value = null
}

async function deleteArm(item) {
  loading.value = true
  let relatedItems = 0
  await armsApi
    .getAllBranchesForArm(studiesGeneralStore.selectedStudy.uid, item.arm_uid)
    .then((resp) => {
      relatedItems += resp.data.length
    })
  await armsApi
    .getAllCohortsForArm(studiesGeneralStore.selectedStudy.uid, item.arm_uid)
    .then((resp) => {
      relatedItems += resp.data.items.length
    })
  await armsApi
    .getAllCellsForArm(studiesGeneralStore.selectedStudy.uid, item.arm_uid)
    .then((resp) => {
      relatedItems += resp.data.length
    })
  const options = {
    type: 'warning',
    cancelLabel: t('_global.cancel'),
    agreeLabel: t('_global.continue'),
  }
  if (relatedItems === 0) {
    armsApi
      .delete(studiesGeneralStore.selectedStudy.uid, item.arm_uid)
      .then(() => {
        notificationHub.add({
          msg: t('StudyArmsTable.arm_deleted'),
        })
        table.value.filterTable()
      })
  } else if (
    await confirm.value.open(
      t('StudyArmsTable.arm_delete_notification'),
      options
    )
  ) {
    armsApi
      .delete(studiesGeneralStore.selectedStudy.uid, item.arm_uid)
      .then(() => {
        notificationHub.add({
          msg: t('StudyArmsTable.arm_deleted'),
        })
        table.value.filterTable()
      })
  }
  loading.value = false
}

function changeOrder(armUid, newOrder) {
  armsApi
    .updateArmOrder(studiesGeneralStore.selectedStudy.uid, armUid, newOrder)
    .then(() => {
      table.value.filterTable()
    })
    .catch(() => {
      table.value.filterTable()
    })
}
</script>

<style scoped lang="scss">
table {
  width: max-content;
  text-align: left;
  border-spacing: 0px;
  border-collapse: collapse;
}
thead {
  background-color: #e5e5e5;
  color: rgba(26, 26, 26, 0.6);
}
tr {
  &.section {
    background-color: #e5e5e5;
  }
}
tbody tr {
  border-bottom: 1px solid #e5e5e5;
}
tbody tr td {
  border-left-style: outset;
  border-bottom-style: outset;
  border-width: 1px !important;
  border-color: rgb(var(--v-theme-nnFadedBlue200)) !important;
}
th {
  background-color: #e5e5e5;
  padding: 6px;
  font-size: 14px !important;
}
</style>
