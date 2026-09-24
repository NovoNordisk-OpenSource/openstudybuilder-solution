<template>
  <div>
    <NNTable
      ref="table"
      table-id="library-crf-collections-table"
      :headers="headers"
      :items="collections"
      item-value="uid"
      sort-desc
      :items-length="total"
      :initial-sort-by="[{ key: 'name', order: 'asc' }]"
      column-data-resource="odms/study-events"
      :export-config="{
        objectLabel: 'CRFCollections',
        dataUrl: 'odms/study-events',
      }"
      @filter="getCollections"
    >
      <template #actions="">
        <v-btn
          class="ml-2"
          icon
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          data-cy="add-crf-collection"
          :disabled="!accessGuard.checkPermission($roles.LIBRARY_WRITE)"
          @click.stop="openForm()"
        >
          <v-icon>mdi-plus</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('CRFCollections.add_collection') }}
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
      <template #[`item.relations`]="{ item }">
        <v-btn
          size="x-small"
          color="primary"
          icon="mdi-family-tree"
          @click="openRelationsTree(item)"
        />
      </template>
    </NNTable>
    <v-dialog v-model="showForm" persistent>
      <CrfCollectionForm
        :selected-collection="selectedCollection"
        :read-only-prop="
          selectedCollection && selectedCollection.status === statuses.FINAL
        "
        @close="closeForm"
      />
    </v-dialog>
    <v-dialog
      v-model="showCollectionHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeCollectionHistory"
    >
      <HistoryTable
        :title="collectionHistoryTitle"
        :headers="headers"
        :items="collectionHistoryItems"
        :items-total="collectionHistoryItems.length"
        @close="closeCollectionHistory"
      />
    </v-dialog>
    <CrfApprovalSummaryConfirmDialog ref="confirmApproval" />
  </div>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import NNTable from '@/components/tools/NNTable.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import crfs from '@/api/crfs'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import CrfApprovalSummaryConfirmDialog from '@/components/library/crfs/CrfApprovalSummaryConfirmDialog.vue'
import CrfCollectionForm from '@/components/library/crfs/CrfCollectionForm.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import filteringParameters from '@/utils/filteringParameters'
import crfTypes from '@/constants/crfTypes'
import statuses from '@/constants/statuses'
import { useAccessGuard } from '@/composables/accessGuard'
import { useCrfsStore } from '@/stores/crfs'
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
const confirmApproval = ref(null)

const showForm = ref(false)
const showCollectionHistory = ref(false)
const selectedCollection = ref(null)
const filters = ref('')
const collectionHistoryItems = ref([])

const crfsStore = useCrfsStore()
const total = computed(() => crfsStore.totalCollections)
const collections = computed(() => crfsStore.collections)

const headers = computed(() => [
  { title: '', key: 'actions', width: '1%' },
  { title: t('_global.library'), key: 'library_name' },
  { title: t('CRFCollections.oid'), key: 'oid' },
  { title: t('_global.name'), key: 'name' },
  { title: t('CRFCollections.effective_date'), key: 'effective_date' },
  { title: t('CRFCollections.retired_date'), key: 'retired_date' },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.modified_by'), key: 'author_username' },
  { title: t('_global.version'), key: 'version' },
  { title: t('_global.status'), key: 'status' },
])

const collectionHistoryTitle = computed(() => {
  if (selectedCollection.value) {
    return t('CRFCollections.collection_history_title', {
      collectionUid: selectedCollection.value.uid,
    })
  }
  return ''
})

async function approve(item) {
  const ok = await confirmApproval.value?.open({
    agreeLabel: t('CRFCollections.approve_collection'),
    collection: item,
  })
  if (ok) {
    crfs.approve('study-events', item.uid).then(() => {
      table.value?.filterTable?.()
      notificationHub?.add({
        msg: t('CRFCollections.approved'),
      })
    })
  }
}

function inactivateCollection(item) {
  crfs.inactivate('study-events', item.uid).then(() => {
    table.value?.filterTable?.()
    notificationHub?.add({
      msg: t('CRFCollections.inactivated'),
    })
  })
}

function reactivateCollection(item) {
  crfs.reactivate('study-events', item.uid).then(() => {
    table.value?.filterTable?.()
    notificationHub?.add({
      msg: t('CRFCollections.reactivated'),
    })
  })
}

function newCollectionVersion(item) {
  crfs.newVersion('study-events', item.uid).then(() => {
    table.value?.filterTable?.()
    notificationHub?.add({
      msg: t('_global.new_version_success'),
    })
  })
}

function deleteCollection(item) {
  crfs.delete('study-events', item.uid).then(() => {
    table.value?.filterTable?.()
    notificationHub?.add({
      msg: t('CRFCollections.deleted'),
    })
  })
}

function edit(item) {
  crfs.getCollection(item.uid).then((resp) => {
    selectedCollection.value = resp.data
    showForm.value = true
  })
}

async function openCollectionHistory(collection) {
  selectedCollection.value = collection
  const resp = await crfs.getCollectionAuditTrail(collection.uid)
  collectionHistoryItems.value = resp.data
  showCollectionHistory.value = true
}

function closeCollectionHistory() {
  showCollectionHistory.value = false
  selectedCollection.value = null
}

function openForm() {
  selectedCollection.value = null
  showForm.value = true
}

function closeForm() {
  selectedCollection.value = null
  showForm.value = false
  table.value?.filterTable?.()
}

function getCollections(filterString, options, filtersUpdated) {
  if (filterString) {
    filters.value = filterString
  }
  const params = filteringParameters.prepareParameters(
    options,
    filterString,
    filtersUpdated
  )
  crfsStore.fetchCollections(params)
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
    click: edit,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'delete'),
    accessRole: roles.LIBRARY_WRITE,
    click: deleteCollection,
  },
  {
    label: t('_global.new_version'),
    icon: 'mdi-plus-circle-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'new_version'),
    accessRole: roles.LIBRARY_WRITE,
    click: newCollectionVersion,
  },
  {
    label: t('_global.inactivate'),
    icon: 'mdi-close-octagon-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'inactivate'),
    accessRole: roles.LIBRARY_WRITE,
    click: inactivateCollection,
  },
  {
    label: t('_global.reactivate'),
    icon: 'mdi-undo-variant',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'reactivate'),
    accessRole: roles.LIBRARY_WRITE,
    click: reactivateCollection,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openCollectionHistory,
  },
])

watch(
  () => props.elementProp,
  (value) => {
    if (
      value?.tab === 'collections' &&
      value?.type === crfTypes.COLLECTION &&
      value?.uid
    ) {
      edit({ uid: value.uid })
    }
  }
)
</script>
