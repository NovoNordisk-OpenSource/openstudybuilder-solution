<template>
  <NNTable
    table-id="studies-compound-dosings-table"
    :headers="headers"
    :items="formattedStudyCompoundDosings"
    :items-length="studiesCompoundsStore.studyCompoundDosingTotal"
    item-value="study_compound_dosing_uid"
    :column-data-resource="`studies/${selectedStudy.uid}/study-compound-dosings`"
    :history-config="{
      dataFetcher: fetchCompoundDosingsHistory,
      title: $t('StudyCompoundDosingTable.global_history_title'),
    }"
    :export-config="{
      objectLabel: 'StudyCompoundDosings',
      dataUrl: exportDataUrl,
    }"
    @filter="fetchStudyCompoundDosings"
  >
    <template #actions="">
      <v-btn
        data-cy="add-study-compound-dosing"
        class="ml-2"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        :disabled="
          !accessGuard.checkPermission($roles.STUDY_WRITE) ||
          selectedStudyVersion !== null
        "
        @click.stop="showForm = true"
      >
        <v-icon>mdi-plus</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ $t('StudyCompoundForm.add_title') }}
        </v-tooltip>
      </v-btn>
    </template>
    <template #[`item.actions`]="{ item }">
      <ActionsMenu :actions="actions" :item="item" />
    </template>
  </NNTable>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  <v-dialog
    v-model="showForm"
    persistent
    fullscreen
    content-class="fullscreen-dialog"
  >
    <CompoundDosingForm
      :study-compound-dosing-uid="
        selectedStudyCompoundDosing?.study_compound_dosing_uid ?? null
      "
      @close="closeForm"
    />
  </v-dialog>
  <v-dialog
    v-model="showHistory"
    persistent
    :fullscreen="$globals.historyDialogFullscreen"
    @keydown.esc="closeHistory"
  >
    <HistoryTable
      :title="studyCompoundDosingHistoryTitle"
      :headers="headers"
      :items="compoundDosingHistoryItems"
      @close="closeHistory"
    />
  </v-dialog>
</template>

<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import CompoundDosingForm from './CompoundDosingForm.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import dataFormating from '@/utils/dataFormating'
import NNTable from '@/components/tools/NNTable.vue'
import study from '@/api/study'
import filteringParameters from '@/utils/filteringParameters'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesCompoundsStore } from '@/stores/studies-compounds'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const roles = inject('roles')
const accessGuard = useAccessGuard()
const studiesCompoundsStore = useStudiesCompoundsStore()
const studiesGeneralStore = useStudiesGeneralStore()

const actions = [
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: () => !selectedStudyVersion.value,
    click: editStudyCompoundDosing,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: () => !selectedStudyVersion.value,
    click: deleteStudyCompoundDosing,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openHistory,
  },
]

const headers = [
  { title: '', key: 'actions', width: '5%' },
  { title: '#', key: 'order' },
  {
    title: t('StudyCompoundDosingTable.element'),
    key: 'study_element.name',
  },
  {
    title: t('StudyCompoundDosingTable.compound'),
    key: 'study_compound.compound.name',
  },
  {
    title: t('StudyCompoundDosingTable.medicinal_product'),
    key: 'study_compound.medicinal_product.name',
  },
  {
    title: t('StudyCompoundDosingTable.compound_alias'),
    key: 'study_compound.compound_alias.name',
  },
  {
    title: t('StudyCompoundDosingTable.preferred_alias'),
    key: 'study_compound.compound_alias.is_preferred_synonym',
  },
  {
    title: t('StudyCompoundDosingTable.dose_value'),
    key: 'dose_value',
  },
  {
    title: t('StudyCompoundDosingTable.dose_frequency'),
    key: 'dose_frequency.term_name',
  },
  {
    title: t('StudyCompoundDosingTable.composition'),
    key: 'composition',
  },
]
const selectedStudyCompoundDosing = ref(null)
const showForm = ref(false)
const showHistory = ref(false)
const compoundDosingHistoryItems = ref([])
const confirm = ref()

const selectedStudy = computed(() => studiesGeneralStore.selectedStudy)
const selectedStudyVersion = computed(
  () => studiesGeneralStore.selectedStudyVersion
)
const exportDataUrl = computed(() => {
  return `studies/${selectedStudy.value.uid}/study-compound-dosings`
})
const formattedStudyCompoundDosings = computed(() => {
  // clone objects to avoid mutating the store state
  const items = JSON.parse(
    JSON.stringify(studiesCompoundsStore.studyCompoundDosings)
  )
  return transformItems(items)
})
const studyCompoundDosingHistoryTitle = computed(() => {
  if (selectedStudyCompoundDosing.value) {
    return t('StudyCompoundDosingTable.study_compound_dosing_history_title', {
      studyCompoundDosingUid:
        selectedStudyCompoundDosing.value.study_compound_dosing_uid,
    })
  }
  return ''
})

onMounted(() => {
  studiesCompoundsStore.fetchStudyCompoundDosings(selectedStudy.value.uid)
})

function fetchStudyCompoundDosings(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  params.studyUid = selectedStudy.value.uid
  studiesCompoundsStore.fetchStudyCompoundDosings(
    selectedStudy.value.uid,
    params
  )
}

async function deleteStudyCompoundDosing(studyCompoundDosing) {
  const options = { type: 'warning' }
  const compound = studyCompoundDosing.study_compound.compound_alias.name
  const element = studyCompoundDosing.study_element.name
  const msg = t('StudyCompoundDosingTable.confirm_delete', {
    compound,
    element,
  })
  if (!(await confirm.value.open(msg, options))) {
    return
  }
  studiesCompoundsStore
    .deleteStudyCompoundDosing(
      selectedStudy.value.uid,
      studyCompoundDosing.study_compound_dosing_uid
    )
    .then(() => {
      notificationHub.add({
        msg: t('StudyCompoundDosingTable.delete_success'),
      })
    })
}
function editStudyCompoundDosing(studyCompoundDosing) {
  selectedStudyCompoundDosing.value = studyCompoundDosing
  showForm.value = true
}
async function fetchCompoundDosingsHistory() {
  const resp = await study.getStudyCompoundDosingsAuditTrail(
    selectedStudy.value.uid
  )
  return transformItems(resp.data)
}
async function openHistory(item) {
  selectedStudyCompoundDosing.value = item
  const resp = await study.getStudyCompoundDosingAuditTrail(
    selectedStudy.value.uid,
    item.study_compound_dosing_uid
  )
  compoundDosingHistoryItems.value = transformItems(resp.data)
  showHistory.value = true
}
function closeHistory() {
  selectedStudyCompoundDosing.value = null
  showHistory.value = false
}
function closeForm() {
  showForm.value = false
  selectedStudyCompoundDosing.value = null
}
function transformItems(items) {
  const result = []
  for (const item of items) {
    const newItem = { ...item }
    if (newItem.study_compound.compound_alias) {
      newItem.study_compound.compound_alias.is_preferred_synonym =
        dataFormating.yesno(
          newItem.study_compound.compound_alias.is_preferred_synonym
        )
    }
    if (newItem.dose_value) {
      newItem.dose_value = dataFormating.numericValue(newItem.dose_value)
    }
    result.push(newItem)
  }
  return result
}
</script>
