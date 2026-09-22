<template>
  <NNTable
    table-id="studies-protocol-versions-table"
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
    <template #[`item.protocol_version`]="{ item }">
      {{ getProtocolVersion(item) }}
    </template>
  </NNTable>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '@/api/study'
import filteringParameters from '@/utils/filteringParameters'
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const { t } = useI18n()
const studiesGeneralStore = useStudiesGeneralStore()

const headers = [
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
    key: 'reason_for_lock_name',
  },
  {
    title: t('Study.other_reason_for_locking_releasing'),
    key: 'other_reason_for_locking_releasing',
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
    title: t('Study.latest_metadata_version'),
    key: 'metadata_version',
  },
  {
    title: t('Study.original_metadata_version'),
    key: 'original_metadata_version',
  },
]
const items = ref([])
const total = ref(0)

function getProtocolVersion(item) {
  if (
    !item.protocol_header_major_version &&
    !item.protocol_header_minor_version
  )
    return
  return `${item.protocol_header_major_version}.${item.protocol_header_minor_version}`
}

function fetchItems(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  params.only_latest_major_protocol_version = true
  api
    .getStudySnapshotHistory(studiesGeneralStore.selectedStudy.uid, params)
    .then((resp) => {
      items.value = resp.data.items
      total.value = resp.data.total
    })
}
</script>
