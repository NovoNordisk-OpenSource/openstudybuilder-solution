<template>
  <StudybuilderTemplateTable
    ref="table"
    :url-prefix="urlPrefix"
    translation-type="EndpointTemplateTable"
    object-type="endpointTemplates"
    :headers="headers"
    column-data-resource="endpoint-templates"
    fullscreen-form
    :history-formating-func="formatHistoryItem"
    :history-excluded-headers="historyExcludedHeaders"
    :prepare-duplicate-payload-func="prepareDuplicatePayload"
    :default-filters="defaultFilters"
  >
    <template #editform="{ closeForm, selectedObject, preInstanceMode }">
      <EndpointTemplatePreInstanceForm
        v-if="preInstanceMode"
        :pre-instance="selectedObject"
        @close="closeForm"
        @success="refreshTable()"
      />
      <EndpointTemplateForm
        v-else
        :template="selectedObject"
        @close="closeForm"
        @template-added="refreshTable"
        @template-updated="refreshTable"
      />
    </template>
    <template #[`item.categories.name.sponsor_preferred_name`]="{ item }">
      <template v-if="item.categories && item.categories.length">
        {{ $filters.terms(item.categories) }}
      </template>
      <template v-else>
        {{ $t('_global.not_applicable_long') }}
      </template>
    </template>
    <template #[`item.sub_categories.name.sponsor_preferred_name`]="{ item }">
      <template v-if="item.sub_categories && item.sub_categories.length">
        {{ $filters.terms(item.sub_categories) }}
      </template>
      <template v-else>
        {{ $t('_global.not_applicable_long') }}
      </template>
    </template>
    <template
      #indexingDialog="{ closeDialog, template, show, preInstanceMode }"
    >
      <TemplateIndexingDialog
        :show="show"
        :template="template"
        :prepare-payload-func="prepareIndexingPayload"
        :url-prefix="urlPrefix"
        :pre-instance-mode="preInstanceMode"
        @close="closeDialog"
        @updated="refreshTable"
      >
        <template #form="{ form }">
          <EndpointTemplateIndexingForm
            ref="indexingForm"
            :form="form"
            :template="template"
          />
        </template>
      </TemplateIndexingDialog>
    </template>
    <template #preInstanceForm="{ closeDialog, template }">
      <EndpointTemplatePreInstanceForm
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
import dataFormating from '@/utils/dataFormating'
import EndpointTemplateForm from '@/components/library/EndpointTemplateForm.vue'
import EndpointTemplateIndexingForm from './EndpointTemplateIndexingForm.vue'
import EndpointTemplatePreInstanceForm from './EndpointTemplatePreInstanceForm.vue'
import StudybuilderTemplateTable from '@/components/library/StudybuilderTemplateTable.vue'
import TemplateIndexingDialog from './TemplateIndexingDialog.vue'

const { t } = useI18n()

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
  { title: t('_global.indications'), key: 'indications.name' },
  {
    title: t('EndpointTemplateTable.endpoint_cat'),
    key: 'categories.name.sponsor_preferred_name',
  },
  {
    title: t('EndpointTemplateTable.endpoint_sub_cat'),
    key: 'sub_categories.name.sponsor_preferred_name',
  },
]
const historyExcludedHeaders = [
  'indications.name',
  'categories.name.sponsor_preferred_name',
  'sub_categories.name.sponsor_preferred_name',
]
const urlPrefix = '/endpoint-templates'

function prepareIndexingPayload(form) {
  return indexingForm.value.preparePayload(form)
}
function prepareDuplicatePayload(payload, preInstance) {
  if (preInstance.categories && preInstance.categories.length) {
    payload.category_uids = preInstance.categories.map((item) => item.term_uid)
  } else {
    payload.category_uids = []
  }
  if (preInstance.sub_categories && preInstance.sub_categories.length) {
    payload.sub_category_uids = preInstance.sub_categories.map(
      (item) => item.term_uid
    )
  } else {
    payload.sub_category_uids = []
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
  if (item.categories) {
    item.categories = {
      name: {
        sponsor_preferred_name: dataFormating.terms(item.categories),
      },
    }
  } else {
    item.categories = {
      name: {
        sponsor_preferred_name: t('_global.not_applicable_long'),
      },
    }
  }
  if (item.sub_categories) {
    item.sub_categories = {
      name: {
        sponsor_preferred_name: dataFormating.terms(item.sub_categories),
      },
    }
  } else {
    item.sub_categories = {
      name: {
        sponsor_preferred_name: t('_global.not_applicable_long'),
      },
    }
  }
}
</script>
