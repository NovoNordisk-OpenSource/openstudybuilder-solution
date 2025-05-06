<template>
  <div>
    <NNTable
      ref="table"
      :headers="headers"
      item-value="arm_uid"
      :items-length="total"
      :export-data-url="exportDataUrl"
      export-object-label="StudyArms"
      :items="arms"
      :column-data-resource="`studies/${studiesGeneralStore.selectedStudy.uid}/study-arms`"
      :history-data-fetcher="fetchArmsHistory"
      :history-title="$t('StudyArmsTable.global_history_title')"
      disable-filtering
      :hide-default-body="sortMode && arms.length > 0"
      @filter="fetchStudyArms"
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
      <template #tbody>
        <tbody v-show="sortMode" ref="parent">
          <tr v-for="arm in arms" :key="arm.arm_uid">
            <td>
              <v-icon size="small"> mdi-sort </v-icon>
            </td>
            <td>{{ arm.order }}</td>
            <td>{{ arm.arm_type?.sponsor_preferred_name }}</td>
            <td>{{ arm.name }}</td>
            <td>{{ arm.short_name }}</td>
            <td>{{ arm.randomization_group }}</td>
            <td>{{ arm.code }}</td>
            <td>{{ arm.number_of_subjects }}</td>
            <td>
              <div
                v-for="branch of arm.arm_connected_branch_arms"
                :key="branch.branch_arm_uid"
              >
                {{ branch.name }}
              </div>
            </td>
            <td>{{ arm.description }}</td>
            <td>
              <v-chip :color="arm.arm_colour" size="small" variant="flat">
                <span>&nbsp;</span>
                <span>&nbsp;</span>
              </v-chip>
            </td>
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
        {{ $filters.date(item.start_date) }}
      </template>
      <template #[`item.arm_connected_branch_arms`]="{ item }">
        <div v-if="item.arm_connected_branch_arms">
          <router-link
            v-for="branch of item.arm_connected_branch_arms"
            :key="branch.branch_arm_uid"
            :to="{
              name: 'StudyBranchArmOverview',
              params: {
                study_id: studiesGeneralStore.selectedStudy.uid,
                id: branch.branch_arm_uid,
              },
            }"
          >
            {{ branch.name }}
          </router-link>
        </div>
      </template>
      <template #[`item.arm_colour`]="{ item }">
        <v-chip :color="item.arm_colour" size="small" variant="flat">
          <span>&nbsp;</span>
          <span>&nbsp;</span>
        </v-chip>
      </template>
      <template #[`item.arm_type.sponsor_preferred_name`]="{ item }">
        <CTTermDisplay :term="item.arm_type" />
      </template>
      <template #[`item.actions`]="{ item }">
        <ActionsMenu :actions="actions" :item="item" />
      </template>
      <template #actions="">
        <v-btn
          class="ml-2"
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          :title="$t('StudyArmsForm.add_arm')"
          data-cy="add-study-arm"
          :disabled="
            !accessGuard.checkPermission($roles.STUDY_WRITE) ||
            studiesGeneralStore.selectedStudyVersion !== null
          "
          icon="mdi-plus"
          @click.stop="showArmsForm = true"
        />
      </template>
    </NNTable>
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
import CTTermDisplay from '@/components/tools/CTTermDisplay.vue'
import StudyArmsForm from '@/components/studies/StudyArmsForm.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import filteringParameters from '@/utils/filteringParameters'
import studyEpochs from '@/api/studyEpochs'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { computed, inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDragAndDrop } from '@formkit/drag-and-drop/vue'

const { t } = useI18n()
const eventBusEmit = inject('eventBusEmit')
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

const headers = [
  { title: '', key: 'actions', width: '1%' },
  { title: '#', key: 'order', width: '5%' },
  {
    title: t('StudyArmsTable.type'),
    key: 'arm_type.sponsor_preferred_name',
    width: '7%',
  },
  { title: t('StudyArmsTable.name'), key: 'name' },
  { title: t('StudyArmsTable.short_name'), key: 'short_name' },
  {
    title: t('StudyArmsTable.randomisation_group'),
    key: 'randomization_group',
  },
  { title: t('StudyArmsTable.code'), key: 'code' },
  {
    title: t('StudyArmsTable.number_of_subjects'),
    key: 'number_of_subjects',
    width: '1%',
  },
  {
    title: t('StudyArmsTable.connected_branches'),
    key: 'arm_connected_branch_arms',
  },
  { title: t('StudyArmsTable.description'), key: 'description' },
  { title: t('StudyBranchArms.colour'), key: 'arm_colour' },
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

function closeForm() {
  armToEdit.value = {}
  showArmsForm.value = false
  table.value.filterTable()
}

function editArm(item) {
  armToEdit.value = item
  showArmsForm.value = true
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
        eventBusEmit('notification', {
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
        eventBusEmit('notification', {
          msg: t('StudyArmsTable.arm_deleted'),
        })
        table.value.filterTable()
      })
  }
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
