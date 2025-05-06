<template>
  <div>
    <NNTable
      ref="table"
      :headers="headers"
      item-value="branch_arm_uid"
      :items-length="total"
      :items="branchArms"
      :no-data-text="
        arms.length === 0 ? $t('StudyBranchArms.no_data') : undefined
      "
      :export-data-url="exportDataUrl"
      export-object-label="StudyBranches"
      :history-data-fetcher="fetchBranchArmsHistory"
      :history-title="$t('StudyBranchArms.global_history_title')"
      disable-filtering
      :hide-default-body="sortMode && branchArms.length > 0"
      @filter="fetchStudyBranchArms"
    >
      <template #afterSwitches>
        <div :title="$t('NNTableTooltips.reorder_content')">
          <v-switch
            v-model="sortMode"
            :label="$t('NNTable.reorder_content')"
            hide-details
            class="mr-6"
            color="primary"
            :disabled="!accessGuard.checkPermission($roles.STUDY_WRITE)"
          />
        </div>
      </template>
      <template #actions="">
        <v-btn
          class="ml-2"
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          :title="$t('StudyBranchArms.add_branch')"
          data-cy="add-study-branch-arm"
          :disabled="
            !accessGuard.checkPermission($roles.STUDY_WRITE) ||
            studiesGeneralStore.selectedStudyVersion !== null
          "
          icon="mdi-plus"
          @click.stop="addBranchArm"
        />
      </template>
      <template #tbody>
        <tbody v-show="sortMode" ref="parent">
          <tr v-for="branch in branchArms" :key="branch.branch_arm_uid">
            <td>
              <v-icon size="small"> mdi-sort </v-icon>
            </td>
            <td>{{ branch.order }}</td>
            <td>{{ branch.arm_root.name }}</td>
            <td>{{ branch.name }}</td>
            <td>{{ branch.short_name }}</td>
            <td>{{ branch.randomization_group }}</td>
            <td>{{ branch.code }}</td>
            <td>{{ branch.number_of_subjects }}</td>
            <td>{{ branch.description }}</td>
            <td>
              <v-chip :color="branch.colour_code" size="small" variant="flat">
                <span>&nbsp;</span>
                <span>&nbsp;</span>
              </v-chip>
            </td>
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
      <template #[`item.colour_code`]="{ item }">
        <v-chip
          :data-cy="'color=' + item.colour_code"
          :color="item.colour_code"
          size="small"
          variant="flat"
        >
          <span>&nbsp;</span>
          <span>&nbsp;</span>
        </v-chip>
      </template>
      <template #[`item.start_date`]="{ item }">
        {{ $filters.date(item.start_date) }}
      </template>
      <template #[`item.actions`]="{ item }">
        <ActionsMenu :actions="actions" :item="item" />
      </template>
    </NNTable>
    <StudyBranchesForm
      :open="showBranchArmsForm"
      :edited-branch-arm="branchArmToEdit"
      :arms="arms"
      @close="closeForm"
    />
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
import StudyBranchesForm from '@/components/studies/StudyBranchesForm.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import studyEpochs from '@/api/studyEpochs'
import { useAccessGuard } from '@/composables/accessGuard'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import filteringParameters from '@/utils/filteringParameters'
import { computed, onMounted, inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDragAndDrop } from '@formkit/drag-and-drop/vue'

const { t } = useI18n()
const eventBusEmit = inject('eventBusEmit')
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
  {
    title: t('StudyBranchArms.arm_name'),
    key: 'arm_root.name',
    historyHeader: 'arm_root_uid',
  },
  { title: t('StudyBranchArms.name'), key: 'name' },
  { title: t('StudyBranchArms.short_name'), key: 'short_name' },
  {
    title: t('StudyBranchArms.randomisation_group'),
    key: 'randomization_group',
  },
  { title: t('StudyBranchArms.code'), key: 'code' },
  {
    title: t('StudyBranchArms.number_of_subjects'),
    key: 'number_of_subjects',
  },
  { title: t('StudyBranchArms.description'), key: 'description' },
  { title: t('StudyBranchArms.colour'), key: 'colour_code' },
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
    condition: () => !studiesGeneralStore.selectedStudyVersion,
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
})

async function fetchBranchArmsHistory() {
  const resp = await studyEpochs.getStudyBranchesVersions(
    studiesGeneralStore.selectedStudy.uid
  )
  return resp.data
}

function fetchStudyArms() {
  const params = {
    total_count: true,
    page_size: 0,
  }
  armsApi
    .getAllForStudy(studiesGeneralStore.selectedStudy.uid, { params })
    .then((resp) => {
      arms.value = resp.data.items
    })
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
      branchArms.value = resp.data
      total.value = resp.data.length
    })
}

function closeForm() {
  branchArmToEdit.value = {}
  showBranchArmsForm.value = false
  table.value.filterTable()
}

function editBranchArm(item) {
  branchArmToEdit.value = item
  showBranchArmsForm.value = true
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
        eventBusEmit('notification', {
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
        eventBusEmit('notification', {
          msg: t('StudyBranchArms.branch_deleted'),
        })
      })
  }
}

async function addBranchArm() {
  fetchStudyArms()
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
