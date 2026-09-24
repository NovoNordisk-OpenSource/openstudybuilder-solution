<template>
  <v-card elevation="0" class="rounded-0">
    <v-alert
      v-if="disableEdit && studiesGeneralStore.selectedStudy.study_parent_part"
      color="nnLightBlue200"
      icon="mdi-information-outline"
      class="text-nnTrueBlue my-2 mx-4 sub-study-alert"
    >
      {{ $t('_global.sub_study_edit_warning') }}
    </v-alert>
    <v-card-title
      style="z-index: 3; position: relative"
      class="pt-0 mt-3 d-flex align-center"
    >
      <v-spacer />
      <slot name="topActions" />
      <v-btn
        v-if="copyFromStudy"
        data-cy="copy-from-study"
        class="ml-2"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        :disabled="
          !checkPermission($roles.STUDY_WRITE) ||
          studiesGeneralStore.selectedStudyVersion !== null
        "
        @click.stop="openCopyForm"
      >
        <v-icon>mdi-content-copy</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ $t('NNTableTooltips.copy_from_study') }}
        </v-tooltip>
      </v-btn>
      <v-btn
        class="ml-2"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        :disabled="
          !checkPermission($roles.STUDY_WRITE) ||
          studiesGeneralStore.selectedStudyVersion !== null ||
          disableEdit
        "
        data-cy="edit-content"
        @click.stop="openForm"
      >
        <v-icon>mdi-pencil-outline</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ $t('NNTableTooltips.edit_content') }}
        </v-tooltip>
      </v-btn>
      <v-btn
        class="ml-2"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        @click="openHistory"
      >
        <v-icon>mdi-history</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ $t('NNTableTooltips.history') }}
        </v-tooltip>
      </v-btn>
    </v-card-title>
    <v-card-text>
      <v-data-table
        :headers="headers"
        :items="computedParams"
        :loading="loading"
        item-value="name"
        :items-per-page="15"
        :items-per-page-options="itemsPerPageOptions"
      >
        <template #[`item.values`]="{ item }">
          <MetadataValueDisplay
            :param="getParam(item.key)"
            :metadata="metadata"
          />
        </template>
        <template #[`item.reason_for_missing`]="{ item }">
          <CTTermDisplay
            v-if="metadata[item.null_value_key]"
            :term="metadata[item.null_value_key]"
          />
        </template>
      </v-data-table>
      <slot
        name="form"
        :open-handler="showForm"
        :close-handler="closeForm"
        :data="metadata"
        :data-to-copy="dataToCopy"
        :form-key="formKey"
      />

      <v-dialog
        v-model="showCopyForm"
        persistent
        max-width="1000px"
        @keydown.esc="closeCopyForm"
      >
        <CopyFromStudyForm
          :component="component"
          :params="params"
          :metadata="metadata"
          @close="closeCopyForm"
          @applied="onCopyApplied"
        />
      </v-dialog>

      <v-dialog
        v-model="showHistory"
        persistent
        :fullscreen="$globals.historyDialogFullscreen"
        @keydown.esc="closeHistory"
      >
        <HistoryTable
          :headers="historyHeaders"
          :items="historyItems"
          :items-total="historyItems.length"
          :title="historyTitle"
          :export-name="component"
          start-date-header="date"
          change-field="action"
          simple-styling
          @close="closeHistory"
        />
      </v-dialog>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import CopyFromStudyForm from '@/components/tools/CopyFromStudyForm.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import CTTermDisplay from '@/components/tools/CTTermDisplay.vue'
import MetadataValueDisplay from '@/components/tools/MetadataValueDisplay.vue'
import study from '@/api/study'
import tablesConstants from '@/constants/tables'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const props = defineProps({
  params: {
    type: Array,
    default: () => [],
  },
  metadata: {
    type: Object,
    default: undefined,
  },
  firstColLabel: {
    type: String,
    default: '',
  },
  persistentDialog: {
    type: Boolean,
    default: false,
  },
  formMaxWidth: {
    type: String,
    required: false,
    default: '',
  },
  copyFromStudy: {
    type: Boolean,
    default: false,
  },
  component: {
    type: String,
    default: '',
  },
  withReasonForMissing: {
    type: Boolean,
    default: true,
  },
  disableEdit: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['updated'])

const { t } = useI18n()
const { checkPermission } = useAccessGuard()
const studiesGeneralStore = useStudiesGeneralStore()

const historyItems = ref([])
const showHistory = ref(false)
const showForm = ref(false)
const formKey = ref(0)
const showCopyForm = ref(false)
const dataToCopy = ref({})

const headers = computed(() => {
  const result = [
    { title: props.firstColLabel, key: 'name', width: '30%' },
    { title: t('StudyMetadataSummary.selected_values'), key: 'values' },
  ]
  if (props.withReasonForMissing) {
    result.push({
      title: t('StudyMetadataSummary.reason_for_missing'),
      key: 'reason_for_missing',
    })
  }
  return result
})

const historyHeaders = [
  { title: t('HistoryTable.field'), key: 'field' },
  { title: t('HistoryTable.value_before'), key: 'before_value.term_uid' },
  { title: t('HistoryTable.value_after'), key: 'after_value.term_uid' },
  { title: t('_global.user'), key: 'author_username' },
]

const itemsPerPageOptions = tablesConstants.ITEMS_PER_PAGE_OPTIONS

const displayFunctions = {
  yesno: yesnoDisplay,
  duration: durationDisplay,
  dictionaryTerms: dictionaryTermsDisplay,
}

const computedParams = computed(() => buildTableParams(props.params))
const historyTitle = computed(
  () =>
    `${props.component} ${t('HistoryTable.fields')} ${t('HistoryTable.history')} (${studiesGeneralStore.selectedStudy.uid})`
)

function openForm() {
  formKey.value++
  showForm.value = true
}

function closeForm() {
  dataToCopy.value = {}
  showForm.value = false
}

function onCopyApplied() {
  showCopyForm.value = false
  emit('updated')
}

function openCopyForm() {
  showCopyForm.value = true
}

function closeCopyForm() {
  showCopyForm.value = false
}

async function openHistory() {
  historyItems.value = []
  const resp = await study.getStudyFieldsAuditTrail(
    studiesGeneralStore.selectedStudy.uid,
    props.component
  )
  for (const group of resp.data) {
    for (const groupItem of group.actions) {
      historyItems.value.push({
        author_username: group.author_username,
        date: group.date,
        field: groupItem.field,
        action: groupItem.action,
        before_value: groupItem.before_value,
        after_value: groupItem.after_value,
      })
    }
  }
  showHistory.value = true
}

function closeHistory() {
  showHistory.value = false
}

function getParam(name) {
  return props.params.find((p) => p.name === name)
}

function buildTableParams(fields) {
  const result = []
  fields.forEach((field) => {
    let nullValueName = null
    if (field.nullValueName === undefined) {
      nullValueName = field.name
      const suffixes = ['_code', '_codes']
      suffixes.forEach((suffix) => {
        if (nullValueName.endsWith(suffix)) {
          nullValueName = nullValueName.replace(suffix, '')
        }
      })
      nullValueName += '_null_value_code'
    } else {
      nullValueName = field.nullValueName
    }
    let values = props.metadata[field.name]
    if (
      field.name === 'sex_of_participants_code' &&
      values !== undefined &&
      values !== null
    ) {
      values = values.name
    }
    if (field.name === 'study_stop_rules' && values == null) {
      values = t('StudyDefineForm.none')
    }
    result.push({
      key: field.name,
      name: field.label,
      values:
        values !== undefined &&
        values !== null &&
        field.valuesDisplay &&
        !['term', 'terms'].includes(field.valuesDisplay) &&
        field.name !== 'sex_of_participants_code'
          ? displayFunctions[field.valuesDisplay](values)
          : values,
      null_value_key: nullValueName,
    })
  })
  return result
}

function yesnoDisplay(value) {
  return value ? t('_global.yes') : t('_global.no')
}

function durationDisplay(value) {
  return `${value.duration_value} ${value.duration_unit_code.name}`
}

function dictionaryTermsDisplay(value) {
  return value.map((item) => item.name).join(', ')
}
</script>
