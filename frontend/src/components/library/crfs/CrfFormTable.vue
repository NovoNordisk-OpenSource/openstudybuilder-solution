<template>
  <div>
    <NNTable
      ref="table"
      table-id="library-crf-forms-table"
      :headers="headers"
      :items="forms"
      item-value="uid"
      :items-length="total"
      :initial-sort-by="[{ key: 'name', order: 'asc' }]"
      column-data-resource="odms/forms"
      :export-config="{ objectLabel: 'CRFForms', dataUrl: 'odms/forms' }"
      @filter="getForms"
    >
      <template #actions="">
        <v-btn
          class="ml-2"
          icon
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          data-cy="add-crf-form"
          :disabled="!accessGuard.checkPermission($roles.LIBRARY_WRITE)"
          @click.stop="openForm"
        >
          <v-icon>mdi-plus</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('CRFForms.add_form') }}
          </v-tooltip>
        </v-btn>
      </template>
      <template #[`item.name`]="{ item }">
        <v-tooltip bottom>
          <template #activator="{ props }">
            <div v-bind="props">
              {{
                item.name.length > 40
                  ? item.name.substring(0, 40) + '...'
                  : item.name
              }}
            </div>
          </template>
          <span>{{ item.name }}</span>
        </v-tooltip>
      </template>
      <template #[`item.repeating`]="{ item }">
        {{ item.repeating }}
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
      <template #[`item.status`]="{ item }">
        <StatusChip :status="item.status" />
      </template>
      <template #[`item.actions`]="{ item }">
        <ActionsMenu :actions="actions" :item="item" />
      </template>
    </NNTable>
    <v-dialog v-model="showForm" persistent content-class="fullscreen-dialog">
      <CrfFormForm
        :selected-form="selectedForm"
        :read-only-prop="selectedForm && selectedForm.status === statuses.FINAL"
        @close="closeForm"
      />
    </v-dialog>
    <v-dialog
      v-model="showFormHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeFormHistory"
    >
      <HistoryTable
        :title="formHistoryTitle"
        :headers="headers"
        :items="formHistoryItems"
        :items-total="formHistoryItems.length"
        @close="closeFormHistory"
      />
    </v-dialog>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
    <CrfApprovalSummaryConfirmDialog ref="confirmApproval" />
    <CrfNewVersionSummaryConfirmDialog ref="confirmNewVersion" />
  </div>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import crfs from '@/api/crfs'
import CrfFormForm from '@/components/library/crfs/CrfFormForm.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import statuses from '@/constants/statuses'
import filteringParameters from '@/utils/filteringParameters'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import CrfApprovalSummaryConfirmDialog from '@/components/library/crfs/CrfApprovalSummaryConfirmDialog.vue'
import crfTypes from '@/constants/crfTypes'
import { useAccessGuard } from '@/composables/accessGuard'
import { useCrfsStore } from '@/stores/crfs'
import CrfNewVersionSummaryConfirmDialog from '@/components/library/crfs/CrfNewVersionSummaryConfirmDialog.vue'

const props = defineProps({
  elementProp: {
    type: Object,
    default: null,
  },
})

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const roles = inject('roles')
const accessGuard = useAccessGuard()

const table = ref(null)
const confirm = ref(null)
const confirmApproval = ref(null)
const confirmNewVersion = ref(null)

const showForm = ref(false)
const selectedForm = ref(null)
const filters = ref('')
const showFormHistory = ref(false)
const formHistoryItems = ref([])

const crfsStore = useCrfsStore()
const total = computed(() => crfsStore.totalForms)
const forms = computed(() => crfsStore.forms)

const headers = computed(() => [
  { title: '', key: 'actions', width: '1%' },
  { title: t('_global.library'), key: 'library_name' },
  { title: t('CRFForms.oid'), key: 'oid' },
  { title: t('_global.name'), key: 'name' },
  {
    title: t('CRFFormTable.repeating'),
    key: 'repeating',
    width: '1%',
  },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.modified_by'), key: 'author_username' },
  { title: t('_global.version'), key: 'version', width: '1%' },
  { title: t('_global.status'), key: 'status', width: '1%' },
])

const formHistoryTitle = computed(() => {
  if (selectedForm.value) {
    return t('CRFFormTable.form_history_title', {
      formUid: selectedForm.value.uid,
    })
  }
  return ''
})

async function deleteForm(item) {
  let relationships = 0
  await crfs.getRelationships(item.uid, 'forms').then((resp) => {
    if (resp.data.OdmStudyEvent && resp.data.OdmStudyEvent.length > 0) {
      relationships = resp.data.OdmStudyEvent.length
    }
  })
  const options = {
    type: 'warning',
    cancelLabel: t('_global.cancel'),
    agreeLabel: t('_global.continue'),
  }

  if (
    relationships < 1 ||
    (await confirm.value?.open(
      `${t('CRFForms.delete_warning', { count: relationships })}`,
      options
    ))
  ) {
    crfs.delete('forms', item.uid).then(() => {
      table.value?.filterTable?.()
      notificationHub?.add({
        msg: t('CRFForms.deleted'),
      })
    })
  }
}

async function approve(item) {
  const ok = await confirmApproval.value?.open({
    agreeLabel: t('CRFForms.approve_form'),
    form: item,
  })
  if (ok) {
    crfs.approve('forms', item.uid).then(() => {
      table.value?.filterTable?.()
      notificationHub?.add({
        msg: t('CRFForms.approved'),
      })
    })
  }
}

function inactivate(item) {
  crfs.inactivate('forms', item.uid).then(() => {
    table.value?.filterTable?.()
    notificationHub?.add({
      msg: t('CRFForms.inactivated'),
    })
  })
}

function reactivate(item) {
  crfs.reactivate('forms', item.uid).then(() => {
    table.value?.filterTable?.()
    notificationHub?.add({
      msg: t('CRFForms.reactivated'),
    })
  })
}

async function newVersion(item) {
  const ok = await confirmNewVersion.value?.open({
    agreeLabel: t('CRFForms.create_new_version'),
    form: item,
  })
  if (ok) {
    crfs.newVersion('forms', item.uid).then(() => {
      table.value?.filterTable?.()
      notificationHub?.add({
        msg: t('_global.new_version_success'),
      })
    })
  }
}

function view(item) {
  crfs.getForm(item.uid).then((resp) => {
    selectedForm.value = resp.data
    showForm.value = true
  })
}

function openForm() {
  selectedForm.value = null
  showForm.value = true
}

async function closeForm() {
  showForm.value = false
  selectedForm.value = null
  table.value?.filterTable?.()
}

async function openFormHistory(form) {
  selectedForm.value = form
  const resp = await crfs.getFormAuditTrail(form.uid)
  formHistoryItems.value = resp.data
  showFormHistory.value = true
}

function closeFormHistory() {
  selectedForm.value = null
  showFormHistory.value = false
}

async function getForms(filterString, options, filtersUpdated) {
  if (filterString) {
    filters.value = filterString
  }
  const params = filteringParameters.prepareParameters(
    options,
    filterString,
    filtersUpdated
  )
  crfsStore.fetchForms(params)
}

const actions = computed(() => [
  {
    label: t('_global.approve'),
    icon: 'mdi-check-decagram',
    iconColor: 'success',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'approve'),
    accessRole: roles.LIBRARY_WRITE,
    click: approve,
  },
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'edit'),
    accessRole: roles.LIBRARY_WRITE,
    click: view,
  },
  {
    label: t('_global.view'),
    icon: 'mdi-eye-outline',
    iconColor: 'primary',
    condition: (item) => item.status === statuses.FINAL,
    click: view,
  },
  {
    label: t('_global.new_version'),
    icon: 'mdi-plus-circle-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'new_version'),
    accessRole: roles.LIBRARY_WRITE,
    click: newVersion,
  },
  {
    label: t('_global.inactivate'),
    icon: 'mdi-close-octagon-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'inactivate'),
    accessRole: roles.LIBRARY_WRITE,
    click: inactivate,
  },
  {
    label: t('_global.reactivate'),
    icon: 'mdi-undo-variant',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'reactivate'),
    accessRole: roles.LIBRARY_WRITE,
    click: reactivate,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'delete'),
    accessRole: roles.LIBRARY_WRITE,
    click: deleteForm,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openFormHistory,
  },
])

watch(
  () => props.elementProp,
  (value) => {
    if (value?.tab === 'forms' && value?.type === crfTypes.FORM && value?.uid) {
      view({ uid: value.uid })
    }
  }
)
</script>
