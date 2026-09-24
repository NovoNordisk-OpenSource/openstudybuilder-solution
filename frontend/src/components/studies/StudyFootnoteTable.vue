<template>
  <div class="page-title d-flex align-center ml-4">
    {{ $t('StudyFootnoteTable.footnotes') }}
  </div>
  <NNTable
    ref="table"
    table-id="studies-footnotes-table"
    :headers="headers"
    :items="footnotesStore.studyFootnotes"
    item-value="uid"
    :column-data-resource="`studies/${studiesGeneralStore.selectedStudy.uid}/study-soa-footnotes`"
    hide-default-switches
    :modifiable-table="false"
    hide-export-button
    :items-length="footnotesStore.total"
    :history-config="{
      dataFetcher: fetchFootnotesHistory,
      htmlFields: historyHtmlFields,
      title: $t('StudyFootnoteTable.global_history_title'),
    }"
    :export-config="{ objectLabel: 'StudyFootnotes', dataUrl: exportDataUrl }"
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
      <div
        v-if="item.referenced_items.length > 0 && activeFootnote !== item"
        :class="checkIfAnyItemHidden(item) ? 'warning' : ''"
      >
        <v-icon
          v-if="checkIfAnyItemHidden(item)"
          v-tooltip:top="$t('StudyFootnoteTable.hidden_activity_warning')"
          class="mr-2"
        >
          mdi-eye-off-outline
        </v-icon>
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
import { computed, inject, ref, watch } from 'vue'
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
import { useFootnotesStore } from '@/stores/studies-footnotes'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const roles = inject('roles')
const emit = defineEmits([
  'enableFootnoteMode',
  'update',
  'removeElementFromFootnote',
])
const route = useRoute()

const accessGuard = useAccessGuard()
const studiesGeneralStore = useStudiesGeneralStore()
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
    label: t('StudyFootnoteTable.remove'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    click: deleteStudyFootnote,
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openHistory,
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

function checkIfAnyItemHidden(item) {
  let returnValue = false
  item.referenced_items.forEach((item) => {
    if (!item.visible_in_protocol_soa) {
      returnValue = true
    }
  })
  return returnValue
}

function enableFootnoteMode(footnote) {
  emit('enableFootnoteMode', footnote)
  activeFootnote.value = footnote
}

function disableFootnoteMode() {
  activeFootnote.value = null
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
  try {
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
  } catch (error) {
    console.error(error)
  }
}

function footnoteUpdateAborted(item) {
  return item.accepted_version ? '' : 'error'
}

function closeEditForm() {
  showEditForm.value = false
  selectedFootnote.value = null
  table.value.filterTable()
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

function filterTable() {
  table.value.filterTable()
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
    await confirm.value.openHtml(
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
        notificationHub.add({
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
    '\n' +
    t('StudyFootnoteTable.old_version') +
    '\n' +
    item.footnote.name_plain +
    '\n' +
    t('StudyFootnoteTable.new_version') +
    '\n' +
    item.latest_footnote.name_plain

  if (await confirm.value.open(message, options)) {
    footnotesStore
      .updateStudyFootnoteVersion(
        studiesGeneralStore.selectedStudy.uid,
        item.uid
      )
      .then(() => {
        table.value.filterTable()
        notificationHub.add({
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
        notificationHub.add({
          msg: t('StudyFootnoteTable.footnote_version_accepted'),
        })
      })
  }
}
defineExpose({
  filterTable,
  disableFootnoteMode,
})
</script>
<style>
.warning {
  background-color: rgb(var(--v-theme-nnGoldenSun200));
  height: 30px;
  width: max-content;
  padding-inline: 10px;
  align-content: center;
  text-align: center;
  border-radius: 5px;
  color: black;
}
</style>
