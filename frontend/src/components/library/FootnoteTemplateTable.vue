<template>
  <StudybuilderTemplateTable
    ref="table"
    :url-prefix="urlPrefix"
    translation-type="FootnoteTemplateTable"
    object-type="footnoteTemplates"
    :headers="headers"
    :extra-filters-func="getExtraFilters"
    column-data-resource="footnote-templates"
    :column-data-parameters="columnDataParameters"
    fullscreen-form
    :history-formating-func="formatHistoryItem"
    :history-excluded-headers="historyExcludedHeaders"
    :export-data-url-params="columnDataParameters"
    double-breadcrumb
    :prepare-duplicate-payload-func="prepareDuplicatePayload"
    :default-filters="defaultFilters"
  >
    <template #editform="{ closeForm, selectedObject, preInstanceMode }">
      <FootnoteTemplatePreInstanceForm
        v-if="preInstanceMode"
        :pre-instance="selectedObject"
        :footnote-type="footnoteType"
        @close="closeForm"
        @success="refreshTable"
      />
      <FootnoteTemplateForm
        v-else
        :footnote-type="footnoteType"
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
        :show="show"
        :template="template"
        :prepare-payload-func="prepareIndexingPayload"
        :url-prefix="urlPrefix"
        :pre-instance-mode="preInstanceMode"
        @close="closeDialog"
        @updated="refreshTable"
      >
        <template #form="{ form }">
          <FootnoteTemplateIndexingForm
            ref="indexingForm"
            :form="form"
            :template="template"
          />
        </template>
      </TemplateIndexingDialog>
    </template>
    <template #preInstanceForm="{ closeDialog, template }">
      <FootnoteTemplatePreInstanceForm
        :template="template"
        :footnote-type="footnoteType"
        @close="closeDialog"
        @success="refreshTable"
      />
    </template>
  </StudybuilderTemplateTable>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import FootnoteTemplateForm from './FootnoteTemplateForm.vue'
import FootnoteTemplateIndexingForm from './FootnoteTemplateIndexingForm.vue'
import FootnoteTemplatePreInstanceForm from './FootnoteTemplatePreInstanceForm.vue'
import StudybuilderTemplateTable from '@/components/library/StudybuilderTemplateTable.vue'
import TemplateIndexingDialog from './TemplateIndexingDialog.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const props = defineProps({
  footnoteType: {
    type: Object,
    default: null,
  },
})
const { t } = useI18n()

const studiesGeneralStore = useStudiesGeneralStore()
studiesGeneralStore.fetchNullValues()

const table = ref()
const indexingForm = ref()

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
  {
    title: t('FootnoteTemplateTable.indications'),
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
  {
    title: t('ActivityTemplateTable.activity_name'),
    key: 'activities',
  },
]
const historyExcludedHeaders = [
  'indications.name',
  'categories.name.sponsor_preferred_name',
  'sub_categories.name.sponsor_preferred_name',
  'activity_groups',
  'activity_subgroups',
  'activities',
]
const urlPrefix = '/footnote-templates'

const columnDataParameters = computed(() => {
  const keyName =
    table.value && table.value.tab === 'pre-instances'
      ? 'template_type_uid'
      : 'type.term_uid'
  const filters = {}
  filters[keyName] = { v: [props.footnoteType.term_uid], op: 'eq' }
  return { filters }
})

function displayList(items) {
  return items.map((item) => item.name).join(', ')
}
function getExtraFilters(filters, preInstanceMode) {
  if (!preInstanceMode) {
    filters['type.term_uid'] = { v: [props.footnoteType.term_uid] }
  } else {
    filters.template_type_uid = { v: [props.footnoteType.term_uid] }
  }
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
