<template>
  <div>
    <NNTable
      ref="table"
      table-id="library-crf-items-table"
      :headers="headers"
      :items="items"
      item-value="uid"
      :items-length="total"
      :initial-sort-by="[{ key: 'name', order: 'asc' }]"
      column-data-resource="odms/items"
      :export-config="{ objectLabel: 'CRFItems', dataUrl: 'odms/items' }"
      @filter="getItems"
    >
      <template #actions="">
        <v-btn
          class="ml-2"
          icon
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          data-cy="add-crf-item"
          :disabled="!accessGuard.checkPermission($roles.LIBRARY_WRITE)"
          @click.stop="showForm = true"
        >
          <v-icon>mdi-plus</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('CRFItems.add_title') }}
          </v-tooltip>
        </v-btn>
      </template>
      <template #[`item.name`]="{ item }">
        <v-tooltip bottom>
          <template #activator="{ props }">
            <div v-bind="props">
              <NNParameterHighlighter
                :name="
                  item.name.length > 40
                    ? item.name.substring(0, 40) + '...'
                    : item.name
                "
                :show-prefix-and-postfix="false"
              />
            </div>
          </template>
          <span>{{ item.name }}</span>
        </v-tooltip>
      </template>
      <template #[`item.datatype`]="{ item }">
        {{ item.datatype.submission_value }}
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
        <ActionsMenu
          :actions="actions"
          :item="item"
          :badge="actionsMenuBadge(item)"
        />
      </template>
    </NNTable>
    <v-dialog v-model="showForm" persistent content-class="fullscreen-dialog">
      <CrfItemForm
        :selected-item="selectedItem"
        :start-step="openStep"
        :read-only-prop="
          selectedItem && selectedItem.status === constants.FINAL
        "
        @close="closeForm"
        @new-version="newVersion"
        @approve="approve"
      />
    </v-dialog>
    <v-dialog
      v-model="showItemHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeItemHistory"
    >
      <HistoryTable
        :title="itemHistoryTitle"
        :headers="headers"
        :items="itemHistoryItems"
        :items-total="itemHistoryItems.length"
        @close="closeItemHistory"
      />
    </v-dialog>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
    <CrfNewVersionSummaryConfirmDialog ref="confirmNewVersion" />
  </div>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import NNTable from '@/components/tools/NNTable.vue'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import crfs from '@/api/crfs'
import CrfItemForm from '@/components/library/crfs/CrfItemForm.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import constants from '@/constants/statuses'
import filteringParameters from '@/utils/filteringParameters'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
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
const confirmNewVersion = ref(null)

const showForm = ref(false)
const filters = ref('')
const selectedItem = ref(null)
const showItemHistory = ref(false)
const itemHistoryItems = ref([])
const openStep = ref(null)

const crfsStore = useCrfsStore()
const total = computed(() => crfsStore.totalItems)
const items = computed(() => crfsStore.items)

const headers = computed(() => [
  { title: '', key: 'actions', width: '1%' },
  { title: t('_global.library'), key: 'library_name' },
  { title: t('CRFItems.oid'), key: 'oid' },
  { title: t('_global.name'), key: 'name' },
  { title: t('CRFItems.type'), key: 'datatype', width: '1%' },
  { title: t('CRFItems.length'), key: 'length', width: '1%' },
  { title: t('CRFItems.sds_name'), key: 'sds_var_name' },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.modified_by'), key: 'author_username' },
  { title: t('_global.version'), key: 'version', width: '1%' },
  { title: t('_global.status'), key: 'status', width: '1%' },
])

const itemHistoryTitle = computed(() => {
  if (selectedItem.value) {
    return t('CRFItems.item_history_title', {
      itemUid: selectedItem.value.uid,
    })
  }
  return ''
})

function actionsMenuBadge(item) {
  if (item.terms?.some((term) => isTermRemoved(term))) {
    return {
      color: 'warning',
      icon: 'mdi-alert-outline',
      tooltip: t('CRFItems.update_terms_tooltip'),
    }
  }
  return undefined
}

function isTermRemoved(term) {
  return !(term.name ?? term.submission_value)
}

function closeForm() {
  showForm.value = false
  selectedItem.value = null
  openStep.value = null
  table.value?.filterTable?.()
}

function approve(item) {
  crfs.approve('items', item.uid).then(() => {
    table.value?.filterTable?.()
    notificationHub?.add({
      msg: t('CRFItems.approved'),
    })
  })
}

async function deleteItem(item) {
  let relationships = 0
  await crfs.getRelationships(item.uid, 'items').then((resp) => {
    if (resp.data.OdmItemGroup && resp.data.OdmItemGroup.length > 0) {
      relationships = resp.data.OdmItemGroup.length
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
      `${t('CRFItems.delete_warning', { count: relationships })}`,
      options
    ))
  ) {
    crfs.delete('items', item.uid).then(() => {
      table.value?.filterTable?.()
      notificationHub?.add({
        msg: t('CRFItems.deleted'),
      })
    })
  }
}

function inactivate(item) {
  crfs.inactivate('items', item.uid).then(() => {
    table.value?.filterTable?.()
    notificationHub?.add({
      msg: t('CRFItems.inactivated'),
    })
  })
}

function reactivate(item) {
  crfs.reactivate('items', item.uid).then(() => {
    table.value?.filterTable?.()
    notificationHub?.add({
      msg: t('CRFItems.reactivated'),
    })
  })
}

async function newVersion(item) {
  const ok = await confirmNewVersion.value?.open({
    agreeLabel: t('CRFItems.create_new_version'),
    item: item,
  })
  if (ok) {
    crfs.newVersion('items', item.uid).then(() => {
      table.value?.filterTable?.()
      notificationHub?.add({
        msg: t('_global.new_version_success'),
      })
    })
  }
}

function manageActivityInstancesLinks(item) {
  view(item, 'activity_instance_links')
}

function view(item, step) {
  if (step) {
    openStep.value = step
  }
  crfs.getItem(item.uid).then((resp) => {
    selectedItem.value = resp.data
    showForm.value = true
  })
}

async function openItemHistory(item) {
  selectedItem.value = item
  const resp = await crfs.getItemAuditTrail(item.uid)
  itemHistoryItems.value = resp.data
  showItemHistory.value = true
}

function closeItemHistory() {
  selectedItem.value = null
  showItemHistory.value = false
}

function getItems(filterString, options, filtersUpdated) {
  if (filterString) {
    filters.value = filterString
  }
  const params = filteringParameters.prepareParameters(
    options,
    filterString,
    filtersUpdated
  )
  crfsStore.fetchItems(params)
}

const actions = computed(() => [
  {
    label: t('CRFItems.update_terms'),
    icon: 'mdi-alert',
    iconColor: () => 'warning',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'edit') &&
      item.terms?.some((term) => isTermRemoved(term)),
    accessRole: roles.LIBRARY_WRITE,
    click: (item) => view(item, 'terms'),
  },
  {
    label: t('_global.approve'),
    icon: 'mdi-check-decagram',
    iconColor: () => 'success',
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
    label: t('CRFItems.manage_activity_instance_links'),
    icon: 'mdi-link',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'edit'),
    accessRole: roles.LIBRARY_WRITE,
    click: manageActivityInstancesLinks,
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
    click: deleteItem,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openItemHistory,
  },
])

watch(
  () => props.elementProp,
  (value) => {
    if (value?.tab === 'items' && value?.type === crfTypes.ITEM && value?.uid) {
      view(value)
    }
  }
)
</script>
