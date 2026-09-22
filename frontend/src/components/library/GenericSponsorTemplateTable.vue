<template>
  <div>
    <NNTable
      ref="tableRef"
      v-model="selected"
      table-id="library-generic-sponsor-templates-table"
      :headers="updatedHeaders"
      :items="templates"
      item-value="uid"
      :items-length="total"
      :initial-sort-by="[{ key: 'start_date' }]"
      sort-desc
      :column-data-resource="urlPrefix"
      :column-data-parameters="extendedColumnDataParameters"
      :default-filters="defaultFilters"
      :history-config="{
        changeFieldLabel: $t('_global.change_description'),
        excludedHeaders: historyExcludedHeaders,
        dataFetcher: fetchGlobalAuditTrail,
        changeField: 'change_description',
        htmlFields: ['template_name', 'name', 'guidance_text'],
        title: $t('_global.audit_trail'),
      }"
      :export-config="{
        dataUrlParams: exportDataUrlParams,
        objectLabel: exportFileLabel,
        dataUrl: urlPrefix,
      }"
      @filter="filter"
    >
      <template #actions>
        <v-btn
          v-if="!preInstanceMode"
          class="ml-2"
          icon
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          data-cy="add-template"
          :disabled="!accessGuard.checkPermission($roles.LIBRARY_WRITE)"
          @click="createTemplate()"
        >
          <v-icon>mdi-plus</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t(`${translationType}.add`) }}
          </v-tooltip>
        </v-btn>
      </template>
      <template v-for="(_, slot) of $slots" #[slot]="scope">
        <slot :name="slot" v-bind="scope" />
      </template>
      <template #[`item.indications.name`]="{ item }">
        <template v-if="item.indications && item.indications.length">
          {{ $filters.names(item.indications) }}
        </template>
        <template v-else>
          {{ $t('_global.not_applicable_long') }}
        </template>
      </template>
      <template #[`item.template_name`]="{ item }">
        <NNParameterHighlighter
          :name="item.template_name"
          default-color="orange"
        />
      </template>
      <template #[`item.name`]="{ item }">
        <NNParameterHighlighter
          :name="item.name"
          default-color="green"
          :show-prefix-and-postfix="false"
        />
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
      <template #[`item.actions`]="{ item }">
        <ActionsMenu :actions="actions" :item="item" />
      </template>
    </NNTable>
    <v-dialog
      :key="key"
      v-model="showForm"
      persistent
      :fullscreen="fullscreenForm"
      :max-width="fullscreenForm ? null : '800px'"
      :content-class="fullscreenForm ? 'fullscreen-dialog' : 'top-dialog'"
      @keydown.esc="closeForm"
    >
      <slot
        name="editform"
        :close-form="closeForm"
        :selected-object="selectedObject"
        :filter="filter"
        :update-template="updateTemplate"
        :pre-instance-mode="preInstanceMode"
      />
    </v-dialog>
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
        :items-total="historyItems.length"
        :html-fields="historyHtmlFields"
        :excluded-headers="historyExcludedHeaders"
        @close="closeHistory"
      />
    </v-dialog>
    <ConfirmDialog ref="confirm" :action-cols="5" :text-cols="6" />
    <v-dialog v-model="showIndexingForm" persistent max-width="800px">
      <slot
        name="indexingDialog"
        :close-dialog="() => (showIndexingForm = false)"
        :template="selectedObject"
        :show="showIndexingForm"
        :pre-instance-mode="preInstanceMode"
      />
    </v-dialog>
    <v-dialog
      v-model="showPreInstanceForm"
      persistent
      fullscreen
      content-class="fullscreen-dialog"
      @keydown.esc="closeForm"
    >
      <slot
        name="preInstanceForm"
        :close-dialog="closePreInstanceForm"
        :template="selectedObject"
      />
    </v-dialog>
  </div>
</template>

<script setup>
import { computed, inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import templatePreInstances from '@/api/templatePreInstances'
import templatesApi from '@/api/templates'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import dataFormating from '@/utils/dataFormating'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import libraryConstants from '@/constants/libraries'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter.vue'
import NNTable from '@/components/tools/NNTable.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import statuses from '@/constants/statuses'
import filteringParameters from '@/utils/filteringParameters'
import { useAccessGuard } from '@/composables/accessGuard'
import { i18n } from '@/plugins/i18n'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const roles = inject('roles')
const props = defineProps({
  urlPrefix: {
    type: String,
    default: '',
  },
  translationType: {
    type: String,
    default: '',
  },
  objectType: {
    type: String,
    default: '',
  },
  columnDataResource: {
    type: String,
    default: '',
  },
  columnDataParameters: {
    type: Object,
    default: null,
    required: false,
  },
  headers: {
    type: Array,
    default: function () {
      return [
        {
          title: '',
          key: 'actions',
          width: '1%',
        },
        { title: i18n.t('_global.library'), key: 'library.name' },
        { title: i18n.t('_global.template'), key: 'name', width: '30%' },
        { title: i18n.t('_global.modified'), key: 'start_date' },
        { title: i18n.t('_global.modified_by'), key: 'fixme' },
        { title: i18n.t('_global.status'), key: 'status' },
        { title: i18n.t('_global.version'), key: 'version' },
      ]
    },
  },
  extraFiltersFunc: {
    type: Function,
    default: null,
    required: false,
  },
  fullscreenForm: {
    type: Boolean,
    default: false,
  },
  withIndexingProperties: {
    type: Boolean,
    default: true,
  },
  historyFormatingFunc: {
    type: Function,
    default: null,
    required: false,
  },
  historyExcludedHeaders: {
    type: Array,
    default: null,
    required: false,
  },
  exportObjectLabel: {
    type: String,
    default: null,
    required: false,
  },
  exportDataUrlParams: {
    type: Object,
    default: null,
    required: false,
  },
  preInstanceMode: {
    type: Boolean,
    default: false,
  },
  prepareDuplicatePayloadFunc: {
    type: Function,
    default: null,
    required: false,
  },
  defaultFilters: {
    type: Array,
    default: null,
    required: false,
  },
})

const emit = defineEmits(['refresh'])
const accessGuard = useAccessGuard()

const actions = [
  {
    label: t('_global.add_pre_instance'),
    icon: 'mdi-plus-circle-outline',
    iconColor: 'primary',
    condition: (item) =>
      props.objectType !== 'timeframeTemplates' &&
      !props.preInstanceMode &&
      item.status === statuses.FINAL,
    click: openPreInstanceForm,
    accessRole: roles.LIBRARY_WRITE,
  },
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'edit'),
    click: editTemplate,
    accessRole: roles.LIBRARY_WRITE,
  },
  {
    label: t('_global.approve'),
    icon: 'mdi-check-decagram',
    iconColor: 'success',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'approve'),
    click: approveTemplate,
    accessRole: roles.LIBRARY_WRITE,
  },
  {
    label: t('_global.new_version'),
    icon: 'mdi-plus-circle-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'new_version'),
    click: createNewVersion,
    accessRole: roles.LIBRARY_WRITE,
  },
  {
    label: t('_global.duplicate'),
    icon: 'mdi-content-copy',
    iconColor: 'primary',
    condition: (item) =>
      props.preInstanceMode && item.status === statuses.FINAL,
    click: duplicatePreInstance,
    accessRole: roles.LIBRARY_WRITE,
  },
  {
    label: t('_global.inactivate'),
    icon: 'mdi-close-octagon-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'inactivate'),
    click: inactivateTemplate,
    accessRole: roles.LIBRARY_WRITE,
  },
  {
    label: t('_global.reactivate'),
    icon: 'mdi-undo-variant',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'reactivate'),
    click: reactivateTemplate,
    accessRole: roles.LIBRARY_WRITE,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'delete'),
    click: deleteTemplate,
    accessRole: roles.LIBRARY_WRITE,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openTemplateHistory,
  },
]
if (props.withIndexingProperties) {
  actions.unshift({
    label: t('_global.edit_indexing'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: (item) => item.status === statuses.FINAL,
    click: editTemplateIndexing,
    accessRole: roles.LIBRARY_WRITE,
  })
}

let api

const historyHtmlFields = ['name', 'guidance_text']
const historyItems = ref([])
const showForm = ref(false)
const showIndexingForm = ref(false)
const showHistory = ref(false)
const showPreInstanceForm = ref(false)
const selectedObject = ref(null)
const selected = ref([])
const templates = ref([])
const total = ref(0)
const key = ref(0)
const confirm = ref()
const tableRef = ref()

const updatedHeaders = computed(() => {
  const result = JSON.parse(JSON.stringify(props.headers))
  if (props.preInstanceMode) {
    const index = result.findIndex((header) => header.value === 'name')
    if (index !== -1) {
      result[index].text = t('_global.pre_instance_template')
      result.splice(index, 0, {
        title: t('_global.parent_template'),
        key: 'template_name',
      })
    }
  }
  return result
})
const historyTitle = computed(() => {
  if (selectedObject.value) {
    return t('GenericTemplateTable.template_history_title', {
      templateUid: selectedObject.value.uid,
    })
  }
  return ''
})
const extendedColumnDataParameters = computed(() => {
  const result = props.columnDataParameters
    ? { ...props.columnDataParameters }
    : { filters: {} }
  result.filters['library.name'] = { v: [libraryConstants.LIBRARY_SPONSOR] }
  return result
})
const exportFileLabel = computed(() => {
  return props.exportObjectLabel ? props.exportObjectLabel : props.objectType
})

function createTemplate() {
  selectedObject.value = null
  showForm.value = true
}
function editTemplate(template) {
  selectedObject.value = template
  showForm.value = true
}
function updateTemplate(template, status) {
  templates.value.filter((item, pos) => {
    if (item.uid === template.uid && item.status === status) {
      templates.value[pos] = template
      return true
    }
    return false
  })
}
async function approveTemplate(template) {
  if (template.uid.includes('ActivityInstructionTemplate')) {
    // Temporary workaround for Activity Templates, will be deleted after backend instantiations activities implement
    const resp = await api.approveCascade(template.uid, false)
    updateTemplate(resp.data, template.status)
    notificationHub.add({
      msg: t(props.translationType + '.approve_success'),
    })
  } else {
    const resp = await api.approveCascade(template.uid, true)
    updateTemplate(resp.data, template.status)
    const msg = t(
      props.translationType +
        (props.preInstanceMode
          ? '.approve_pre_instance_success'
          : '.approve_success')
    )
    notificationHub.add({ msg })
  }
  emit('refresh')
}
function inactivateTemplate(template) {
  api.inactivate(template.uid).then((resp) => {
    updateTemplate(resp.data, template.status)
    notificationHub.add({
      msg: t(
        props.translationType +
          (props.preInstanceMode
            ? '.inactivate_pre_instance_success'
            : '.inactivate_success')
      ),
    })
    emit('refresh')
  })
}
function reactivateTemplate(template) {
  api.reactivate(template.uid).then((resp) => {
    updateTemplate(resp.data, template.status)
    notificationHub.add({
      msg: t(
        props.translationType +
          (props.preInstanceMode
            ? '.reactivate_pre_instance_success'
            : '.approve_success')
      ),
    })
    emit('refresh')
  })
}
function deleteTemplate(template) {
  api.delete(template.uid).then(() => {
    const key = props.preInstanceMode
      ? `${props.translationType}.delete_pre_instance_success`
      : `${props.translationType}.delete_success`
    notificationHub.add({ msg: t(key) })
    tableRef.value.filterTable()
  })
}
function editTemplateIndexing(template) {
  selectedObject.value = template
  showIndexingForm.value = true
}
async function fetchGlobalAuditTrail(options) {
  options.filters = {
    ['library.name']: { v: [libraryConstants.LIBRARY_SPONSOR] },
  }
  if (props.extraFiltersFunc) {
    props.extraFiltersFunc(options.filters, props.preInstanceMode)
  }
  const resp = await api.getAuditTrail(options)
  if (props.historyFormatingFunc) {
    for (const item of resp.data.items) {
      props.historyFormatingFunc(item)
    }
  }
  return resp.data
}
async function openTemplateHistory(template) {
  selectedObject.value = template
  const resp = await api.getVersions(template.uid)
  historyItems.value = transformItems(resp.data)
  showHistory.value = true
}
function closeHistory() {
  selectedObject.value = null
  showHistory.value = false
}
function openPreInstanceForm(template) {
  selectedObject.value = template
  showPreInstanceForm.value = true
}
function closePreInstanceForm() {
  selectedObject.value = null
  showPreInstanceForm.value = false
}
async function createNewVersion(template) {
  if (template.studyCount > 0) {
    const options = {
      cancelLabel: t('_global.cancel_cascade_update'),
      agreeLabel: t('_global.create_new_version'),
      type: 'warning',
      width: 1000,
    }
    if (
      !(await confirm.value.open(
        t('_global.cascade_update_warning', template.studyCount, {
          count: template.studyCount,
        }),
        options
      ))
    ) {
      return
    }
  }
  const data = {
    name: template.name,
    change_description: t(
      props.translationType + '.new_version_default_description'
    ),
  }
  api.createNewVersion(template.uid, data).then((resp) => {
    updateTemplate(resp.data, template.status)
    notificationHub.add({
      msg: t(props.translationType + '.new_version_success'),
    })
  })
}
function duplicatePreInstance(item) {
  const data = {
    library_name: item.library.name,
    parameter_terms: item.parameter_terms,
    indication_uids: [],
  }
  if (item.indications) {
    data.indication_uids = item.indications.map((ind) => ind.term_uid)
  }
  if (props.prepareDuplicatePayloadFunc) {
    props.prepareDuplicatePayloadFunc(data, item)
  }
  api.create(item.template_uid, data).then(() => {
    notificationHub.add({
      msg: t(props.translationType + '.duplicate_success'),
    })
    filter()
  })
}
function closeForm() {
  selectedObject.value = null
  showForm.value = false
  key.value += 1
  tableRef.value.filterTable()
}
function filter(filters, options, filtersUpdated) {
  const localFilters = filters ? JSON.parse(filters) : {}
  localFilters['library.name'] = { v: [libraryConstants.LIBRARY_SPONSOR] }
  if (props.extraFiltersFunc) {
    props.extraFiltersFunc(localFilters, props.preInstanceMode)
  }
  const params = filteringParameters.prepareParameters(
    options,
    localFilters,
    filtersUpdated
  )
  api.get(params).then((resp) => {
    if (resp.data.items !== undefined) {
      templates.value = resp.data.items
      total.value = resp.data.total
    } else {
      templates.value = resp.data
      total.value = templates.value.length
    }
  })
}
function getBaseObjectType() {
  let result = props.objectType.replace('Templates', '')
  if (result === 'activity') {
    result = 'activity-instruction'
  }
  return result
}
function transformItems(items) {
  const result = []
  for (const item of items) {
    const newItem = { ...item }
    if (item.indications) {
      if (item.indications.length) {
        newItem.indications.name = dataFormating.names(item.indications)
      } else {
        newItem.indications.name = t('_global.not_applicable_long')
      }
    }
    if (props.historyFormatingFunc) {
      props.historyFormatingFunc(newItem)
    }
    result.push(newItem)
  }
  return result
}

if (!props.preInstanceMode) {
  api = templatesApi(props.urlPrefix)
} else {
  api = templatePreInstances(getBaseObjectType())
}

defineExpose({
  filter,
})
</script>
