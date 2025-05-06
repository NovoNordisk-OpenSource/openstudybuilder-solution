<template>
  <NNTable
    :headers="headers"
    :items="items"
    :column-data-resource="!sortMode ? 'studies' : undefined"
    :items-length="total"
    item-value="uid"
    :initial-sort-by="[
      {
        key: 'current_metadata.identification_metadata.subpart_id',
        order: 'asc',
      },
    ]"
    :no-data-text="
      Boolean(studiesGeneralStore.selectedStudy.study_parent_part)
        ? $t('StudySubparts.nested_subparts_warning', {
            subpartStudyId:
              studiesGeneralStore.selectedStudy.current_metadata
                .identification_metadata.study_id,
            parentStudyId:
              studiesGeneralStore.selectedStudy.study_parent_part.study_id,
          })
        : $t('NNTable.no_data')
    "
    :loading-watcher="loading"
    :history-data-fetcher="fetchStudyHistory"
    :history-title="$t('StudySubparts.subparts_history_title')"
    :history-external-headers="historyHeaders"
    :disable-filtering="sortMode"
    :hide-default-body="sortMode && items.length > 0"
    @filter="fetchStudySubparts"
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
        <tr v-for="item in items" :key="item.uid">
          <td>
            <v-icon size="small"> mdi-sort </v-icon>
          </td>
          <td>{{ item.study_parent_part.study_id }}</td>
          <td>
            {{ item.current_metadata.identification_metadata.study_acronym }}
          </td>
          <td>
            {{ item.current_metadata.identification_metadata.subpart_id }}
          </td>
          <td>
            {{
              item.current_metadata.identification_metadata
                .study_subpart_acronym
            }}
          </td>
          <td>
            {{ item.current_metadata.identification_metadata.description }}
          </td>
          <td>
            {{
              $filters.date(
                item.current_metadata.version_metadata.version_timestamp
              )
            }}
          </td>
          <td>{{ item.current_metadata.version_metadata.version_author }}</td>
        </tr>
      </tbody>
    </template>
    <template #actions="">
      <v-btn
        class="ml-2"
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        :title="$t('StudySubparts.add_subpart')"
        :disabled="
          !accessGuard.checkPermission($roles.STUDY_WRITE) ||
          Boolean(studiesGeneralStore.selectedStudy.study_parent_part) ||
          studiesGeneralStore.selectedStudyVersion !== null
        "
        icon="mdi-plus"
        @click.stop="openForm()"
      />
    </template>
    <template #[`item.actions`]="{ item }">
      <ActionsMenu :actions="actions" :item="item" />
    </template>
    <template
      #[`item.current_metadata.version_metadata.version_timestamp`]="{ item }"
    >
      {{
        $filters.date(item.current_metadata.version_metadata.version_timestamp)
      }}
    </template>
  </NNTable>
  <v-dialog
    v-model="form"
    persistent
    fullscreen
    content-class="fullscreen-dialog"
  >
    <StudySubpartForm @close="closeForms()" />
  </v-dialog>
  <StudySubpartEditForm
    :open="editForm"
    :edited-subpart="selectedSubpart"
    @close="closeForms()"
  />
  <v-dialog
    v-model="showSubpartHistory"
    persistent
    :fullscreen="$globals.historyDialogFullscreen"
    @keydown.esc="closeSubpartHistory"
  >
    <HistoryTable
      :title="studySubpartHistoryTitle"
      :headers="historyHeaders"
      :items="subpartHistoryItems"
      :items-total="subpartHistoryItemsTotal"
      @refresh="(options) => fetchSubpartHistory(options)"
      @close="closeSubpartHistory"
    />
  </v-dialog>
</template>

<script setup>
import { computed, inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import studies from '@/api/study'
import filteringParameters from '@/utils/filteringParameters'
import NNTable from '@/components/tools/NNTable.vue'
import StudySubpartForm from '@/components/studies/StudySubpartForm.vue'
import StudySubpartEditForm from '@/components/studies/StudySubpartEditForm.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import { useDragAndDrop } from '@formkit/drag-and-drop/vue'

const { t } = useI18n()
const eventBusEmit = inject('eventBusEmit')
const roles = inject('roles')
const accessGuard = useAccessGuard()
const studiesGeneralStore = useStudiesGeneralStore()

const [parent, items] = useDragAndDrop([], {
  onDragend: (event) => {
    const newOrder =
      (event.draggedNode.data.value.current_metadata
        ? event.draggedNode.data.value.current_metadata.identification_metadata.subpart_id.charCodeAt(
            0
          ) - 96
        : 0) -
      (event.state.initialIndex - event.state.targetIndex)
    changeOrder(event.draggedNode.data.value.uid, newOrder)
  },
})

const total = ref(0)
const headers = [
  { title: '', key: 'actions', width: '1%' },
  { title: t('StudySubparts.study_id'), key: 'study_parent_part.study_id' },
  {
    title: t('StudySubparts.study_acronym'),
    key: 'current_metadata.identification_metadata.study_acronym',
  },
  {
    title: t('StudySubparts.subpart_id'),
    key: 'current_metadata.identification_metadata.subpart_id',
  },
  {
    title: t('StudySubparts.subpart_acronym'),
    key: 'current_metadata.identification_metadata.study_subpart_acronym',
  },
  {
    title: t('_global.description'),
    key: 'current_metadata.identification_metadata.description',
  },
  {
    title: t('_global.modified'),
    key: 'current_metadata.version_metadata.version_timestamp',
  },
  {
    title: t('_global.modified_by'),
    key: 'current_metadata.version_metadata.version_author',
  },
]
const historyHeaders = [
  { title: t('StudySubparts.study_id'), key: 'subpart_uid' },
  { title: t('StudySubparts.study_acronym'), key: 'study_acronym' },
  { title: t('StudySubparts.subpart_id'), key: 'subpart_id' },
  { title: t('_global.modified_by'), key: 'author_username' },
]
const actions = [
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    accessRole: roles.STUDY_WRITE,
    click: editSubpart,
  },
  {
    label: t('_global.remove'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    accessRole: roles.STUDY_WRITE,
    click: removeSubpart,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openSubpartHistory,
  },
]
const form = ref(false)
const editForm = ref(false)
const selectedSubpart = ref(null)
const loading = ref(false)
const subpartHistoryItems = ref([])
const subpartHistoryItemsTotal = ref(0)
const showSubpartHistory = ref(false)
const sortMode = ref(false)

const studySubpartHistoryTitle = computed(() => {
  if (selectedSubpart.value) {
    return t('StudySubparts.subpart_history_title', {
      subpartUid: selectedSubpart.value.uid,
    })
  }
  return ''
})

function fetchStudySubparts(filters, options, filtersUpdated) {
  if (filters) {
    const filtersObj = JSON.parse(filters)
    filtersObj['study_parent_part.uid'] = {
      v: [studiesGeneralStore.selectedStudy.uid],
    }
    filters = filtersObj
  } else {
    filters = {
      'study_parent_part.uid': { v: [studiesGeneralStore.selectedStudy.uid] },
    }
  }
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  params.filters = JSON.stringify(params.filters)
  studies.get(params).then((resp) => {
    items.value = resp.data.items
    total.value = resp.data.total
    loading.value = false
  })
}
function openForm() {
  form.value = true
}
function closeForms() {
  selectedSubpart.value = {}
  form.value = false
  editForm.value = false
  fetchStudySubparts()
}
function editSubpart(subpart) {
  selectedSubpart.value = subpart
  editForm.value = true
}
function removeSubpart(subpart) {
  delete subpart.current_metadata.study_description
  subpart.study_parent_part_uid = null
  subpart.current_metadata.identification_metadata.study_number = null
  studies.updateStudy(subpart.uid, subpart).then(() => {
    fetchStudySubparts()
    eventBusEmit('notification', { msg: t('StudySubparts.substudy_removed') })
  })
}

function changeOrder(uid, newOrder) {
  loading.value = true
  const data = {
    uid: uid,
    subpart_id: String.fromCharCode(
      Math.floor(newOrder) + 'a'.charCodeAt(0) - 1
    ).toLowerCase(),
  }
  studies
    .reorderStudySubpart(studiesGeneralStore.selectedStudy.uid, data)
    .then(() => {
      fetchStudySubparts()
    })
}
async function fetchStudyHistory(options) {
  let params = filteringParameters.prepareParameters(options)
  params.is_subpart = false
  const resp = await studies.getStudyAuditTrail(
    studiesGeneralStore.selectedStudy.uid,
    params
  )
  if (options) {
    const firstIndex = (options.page - 1) * options.itemsPerPage
    const lastIndex = options.page * options.itemsPerPage
    return {
      items: resp.data.slice(firstIndex, lastIndex),
      total: resp.data.length,
    }
  }
}
async function openSubpartHistory(subpart) {
  selectedSubpart.value = subpart
  const params = {
    is_subpart: true,
  }
  const resp = await studies.getStudyAuditTrail(subpart.uid, params)
  subpartHistoryItems.value = resp.data.slice(0, 9)
  subpartHistoryItemsTotal.value = resp.data.length
  showSubpartHistory.value = true
}
async function fetchSubpartHistory(options) {
  let params = filteringParameters.prepareParameters(options)
  params.is_subpart = true
  const resp = await studies.getStudyAuditTrail(
    selectedSubpart.value.uid,
    params
  )
  const firstIndex = (options.page - 1) * options.itemsPerPage
  const lastIndex = options.page * options.itemsPerPage
  subpartHistoryItems.value = resp.data.slice(firstIndex, lastIndex)
}
function closeSubpartHistory() {
  selectedSubpart.value = {}
  showSubpartHistory.value = false
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
