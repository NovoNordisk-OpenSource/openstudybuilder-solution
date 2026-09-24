<template>
  <StudybuilderTemplateTable
    ref="table"
    :url-prefix="urlPrefix"
    translation-type="CriteriaTemplateTable"
    object-type="criteriaTemplates"
    :headers="headers"
    :extra-filters-func="getExtraFilters"
    column-data-resource="criteria-templates"
    :column-data-parameters="columnDataParameters"
    fullscreen-form
    :history-formating-func="formatHistoryItem"
    :history-excluded-headers="historyExcludedHeaders"
    :export-data-url-params="columnDataParameters"
    double-breadcrumb
    :prepare-duplicate-payload-func="prepareDuplicatePayload"
    :default-filters="defaultFilters"
    :extra-route-params="extraRouteParams"
    @refresh="refreshTable"
  >
    <template #editform="{ closeForm, selectedObject, preInstanceMode }">
      <CriteriaTemplatePreInstanceForm
        v-if="preInstanceMode"
        :pre-instance="selectedObject"
        :criteria-type="criteriaType"
        @close="closeForm"
        @success="refreshTable"
      />
      <CriteriaTemplateForm
        v-else
        :criteria-type="criteriaType"
        :template="selectedObject"
        @close="closeForm"
        @template-added="refreshTable"
        @template-updated="refreshTable"
      />
    </template>
    <template #[`item.guidance_text`]="{ item }">
      <div v-html="sanitizeHTML(item.guidance_text)" />
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
          <CriteriaTemplateIndexingForm
            ref="indexingForm"
            :form="form"
            :template="template"
          />
        </template>
      </TemplateIndexingDialog>
    </template>
    <template #preInstanceForm="{ closeDialog, template }">
      <CriteriaTemplatePreInstanceForm
        :template="template"
        :criteria-type="criteriaType"
        @close="closeDialog"
        @success="refreshTable"
      />
    </template>
  </StudybuilderTemplateTable>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import CriteriaTemplateForm from './CriteriaTemplateForm.vue'
import CriteriaTemplateIndexingForm from './CriteriaTemplateIndexingForm.vue'
import CriteriaTemplatePreInstanceForm from './CriteriaTemplatePreInstanceForm.vue'
import dataFormating from '@/utils/dataFormating'
import StudybuilderTemplateTable from '@/components/library/StudybuilderTemplateTable.vue'
import TemplateIndexingDialog from './TemplateIndexingDialog.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { sanitizeHTML } from '@/utils/sanitize'

const props = defineProps({
  criteriaType: {
    type: Object,
    default: null,
  },
})
const { t } = useI18n()
const studiesGeneralStore = useStudiesGeneralStore()

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
  {
    title: t('CriteriaTemplateTable.guidance_text'),
    key: 'guidance_text',
    width: '30%',
  },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.status'), key: 'status' },
  { title: t('_global.version'), key: 'version' },
]
const defaultFilters = [
  { title: t('CriteriaTemplateTable.indications'), key: 'indications.name' },
  {
    title: t('CriteriaTemplateTable.criterion_cat'),
    key: 'categories.name.sponsor_preferred_name',
  },
  {
    title: t('CriteriaTemplateTable.criterion_sub_cat'),
    key: 'sub_categories.name.sponsor_preferred_name',
  },
]
const historyExcludedHeaders = [
  'indications.name',
  'categories.name.sponsor_preferred_name',
  'sub_categories.name.sponsor_preferred_name',
]
const urlPrefix = '/criteria-templates'

const columnDataParameters = computed(() => {
  const keyName =
    table.value && table.value.tab === 'pre-instances'
      ? 'template_type_uid'
      : 'type.term_uid'
  const filters = {}
  filters[keyName] = { v: [props.criteriaType.term_uid], op: 'eq' }
  return { filters }
})
const extraRouteParams = computed(() => {
  return { type: props.criteriaType.sponsor_preferred_name }
})

function getExtraFilters(filters, preInstanceMode) {
  if (!preInstanceMode) {
    filters['type.term_uid'] = { v: [props.criteriaType.term_uid] }
  } else {
    filters.template_type_uid = { v: [props.criteriaType.term_uid] }
  }
}
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

function refreshTable(tab) {
  if (table.value.$refs.sponsorTable && (!tab || tab === 'parent')) {
    table.value.$refs.sponsorTable.filter()
  }
  if (table.value.$refs.preInstanceTable && (!tab || tab === 'pre-instances')) {
    table.value.$refs.preInstanceTable.filter()
  }
}

function formatHistoryItem(item) {
  if (item.categories) {
    item.categories = {
      name: { sponsor_preferred_name: dataFormating.terms(item.categories) },
    }
  } else {
    item.categories = {
      name: { sponsor_preferred_name: t('_global.not_applicable_long') },
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
      name: { sponsor_preferred_name: t('_global.not_applicable_long') },
    }
  }
}

function restoreTab() {
  table.value.restoreTab()
}

studiesGeneralStore.fetchNullValues()

defineExpose({
  restoreTab,
})
</script>
