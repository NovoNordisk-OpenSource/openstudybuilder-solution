<template>
  <div>
    <NNTable
      ref="table"
      table-id="studies-cohorts-table"
      :headers="headers"
      item-value="cohort_uid"
      :items-length="total"
      :items="cohorts"
      disable-filtering
      :hide-default-body="sortMode && cohorts.length > 0"
      :history-config="{
        dataFetcher: fetchCohortsHistory,
        title: $t('StudyCohorts.global_history_title'),
      }"
      :export-config="{
        dataUrlParams: { split_if_in_multiple_arms_and_branches: true },
        objectLabel: 'StudyCohorts',
        dataUrl: exportDataUrl,
      }"
      @filter="fetchStudyCohorts"
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
          data-cy="add-study-cohort"
          :disabled="
            !accessGuard.checkPermission($roles.STUDY_WRITE) ||
            studiesGeneralStore.selectedStudyVersion !== null
          "
          @click.stop="showForm()"
        >
          <v-icon>mdi-plus</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('StudyCohorts.add_study_cohort') }}
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
            {{ $t('StudyCohorts.cohorts_stepper') }}
          </v-tooltip>
        </v-btn>
      </template>
      <template #tbody>
        <tbody v-show="sortMode" ref="parent">
          <tr v-for="cohort in cohorts" :key="cohort.cohort_uid">
            <td>
              <v-icon size="small"> mdi-sort </v-icon>
            </td>
            <td>{{ cohort.order }}</td>
            <td>{{ cohort.name }}</td>
            <td>{{ cohort.short_name }}</td>
            <td>{{ cohort.code }}</td>
            <td>{{ cohort.number_of_subjects }}</td>
            <td>
              <div v-html="sanitizeHTML(getArmsDisplay(cohort))" />
            </td>
            <td>
              <div v-html="sanitizeHTML(getBranchesDisplay(cohort))" />
            </td>
            <td>{{ cohort.description }}</td>
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
        <div v-html="sanitizeHTML(getArmsDisplay(item))" />
      </template>
      <template #[`item.branch_arm_roots`]="{ item }">
        <div v-html="sanitizeHTML(getBranchesDisplay(item))" />
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
    <StudyCohortsForm
      :open="form"
      :edited-cohort="cohortToEdit"
      :arms="arms"
      :branches="branches"
      @close="closeForm"
    />
    <v-dialog
      v-model="showCohortsStepper"
      persistent
      fullscreen
      content-class="fullscreen-dialog"
    >
      <CohortsStepper
        :design-class="designClass"
        :initial-step="3"
        @close="closeCohortStepper"
      />
    </v-dialog>
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
import cohortsApi from '@/api/cohorts'
import StudyCohortsForm from '@/components/studies/StudyCohortsForm.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import CohortsStepper from './CohortsStepper.vue'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import HistoryTable from '@/components/tools/HistoryTable.vue'
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
  { title: t('StudyCohorts.cohort_name'), key: 'name' },
  { title: t('StudyCohorts.cohort_short_name'), key: 'short_name' },
  { title: t('StudyCohorts.cohort_code'), key: 'code' },
  {
    title: t('StudyCohorts.number_of_participants'),
    key: 'number_of_subjects',
  },
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
  { title: t('_global.description'), key: 'description' },
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
const showCohortsStepper = ref(false)
const designClass = ref('')
const editStepper = ref(false)

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
      branches.value = resp.data.items
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

function closeCohortStepper() {
  showCohortsStepper.value = false
  cohortsApi
    .checkDesignClassEditable(studiesGeneralStore.selectedStudy.uid)
    .then((resp) => {
      editStepper.value = !resp.data
    })
  table.value.filterTable()
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
  if (designClass.value === cohortConstants.MANUAL) {
    cohortToEdit.value = item
    form.value = true
  } else {
    showCohortsStepper.value = true
  }
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
    .deleteCohort(
      studiesGeneralStore.selectedStudy.uid,
      item.cohort_uid,
      designClass.value !== cohortConstants.MANUAL
    )
    .then(() => {
      table.value.filterTable()
      notificationHub.add({
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

function getBranchesDisplay(cohort) {
  return cohort.branch_arm_roots
    ?.map((branch) => `&#9679; ${escapeHTML(branch.name)}`)
    .join('<br />')
}
function getArmsDisplay(cohort) {
  return cohort.arm_roots
    ?.map((arm) => `&#9679; ${escapeHTML(arm.name)}`)
    .join('<br />')
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
