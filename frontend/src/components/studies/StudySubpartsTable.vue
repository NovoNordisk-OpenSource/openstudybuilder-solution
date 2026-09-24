<template>
  <NNTable
    ref="tableRef"
    table-id="studies-subparts-table"
    :headers="headers"
    :items="paginatedItems"
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
            subpartStudyId: studiesGeneralStore.studyId,
            parentStudyId:
              studiesGeneralStore.selectedStudy.study_parent_part.study_id,
          })
        : $t('NNTable.no_data')
    "
    :loading-watcher="loading"
    disable-filtering
    hide-search-field
    :modifiable-table="false"
    :hide-default-body="sortMode && items.length > 0"
    :history-config="{
      externalHeaders: historyHeaders,
      dataFetcher: fetchStudyHistory,
      title: $t('StudySubparts.subparts_history_title'),
    }"
    :export-config="{
      dataUrlParams: exportDataUrlParams,
      objectLabel: 'StudySubparts',
      dataUrl: exportDataUrl,
    }"
    @filter="fetchStudySubparts"
  >
    <template #beforeSearch>
      <v-text-field
        v-model="searchString"
        clearable
        clear-icon="mdi-close"
        prepend-inner-icon="mdi-magnify"
        :label="$t('_global.search')"
        single-line
        color="nnBaseBlue"
        hide-details
        style="min-width: 240px; max-width: 300px"
        class="searchFieldLabel ml-0"
        data-cy="search-field"
      />
    </template>
    <template #afterSwitches>
      <div :title="$t('NNTableTooltips.reorder_content')">
        <v-switch
          v-model="sortMode"
          :label="$t('NNTable.reorder_content')"
          hide-details
          class="mr-6"
          :disabled="
            !accessGuard.checkPermission($roles.STUDY_WRITE) ||
            searchString?.length > 0
          "
        />
      </div>
    </template>
    <template #tbody>
      <tbody v-show="sortMode" ref="parent">
        <tr v-for="item in items" :key="item.uid">
          <td>
            <v-icon size="small"> mdi-sort </v-icon>
          </td>
          <td>{{ item.id }}</td>
          <td>
            {{ item.acronym }}
          </td>
          <td>
            {{ item.subpart_id }}
          </td>
          <td>
            {{ item.subpart_acronym }}
            <v-tooltip
              v-if="!isValidSubpartAcronym(item.subpart_acronym)"
              location="top"
            >
              <template #activator="{ props }">
                <v-icon v-bind="props" size="small" color="error" class="ml-1">
                  mdi-alert
                </v-icon>
              </template>
              {{ $t('StudySubparts.invalid_subpart_acronym') }}
            </v-tooltip>
          </td>
          <td>
            {{ item.description }}
          </td>
          <td>
            {{ $filters.date(item.version_start_date) }}
          </td>
          <td>{{ item.version_author }}</td>
        </tr>
      </tbody>
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
          Boolean(studiesGeneralStore.selectedStudy.study_parent_part) ||
          studiesGeneralStore.selectedStudyVersion !== null
        "
        @click.stop="openForm()"
      >
        <v-icon>mdi-plus</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ $t('StudySubparts.add_subpart') }}
        </v-tooltip>
      </v-btn>
    </template>
    <template #[`item.actions`]="{ item }">
      <ActionsMenu :actions="actions" :item="item" />
    </template>
    <template #[`item.subpart_acronym`]="{ item }">
      {{ item.subpart_acronym }}
      <v-tooltip
        v-if="!isValidSubpartAcronym(item.subpart_acronym)"
        location="top"
      >
        <template #activator="{ props }">
          <v-icon v-bind="props" size="small" color="error" class="ml-1">
            mdi-alert
          </v-icon>
        </template>
        {{ $t('StudySubparts.invalid_subpart_acronym') }}
      </v-tooltip>
    </template>
    <template #[`item.version_start_date`]="{ item }">
      {{ $filters.date(item.version_start_date) }}
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
import { computed, inject, ref, watch } from 'vue'
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
const notificationHub = inject('notificationHub')
const roles = inject('roles')
const accessGuard = useAccessGuard()
const studiesGeneralStore = useStudiesGeneralStore()
const tableRef = ref()

const [parent, items] = useDragAndDrop([], {
  onDragend: (event) => {
    const newOrder =
      (event.draggedNode.data.value
        ? event.draggedNode.data.value.subpart_id.charCodeAt(0) - 96
        : 0) -
      (event.state.initialIndex - event.state.targetIndex)
    changeOrder(event.draggedNode.data.value.uid, newOrder)
  },
})

const filteredItems = ref([])
const paginatedItems = ref([])

const total = ref(0)
const headers = [
  { title: '', key: 'actions', width: '1%' },
  {
    title: t('StudySubparts.study_id'),
    key: 'id',
  },
  {
    title: t('StudySubparts.study_acronym'),
    key: 'acronym',
  },
  {
    title: t('StudySubparts.subpart_id'),
    key: 'subpart_id',
  },
  {
    title: t('StudySubparts.subpart_acronym'),
    key: 'subpart_acronym',
  },
  {
    title: t('_global.description'),
    key: 'description',
  },
  {
    title: t('_global.modified'),
    key: 'version_start_date',
  },
  {
    title: t('_global.modified_by'),
    key: 'version_author',
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
const searchString = ref('')

watch(searchString, () => {
  tableRef.value.filterTable()
})

const studySubpartHistoryTitle = computed(() => {
  if (selectedSubpart.value) {
    return t('StudySubparts.subpart_history_title', {
      subpartUid: selectedSubpart.value.uid,
    })
  }
  return ''
})

const exportDataUrl = computed(() => {
  return `studies`
})

const exportDataUrlParams = computed(() => {
  return {
    filters: {
      'study_parent_part.uid': {
        v: [studiesGeneralStore.selectedStudy.uid],
      },
    },
  }
})

function fetchStudySubparts(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  studies.getAllList(params).then((resp) => {
    items.value = resp.data.filter(
      (item) =>
        item.subpart_acronym !== null &&
        item.main_id ===
          studiesGeneralStore.selectedStudy.current_metadata
            .identification_metadata.study_id
    )
    filteredItems.value = items.value
    total.value = items.value.length
    handlePagination(params)
    loading.value = false
  })
}
function handlePagination(params) {
  // Free text search
  let filteredTotal = 0
  if (searchString.value?.length >= 3) {
    filteredItems.value = filteredItems.value.filter((obj) =>
      Object.values(obj).some((value) =>
        String(value).toLowerCase().includes(searchString.value.toLowerCase())
      )
    )
  }

  // Pagination
  filteredTotal = filteredItems.value.length
  paginatedItems.value =
    params.page_size > 0
      ? filteredItems.value.slice(
          (params.page_number - 1) * params.page_size,
          params.page_number * params.page_size
        )
      : filteredItems.value
  total.value = filteredTotal
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
  subpart.study_parent_part_uid = null
  subpart.current_metadata = {
    identification_metadata: {
      study_number: null,
    },
  }
  studies.updateStudy(subpart.uid, subpart).then(() => {
    fetchStudySubparts()
    notificationHub.add({ msg: t('StudySubparts.substudy_removed') })
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
    return {
      items: resp.data.items,
      total: resp.data.total,
    }
  }
}
async function openSubpartHistory(subpart) {
  selectedSubpart.value = subpart
  showSubpartHistory.value = true
}
async function fetchSubpartHistory(options) {
  let params = filteringParameters.prepareParameters(options)
  params.is_subpart = true
  const resp = await studies.getStudyAuditTrail(
    selectedSubpart.value.uid,
    params
  )
  subpartHistoryItems.value = resp.data.items
  subpartHistoryItemsTotal.value = resp.data.total
}
function isValidSubpartAcronym(value) {
  if (!value) return false
  return /^[A-Z0-9]+$/.test(value) && value.length <= 10
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
