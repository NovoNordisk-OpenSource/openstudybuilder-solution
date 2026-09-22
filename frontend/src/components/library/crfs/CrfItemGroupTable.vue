<template>
  <div>
    <NNTable
      ref="table"
      table-id="library-crf-item-groups-table"
      :headers="headers"
      :items="itemGroups"
      item-value="uid"
      :items-length="total"
      :initial-sort-by="[{ key: 'name', order: 'asc' }]"
      column-data-resource="odms/item-groups"
      :export-config="{
        objectLabel: 'CRFItemGroups',
        dataUrl: 'odms/item-groups',
      }"
      @filter="getItemGroups"
    >
      <template #actions="">
        <v-btn
          class="ml-2"
          icon
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          data-cy="add-crf-item-group"
          :disabled="!accessGuard.checkPermission($roles.LIBRARY_WRITE)"
          @click.stop="openForm"
        >
          <v-icon>mdi-plus</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('CRFItemGroups.add_group') }}
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
    <v-dialog
      v-model="showForm"
      persistent
      fullscreen
      content-class="fullscreen-dialog"
    >
      <CrfItemGroupForm
        :selected-group="selectedGroup"
        :read-only-prop="
          selectedGroup && selectedGroup.status === constants.FINAL
        "
        @close="closeForm"
      />
    </v-dialog>
    <v-dialog
      v-model="showGroupHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeGroupHistory"
    >
      <HistoryTable
        :title="groupHistoryTitle"
        :headers="headers"
        :items="groupHistoryItems"
        :items-total="groupHistoryItems.length"
        @close="closeGroupHistory"
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
import CrfItemGroupForm from '@/components/library/crfs/CrfItemGroupForm.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import constants from '@/constants/statuses'
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
const selectedGroup = ref(null)
const filters = ref('')
const showGroupHistory = ref(false)
const groupHistoryItems = ref([])

const crfsStore = useCrfsStore()
const total = computed(() => crfsStore.totalItemGroups)
const itemGroups = computed(() => crfsStore.itemGroups)

const headers = computed(() => [
  { title: '', key: 'actions', width: '1%' },
  { title: t('_global.library'), key: 'library_name' },
  { title: t('CRFItemGroups.oid'), key: 'oid' },
  { title: t('_global.name'), key: 'name' },
  {
    title: t('CRFItemGroups.repeating'),
    key: 'repeating',
    width: '1%',
  },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.modified_by'), key: 'author_username' },
  { title: t('_global.version'), key: 'version', width: '1%' },
  { title: t('_global.status'), key: 'status', width: '1%' },
])

const groupHistoryTitle = computed(() => {
  if (selectedGroup.value) {
    return t('CRFItemGroups.group_history_title', {
      groupUid: selectedGroup.value.uid,
    })
  }
  return ''
})

async function deleteGroup(item) {
  let relationships = 0
  await crfs.getRelationships(item.uid, 'item-groups').then((resp) => {
    if (resp.data.OdmForm && resp.data.OdmForm.length > 0) {
      relationships = resp.data.OdmForm.length
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
      `${t('CRFItemGroups.delete_warning', { count: relationships })}`,
      options
    ))
  ) {
    crfs.delete('item-groups', item.uid).then(() => {
      getItemGroups()
      notificationHub?.add({
        msg: t('CRFItemGroups.deleted'),
      })
    })
  }
}

async function approve(item) {
  const ok = await confirmApproval.value?.open({
    agreeLabel: t('CRFItemGroups.approve_group'),
    itemGroup: item,
  })
  if (ok) {
    crfs.approve('item-groups', item.uid).then(() => {
      table.value?.filterTable?.()
      notificationHub?.add({
        msg: t('CRFItemGroups.approved'),
      })
    })
  }
}

function inactivate(item) {
  crfs.inactivate('item-groups', item.uid).then(() => {
    table.value?.filterTable?.()
    notificationHub?.add({
      msg: t('CRFItemGroups.inactivated'),
    })
  })
}

function reactivate(item) {
  crfs.reactivate('item-groups', item.uid).then(() => {
    table.value?.filterTable?.()
    notificationHub?.add({
      msg: t('CRFItemGroups.reactivated'),
    })
  })
}

async function newVersion(item) {
  const ok = await confirmNewVersion.value?.open({
    agreeLabel: t('CRFItemGroups.create_new_version'),
    itemGroup: item,
  })
  if (ok) {
    crfs.newVersion('item-groups', item.uid).then(() => {
      table.value?.filterTable?.()
      notificationHub?.add({
        msg: t('_global.new_version_success'),
      })
    })
  }
}

function view(item) {
  crfs.getItemGroup(item.uid).then((resp) => {
    selectedGroup.value = resp.data
    showForm.value = true
  })
}

function openForm() {
  showForm.value = true
}

async function openGroupHistory(group) {
  selectedGroup.value = group
  const resp = await crfs.getGroupAuditTrail(group.uid)
  groupHistoryItems.value = resp.data
  showGroupHistory.value = true
}

function closeGroupHistory() {
  selectedGroup.value = null
  showGroupHistory.value = false
}

async function closeForm() {
  showForm.value = false
  selectedGroup.value = null
  table.value?.filterTable?.()
}

function getItemGroups(filterString, options, filtersUpdated) {
  if (filterString) {
    filters.value = filterString
  }
  const params = filteringParameters.prepareParameters(
    options,
    filterString,
    filtersUpdated
  )
  crfsStore.fetchItemGroups(params)
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
    condition: (item) => item.status === constants.FINAL,
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
    click: deleteGroup,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openGroupHistory,
  },
])

watch(
  () => props.elementProp,
  (value) => {
    if (
      value?.tab === 'item-groups' &&
      value?.type === crfTypes.ITEM_GROUP &&
      value?.uid
    ) {
      view({ uid: value.uid })
    }
  }
)
</script>
