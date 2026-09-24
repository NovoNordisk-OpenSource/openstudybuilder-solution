<template>
  <NNTable
    table-id="studies-compounds-table"
    :headers="headers"
    :items="formattedStudyCompounds"
    item-value="study_compound_uid"
    :column-data-resource="`studies/${selectedStudy.uid}/study-compounds`"
    :items-length="studiesCompoundsStore.studyCompoundTotal"
    :history-config="{
      dataFetcher: fetchCompoundsHistory,
      title: $t('StudyCompoundTable.global_history_title'),
    }"
    :export-config="{ objectLabel: 'StudyCompounds', dataUrl: exportDataUrl }"
    @filter="fetchCompounds"
  >
    <template #actions="">
      <v-btn
        data-cy="add-study-compound"
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
    <template #[`item.order`]="{ item }">
      <router-link
        :to="{
          name: 'StudyCompoundOverview',
          params: { study_id: selectedStudy.uid, id: item.study_compound_uid },
        }"
      >
        {{ item.order }}
      </router-link>
    </template>
  </NNTable>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  <v-dialog
    v-model="showForm"
    persistent
    fullscreen
    content-class="fullscreen-dialog"
  >
    <CompoundForm
      :study-compound="selectedStudyCompound"
      @added="fetchCompounds"
      @close="closeForm"
    />
  </v-dialog>
  <v-dialog
    v-model="showCompoundHistory"
    persistent
    :fullscreen="$globals.historyDialogFullscreen"
    @keydown.esc="closeStudyCompoundHistory"
  >
    <HistoryTable
      :title="studyCompoundHistoryTitle"
      :headers="headers"
      :items="compoundHistoryItems"
      @close="closeStudyCompoundHistory"
    />
  </v-dialog>
</template>

<script setup>
import { computed, inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import CompoundForm from './CompoundForm.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import dataFormating from '@/utils/dataFormating'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import filteringParameters from '@/utils/filteringParameters'
import NNTable from '@/components/tools/NNTable.vue'
import study from '@/api/study'
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
    click: editStudyCompound,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: () => !selectedStudyVersion.value,
    click: deleteStudyCompound,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openStudyCompoundHistory,
  },
]

const compoundHistoryItems = ref([])

const headers = [
  { title: '', key: 'actions', width: '5%' },
  { title: '#', key: 'order' },
  {
    title: t('StudyCompoundTable.type_of_treatment'),
    key: 'type_of_treatment.term_name',
  },
  {
    title: t('StudyCompoundTable.reason_for_missing'),
    key: 'reason_for_missing_null_value.term_name',
  },
  { title: t('StudyCompoundTable.compound'), key: 'compound.name' },
  {
    title: t('StudyCompoundTable.compound_alias'),
    key: 'compound_alias.name',
  },
  {
    title: t('StudyCompoundTable.medicinal_product'),
    key: 'medicinal_product.name',
  },
  {
    title: t('StudyCompoundTable.dose_frequency'),
    key: 'medicinal_product.dose_frequencies',
  },
]
const selectedStudyCompound = ref(null)
const showCompoundHistory = ref(false)
const showForm = ref(false)
const confirm = ref()

const selectedStudy = computed(() => studiesGeneralStore.selectedStudy)
const selectedStudyVersion = computed(
  () => studiesGeneralStore.selectedStudyVersion
)
const exportDataUrl = computed(() => {
  return `studies/${selectedStudy.value.uid}/study-compounds`
})
const studyCompoundHistoryTitle = computed(() => {
  if (selectedStudyCompound.value) {
    return t('StudyCompoundTable.study_compound_history_title', {
      studyCompoundUid: selectedStudyCompound.value.study_compound_uid,
    })
  }
  return ''
})
const formattedStudyCompounds = computed(() => {
  // clone objects to avoid mutating the store state
  const items = JSON.parse(JSON.stringify(studiesCompoundsStore.studyCompounds))
  return transformItems(items)
})

function fetchCompounds(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  params.studyUid = selectedStudy.value.uid
  studiesCompoundsStore.fetchStudyCompounds(params)
}
async function fetchCompoundsHistory() {
  const resp = await study.getStudyCompoundsAuditTrail(selectedStudy.value.uid)
  return transformItems(resp.data)
}
async function deleteStudyCompound(studyCompound) {
  const options = { type: 'warning' }
  let msg
  if (studyCompound.compound) {
    const compound = studyCompound.compound.name
    const context = { compound }
    if (studyCompound.study_compound_dosing_count) {
      context.compoundDosings = studyCompound.study_compound_dosing_count
      msg = t('StudyCompoundTable.confirm_delete_cascade', context)
    } else {
      msg = t('StudyCompoundTable.confirm_delete', context)
    }
  } else {
    msg = t('StudyCompoundTable.confirm_delete_na')
  }
  if (!(await confirm.value.open(msg, options))) {
    return
  }
  studiesCompoundsStore
    .deleteStudyCompound(
      selectedStudy.value.uid,
      studyCompound.study_compound_uid
    )
    .then(() => {
      notificationHub.add({
        msg: t('StudyCompoundTable.delete_compound_success'),
      })
    })
}
function editStudyCompound(studyCompound) {
  const originalItem = studiesCompoundsStore.studyCompounds.find(
    (item) => item.study_compound_uid === studyCompound.study_compound_uid
  )
  selectedStudyCompound.value = originalItem
  showForm.value = true
}
async function openStudyCompoundHistory(studyCompound) {
  selectedStudyCompound.value = studyCompound
  const resp = await study.getStudyCompoundAuditTrail(
    selectedStudy.value.uid,
    studyCompound.study_compound_uid
  )
  compoundHistoryItems.value = transformItems(resp.data)
  showCompoundHistory.value = true
}
function closeStudyCompoundHistory() {
  selectedStudyCompound.value = null
  showCompoundHistory.value = false
}
function closeForm() {
  showForm.value = false
  selectedStudyCompound.value = null
}
function transformItems(items) {
  const result = []
  for (const item of items) {
    const newItem = JSON.parse(JSON.stringify(item))
    if (newItem.compound) {
      newItem.compound.is_name_inn = dataFormating.yesno(
        newItem.compound.is_name_inn
      )
    }
    if (newItem.compound_alias) {
      newItem.compound_alias.is_preferred_synonym = dataFormating.yesno(
        newItem.is_preferred_synonym
      )
    }
    if (newItem.medicinal_product) {
      newItem.medicinal_product.dose_frequencies = dataFormating.names(
        newItem.medicinal_product.dose_frequencies || []
      )
    }
    result.push(newItem)
  }
  return result
}
</script>
