<template>
  <div>
    <NNTable
      ref="table"
      :table-id="tableId"
      :headers="headers"
      :items="studyEpochs"
      item-value="uid"
      :items-length="total"
      :column-data-resource="
        !sortMode
          ? `studies/${studiesGeneralStore.selectedStudy.uid}/study-epochs`
          : undefined
      "
      :disable-filtering="sortMode"
      :hide-default-body="sortMode && studyEpochs.length > 0"
      :history-config="{
        dataFetcher: fetchEpochsHistory,
        title: $t('StudyEpochTable.global_history_title'),
      }"
      :export-config="{
        objectLabel: 'StudyEpochs',
        dataUrl: exportDataUrl,
        dataUrlParams: showLagTime ? { with_lag_time: true } : undefined,
      }"
      @filter="fetchEpochs"
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
          <tr v-for="epoch in studyEpochs" :key="epoch.uid">
            <td>
              <v-icon size="small"> mdi-sort </v-icon>
            </td>
            <td>{{ epoch.order }}</td>
            <td>{{ epoch.epoch_ctterm.sponsor_preferred_name }}</td>
            <td>{{ epoch.epoch_type_ctterm.sponsor_preferred_name }}</td>
            <td>{{ epoch.epoch_subtype_ctterm.sponsor_preferred_name }}</td>
            <td>{{ epoch.start_rule }}</td>
            <td>{{ epoch.end_rule }}</td>
            <td>{{ epoch.description }}</td>
            <td>{{ epoch.study_visit_count }}</td>
            <template v-if="showLagTime">
              <td v-for="field in lagTimeFields" :key="field">
                {{ formatLagTime(epoch, field) }}
              </td>
            </template>
            <td>
              <v-chip :color="epoch.color_hash" size="small" variant="flat">
                <span>&nbsp;</span>
                <span>&nbsp;</span>
              </v-chip>
            </td>
          </tr>
        </tbody>
      </template>
      <template #[`item.color_hash`]="{ item }">
        <v-chip
          :data-cy="'color=' + item.color_hash"
          :color="item.color_hash"
          size="small"
          variant="flat"
        >
          <span>&nbsp;</span>
          <span>&nbsp;</span>
        </v-chip>
      </template>
      <template #[`item.epoch_ctterm.sponsor_preferred_name`]="{ item }">
        <router-link
          :to="{
            name: 'StudyEpochOverview',
            params: {
              study_id: studiesGeneralStore.selectedStudy.uid,
              id: item.uid,
            },
          }"
        >
          <CTTermDisplay :term="item.epoch_ctterm" />
        </router-link>
      </template>
      <template #[`item.epoch_type_ctterm.sponsor_preferred_name`]="{ item }">
        <CTTermDisplay :term="item.epoch_type_ctterm" />
      </template>
      <template
        #[`item.epoch_subtype_ctterm.sponsor_preferred_name`]="{ item }"
      >
        <CTTermDisplay :term="item.epoch_subtype_ctterm" />
      </template>
      <template
        v-for="field in lagTimeFields"
        #[`item.${field}`]="{ item }"
        :key="field"
      >
        {{ formatLagTime(item, field) }}
      </template>
      <template #[`item.actions`]="{ item }">
        <ActionsMenu :actions="actions" :item="item" />
      </template>
      <template #actions="">
        <v-btn
          data-cy="create-epoch"
          class="ml-2"
          icon
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          :disabled="
            !accessGuard.checkPermission($roles.STUDY_WRITE) ||
            studiesGeneralStore.selectedStudyVersion !== null
          "
          @click="createEpoch()"
        >
          <v-icon>mdi-plus</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('StudyEpochForm.add_title') }}
          </v-tooltip>
        </v-btn>
      </template>
    </NNTable>
    <v-dialog
      v-model="showForm"
      persistent
      fullscreen
      content-class="fullscreen-dialog"
    >
      <StudyEpochForm :study-epoch="selectedStudyEpoch" @close="closeForm" />
    </v-dialog>
    <v-dialog
      v-model="showEpochHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeEpochHistory"
    >
      <HistoryTable
        :title="studyEpochHistoryTitle"
        :headers="headers"
        :items="epochHistoryItems"
        :items-total="epochHistoryItems.length"
        @close="closeEpochHistory"
      />
    </v-dialog>
  </div>
</template>

<script setup>
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StudyEpochForm from './StudyEpochForm.vue'
import epochsApi from '@/api/studyEpochs'
import filteringParameters from '@/utils/filteringParameters'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import CTTermDisplay from '@/components/tools/CTTermDisplay.vue'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useEpochsStore } from '@/stores/studies-epochs'
import { useUnitsStore } from '@/stores/units'
import { useFeatureFlagsStore } from '@/stores/feature-flags'
import { computed, onMounted, inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDragAndDrop } from '@formkit/drag-and-drop/vue'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const roles = inject('roles')
const studiesGeneralStore = useStudiesGeneralStore()
const accessGuard = useAccessGuard()
const table = ref()
const epochsStore = useEpochsStore()
const unitsStore = useUnitsStore()
const featureFlagsStore = useFeatureFlagsStore()

const [parent, studyEpochs] = useDragAndDrop([], {
  onDragend: (event) => {
    const newOrder =
      event.draggedNode.data.value.order -
      (event.state.initialIndex - event.state.targetIndex)
    changeOrder(event.draggedNode.data.value.uid, newOrder)
  },
})

const actions = [
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'edit') &&
      !studiesGeneralStore.selectedStudyVersion,
    click: editEpoch,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'delete') &&
      !studiesGeneralStore.selectedStudyVersion,
    click: deleteEpoch,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openEpochHistory,
  },
]
// Lag time only carries data migrated from MMA.
const lagTimeFields = ['ae_lag_time', 'hypo_lag_time', 'ce_lag_time']
const showLagTime = computed(() =>
  featureFlagsStore.getFeatureFlag('study_epoch_lag_time')
)

// Own layout key per flag state: NNTable hides headers missing from the saved
// column layout, so a layout stored while the flag was off would keep the lag
// columns hidden after switching it on.
const tableId = computed(() =>
  showLagTime.value ? 'studies-epochs-table-lag' : 'studies-epochs-table'
)

function formatLagTime(item, field) {
  if (item[field] === null || item[field] === undefined) {
    return ''
  }
  return `${item[field]} ${item[`${field}_unit_name`] || ''}`.trim()
}

const headers = computed(() => [
  { title: '', key: 'actions', width: '1%' },
  { title: t('StudyEpochTable.number'), key: 'order', width: '5%' },
  {
    title: t('StudyEpochTable.name'),
    key: 'epoch_ctterm.sponsor_preferred_name',
  },
  {
    title: t('StudyEpochTable.type'),
    key: 'epoch_type_ctterm.sponsor_preferred_name',
  },
  {
    title: t('StudyEpochTable.sub_type'),
    key: 'epoch_subtype_ctterm.sponsor_preferred_name',
  },
  { title: t('StudyEpochTable.start_rule'), key: 'start_rule' },
  { title: t('StudyEpochTable.end_rule'), key: 'end_rule' },
  {
    title: t('StudyEpochTable.description'),
    key: 'description',
    width: '20%',
  },
  {
    title: t('StudyEpochTable.visit_count'),
    key: 'study_visit_count',
  },
  ...(showLagTime.value
    ? lagTimeFields.map((field) => ({
        title: t(`StudyEpochForm.${field}`),
        key: field,
      }))
    : []),
  { title: t('StudyEpochTable.colour'), key: 'color_hash' },
])
const selectedStudyEpoch = ref(null)
const showForm = ref(false)
const showEpochHistory = ref(false)
const epochHistoryItems = ref([])
const total = ref(0)
const sortMode = ref(false)

const exportDataUrl = computed(() => {
  return `studies/${studiesGeneralStore.selectedStudy.uid}/study-epochs`
})
const studyEpochHistoryTitle = computed(() => {
  if (selectedStudyEpoch.value) {
    return t('StudyEpochTable.study_epoch_history_title', {
      epochUid: selectedStudyEpoch.value.uid,
    })
  }
  return ''
})

onMounted(() => {
  unitsStore.fetchUnits()
})

async function fetchEpochsHistory() {
  const resp = await epochsApi.getStudyEpochsVersions(
    studiesGeneralStore.selectedStudy.uid
  )
  return resp.data
}

function fetchEpochs(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  params.study_uid = studiesGeneralStore.selectedStudy.uid
  return epochsApi
    .getFilteredEpochs(studiesGeneralStore.selectedStudy.uid, params)
    .then((resp) => {
      studyEpochs.value = resp.data.items
      total.value = resp.data.total
    })
}

function editEpoch(item) {
  selectedStudyEpoch.value = item
  showForm.value = true
}

function changeOrder(epochUid, newOrder) {
  epochsApi
    .reorderStudyEpoch(
      studiesGeneralStore.selectedStudy.uid,
      epochUid,
      newOrder
    )
    .then(() => {
      table.value.filterTable()
    })
    .catch((err) => {
      console.log(err)
      table.value.filterTable()
    })
}

function createEpoch() {
  selectedStudyEpoch.value = null
  showForm.value = true
}

function closeForm() {
  selectedStudyEpoch.value = null
  showForm.value = false
  table.value.filterTable()
}

function deleteEpoch(item) {
  if (item.study_visit_count > 0) {
    const epoch = item.epoch_name
    notificationHub.add({
      type: 'warning',
      msg: t('StudyEpochTable.epoch_linked_to_visits_warning', {
        epoch,
      }),
    })
    return
  }
  epochsStore
    .deleteStudyEpoch({
      studyUid: studiesGeneralStore.selectedStudy.uid,
      studyEpochUid: item.uid,
    })
    .then(() => {
      notificationHub.add({
        msg: t('StudyEpochTable.delete_success'),
      })
      table.value.filterTable()
    })
}

async function openEpochHistory(epoch) {
  selectedStudyEpoch.value = epoch
  const resp = await epochsApi.getStudyEpochVersions(
    studiesGeneralStore.selectedStudy.uid,
    epoch.uid
  )
  epochHistoryItems.value = resp.data
  showEpochHistory.value = true
}

function closeEpochHistory() {
  selectedStudyEpoch.value = null
  showEpochHistory.value = false
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
