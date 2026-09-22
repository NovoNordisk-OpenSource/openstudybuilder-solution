<template>
  <StudybuilderTemplateTable
    ref="table"
    :url-prefix="urlPrefix"
    translation-type="ActivityTemplateTable"
    object-type="activityTemplates"
    :headers="headers"
    fullscreen-form
    :history-formating-func="formatHistoryItem"
    :history-excluded-headers="historyExcludedHeaders"
    :prepare-duplicate-payload-func="prepareDuplicatePayload"
    :default-filters="defaultFilters"
  >
    <template #editform="{ closeForm, selectedObject, preInstanceMode }">
      <ActivityTemplatePreInstanceForm
        v-if="preInstanceMode"
        :pre-instance="selectedObject"
        @close="closeForm"
        @success="refreshTable"
      />
      <ActivityTemplateForm
        v-else
        :template="selectedObject"
        @close="closeForm"
        @template-added="refreshTable"
        @template-updated="refreshTable"
      />
    </template>
    <template #[`item.activity_groups`]="{ item }">
      <template v-if="item.activity_groups && item.activity_groups.length">
        {{ displayList(item.activity_groups) }}
      </template>
      <template v-else>
        {{ $t('_global.not_applicable_long') }}
      </template>
    </template>
    <template #[`item.activity_subgroups`]="{ item }">
      <template
        v-if="item.activity_subgroups && item.activity_subgroups.length"
      >
        {{ displayList(item.activity_subgroups) }}
      </template>
      <template v-else>
        {{ $t('_global.not_applicable_long') }}
      </template>
    </template>
    <template #[`item.activities`]="{ item }">
      <template v-if="item.activities && item.activities.length">
        {{ displayList(item.activities) }}
      </template>
      <template v-else>
        {{ $t('_global.not_applicable_long') }}
      </template>
    </template>
    <template
      #indexingDialog="{ closeDialog, template, show, preInstanceMode }"
    >
      <TemplateIndexingDialog
        :template="template"
        :prepare-payload-func="prepareIndexingPayload"
        :url-prefix="urlPrefix"
        :show="show"
        :pre-instance-mode="preInstanceMode"
        @close="closeDialog"
        @updated="refreshTable"
      >
        <template #form="{ form }">
          <ActivityTemplateIndexingForm
            ref="indexingForm"
            :form="form"
            :template="template"
          />
        </template>
      </TemplateIndexingDialog>
    </template>
    <template #preInstanceForm="{ closeDialog, template }">
      <ActivityTemplatePreInstanceForm
        :template="template"
        @close="closeDialog"
        @success="refreshTable"
      />
    </template>
  </StudybuilderTemplateTable>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import ActivityTemplateForm from './ActivityTemplateForm.vue'
import ActivityTemplateIndexingForm from './ActivityTemplateIndexingForm.vue'
import ActivityTemplatePreInstanceForm from './ActivityTemplatePreInstanceForm.vue'
import StudybuilderTemplateTable from '@/components/library/StudybuilderTemplateTable.vue'
import TemplateIndexingDialog from './TemplateIndexingDialog.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const { t } = useI18n()
const studiesGeneralStore = useStudiesGeneralStore()
studiesGeneralStore.fetchNullValues()

const indexingForm = ref()
const table = ref()

const headers = [
  {
    title: '',
    key: 'actions',
    width: '1%',
  },
  { title: t('_global.sequence_number'), key: 'sequence_id' },
  {
    title: t('ActivityTemplateTable.activity_name'),
    key: 'activities',
  },
  {
    title: t('_global.parent_template'),
    key: 'name',
    width: '30%',
    filteringName: 'name_plain',
  },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.status'), key: 'status' },
  { title: t('_global.version'), key: 'version' },
]
const defaultFilters = [
  {
    title: t('ActivityTemplateTable.indications'),
    key: 'indications.name',
  },
  {
    title: t('ActivityTemplateTable.activity_group'),
    key: 'activity_groups',
  },
  {
    title: t('ActivityTemplateTable.activity_subgroup'),
    key: 'activity_subgroups',
  },
]
const historyExcludedHeaders = [
  'indications.name',
  'activities',
  'activity_groups',
  'activity_subgroups',
]
const urlPrefix = '/activity-instruction-templates'

function displayList(items) {
  return items.map((item) => item.name).join(', ')
}
function prepareIndexingPayload(form) {
  return indexingForm.value.preparePayload(form)
}
function prepareDuplicatePayload(payload, preInstance) {
  if (preInstance.activities && preInstance.activities.length) {
    payload.activity_uids = preInstance.activities.map((item) => item.uid)
  } else {
    payload.activity_uids = []
  }
  if (preInstance.activity_groups && preInstance.activity_groups.length) {
    payload.activity_group_uids = preInstance.activity_groups.map(
      (item) => item.uid
    )
  } else {
    payload.activity_group_uids = []
  }
  if (preInstance.activity_subgroups && preInstance.activity_subgroups.length) {
    payload.activity_subgroup_uids = preInstance.activity_subgroups.map(
      (item) => item.uid
    )
  } else {
    payload.activity_subgroup_uids = []
  }
}
function refreshTable() {
  if (table.value.sponsorTable) {
    table.value.sponsorTable.filter()
  }
  if (table.value.preInstanceTable) {
    table.value.preInstanceTable.filter()
  }
}
function formatHistoryItem(item) {
  if (item.activity_groups) {
    item.activity_groups = displayList(item.activity_groups)
  }
  if (item.activity_subgroups) {
    item.activity_subgroups = displayList(item.activity_subgroups)
  }
  if (item.activities) {
    item.activities = displayList(item.activities)
  }
}
</script>
