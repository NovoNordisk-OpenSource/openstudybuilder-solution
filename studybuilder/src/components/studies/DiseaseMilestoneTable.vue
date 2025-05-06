<template>
  <div>
    <NNTable
      ref="table"
      :headers="headers"
      :items="diseaseMilestones"
      item-value="uid"
      fixed-header
      :items-length="total"
      :history-data-fetcher="fetchDiseaseMilestonesHistory"
      :history-title="$t('DiseaseMilestoneTable.global_history_title')"
      export-object-label="DiseaseMilestones"
      :export-data-url="exportDataUrl"
      :column-data-resource="exportDataUrl"
      disable-filtering
      :hide-default-body="sortMode && diseaseMilestones.length > 0"
      @filter="fetchDiseaseMilestones"
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
          <tr v-for="milestone in diseaseMilestones" :key="milestone.uid">
            <td>
              <v-icon size="small"> mdi-sort </v-icon>
            </td>
            <td>{{ milestone.order }}</td>
            <td>{{ milestone.disease_milestone_type_name }}</td>
            <td>{{ milestone.disease_milestone_type_definition }}</td>
            <td>{{ $filters.yesno(milestone.repetition_indicator) }}</td>
            <td>{{ $filters.date(milestone.start_date) }}</td>
            <td>{{ milestone.author_username }}</td>
          </tr>
        </tbody>
      </template>
      <template #actions="">
        <v-btn
          data-cy="create-disease-milestone"
          class="ml-2"
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          :title="$t('DiseaseMilestoneForm.add_title')"
          :disabled="
            !accessGuard.checkPermission($roles.STUDY_WRITE) ||
            studiesGeneralStore.selectedStudyVersion !== null
          "
          icon="mdi-plus"
          @click="createDiseaseMilestone()"
        />
      </template>
      <template #[`item.actions`]="{ item }">
        <div class="pr-0 mr-0">
          <ActionsMenu :actions="actions" :item="item" />
        </div>
      </template>
      <template #[`item.repetition_indicator`]="{ item }">
        {{ $filters.yesno(item.repetition_indicator) }}
      </template>
      <template #[`item.start_date`]="{ item }">
        {{ $filters.date(item.start_date) }}
      </template>
    </NNTable>
    <DiseaseMilestoneForm
      :open="showForm"
      :disease-milestone="selectedDiseaseMilestone"
      @close="closeForm"
    />
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
    <v-dialog
      v-model="showHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeHistory"
    >
      <HistoryTable
        :title="diseaseMilestoneHistoryTitle"
        :headers="headers"
        :items="historyItems"
        :items-total="historyItems.length"
        @close="closeHistory"
      />
    </v-dialog>
  </div>
</template>

<script setup>
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import dataFormating from '@/utils/dataFormating'
import DiseaseMilestoneForm from './DiseaseMilestoneForm.vue'
import filteringParameters from '@/utils/filteringParameters'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import NNTable from '@/components/tools/NNTable.vue'
import study from '@/api/study'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { computed, inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDragAndDrop } from '@formkit/drag-and-drop/vue'

const [parent, diseaseMilestones] = useDragAndDrop([], {
  onDragend: (event) => {
    const newOrder =
      event.draggedNode.data.value.order -
      (event.state.initialIndex - event.state.targetIndex)
    changeOrder(event.draggedNode.data.value.uid, newOrder)
  },
})

const { t } = useI18n()
const eventBusEmit = inject('eventBusEmit')
const roles = inject('roles')
const studiesGeneralStore = useStudiesGeneralStore()
const accessGuard = useAccessGuard()
const table = ref()
const confirm = ref()

const actions = [
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    click: editDiseaseMilestone,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    click: deleteDiseaseMilestone,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openHistory,
  },
]
const headers = [
  { title: '', key: 'actions', width: '1%' },
  { title: '#', key: 'order', width: '5%' },
  {
    title: t('DiseaseMilestone.disease_milestone_type'),
    key: 'disease_milestone_type_name',
  },
  {
    title: t('_global.definition'),
    key: 'disease_milestone_type_definition',
  },
  {
    title: t('DiseaseMilestone.repetition_indicator'),
    key: 'repetition_indicator',
  },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.modified_by'), key: 'author_username' },
]
const historyItems = ref([])
const selectedDiseaseMilestone = ref(null)
const showForm = ref(false)
const showHistory = ref(false)
const total = ref(0)
const sortMode = ref(false)

const exportDataUrl = computed(() => {
  return `studies/${studiesGeneralStore.selectedStudy.uid}/study-disease-milestones`
})
const diseaseMilestoneHistoryTitle = computed(() => {
  if (selectedDiseaseMilestone.value) {
    return t('DiseaseMilestoneTable.item_history_title', {
      uid: selectedDiseaseMilestone.value.uid,
    })
  }
  return ''
})

function fetchDiseaseMilestones(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  study
    .getStudyDiseaseMilestones(studiesGeneralStore.selectedStudy.uid, params)
    .then((resp) => {
      diseaseMilestones.value = resp.data.items
      total.value = resp.data.total
    })
}

function formatItems(items) {
  const result = []
  for (const item of items) {
    item.repetition_indicator = dataFormating.yesno(item.repetition_indicator)
    result.push(item)
  }
  return result
}

async function fetchDiseaseMilestonesHistory() {
  const resp = await study.getStudyDiseaseMilestonesAuditTrail(
    studiesGeneralStore.selectedStudy.uid
  )
  return formatItems(resp.data)
}

function createDiseaseMilestone() {
  selectedDiseaseMilestone.value = null
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  table.value.filterTable()
}

function editDiseaseMilestone(item) {
  selectedDiseaseMilestone.value = item
  showForm.value = true
}

async function deleteDiseaseMilestone(item) {
  const options = { type: 'warning' }
  const context = { name: item.disease_milestone_type_name }
  const msg = t('DiseaseMilestoneTable.confirm_delete', context)
  if (!(await confirm.value.open(msg, options))) {
    return
  }
  study
    .deleteStudyDiseaseMilestone(
      studiesGeneralStore.selectedStudy.uid,
      item.uid
    )
    .then(() => {
      eventBusEmit('notification', {
        msg: t('DiseaseMilestoneTable.delete_success'),
      })
      table.value.filterTable()
    })
}

async function openHistory(item) {
  selectedDiseaseMilestone.value = item
  const resp = await study.getStudyDiseaseMilestoneAuditTrail(
    studiesGeneralStore.selectedStudy.uid,
    item.uid
  )
  historyItems.value = formatItems(resp.data)
  showHistory.value = true
}

function closeHistory() {
  showHistory.value = false
}

function changeOrder(milestoneUid, newOrder) {
  study
    .updateStudyDiseaseMilestoneOrder(
      studiesGeneralStore.selectedStudy.uid,
      milestoneUid,
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
