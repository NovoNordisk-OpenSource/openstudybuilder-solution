<template>
  <NNTable
    ref="tableRef"
    table-id="library-crf-extensions-table"
    :headers="headers"
    :items="namespaces"
    item-value="uid"
    :items-length="total"
    column-data-resource="odms/vendor-namespaces"
    :export-config="{
      objectLabel: 'CRFNamespaces',
      dataUrl: 'odms/vendor-namespaces',
    }"
    @filter="getNamespaces"
  >
    <template #actions="">
      <v-btn
        class="ml-2"
        data-cy="open-create-form"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        :disabled="!accessGuard.checkPermission($roles.LIBRARY_WRITE)"
        @click.stop="openCreateForm"
      >
        <v-icon>mdi-plus</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ $t('CRFExtensions.new_namespace') }}
        </v-tooltip>
      </v-btn>
    </template>
    <template #[`item.actions`]="{ item }">
      <ActionsMenu :actions="actions" :item="item" />
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
  </NNTable>
  <CrfExtensionsCreateForm
    :edit-item="editItem"
    :open="showCreateForm"
    @close="closeCreateForm"
  />
  <CrfExtensionsEditForm
    :edit-item="editItem"
    :open="showEditForm"
    fullscreen-form
    @close="closeEditForm"
  />
  <ConfirmDialog ref="confirmRef" :text-cols="6" :action-cols="5" />
</template>

<script setup>
import { inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import NNTable from '@/components/tools/NNTable.vue'
import crfs from '@/api/crfs'
import filteringParameters from '@/utils/filteringParameters'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import CrfExtensionsCreateForm from '@/components/library/crfs/CrfExtensionsCreateForm.vue'
import CrfExtensionsEditForm from '@/components/library/crfs/CrfExtensionsEditForm.vue'
import actionsConst from '@/constants/actions'
import { useAccessGuard } from '@/composables/accessGuard'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'

const accessGuard = useAccessGuard()
const notificationHub = inject('notificationHub')
const roles = inject('roles')
const { t } = useI18n()
const tableRef = ref()
const confirmRef = ref()

const actions = [
  {
    label: t('CRFExtensions.edit_extension'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === actionsConst.EDIT),
    accessRole: roles.LIBRARY_WRITE,
    click: openEditForm,
  },
  {
    label: t('CRFExtensions.edit_namespace'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === actionsConst.EDIT),
    accessRole: roles.LIBRARY_WRITE,
    click: openCreateForm,
  },
  {
    label: t('_global.approve'),
    icon: 'mdi-check-decagram',
    iconColor: 'success',
    condition: (item) =>
      item.possible_actions.find((action) => action === actionsConst.APPROVE),
    accessRole: roles.LIBRARY_WRITE,
    click: approve,
  },
  {
    label: t('_global.new_version'),
    icon: 'mdi-plus-circle-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find(
        (action) => action === actionsConst.NEW_VERSION
      ),
    accessRole: roles.LIBRARY_WRITE,
    click: newVersion,
  },
  {
    label: t('_global.inactivate'),
    icon: 'mdi-close-octagon-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find(
        (action) => action === actionsConst.INACTIVATE
      ),
    accessRole: roles.LIBRARY_WRITE,
    click: inactivate,
  },
  {
    label: t('_global.reactivate'),
    icon: 'mdi-undo-variant',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find(
        (action) => action === actionsConst.REACTIVATE
      ),
    accessRole: roles.LIBRARY_WRITE,
    click: reactivate,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: (item) =>
      item.possible_actions.find((action) => action === actionsConst.DELETE),
    accessRole: roles.LIBRARY_WRITE,
    click: deleteNamespace,
  },
]
const headers = [
  { title: '', key: 'actions', width: '1%' },
  { title: t('_global.name'), key: 'name' },
  { title: t('CRFExtensions.prefix'), key: 'prefix' },
  { title: t('CRFExtensions.url'), key: 'url' },
  { title: t('_global.status'), key: 'status' },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.modified_by'), key: 'author_username' },
  { title: t('_global.version'), key: 'version' },
]
const total = ref(0)
const namespaces = ref([])
const showCreateForm = ref(false)
const showEditForm = ref(false)
const editItem = ref({})

function getNamespaces(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  params.fields =
    'uid,name,prefix,url,status,start_date,author_username,version,possible_actions'

  crfs.getAllNamespaces(params).then((resp) => {
    namespaces.value = resp.data.items
    total.value = resp.data.total
  })
}

function approve(item) {
  crfs.approve('vendor-namespaces', item.uid).then(() => {
    tableRef.value.filterTable()
  })
}

function inactivate(item) {
  crfs.inactivate('vendor-namespaces', item.uid).then(() => {
    tableRef.value.filterTable()
  })
}

function reactivate(item) {
  crfs.reactivate('vendor-namespaces', item.uid).then(() => {
    tableRef.value.filterTable()
  })
}

function newVersion(item) {
  crfs.newVersion('vendor-namespaces', item.uid).then(() => {
    tableRef.value.filterTable()
  })
}
async function deleteNamespace(item) {
  const options = {
    type: 'warning',
    cancelLabel: t('_global.cancel'),
    agreeLabel: t('_global.delete'),
  }
  if (
    await confirmRef.value.open(
      t('CRFExtensions.namespace_delete_warning'),
      options
    )
  ) {
    crfs.delete('vendor-namespaces', item.uid).then(() => {
      notificationHub.add({
        msg: t('CRFExtensions.namespace_deleted'),
      })
      tableRef.value.filterTable()
    })
  }
}

function openCreateForm(item) {
  editItem.value = item.uid ? item : {}
  showCreateForm.value = true
}

function closeCreateForm() {
  editItem.value = {}
  showCreateForm.value = false
  tableRef.value.filterTable()
}

function openEditForm(item) {
  editItem.value = item
  showEditForm.value = true
}

function closeEditForm() {
  editItem.value = {}
  showEditForm.value = false
  tableRef.value.filterTable()
}
</script>
