<template>
  <div>
    <NNTable
      ref="table"
      :headers="headers"
      item-value="cohort_uid"
      :items-length="total"
      :items="cohorts"
      :history-data-fetcher="fetchCohortsHistory"
      :history-title="$t('StudyCohorts.global_history_title')"
      :export-data-url="exportDataUrl"
      export-object-label="StudyCohors"
      disable-filtering
      :hide-default-body="sortMode && cohorts.length > 0"
      @filter="fetchStudyCohorts"
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
          :title="$t('StudyCohorts.add_study_cohort')"
          data-cy="add-study-cohort"
          :disabled="
            !accessGuard.checkPermission($roles.STUDY_WRITE) ||
            studiesGeneralStore.selectedStudyVersion !== null
          "
          icon="mdi-plus"
          @click.stop="showForm()"
        />
      </template>
      <template #tbody>
        <tbody v-show="sortMode" ref="parent">
          <tr v-for="cohort in cohorts" :key="cohort.cohort_uid">
            <td>
              <v-icon size="small"> mdi-sort </v-icon>
            </td>
            <td>{{ cohort.order }}</td>
            <td>
              <div v-for="arm of cohort.arm_roots" :key="arm.arm_uid">
                {{ arm.name }}
              </div>
            </td>
            <td>
              <div
                v-for="branch of cohort.branch_arm_roots"
                :key="branch.branch_arm_uid"
              >
                {{ branch.name }}
              </div>
            </td>
            <td>{{ cohort.name }}</td>
            <td>{{ cohort.short_name }}</td>
            <td>{{ cohort.code }}</td>
            <td>{{ cohort.number_of_subjects }}</td>
            <td>{{ cohort.description }}</td>
            <td>
              <v-chip :color="cohort.colour_code" size="small" variant="flat">
                <span>&nbsp;</span>
                <span>&nbsp;</span>
              </v-chip>
            </td>
            <td>{{ $filters.date(cohort.start_date) }}</td>
            <td>{{ cohort.author_username }}</td>
          </tr>
        </tbody>
      </template>
      <template #[`item.name`]="{ item }">
        <router-link
          :to="{
            name: 'StudyCohortOverview',
            params: {
              study_id: studiesGeneralStore.selectedStudy.uid,
              id: item.cohort_uid,
            },
          }"
        >
          {{ item.name }}
        </router-link>
      </template>
      <template #[`item.arm_roots`]="{ item }">
        <router-link
          v-for="arm of item.arm_roots"
          :key="arm.arm_uid"
          :to="{
            name: 'StudyArmOverview',
            params: {
              study_id: studiesGeneralStore.selectedStudy.uid,
              id: arm.arm_uid,
            },
          }"
        >
          {{ arm.name }}
        </router-link>
      </template>
      <template #[`item.branch_arm_roots`]="{ item }">
        <div v-if="item.branch_arm_roots">
          <router-link
            v-for="branch of item.branch_arm_roots"
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
    <StudyCohortsForm
      :open="form"
      :edited-cohort="cohortToEdit"
      :arms="arms"
      :branches="branches"
      @close="closeForm"
    />
    <v-dialog
      v-model="showCohortHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeCohortHistory"
    >
      <HistoryTable
        :title="studyCohortHistoryTitle"
        :headers="headers"
        :items="cohortHistoryItems"
        :items-total="cohortHistoryItems.length"
        @close="closeCohortHistory"
      />
    </v-dialog>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  </div>
</template>

<script setup>
import NNTable from '@/components/tools/NNTable.vue'
import armsApi from '@/api/arms'
import StudyCohortsForm from '@/components/studies/StudyCohortsForm.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import HistoryTable from '@/components/tools/HistoryTable.vue'
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

const [parent, cohorts] = useDragAndDrop([], {
  onDragend: (event) => {
    const newOrder =
      event.draggedNode.data.value.order -
      (event.state.initialIndex - event.state.targetIndex)
    changeOrder(event.draggedNode.data.value.cohort_uid, newOrder)
  },
})

const headers = [
  { title: '', key: 'actions', width: '1%' },
  { title: '#', key: 'order', width: '5%' },
  {
    title: t('StudyCohorts.arm_name'),
    key: 'arm_roots',
    historyHeader: 'arm_roots_uids',
  },
  {
    title: t('StudyCohorts.branch_arm_name'),
    key: 'branch_arm_roots',
    historyHeader: 'branch_arm_roots_uids',
    filteringName: 'branch_arm_roots.name',
  },
  { title: t('StudyCohorts.cohort_name'), key: 'name' },
  { title: t('StudyCohorts.cohort_short_name'), key: 'short_name' },
  { title: t('StudyCohorts.cohort_code'), key: 'code' },
  {
    title: t('StudyCohorts.number_of_subjects'),
    key: 'number_of_subjects',
  },
  { title: t('_global.description'), key: 'description' },
  { title: t('StudyCohorts.colour'), key: 'colour_code' },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.modified_by'), key: 'author_username' },
]
const actions = [
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    click: editCohort,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    click: deleteCohort,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openCohortHistory,
  },
]
const total = ref(0)
const form = ref(false)
const arms = ref([])
const branches = ref([])
const cohortToEdit = ref({})
const showCohortHistory = ref(false)
const cohortHistoryItems = ref([])
const selectedCohort = ref(null)
const sortMode = ref(false)

const exportDataUrl = computed(() => {
  return `studies/${studiesGeneralStore.selectedStudy.uid}/study-cohorts`
})

const studyCohortHistoryTitle = computed(() => {
  if (selectedCohort.value) {
    return t('StudyCohorts.study_arm_history_title', {
      cohortUid: selectedCohort.value.cohort_uid,
    })
  }
  return ''
})

onMounted(() => {
  fetchStudyArmsAndBranches()
})

async function fetchCohortsHistory() {
  const resp = await armsApi.getStudyCohortsVersions(
    studiesGeneralStore.selectedStudy.uid
  )
  return resp.data
}

function fetchStudyArmsAndBranches() {
  const params = {
    total_count: true,
    page_size: 0,
  }
  armsApi
    .getAllForStudy(studiesGeneralStore.selectedStudy.uid, { params })
    .then((resp) => {
      arms.value = resp.data.items
    })
  armsApi
    .getAllBranchArms(studiesGeneralStore.selectedStudy.uid, params)
    .then((resp) => {
      branches.value = resp.data
    })
}

function fetchStudyCohorts(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  params.study_uid = studiesGeneralStore.selectedStudy.uid
  armsApi
    .getAllCohorts(studiesGeneralStore.selectedStudy.uid, params)
    .then((resp) => {
      cohorts.value = resp.data.items
      total.value = resp.data.total
    })
}

function showForm() {
  form.value = true
}

function closeForm() {
  form.value = false
  cohortToEdit.value = {}
  table.value.filterTable()
}

function editCohort(item) {
  cohortToEdit.value = item
  form.value = true
}

async function openCohortHistory(cohort) {
  selectedCohort.value = cohort
  const resp = await armsApi.getStudyCohortVersions(
    studiesGeneralStore.selectedStudy.uid,
    cohort.cohort_uid
  )
  cohortHistoryItems.value = resp.data
  showCohortHistory.value = true
}

function closeCohortHistory() {
  showCohortHistory.value = false
  selectedCohort.value = null
}

function deleteCohort(item) {
  armsApi
    .deleteCohort(studiesGeneralStore.selectedStudy.uid, item.cohort_uid)
    .then(() => {
      table.value.filterTable()
      eventBusEmit('notification', {
        msg: t('StudyCohorts.cohort_deleted'),
      })
    })
}

function changeOrder(cohortUid, newOrder) {
  armsApi
    .updateCohortOrder(
      studiesGeneralStore.selectedStudy.uid,
      cohortUid,
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
