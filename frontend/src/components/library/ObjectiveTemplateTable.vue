<template>
  <StudybuilderTemplateTable
    ref="table"
    :url-prefix="urlPrefix"
    translation-type="ObjectiveTemplateTable"
    object-type="objectiveTemplates"
    :headers="headers"
    column-data-resource="objective-templates"
    :history-formating-func="formatHistoryItem"
    :history-excluded-headers="historyExcludedHeaders"
    fullscreen-form
    :prepare-duplicate-payload-func="prepareDuplicatePayload"
    :default-filters="defaultFilters"
    @refresh="refreshTable"
  >
    <template #editform="{ closeForm, selectedObject, preInstanceMode }">
      <ObjectiveTemplatePreInstanceForm
        v-if="preInstanceMode"
        :pre-instance="selectedObject"
        @close="closeForm"
        @success="refreshTable()"
      />
      <ObjectiveTemplateForm
        v-else
        :template="selectedObject"
        @close="closeForm"
        @template-added="refreshTable()"
        @template-updated="refreshTable()"
      />
    </template>
    <template #[`item.is_confirmatory_testing`]="{ item }">
      <template v-if="item.is_confirmatory_testing !== null">
        {{ $filters.yesno(item.is_confirmatory_testing) }}
      </template>
      <template v-else>
        {{ $t('_global.not_applicable_long') }}
      </template>
    </template>
    <template #[`item.categories.name.sponsor_preferred_name`]="{ item }">
      <template v-if="item.categories && item.categories.length">
        {{ $filters.terms(item.categories) }}
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
          <ObjectiveTemplateIndexingForm
            ref="indexingForm"
            :form="form"
            :template="template"
          />
        </template>
      </TemplateIndexingDialog>
    </template>
    <template #preInstanceForm="{ closeDialog, template }">
      <ObjectiveTemplatePreInstanceForm
        :template="template"
        @close="closeDialog"
        @success="refreshTable()"
      />
    </template>
  </StudybuilderTemplateTable>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import dataFormating from '@/utils/dataFormating'
import ObjectiveTemplateForm from '@/components/library/ObjectiveTemplateForm.vue'
import ObjectiveTemplateIndexingForm from './ObjectiveTemplateIndexingForm.vue'
import ObjectiveTemplatePreInstanceForm from './ObjectiveTemplatePreInstanceForm.vue'
import StudybuilderTemplateTable from '@/components/library/StudybuilderTemplateTable.vue'
import TemplateIndexingDialog from './TemplateIndexingDialog.vue'

const { t } = useI18n()
const table = ref()
const indexingForm = ref()

const headers = ref([
  {
    title: '',
    key: 'actions',
    width: '1%',
  },
  { title: t('_global.sequence_number'), key: 'sequence_id' },
  {
    title: t('_global.parent_template'),
    key: 'name',
    width: '30%',
    filteringName: 'name_plain',
  },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.status'), key: 'status' },
  { title: t('_global.version'), key: 'version' },
])
const defaultFilters = ref([
  { title: t('_global.indications'), key: 'indications.name' },
  {
    title: t('ObjectiveTemplateTable.objective_cat'),
    key: 'categories.name.sponsor_preferred_name',
  },
  {
    title: t('ObjectiveTemplateTable.confirmatory_testing'),
    key: 'is_confirmatory_testing',
  },
])
const historyExcludedHeaders = ref([
  'indications.name',
  'categories.name.sponsor_preferred_name',
  'is_confirmatory_testing',
])
const urlPrefix = ref('/objective-templates')

function prepareIndexingPayload(form) {
  return indexingForm.value.preparePayload(form)
}
function prepareDuplicatePayload(payload, preInstance) {
  if (preInstance?.categories?.length) {
    payload.category_uids = preInstance.categories.map((item) => item.term_uid)
  } else {
    payload.category_uids = []
  }
}
function refreshTable(tab) {
  if (table.value.$refs.sponsorTable && (!tab || tab === 'parent')) {
    table.value.$refs.sponsorTable.filter()
  }
  if (table.value.$refs.preInstanceTable && (!tab || tab === 'pre-instances')) {
    table.value.$refs.preInstanceTable.filter()
  }
}
function formatHistoryItem(item) {
  if (item.is_confirmatory_testing !== null) {
    item.is_confirmatory_testing = dataFormating.yesno(
      item.is_confirmatory_testing
    )
  }
  if (item?.categories?.length) {
    item.categories = {
      name: { sponsor_preferred_name: dataFormating.terms(item.categories) },
    }
  } else {
    item.categories = {
      name: { sponsor_preferred_name: t('_global.not_applicable_long') },
    }
  }
}
</script>
