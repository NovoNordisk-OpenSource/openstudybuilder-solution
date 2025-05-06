<template>
  <NNTable
    ref="tableRef"
    :headers="headers"
    :items="criteria"
    item-value="study_criteria_uid"
    hide-fixed-headers-switch
    :export-data-url="exportDataUrl"
    :export-data-url-params="exportDataUrlParams"
    export-object-label="StudyCriteria"
    :history-data-fetcher="fetchAllCriteriaHistory"
    :history-title="$t('EligibilityCriteriaTable.global_history_title')"
    :history-html-fields="historyHtmlFields"
    :column-data-resource="
      !sortMode
        ? `studies/${studiesGeneralStore.selectedStudy.uid}/study-criteria`
        : undefined
    "
    :items-length="total"
    :disable-filtering="sortMode"
    :hide-default-body="sortMode && criteria.length > 0"
    :filters-modify-function="addTypeFilterToHeader"
    @filter="getStudyCriteria"
  >
    <template #afterSwitches>
      <div :title="$t('NNTableTooltips.reorder_content')">
        <v-switch
          v-model="sortMode"
          :label="$t('NNTable.reorder_content')"
          hide-details
          class="mr-6"
          color="primary"
          :disabled="!accessGuard.checkPermission($roles.STUDY_WRITE)"
        />
      </div>
    </template>
    <template #tbody>
      <tbody v-show="sortMode" ref="parent">
        <tr v-for="crit in criteria" :key="crit.study_criteria_uid">
          <td>
            <v-icon size="small"> mdi-sort </v-icon>
          </td>
          <td>{{ crit.order }}</td>
          <td>
            <NNParameterHighlighter
              :name="
                crit.template ? crit.template.name_plain : crit.criteria.name
              "
              :default-color="crit.template ? 'orange' : 'green'"
            />
          </td>
          <td>
            {{
              crit.template
                ? crit.template.guidance_text
                : crit.criteria.guidance_text
            }}
          </td>
          <td>{{ $filters.yesno(crit.key_criteria) }}</td>
          <td>{{ $filters.date(crit.start_date) }}</td>
          <td>{{ crit.author_username }}</td>
        </tr>
      </tbody>
    </template>
    <template #actions>
      <v-btn
        data-cy="add-study-criteria"
        class="ml-2"
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        :title="$t('EligibilityCriteriaTable.add_criteria')"
        :disabled="
          !accessGuard.checkPermission($roles.STUDY_WRITE) ||
          studiesGeneralStore.selectedStudyVersion !== null
        "
        icon="mdi-plus"
        @click.stop="addCriteria"
      />
    </template>
    <template #[`item.order`]="{ item }">
      {{ item.order }}
      <template v-if="item.criteria">
        <v-tooltip
          v-if="item.criteria.name_plain.length > 200"
          location="bottom"
        >
          <template #activator="{ props }">
            <v-badge
              v-bind="props"
              color="warning"
              icon="mdi-exclamation"
              bordered
              inline
            />
          </template>
          <span>{{
            $t('EligibilityCriteriaTable.criteria_length_warning')
          }}</span>
        </v-tooltip>
      </template>
    </template>
    <template #[`item.criteria.name`]="{ item }">
      <template v-if="item.template">
        <NNParameterHighlighter
          :name="item.template.name"
          default-color="orange"
        />
      </template>
      <template v-else>
        <NNParameterHighlighter
          :name="item.criteria.name"
          :show-prefix-and-postfix="false"
        />
      </template>
    </template>
    <template #[`item.criteria.criteria_template.guidance_text`]="{ item }">
      <template v-if="item.template">
        <span v-html="item.template.guidance_text" />
      </template>
      <template v-else>
        <span v-html="item.criteria.template.guidance_text" />
      </template>
    </template>
    <template #[`item.key_criteria`]="{ item }">
      <v-checkbox
        v-model="item.key_criteria"
        color="primary"
        @update:model-value="updateKeyCriteria($event, item.study_criteria_uid)"
      />
    </template>
    <template #[`item.start_date`]="{ item }">
      {{ $filters.date(item.start_date) }}
    </template>
    <template #[`item.actions`]="{ item }">
      <ActionsMenu
        :key="item.study_criteria_uid"
        :actions="filterEditAction(item)"
        :item="item"
        :badge="actionsMenuBadge(item)"
      />
    </template>
  </NNTable>
  <v-dialog
    v-model="showForm"
    persistent
    fullscreen
    content-class="fullscreen-dialog"
  >
    <EligibilityCriteriaForm
      :criteria-type="criteriaType"
      class="fullscreen-dialog"
      @close="closeForm"
      @added="tableRef.filterTable()"
    />
  </v-dialog>
  <EligibilityCriteriaEditForm
    :open="showEditForm"
    :study-criteria="selectedStudyCriteria"
    @close="closeEditForm"
    @updated="tableRef.filterTable()"
  />
  <v-dialog
    v-model="showHistory"
    persistent
    :fullscreen="$globals.historyDialogFullscreen"
    @keydown.esc="closeHistory"
  >
    <HistoryTable
      :title="studyCriteriaHistoryTitle"
      :headers="headers"
      :items="criteriaHistoryItems"
      :items-total="criteriaHistoryItems.length"
      :html-fields="historyHtmlFields"
      @close="closeHistory"
    />
  </v-dialog>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
</template>

<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import EligibilityCriteriaEditForm from './EligibilityCriteriaEditForm.vue'
import EligibilityCriteriaForm from './EligibilityCriteriaForm.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter.vue'
import NNTable from '@/components/tools/NNTable.vue'
import study from '@/api/study'
import filteringParameters from '@/utils/filteringParameters'
import statuses from '@/constants/statuses'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useDragAndDrop } from '@formkit/drag-and-drop/vue'

const eventBusEmit = inject('eventBusEmit')
const roles = inject('roles')
const props = defineProps({
  criteriaType: {
    type: Object,
    default: undefined,
  },
})
const accessGuard = useAccessGuard()
const studiesGeneralStore = useStudiesGeneralStore()
const { t } = useI18n()
const tableRef = ref()

const [parent, criteria] = useDragAndDrop([], {
  onDragend: (event) => {
    const newOrder =
      event.draggedNode.data.value.order -
      (event.state.initialIndex - event.state.targetIndex)
    changeOrder(event.draggedNode.data.value.study_criteria_uid, newOrder)
  },
})

const criteriaHistoryItems = ref([])
const headers = ref([
  { title: '', key: 'actions', width: '1%' },
  { title: '#', key: 'order', width: '5%' },
  {
    title: props.criteriaType.name.sponsor_preferred_name,
    key: 'criteria.name',
    width: '30%',
  },
  {
    title: t('EligibilityCriteriaTable.guidance_text'),
    key: 'criteria.criteria_template.guidance_text',
    width: '20%',
  },
  { title: t('EligibilityCriteriaTable.key_criteria'), key: 'key_criteria' },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.modified_by'), key: 'author_username' },
])
const actions = ref([
  {
    label: t('EligibilityCriteriaTable.update_version_retired_tooltip'),
    icon: 'mdi-alert-outline',
    iconColor: 'orange',
    condition: (item) => isLatestRetired(item),
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('EligibilityCriteriaTable.update_version_tooltip'),
    icon: 'mdi-bell-ring-outline',
    iconColorFunc: criteriaUpdateAborted,
    condition: (item) =>
      needUpdate(item) && !studiesGeneralStore.selectedStudyVersion,
    click: updateVersion,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    click: editStudyCriteria,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: () => !studiesGeneralStore.selectedStudyVersion,
    click: deleteStudyCriteria,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openHistory,
  },
])
const selectedStudyCriteria = ref(null)
const showEditForm = ref(false)
const showForm = ref(false)
const showHistory = ref(false)
const total = ref(0)
const confirm = ref()
const sortMode = ref(false)

const historyHtmlFields = [
  'criteria.name',
  'criteria.criteria_template.guidance_text',
]

const exportDataUrl = computed(() => {
  return `studies/${studiesGeneralStore.selectedStudy.uid}/study-criteria`
})
const exportDataUrlParams = computed(() => {
  return {
    filters: JSON.stringify({
      'criteria_type.sponsor_preferred_name_sentence_case': {
        v: [props.criteriaType.name.sponsor_preferred_name_sentence_case],
      },
    }),
  }
})
const studyCriteriaHistoryTitle = computed(() => {
  if (selectedStudyCriteria.value) {
    return t('EligibilityCriteriaTable.study_criteria_history_title', {
      studyCriteriaUid: selectedStudyCriteria.value.study_criteria_uid,
    })
  }
  return ''
})

onMounted(() => {
  studiesGeneralStore.fetchTrialPhases()
})

async function fetchAllCriteriaHistory() {
  const resp = await study.getStudyCriteriaAllAuditTrail(
    studiesGeneralStore.selectedStudy.uid,
    props.criteriaType.term_uid
  )
  const auditTrailData = transformItems(resp.data)
  auditTrailData.forEach((item) => {
    if (!item.criteria) {
      item.criteria = item.template
    }
  })
  return auditTrailData
}

function actionsMenuBadge(item) {
  if (needUpdate(item)) {
    return {
      color: item.accepted_version ? 'lightgray' : 'error',
      icon: 'mdi-bell-outline',
    }
  }
  if (!item.criteria && item.template.parameters.length > 0) {
    return {
      color: 'error',
      icon: 'mdi-exclamation',
    }
  }
  return undefined
}

function filterEditAction(item) {
  if (
    (item.criteria && item.criteria.parameter_terms.length > 0) ||
    (item.template && item.template.parameters.length > 0)
  ) {
    return actions.value
  } else {
    return actions.value.slice(1)
  }
}

function addCriteria() {
  showForm.value = true
}

function closeEditForm() {
  showEditForm.value = false
  selectedStudyCriteria.value = null
}

function closeForm() {
  showForm.value = false
}

function closeHistory() {
  selectedStudyCriteria.value = null
  showHistory.value = false
}

async function openHistory(studyCriteria) {
  selectedStudyCriteria.value = studyCriteria
  const resp = await study.getStudyCriteriaAuditTrail(
    studiesGeneralStore.selectedStudy.uid,
    studyCriteria.study_criteria_uid
  )
  criteriaHistoryItems.value = transformItems(resp.data)
  criteriaHistoryItems.value.forEach((item) => {
    if (!item.criteria) {
      item.criteria = item.template
    }
  })
  showHistory.value = true
}

function editStudyCriteria(studyCriteria) {
  showEditForm.value = true
  selectedStudyCriteria.value = studyCriteria
}

async function deleteStudyCriteria(studyCriteria) {
  const options = { type: 'warning' }
  let criterion = studyCriteria.template
    ? studyCriteria.template.name
    : studyCriteria.criteria.name

  criterion = criterion.replaceAll(/\[|\]/g, '')
  if (
    await confirm.value.open(
      t('EligibilityCriteriaTable.confirm_delete', { criterion }),
      options
    )
  ) {
    await study.deleteStudyCriteria(
      studiesGeneralStore.selectedStudy.uid,
      studyCriteria.study_criteria_uid
    )
    tableRef.value.filterTable()
    eventBusEmit('notification', {
      msg: t('EligibilityCriteriaTable.delete_success'),
    })
  }
}

function getStudyCriteria(filters, options, filtersUpdated) {
  try {
    filters = JSON.parse(filters)
    filters['criteria_type.sponsor_preferred_name_sentence_case'] = {
      v: [props.criteriaType.name.sponsor_preferred_name_sentence_case],
    }
  } catch (error) {
    console.error(error)
  }
  filters = JSON.stringify(filters)
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  study
    .getStudyCriteriaWithType(
      studiesGeneralStore.selectedStudy.uid,
      props.criteriaType,
      params
    )
    .then((resp) => {
      criteria.value = transformItems(resp.data.items)
      total.value = resp.data.total
    })
}

function changeOrder(criteriaUid, newOrder) {
  study
    .updateStudyCriteriaOrder(
      studiesGeneralStore.selectedStudy.uid,
      criteriaUid,
      newOrder
    )
    .then(() => {
      tableRef.value.filterTable()
    })
    .catch(() => {
      tableRef.value.filterTable()
    })
}

function updateKeyCriteria(value, studyCriteriaUid) {
  study
    .updateStudyCriteriaKeyCriteria(
      studiesGeneralStore.selectedStudy.uid,
      studyCriteriaUid,
      value
    )
    .then(() => {
      tableRef.value.filterTable()
    })
}

function transformItems(items) {
  const result = []
  for (const item of items) {
    const newItem = { ...item }
    if (newItem.template) {
      newItem.name = item.template.name
      newItem.guidance_text = item.template.guidance_text
    } else {
      newItem.name = item.criteria.name
      newItem.guidance_text = item.criteria.guidance_text
    }
    result.push(newItem)
  }
  return result
}

function needUpdate(item) {
  if (item.latest_criteria) {
    if (!isLatestRetired(item)) {
      return item.criteria.version !== item.latest_criteria.version
    }
  }
  return false
}

function criteriaUpdateAborted(item) {
  return item.accepted_version ? '' : 'error'
}

function isLatestRetired(item) {
  if (item.latest_criteria) {
    return item.latest_criteria.status === statuses.RETIRED
  }
  return false
}

async function updateVersion(item) {
  const options = {
    type: 'warning',
    width: 1000,
    cancelLabel: t('EligibilityCriteriaTable.keep_old_version'),
    agreeLabel: t('EligibilityCriteriaTable.use_new_version'),
  }
  const message =
    t('EligibilityCriteriaTable.update_version_alert') +
    '<br>' +
    t('EligibilityCriteriaTable.previous_version') +
    ' ' +
    item.criteria.name_plain +
    '<br>' +
    t('EligibilityCriteriaTable.new_version') +
    ' ' +
    item.latest_criteria.name_plain

  if (await confirm.value.open(message, options)) {
    study
      .updateStudyCriteriaLatestVersion(item.study_uid, item.study_criteria_uid)
      .then(() => {
        eventBusEmit('notification', {
          msg: t('EligibilityCriteriaTable.update_version_successful'),
        })
        tableRef.value.filterTable()
      })
      .catch((error) => {
        eventBusEmit('notification', {
          type: 'error',
          msg: error.response.data.message,
        })
      })
  } else {
    study
      .updateStudyCriteriaAcceptVersion(item.study_uid, item.study_criteria_uid)
      .then(() => {
        tableRef.value.filterTable()
      })
      .catch((error) => {
        eventBusEmit('notification', {
          type: 'error',
          msg: error.response.data.message,
        })
      })
  }
}

function addTypeFilterToHeader(jsonFilter, params) {
  if (params.field_name === 'criteria.name') {
    jsonFilter['criteria_type.sponsor_preferred_name_sentence_case'] = {
      v: [props.criteriaType.name.sponsor_preferred_name_sentence_case],
    }
  }
  return {
    jsonFilter,
    params,
  }
}
</script>
<style scoped>
tbody tr td {
  border-left-style: outset;
  border-bottom-style: outset;
  border-width: 1px !important;
  border-color: rgb(var(--v-theme-nnFadedBlue200)) !important;
}
</style>
