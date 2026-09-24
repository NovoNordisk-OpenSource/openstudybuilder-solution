<template>
  <NNTable
    ref="tableRef"
    table-id="studies-status-table"
    :headers="headers"
    :items="items"
    column-data-resource="studies"
    hide-default-switches
    hide-export-button
    hide-search-field
    disable-filtering
    :items-length="total"
    @filter="fetchItems"
  >
    <template #beforeTable="">
      <v-btn
        v-if="
          selectedStudyStatus === 'DRAFT' &&
          !studiesGeneralStore.selectedStudy.study_parent_part &&
          isLatestStudySelected()
        "
        class="ml-2"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        data-cy="release-study"
        :disabled="!accessGuard.checkPermission($roles.STUDY_WRITE)"
        :loading="loading"
        @click.stop="releaseStudy"
      >
        <v-icon>mdi-share-variant</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ $t('Study.release') }}
        </v-tooltip>
      </v-btn>
      <v-btn
        v-if="
          selectedStudyStatus === 'DRAFT' &&
          !studiesGeneralStore.selectedStudy.study_parent_part &&
          isLatestStudySelected()
        "
        class="ml-2"
        icon
        size="small"
        color="nnBaseBlue"
        data-cy="lock-study"
        :disabled="!accessGuard.checkPermission($roles.STUDY_WRITE)"
        :loading="loading"
        @click.stop="lockStudy"
      >
        <v-icon>mdi-lock-outline</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ $t('Study.lock') }}
        </v-tooltip>
      </v-btn>
      <v-btn
        v-if="
          selectedStudyStatus === 'LOCKED' &&
          !studiesGeneralStore.selectedStudy.study_parent_part &&
          isLatestStudySelected()
        "
        class="ml-2"
        icon
        size="small"
        color="nnBaseBlue"
        data-cy="unlock-study"
        :disabled="!accessGuard.checkPermission($roles.STUDY_WRITE)"
        :loading="loading"
        @click.stop="unlockStudy"
      >
        <v-icon>mdi-lock-open-outline</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ $t('Study.unlock') }}
        </v-tooltip>
      </v-btn>
    </template>
    <template #[`item.actions`]="{ item }">
      <ActionsMenu
        v-if="checkIfSelectable(item)"
        :actions="actions"
        :item="item"
      />
      <v-progress-circular
        v-if="item.loading"
        color="primary"
        indeterminate
        class="ml-2"
        :width="3"
        :size="20"
      />
    </template>
    <template #[`item.study_status`]="{ item }">
      <div style="display: inline-flex">
        <StatusChip :status="item.study_status[0]" :outlined="false" />
        <StatusChip
          v-if="item.study_status[1]"
          :status="item.study_status[1]"
          class="ml-2"
          :outlined="false"
        />
      </div>
    </template>
    <template #[`item.modified_date`]="{ item }">
      <v-tooltip location="top">
        <template #activator="{ props }">
          <span v-bind="props">{{
            $filters.dateRelative(item.modified_date)
          }}</span>
        </template>
        {{ $filters.date(item.modified_date) }}
      </v-tooltip>
    </template>
    <template #[`item.protocol_version`]="{ item }">
      {{ getProtocolVersion(item) }}
    </template>
    <template #[`item.reason_for_lock`]="{ item }">
      <div>
        <strong>{{ item.reason_for_lock_name }}</strong>
        <template
          v-if="
            item.reason_for_lock_name === 'Other' &&
            item.other_reason_for_locking_releasing
          "
        >
          :
          {{ item.other_reason_for_locking_releasing }}
        </template>
      </div>
    </template>
  </NNTable>
  <StudyStatusForm
    v-if="showStatusForm"
    :action="statusAction"
    :open="showStatusForm"
    :last-version="lastVersion"
    @close="closeStatusForm"
    @status-changed="refreshData"
  />
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
</template>

<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '@/api/study'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import filteringParameters from '@/utils/filteringParameters'
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import StudyStatusForm from './StudyStatusForm.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import _isEmpty from 'lodash/isEmpty'

const { t } = useI18n()
const accessGuard = useAccessGuard()
const studiesGeneralStore = useStudiesGeneralStore()

const selectedStudyStatus = computed(() => studiesGeneralStore.studyStatus)
const selectedStudyVersion = computed(() => studiesGeneralStore.studyVersion)

const headers = [
  { title: '', key: 'actions', width: '1%' },
  {
    title: t('Study.status'),
    key: 'study_status',
  },
  {
    title: t('Study.reason_for_unlock'),
    key: 'reason_for_unlock_name',
  },
  {
    title: t('Study.other_reason_for_unlock'),
    key: 'other_reason_for_unlocking',
  },
  {
    title: t('Study.reason_for_release_or_lock'),
    key: 'reason_for_lock',
  },
  {
    title: t('_global.change_description'),
    key: 'description',
  },
  {
    title: t('Study.protocol_version'),
    key: 'protocol_version',
  },
  {
    title: t('Study.meta_version'),
    key: 'metadata_version',
  },
  {
    title: t('_global.modified'),
    key: 'modified_date',
  },
  {
    title: t('_global.modified_by'),
    key: 'modified_by',
  },
]
const loading = ref(false)
const showStatusForm = ref(false)
const statusAction = ref(null)
const items = ref([])
const total = ref(0)
const actions = [
  {
    label: t('StudyTable.select'),
    icon: 'mdi-check-circle-outline',
    iconColor: 'primary',
    click: selectStudyVersion,
  },
]
const latestStudy = ref({})
const confirm = ref()
const tableRef = ref()
const lastVersion = ref(null)
const isMajorVersion = ref(false)

async function getLastVersion() {
  let resp
  resp = await api.getLatestProtocolVersion(
    studiesGeneralStore.selectedStudy.uid
  )
  if (resp.data) {
    isMajorVersion.value = resp.data.has_final_protocol_locked_version
    lastVersion.value = resp.data.protocol_header_version
  }
}

function getProtocolVersion(item) {
  if (
    !item.protocol_header_major_version &&
    !item.protocol_header_minor_version
  )
    return
  return `${item.protocol_header_major_version}.${item.protocol_header_minor_version}`
}

function checkIfSelectable(studyVersion) {
  return (
    studyVersion.metadata_version !== selectedStudyVersion.value ||
    studyVersion.study_status[0] !== selectedStudyStatus.value
  )
}
async function selectStudyVersion(studyVersion) {
  studyVersion.loading = true
  let resp
  resp = await api.getStudy(
    studiesGeneralStore.selectedStudy.uid,
    true,
    studyVersion.metadata_version ? studyVersion.metadata_version : '0'
  )
  await studiesGeneralStore.selectStudy(resp.data, true)
  studyVersion.loading = false
}
function closeStatusForm() {
  loading.value = false
  showStatusForm.value = false
}
function fetchItems(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  api
    .getStudySnapshotHistory(studiesGeneralStore.selectedStudy.uid, params)
    .then((resp) => {
      items.value = resp.data.items
      total.value = resp.data.total
      if (_isEmpty(params.sort_by) && _isEmpty(params.filters)) {
        latestStudy.value = resp.data.items[0]
      }
      getLastVersion()
    })
}
function isLatestStudySelected() {
  return latestStudy.value.metadata_version === selectedStudyVersion.value
}
function releaseStudy() {
  loading.value = true
  statusAction.value = 'release'
  showStatusForm.value = true
}
function lockStudy() {
  loading.value = true
  statusAction.value = 'lock'
  showStatusForm.value = true
}
async function unlockStudy() {
  loading.value = true
  if (isMajorVersion.value) {
    const options = {
      cancelLabel: t('Study.keep_locked'),
      agreeLabel: t('Study.unlock'),
      type: 'warning',
      width: 1000,
    }
    if (!(await confirm.value.open(t('Study.unlock_warning'), options))) {
      loading.value = false
      return
    }
  }
  statusAction.value = 'unlock'
  showStatusForm.value = true
}
async function refreshData() {
  tableRef.value.filterTable()
}
</script>
