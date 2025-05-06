<template>
  <div class="page-title d-flex align-center ml-4">
    {{ $t('StudyFootnoteTable.footnotes') }}
  </div>
  <NNTable
    ref="table"
    :headers="headers"
    :items="footnotesStore.studyFootnotes"
    item-value="uid"
    :column-data-resource="`studies/${studiesGeneralStore.selectedStudy.uid}/study-soa-footnotes`"
    export-object-label="StudyFootnotes"
    hide-default-switches
    :modifiable-table="false"
    hide-export-button
    :export-data-url="exportDataUrl"
    :items-length="footnotesStore.total"
    :history-data-fetcher="fetchFootnotesHistory"
    :history-title="$t('StudyFootnoteTable.global_history_title')"
    :history-html-fields="historyHtmlFields"
    @filter="fetchFootnotes"
  >
    <template #actions>
      <v-btn
        class="ml-2"
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        data-cy="add-study-footnote"
        :title="$t('StudyFootnoteForm.add_title')"
        :disabled="
          !accessGuard.checkPermission($roles.STUDY_WRITE) ||
          studiesGeneralStore.selectedStudyVersion !== null
        "
        icon="mdi-plus"
        @click="enableFootnoteMode()"
      />
    </template>
    <template #[`item.order`]="{ item }">
      {{ $filters.footnoteSymbol(item.order) }}
    </template>
    <template #[`item.name`]="{ item }">
      <template v-if="item.template">
        <NNParameterHighlighter
          :name="item.template.name"
          default-color="orange"
        />
      </template>
      <template v-else>
        <NNParameterHighlighter
          :name="item.footnote.name"
          :show-prefix-and-postfix="false"
        />
      </template>
    </template>
    <template #[`item.referenced_items`]="{ item }">
      <div v-if="item.referenced_items.length > 0 && activeFootnote !== item">
        {{ $filters.itemNames(item.referenced_items) }}
      </div>
      <div
        v-else-if="item.referenced_items.length > 0 && activeFootnote === item"
        style="display: flex"
      >
        <div v-for="i in item.referenced_items" :key="i.item_uid">
          <v-chip
            color="nnBaseBlue"
            class="mr-2"
            closable
            @click:close="removeElementFromFootnote(item, i)"
          >
            {{ i.item_name }}
          </v-chip>
        </div>
      </div>
      <div v-else class="warning">
        <v-icon class="mr-2">mdi-alert-circle-outline</v-icon
        >{{ $t('StudyFootnoteTable.not_linked_warning') }}
      </div>
    </template>
    <template #[`item.start_date`]="{ item }">
      {{ $filters.date(item.start_date) }}
    </template>
    <template #[`item.actions`]="{ item }">
      <ActionsMenu
        :actions="actions"
        :item="item"
        :badge="actionsMenuBadge(item)"
      />
    </template>
  </NNTable>
  <StudyFootnoteEditForm
    :open="showEditForm"
    :study-footnote="selectedFootnote"
    @close="closeEditForm"
    @updated="table.filterTable()"
    @enable-footnote-mode="enableFootnoteMode"
  />
  <v-dialog
    v-model="showHistory"
    persistent
    :fullscreen="$globals.historyDialogFullscreen"
    @keydown.esc="closeHistory"
  >
    <HistoryTable
      :title="studyFootnoteHistoryTitle"
      :headers="headers"
      :items="footnoteHistoryItems"
      :items-total="footnoteHistoryItems.length"
      :html-fields="historyHtmlFields"
      @close="closeHistory"
    />
  </v-dialog>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import filteringParameters from '@/utils/filteringParameters'
import StudyFootnoteEditForm from '@/components/studies/StudyFootnoteEditForm.vue'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter.vue'
import NNTable from '@/components/tools/NNTable.vue'
import study from '@/api/study'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import dataFormating from '@/utils/dataFormating'
import statuses from '@/constants/statuses'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudyActivitiesStore } from '@/stores/studies-activities'
import { useFootnotesStore } from '@/stores/studies-footnotes'

const { t } = useI18n()
const eventBusEmit = inject('eventBusEmit')
const roles = inject('roles')
const emit = defineEmits([
  'enableFootnoteMode',
  'update',
  'removeElementFromFootnote',
])
const route = useRoute()

const accessGuard = useAccessGuard()
const studiesGeneralStore = useStudiesGeneralStore()
const activitiesStore = useStudyActivitiesStore()
const footnotesStore = useFootnotesStore()

const actions = [
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    click: editStudyFootnote,
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('StudyFootnoteTable.link_unlink'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    click: enableFootnoteMode,
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('StudyFootnoteTable.update_footnote_version'),
    icon: 'mdi-bell-ring-outline',
    iconColorFunc: footnoteUpdateAborted,
    condition: (item) =>
      needUpdate(item) && !studiesGeneralStore.selectedStudyVersion,
    click: updateFootnoteVersion,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openHistory,
  },
  {
    label: t('StudyFootnoteTable.remove'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    click: deleteStudyFootnote,
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    accessRole: roles.STUDY_WRITE,
  },
]
const footnoteHistoryItems = ref([])
const headers = [
  { title: '', key: 'actions', width: '1%' },
  { title: t('_global.order_short'), key: 'order', width: '3%' },
  {
    title: t('StudyFootnoteTable.footnote'),
    key: 'name',
    filteringName: 'footnote.name_plain',
  },
  {
    title: t('StudyFootnoteTable.covered_items'),
    key: 'referenced_items',
    filteringName: 'referenced_items.item_name',
  },
]
const historyHtmlFields = ['footnote.name']
const selectedFootnote = ref(null)
const showEditForm = ref(false)
const showHistory = ref(false)
const confirm = ref()
const table = ref()
const activeFootnote = ref(null)

const exportDataUrl = computed(() => {
  return `studies/${studiesGeneralStore.selectedStudy.uid}/study-soa-footnotes`
})
const studyFootnoteHistoryTitle = computed(() => {
  if (selectedFootnote.value) {
    return t('StudyFootnoteTable.study_footnote_history_title', {
      studyFootnoteUid: selectedFootnote.value.uid,
    })
  }
  return ''
})

watch(
  () => route.params.editFootnote,
  (value) => {
    editStudyFootnote(value)
    route.params.editFootnote = null
  }
)

onMounted(() => {
  activitiesStore.fetchStudyActivities({
    studyUid: studiesGeneralStore.selectedStudy.uid,
  })
})

function enableFootnoteMode(footnote) {
  emit('enableFootnoteMode', footnote)
  activeFootnote.value = footnote
}

function removeElementFromFootnote(footnote, item) {
  emit('removeElementFromFootnote', item.item_uid)
}

function isLatestRetired(item) {
  if (item.latest_objective) {
    return item.latest_objective.status === statuses.RETIRED
  }
  return false
}

function needUpdate(item) {
  if (item.latest_footnote) {
    if (!isLatestRetired(item)) {
      return item.footnote.version !== item.latest_footnote.version
    }
  }
  return false
}

function actionsMenuBadge(item) {
  if (!item.footnote && item.template.parameters.length > 0) {
    return {
      color: 'error',
      icon: 'mdi-exclamation',
    }
  }
  if (needUpdate(item) && !studiesGeneralStore.selectedStudyVersion) {
    return {
      color: item.accepted_version ? 'lightgray' : 'error',
      icon: 'mdi-bell-outline',
    }
  }
  return null
}

function footnoteUpdateAborted(item) {
  return item.accepted_version ? '' : 'error'
}

function closeEditForm() {
  showEditForm.value = false
  selectedFootnote.value = null
}

function closeHistory() {
  selectedFootnote.value = null
  showHistory.value = false
}

async function openHistory(studyFootnote) {
  selectedFootnote.value = studyFootnote
  const resp = await study.getStudyFootnoteAuditTrail(
    studiesGeneralStore.selectedStudy.uid,
    studyFootnote.uid
  )
  resp.data.forEach((element) => {
    element.referenced_items = dataFormating
      .itemNames(element.referenced_items)
      .replaceAll(' ,', '')
    element.name = element.footnote
      ? element.footnote.name_plain
      : element.template.name_plain
  })
  footnoteHistoryItems.value = resp.data
  showHistory.value = true
}

async function fetchFootnotesHistory() {
  const resp = await study.getStudyFootnotesAuditTrail(
    studiesGeneralStore.selectedStudy.uid
  )
  resp.data.forEach((element) => {
    element.referenced_items = dataFormating
      .itemNames(element.referenced_items)
      .replaceAll(' ,', '')
    element.name = element.footnote
      ? element.footnote.name_plain
      : element.template.name_plain
  })
  return resp.data
}

function fetchFootnotes(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  params.studyUid = studiesGeneralStore.selectedStudy.uid
  footnotesStore.fetchStudyFootnotes(params)
}

function editStudyFootnote(studyFootnote) {
  selectedFootnote.value = studyFootnote
  showEditForm.value = true
}

async function deleteStudyFootnote(studyFootnote) {
  const options = {
    type: 'warning',
    agreeLabel: t('StudyFootnoteTable.remove'),
    cancelLabel: t('StudyFootnoteTable.keep'),
    title: t('StudyFootnoteTable.remove'),
  }
  const footnote = studyFootnote.footnote
    ? studyFootnote.footnote.name_plain
    : '(unnamed)'

  if (
    await confirm.value.open(
      t('StudyFootnoteTable.confirm_delete', { footnote }),
      options
    )
  ) {
    footnotesStore
      .deleteStudyFootnote(
        studiesGeneralStore.selectedStudy.uid,
        studyFootnote.uid
      )
      .then(() => {
        table.value.filterTable()
        eventBusEmit('notification', {
          msg: t('StudyFootnoteTable.delete_footnote_success'),
        })
      })
  }
}

async function updateFootnoteVersion(item) {
  const options = {
    type: 'warning',
    width: 1000,
    cancelLabel: t('StudyFootnoteTable.keep_old_version'),
    agreeLabel: t('StudyFootnoteTable.use_new_version'),
  }
  const message =
    t('StudyFootnoteTable.update_version_alert') +
    '</br>' +
    t('StudyFootnoteTable.old_version') +
    item.footnote.name +
    ' ' +
    t('StudyFootnoteTable.new_version') +
    ' ' +
    item.latest_footnote.name

  if (await confirm.value.open(message, options)) {
    footnotesStore
      .updateStudyFootnoteVersion(
        studiesGeneralStore.selectedStudy.uid,
        item.uid
      )
      .then(() => {
        table.value.filterTable()
        eventBusEmit('notification', {
          msg: t('StudyFootnoteTable.footnote_version_updated'),
        })
      })
  } else {
    footnotesStore
      .acceptStudyFootnoteVersion(
        studiesGeneralStore.selectedStudy.uid,
        item.uid
      )
      .then(() => {
        table.value.filterTable()
        eventBusEmit('notification', {
          msg: t('StudyFootnoteTable.footnote_version_accepted'),
        })
      })
  }
}
</script>
<style>
.warning {
  background-color: rgb(var(--v-theme-nnGoldenSun200));
  height: 30px;
  width: 320px;
  align-content: center;
  text-align: center;
  border-radius: 5px;
  color: black;
}
</style>
