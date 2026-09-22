<template>
  <div>
    <NNTable
      ref="table"
      table-id="studies-branches-table"
      :headers="headers"
      item-value="branch_arm_uid"
      :items-length="total"
      :items="branchArms"
      :no-data-text="
        arms.length === 0 ? $t('StudyBranchArms.no_data') : undefined
      "
      disable-filtering
      :hide-default-body="sortMode && branchArms.length > 0"
      :history-config="{
        dataFetcher: fetchBranchArmsHistory,
        title: $t('StudyBranchArms.global_history_title'),
      }"
      :export-config="{ objectLabel: 'StudyBranches', dataUrl: exportDataUrl }"
      @filter="fetchStudyBranchArms"
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
      <template #actions="">
        <v-btn
          v-if="editStepper && designClass === cohortConstants.MANUAL"
          class="ml-2"
          icon
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          data-cy="add-study-branch-arm"
          :disabled="
            !accessGuard.checkPermission($roles.STUDY_WRITE) ||
            studiesGeneralStore.selectedStudyVersion !== null
          "
          @click.stop="addBranchArm"
        >
          <v-icon>mdi-plus</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('StudyBranchArms.add_branch') }}
          </v-tooltip>
        </v-btn>
        <v-btn
          v-else-if="editStepper"
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
            {{ $t('StudyBranchArms.cohorts_stepper') }}
          </v-tooltip>
        </v-btn>
      </template>
      <template #[`item.study_cohort_name`]="{ item }">
        <div v-html="sanitizeHTML(getCohortNames(item))" />
      </template>
      <template #[`item.study_cohort_code`]="{ item }">
        <div v-html="sanitizeHTML(getCohortCodes(item))" />
      </template>
      <template #tbody>
        <tbody v-show="sortMode" ref="parent">
          <tr v-for="branch in branchArms" :key="branch.branch_arm_uid">
            <td>
              <v-icon size="small"> mdi-sort </v-icon>
            </td>
            <td>{{ branch.order }}</td>
            <td>{{ branch.name }}</td>
            <td>{{ branch.short_name }}</td>
            <td>{{ branch.number_of_subjects }}</td>
            <td>{{ branch.arm_root.name }}</td>
            <td><div v-html="sanitizeHTML(getCohortNames(branch))" /></td>
            <td><div v-html="sanitizeHTML(getCohortCodes(branch))" /></td>
            <td>{{ branch.randomization_group }}</td>
            <td>{{ branch.code }}</td>
            <td>{{ $filters.date(branch.start_date) }}</td>
            <td>{{ branch.author_username }}</td>
          </tr>
        </tbody>
      </template>
      <template #[`item.name`]="{ item }">
        <router-link
          :to="{
            name: 'StudyBranchArmOverview',
            params: {
              study_id: studiesGeneralStore.selectedStudy.uid,
              id: item.branch_arm_uid,
            },
          }"
        >
          {{ item.name }}
        </router-link>
      </template>
      <template #[`item.arm_root.name`]="{ item }">
        <router-link
          :to="{
            name: 'StudyArmOverview',
            params: {
              study_id: studiesGeneralStore.selectedStudy.uid,
              id: item.arm_root.arm_uid,
            },
          }"
        >
          {{ item.arm_root.name }}
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
      <template #[`item.actions`]="{ item }">
        <ActionsMenu :actions="actions" :item="item" />
      </template>
    </NNTable>
    <v-dialog
      v-model="showBranchArmsForm"
      persistent
      fullscreen
      content-class="fullscreen-dialog"
    >
      <StudyBranchesForm
        :edited-branch-arm="branchArmToEdit"
        :arms="arms"
        @close="closeForm"
      />
    </v-dialog>
    <v-dialog
      v-model="showCohortsStepper"
      persistent
      fullscreen
      content-class="fullscreen-dialog"
    >
      <CohortsStepper
        :design-class="designClass"
        :initial-step="4"
        @close="closeCohortStepper"
      />
    </v-dialog>
    <v-dialog
      v-model="showBranchHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeBranchHistory"
    >
      <HistoryTable
        :title="studyBranchHistoryTitle"
        :headers="headers"
        :items="branchHistoryItems"
        :items-total="branchHistoryItems.length"
        @close="closeBranchHistory"
      />
    </v-dialog>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  </div>
</template>

<script setup>
import NNTable from '@/components/tools/NNTable.vue'
import armsApi from '@/api/arms'
import cohortsApi from '@/api/cohorts'
import StudyBranchesForm from '@/components/studies/StudyBranchesForm.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import studyEpochs from '@/api/studyEpochs'
import CohortsStepper from './CohortsStepper.vue'
import { useAccessGuard } from '@/composables/accessGuard'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import filteringParameters from '@/utils/filteringParameters'
import { computed, onMounted, inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDragAndDrop } from '@formkit/drag-and-drop/vue'
import { escapeHTML, sanitizeHTML } from '@/utils/sanitize'
import cohortConstants from '@/constants/cohorts'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const roles = inject('roles')
const studiesGeneralStore = useStudiesGeneralStore()
const accessGuard = useAccessGuard()
const table = ref()
const confirm = ref()

const [parent, branchArms] = useDragAndDrop([], {
  onDragend: (event) => {
    const newOrder =
      event.draggedNode.data.value.order -
      (event.state.initialIndex - event.state.targetIndex)
    changeOrder(event.draggedNode.data.value.branch_arm_uid, newOrder)
  },
})

const headers = [
  { title: '', key: 'actions', width: '1%' },
  { title: '#', key: 'order', width: '5%' },
  { title: t('StudyBranchArms.name'), key: 'name' },
  { title: t('StudyBranchArms.short_name'), key: 'short_name' },
  {
    title: t('StudyBranchArms.number_of_participants'),
    key: 'number_of_subjects',
  },
  {
    title: t('StudyBranchArms.arm_name'),
    key: 'arm_root.name',
    historyHeader: 'arm_root_uid',
  },
  {
    title: t('StudyBranchArms.cohort_name'),
    key: 'study_cohort_name',
  },
  {
    title: t('StudyBranchArms.cohort_code'),
    key: 'study_cohort_code',
  },
  {
    title: t('StudyBranchArms.randomisation_group'),
    key: 'randomization_group',
  },
  { title: t('StudyBranchArms.code'), key: 'code' },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.modified_by'), key: 'author_username' },
]
const actions = [
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    click: editBranchArm,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: () =>
      !studiesGeneralStore.selectedStudyVersion &&
      designClass.value === cohortConstants.MANUAL,
    click: deleteBranchArm,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openBranchHistory,
  },
]
const total = ref(0)
const arms = ref([])
const showBranchArmsForm = ref(false)
const branchArmToEdit = ref({})
const showBranchHistory = ref(false)
const branchHistoryItems = ref([])
const selectedBranch = ref(null)
const sortMode = ref(false)
const showCohortsStepper = ref(false)
const designClass = ref('')
const editStepper = ref(false)

const exportDataUrl = computed(() => {
  return `studies/${studiesGeneralStore.selectedStudy.uid}/study-branch-arms`
})

const studyBranchHistoryTitle = computed(() => {
  if (selectedBranch.value) {
    return t('StudyBranchArms.study_branch_history_title', {
      branchUid: selectedBranch.value.branch_arm_uid,
    })
  }
  return ''
})

onMounted(() => {
  fetchStudyArms()
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

function getCohortNames(branch) {
  return branch.study_cohorts
    ?.map((cohort) => `&#9679; ${escapeHTML(cohort.study_cohort_name)}`)
    .join('<br />')
}

function getCohortCodes(branch) {
  return branch.study_cohorts
    ?.map((cohort) => `&#9679; ${escapeHTML(cohort.study_cohort_code)}`)
    .join('<br />')
}

async function fetchBranchArmsHistory() {
  const resp = await studyEpochs.getStudyBranchesVersions(
    studiesGeneralStore.selectedStudy.uid
  )
  return resp.data
}

async function fetchStudyArms() {
  const params = {
    total_count: true,
    page_size: 0,
  }
  const resp = await armsApi.getAllForStudy(
    studiesGeneralStore.selectedStudy.uid,
    { params }
  )
  arms.value = resp.data.items
}

function fetchStudyBranchArms(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  params.study_uid = studiesGeneralStore.selectedStudy.uid
  armsApi
    .getAllBranchArms(studiesGeneralStore.selectedStudy.uid, params)
    .then((resp) => {
      branchArms.value = resp.data.items
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
  table.value.filterTable()
}

function closeForm() {
  branchArmToEdit.value = {}
  showBranchArmsForm.value = false
  table.value.filterTable()
}

function editBranchArm(item) {
  if (designClass.value === cohortConstants.MANUAL) {
    branchArmToEdit.value = item
    showBranchArmsForm.value = true
  } else {
    showCohortsStepper.value = true
  }
}

async function openBranchHistory(branch) {
  selectedBranch.value = branch
  const resp = await studyEpochs.getStudyBranchVersions(
    studiesGeneralStore.selectedStudy.uid,
    branch.branch_arm_uid
  )
  branchHistoryItems.value = resp.data
  showBranchHistory.value = true
}

function closeBranchHistory() {
  showBranchHistory.value = false
  selectedBranch.value = null
}

async function deleteBranchArm(item) {
  let cellsInBranch = 0
  await armsApi
    .getAllCellsForBranch(
      studiesGeneralStore.selectedStudy.uid,
      item.branch_arm_uid
    )
    .then((resp) => {
      cellsInBranch = resp.data.length
    })
  const options = {
    type: 'warning',
    cancelLabel: t('_global.cancel'),
    agreeLabel: t('_global.continue'),
  }
  if (cellsInBranch === 0) {
    armsApi
      .deleteBranchArm(
        studiesGeneralStore.selectedStudy.uid,
        item.branch_arm_uid
      )
      .then(() => {
        table.value.filterTable()
        notificationHub.add({
          msg: t('StudyBranchArms.branch_deleted'),
        })
      })
  } else if (
    await confirm.value.open(
      t('StudyBranchArms.branch_delete_notification'),
      options
    )
  ) {
    armsApi
      .deleteBranchArm(
        studiesGeneralStore.selectedStudy.uid,
        item.branch_arm_uid
      )
      .then(() => {
        table.value.filterTable()
        notificationHub.add({
          msg: t('StudyBranchArms.branch_deleted'),
        })
      })
  }
}

async function addBranchArm() {
  await fetchStudyArms()
  if (arms.value.length === 0) {
    const options = {
      type: 'warning',
      cancelLabel: t('_global.cancel'),
      agreeLabel: t('StudyBranchArms.add_arm'),
      redirect: 'arms',
    }
    if (
      !(await confirm.value.open(t('StudyBranchArms.add_arm_message'), options))
    ) {
      return
    }
  }
  showBranchArmsForm.value = true
}

function changeOrder(branchUid, newOrder) {
  armsApi
    .updateBranchArmOrder(
      studiesGeneralStore.selectedStudy.uid,
      branchUid,
      newOrder
    )
    .then(() => {
      table.value.filterTable()
    })
    .catch(() => {
      table.value.filterTable()
    })
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
