<template>
  <div>
    <NNTable
      ref="table"
      table-id="studies-elements-table"
      :headers="headers"
      :items="studyElements"
      :items-length="total"
      :sort-desc="sortDesc"
      item-value="element_uid"
      :column-data-resource="
        !sortMode
          ? `studies/${studiesGeneralStore.selectedStudy.uid}/study-elements`
          : undefined
      "
      :disable-filtering="sortMode"
      :hide-default-body="sortMode && studyElements.length > 0"
      :history-config="{
        dataFetcher: fetchElementsHistory,
        title: $t('StudyElements.global_history_title'),
      }"
      :export-config="{ objectLabel: 'StudyElements', dataUrl: exportDataUrl }"
      @filter="getStudyElements"
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
          <tr v-for="element in studyElements" :key="element.element_uid">
            <td>
              <v-icon size="small"> mdi-sort </v-icon>
            </td>
            <td>{{ element.order }}</td>
            <td>{{ element.element_type.sponsor_preferred_name }}</td>
            <td>{{ element.element_subtype.sponsor_preferred_name }}</td>
            <td>{{ element.name }}</td>
            <td>{{ element.short_name }}</td>
            <td>{{ element.start_rule }}</td>
            <td>{{ element.end_rule }}</td>
            <td>
              <v-chip
                :color="element.element_colour"
                size="small"
                variant="flat"
              >
                <span>&nbsp;</span>
                <span>&nbsp;</span>
              </v-chip>
            </td>
            <td>{{ element.description }}</td>
            <td>{{ $filters.date(element.start_date) }}</td>
            <td>{{ element.author_username }}</td>
          </tr>
        </tbody>
      </template>
      <template #[`item.name`]="{ item }">
        <router-link
          :to="{
            name: 'StudyElementOverview',
            params: {
              study_id: studiesGeneralStore.selectedStudy.uid,
              id: item.element_uid,
            },
          }"
        >
          {{ item.name }}
        </router-link>
      </template>
      <template #[`item.element_colour`]="{ item }">
        <v-chip
          :data-cy="'color=' + item.element_colour"
          :color="item.element_colour"
          size="small"
          variant="flat"
        >
          <span>&nbsp;</span>
          <span>&nbsp;</span>
        </v-chip>
      </template>
      <template #[`item.element_type.term_name`]="{ item }">
        <CTCodelistTermDisplay :term="item.element_type" />
      </template>
      <template #[`item.element_subtype.term_name`]="{ item }">
        <CTCodelistTermDisplay :term="item.element_subtype" />
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
        <div class="pr-0 mr-0">
          <ActionsMenu :actions="actions" :item="item" />
        </div>
      </template>
      <template #[`item.element_type`]="{ item }">
        {{ getElementType(item) }}
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
          @click.stop="showForm = true"
        >
          <v-icon>mdi-plus</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('StudyElements.add_element') }}
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
      <StudyElementsForm :edited-element="activeElement" @close="closeForm" />
    </v-dialog>
    <v-dialog
      v-model="showElementHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeElementHistory"
    >
      <HistoryTable
        :title="studyElementHistoryTitle"
        :headers="headers"
        :items="elementHistoryItems"
        :items-total="elementHistoryItems.length"
        @close="closeElementHistory"
      />
    </v-dialog>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  </div>
</template>

<script setup>
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import CTCodelistTermDisplay from '../tools/CTCodelistTermDisplay.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StudyElementsForm from './StudyElementsForm.vue'
import armsApi from '@/api/arms'
import terms from '@/api/controlledTerminology/terms'
import filteringParameters from '@/utils/filteringParameters'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { computed, onMounted, inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDragAndDrop } from '@formkit/drag-and-drop/vue'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const roles = inject('roles')
const studiesGeneralStore = useStudiesGeneralStore()
const accessGuard = useAccessGuard()
const table = ref()
const confirm = ref()

const [parent, studyElements] = useDragAndDrop([], {
  onDragend: (event) => {
    const newOrder =
      event.draggedNode.data.value.order -
      (event.state.initialIndex - event.state.targetIndex)
    changeOrder(event.draggedNode.data.value.element_uid, newOrder)
  },
})

const actions = [
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    click: editStudyElement,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    click: deleteStudyElement,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openElementHistory,
  },
]
const headers = [
  { title: '', key: 'actions', width: '1%' },
  { title: '#', key: 'order', width: '5%' },
  {
    title: t('StudyElements.el_type'),
    key: 'element_type.term_name',
  },
  {
    title: t('StudyElements.el_sub_type'),
    key: 'element_subtype.term_name',
  },
  { title: t('StudyElements.el_name'), key: 'name' },
  { title: t('StudyElements.el_short_name'), key: 'short_name' },
  { title: t('StudyElements.el_start_rule'), key: 'start_rule' },
  { title: t('StudyElements.el_end_rule'), key: 'end_rule' },
  { title: t('StudyElements.colour'), key: 'element_colour' },
  { title: t('_global.description'), key: 'description' },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.modified_by'), key: 'author_username' },
]
const showForm = ref(false)
const sortDesc = ref(false)
const activeElement = ref({})
const elementTypes = ref([])
const total = ref(0)
const showElementHistory = ref(false)
const elementHistoryItems = ref([])
const selectedElement = ref(null)
const sortMode = ref(false)

const exportDataUrl = computed(() => {
  return `studies/${studiesGeneralStore.selectedStudy.uid}/study-elements`
})
const studyElementHistoryTitle = computed(() => {
  if (selectedElement.value) {
    return t('StudyElements.study_element_history_title', {
      elementUid: selectedElement.value.element_uid,
    })
  }
  return ''
})

onMounted(() => {
  studiesGeneralStore.fetchUnits()
  terms.getTermsByCodelist('elementTypes').then((resp) => {
    elementTypes.value = resp.data.items
  })
})

async function fetchElementsHistory() {
  const resp = await armsApi.getStudyElementsVersions(
    studiesGeneralStore.selectedStudy.uid
  )
  return resp.data
}

function getStudyElements(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  params.study_uid = studiesGeneralStore.selectedStudy.uid
  armsApi
    .getStudyElements(studiesGeneralStore.selectedStudy.uid, params)
    .then((resp) => {
      studyElements.value = resp.data.items
      total.value = resp.data.total
    })
}

async function deleteStudyElement(element) {
  const options = { type: 'warning' }
  let msg
  const context = { element: element.name }
  if (element.study_compound_dosing_count) {
    context.compoundDosings = element.study_compound_dosing_count
    msg = t('StudyElements.confirm_delete_cascade', context)
  } else {
    msg = t('StudyElements.confirm_delete', context)
  }
  if (!(await confirm.value.open(msg, options))) {
    return
  }
  armsApi
    .deleteStudyElement(
      studiesGeneralStore.selectedStudy.uid,
      element.element_uid
    )
    .then(() => {
      notificationHub.add({
        msg: t('StudyElements.el_deleted'),
      })
      table.value.filterTable()
    })
}

function editStudyElement(item) {
  activeElement.value = item
  showForm.value = true
}

function closeForm() {
  activeElement.value = {}
  showForm.value = false
  table.value.filterTable()
}

async function openElementHistory(element) {
  selectedElement.value = element
  const resp = await armsApi.getStudyElementVersions(
    studiesGeneralStore.selectedStudy.uid,
    element.element_uid
  )
  elementHistoryItems.value = resp.data
  showElementHistory.value = true
}

function closeElementHistory() {
  showElementHistory.value = false
  selectedElement.value = null
}

function getElementType(item) {
  const type = elementTypes.value.filter((el) => el.term_uid === item.code)[0]
  if (item.code && type) {
    return type.sponsor_preferred_name
  }
}

function changeOrder(elementUid, newOrder) {
  armsApi
    .updateElementOrder(
      studiesGeneralStore.selectedStudy.uid,
      elementUid,
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
