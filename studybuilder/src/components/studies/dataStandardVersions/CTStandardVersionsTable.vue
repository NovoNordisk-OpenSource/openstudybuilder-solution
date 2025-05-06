<template>
  <v-card class="rounded-0">
    <v-card-title class="d-flex">
      <v-spacer />
      <v-btn
        size="small"
        color="primary"
        :title="$t('CTStandardVersionsForm.add_title')"
        icon="mdi-plus"
        data-cy="add-ct-standard-version"
        :disabled="selectedStudyVersion !== null"
        @click.stop="showForm = true"
      />
      <v-btn
        class="ml-2"
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        :title="$t('NNTableTooltips.history')"
        icon="mdi-history"
        data-cy="show-ct-standard-version-history"
        @click="openGlobalHistory"
      />
    </v-card-title>
    <v-card-text>
      <v-data-table
        :headers="headers"
        :items="items"
        :loading="loading"
        data-cy="data-table"
      >
        <template #[`item.actions`]="{ item }">
          <ActionsMenu :actions="actions" :item="item" />
        </template>
        <template #[`item.start_date`]="{ item }">
          {{ $filters.date(item.start_date) }}
        </template>
        <template #[`item.automatically_created`]="{ item }">
          <div v-if="editMode">
            <v-checkbox
              v-model="item.automatically_created"
              :disabled="item.disabled && itemsDisabled"
              @update:model-value="disableOthers(item)"
            />
          </div>
          <div v-else>
            {{ $filters.yesno(item.automatically_created) }}
          </div>
        </template>
        <template #bottom />
      </v-data-table>
    </v-card-text>
  </v-card>
  <CTStandardVersionsForm
    :open="showForm"
    :standard-version="selectedStandardVersion"
    @close="closeForm"
    @save="fetchItems"
  />
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  <v-dialog
    v-model="showHistory"
    persistent
    :fullscreen="$globals.historyDialogFullscreen"
    @keydown.esc="closeHistory"
  >
    <HistoryTable
      :title="historyTitle"
      :headers="headers"
      :items="historyItems"
      @close="closeHistory"
    />
  </v-dialog>
</template>

<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import CTStandardVersionsForm from '@/components/studies/dataStandardVersions/CTStandardVersionsForm.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import api from '@/api/study.js'

const { t } = useI18n()
const studiesGeneralStore = useStudiesGeneralStore()
const eventBusEmit = inject('eventBusEmit')
const roles = inject('roles')

const confirm = ref()
const items = ref([])
const historyItems = ref([])
const loading = ref(true)
const showForm = ref(false)
const showHistory = ref(false)
const selectedStandardVersion = ref(null)

const historyTitle = computed(() => {
  return selectedStandardVersion.value
    ? t('CTStandardVersionsTable.item_history_title', {
        item: selectedStandardVersion.value.uid,
      })
    : t('CTStandardVersionsTable.history_title', {
        study: studiesGeneralStore.selectedStudy.uid,
      })
})

const selectedStudyVersion = computed(
  () => studiesGeneralStore.selectedStudyVersion
)

const actions = [
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    accessRole: roles.STUDY_WRITE,
    condition: () => !selectedStudyVersion.value,
    click: editItem,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    accessRole: roles.STUDY_WRITE,
    condition: () => !selectedStudyVersion.value,
    click: deleteItem,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openItemHistory,
  },
]

const headers = [
  { title: '', key: 'actions', width: '1%' },
  {
    title: t('CTStandardVersionsTable.ct_catalogue'),
    key: 'ct_package.catalogue_name',
  },
  {
    title: t('CTStandardVersionsTable.cdisc_ct_package'),
    key: 'ct_package.extends_package',
  },
  {
    title: t('CTStandardVersionsTable.sponsor_ct_package'),
    key: 'ct_package.name',
  },
  {
    title: t('_global.description'),
    key: 'description',
  },
  {
    title: t('CTStandardVersionsTable.automatically_created'),
    key: 'automatically_created',
  },
  {
    title: t('_global.modified'),
    key: 'start_date',
  },
  {
    title: t('_global.modified_by'),
    key: 'author_username',
  },
]

function openGlobalHistory() {
  api
    .getStudyStandardVersionsAuditTrail(studiesGeneralStore.selectedStudy.uid)
    .then((resp) => {
      historyItems.value = resp.data
      showHistory.value = true
    })
}

function openItemHistory(item) {
  selectedStandardVersion.value = item
  api
    .getStudyStandardVersionAuditTrail(
      studiesGeneralStore.selectedStudy.uid,
      item.uid
    )
    .then((resp) => {
      historyItems.value = resp.data
      showHistory.value = true
    })
}

function closeHistory() {
  showHistory.value = false
  selectedStandardVersion.value = null
}

function editItem(item) {
  selectedStandardVersion.value = item
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  selectedStandardVersion.value = null
}

async function deleteItem(item) {
  const options = { type: 'warning' }
  if (
    await confirm.value.open(
      t('CTStandardVersionsTable.confirm_delete', {
        package: item.ct_package.extends_package,
      }),
      options
    )
  ) {
    await api.deleteStudyStandardVersion(
      studiesGeneralStore.selectedStudy.uid,
      item.uid
    )
    fetchItems()
    eventBusEmit('notification', {
      msg: t('CTStandardVersionsTable.delete_success'),
    })
  }
}

function fetchItems() {
  loading.value = true
  api
    .getStudyStandardVersions(studiesGeneralStore.selectedStudy.uid)
    .then((resp) => {
      items.value = resp.data
      loading.value = false
    })
}

onMounted(() => {
  fetchItems()
})
</script>
