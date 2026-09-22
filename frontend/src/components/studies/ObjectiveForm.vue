<template>
  <HorizontalStepperForm
    ref="stepper"
    :title="title"
    :steps="steps"
    :form-observer-getter="getObserver"
    :extra-step-validation="extraStepValidation"
    :help-items="helpItems"
    :edit-data="form"
    @close="close"
    @save="submit"
  >
    <template #[`step.creationMode`]>
      <v-radio-group v-model="creationMode">
        <v-radio
          data-cy="objective-from-template"
          :label="$t('StudyObjectiveForm.template_mode')"
          value="template"
        />
        <v-radio
          data-cy="objective-from-select"
          :label="$t('StudyObjectiveForm.select_mode')"
          value="select"
        />
        <v-radio
          data-cy="objective-from-scratch"
          :label="$t('StudyObjectiveForm.scratch_mode')"
          value="scratch"
        />
      </v-radio-group>
      <v-form ref="studiesFormRef">
        <v-row v-if="creationMode === 'select'">
          <v-col>
            <StudySelectorField
              v-model="formSelectedStudy"
              :data="studies"
              :loading="studiesLoading"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #[`step.selectObjective`]>
      <p class="text-grey text-body-large font-weight-bold">
        {{ $t('StudyObjectiveForm.selected_objectives') }}
      </p>
      <v-data-table
        data-cy="selected-objectives-table"
        :headers="selectedObjectiveHeaders"
        :items="selectedStudyObjectives"
      >
        <template #[`item.objective.name`]="{ item }">
          <NNParameterHighlighter :name="item.objective.name" />
        </template>
        <template #[`item.actions`]="{ item }">
          <v-btn
            icon="mdi-delete-outline"
            color="red"
            variant="text"
            @click="unselectStudyObjective(item)"
          />
        </template>
      </v-data-table>
    </template>
    <template #[`step.selectObjective.after`]>
      <p class="text-grey text-body-large font-weight-bold mb-0 ml-3">
        {{ $t('StudyObjectiveForm.copy_instructions') }}
      </p>
      <v-col cols="12" class="pt-0 mt-0">
        <StudySelectionTable
          :headers="objectiveHeaders"
          data-fetcher-name="getAllStudyObjectives"
          :extra-data-fetcher-filters="extraStudyObjectiveFilters"
          :selected-study="formSelectedStudy"
          column-data-resource="study-objectives"
          @item-selected="selectStudyObjective"
        >
          <template #[`item.objective.name`]="{ item }">
            <NNParameterHighlighter :name="item.objective.name" />
          </template>
          <template #[`item.actions`]="{ item }">
            <v-btn
              :data-cy="$t('StudySelectionTable.copy_item')"
              icon="mdi-content-copy"
              size="small"
              variant="text"
              :color="getCopyButtonColor(item)"
              :disabled="isStudyObjectiveSelected(item)"
              :title="$t('StudySelectionTable.copy_item')"
              @click="selectStudyObjective(item)"
            />
          </template>
        </StudySelectionTable>
      </v-col>
    </template>
    <template #[`step.selectTemplates`]>
      <v-data-table :headers="selectionHeaders" :items="selectedTemplates">
        <template #[`item.name`]="{ item }">
          <NNParameterHighlighter :name="item.name" default-color="orange" />
        </template>
        <template #[`item.actions`]="{ item }">
          <v-btn
            color="red"
            size="small"
            icon="mdi-delete-outline"
            variant="text"
            @click="unselectTemplate(item)"
          />
        </template>
      </v-data-table>
    </template>
    <template #[`step.selectTemplates.after`]>
      <div class="d-flex align-center">
        <p class="text-grey text-body-large font-weight-bold mb-0 ml-3">
          {{ $t('StudyObjectiveForm.copy_instructions') }}
        </p>
        <v-switch
          v-model="preInstanceMode"
          :label="$t('StudyObjectiveForm.show_pre_instances')"
          hide-details
          class="ml-4"
        />
      </div>
      <v-col cols="12" class="pt-0">
        <NNTable
          key="templatesTable"
          table-id="objective-form-templates"
          :headers="tplHeaders"
          :items="templates"
          hide-default-switches
          hide-actions-menu
          :default-filters="defaultTplFilters"
          :items-per-page="15"
          elevation="0"
          :items-length="total"
          :column-data-resource="
            preInstanceMode ? 'objective-pre-instances' : 'objective-templates'
          "
          @filter="getObjectiveTemplates"
        >
          <template #[`item.categories.name.sponsor_preferred_name`]="{ item }">
            <template v-if="item.categories">
              {{ $filters.terms(item.categories) }}
            </template>
            <template v-else>
              {{ $t('_global.not_applicable_long') }}
            </template>
          </template>
          <template #[`item.is_confirmatory_testing`]="{ item }">
            <template v-if="item.is_confirmatory_testing !== null">
              {{ $filters.yesno(item.is_confirmatory_testing) }}
            </template>
            <template v-else>
              {{ $t('_global.not_applicable_long') }}
            </template>
          </template>
          <template #[`item.indications`]="{ item }">
            <template v-if="item.indications">
              {{ $filters.names(item.indications) }}
            </template>
            <template v-else>
              {{ $t('_global.not_applicable_long') }}
            </template>
          </template>
          <template #[`item.name`]="{ item }">
            <NNParameterHighlighter :name="item.name" default-color="orange" />
          </template>
          <template #[`item.actions`]="{ item }">
            <v-btn
              :data-cy="$t('StudyObjectiveForm.copy_template')"
              color="primary"
              size="small"
              :title="$t('StudyObjectiveForm.copy_template')"
              icon="mdi-content-copy"
              variant="text"
              @click="selectObjectiveTemplate(item)"
            />
          </template>
        </NNTable>
      </v-col>
    </template>
    <template #[`step.createTemplate`]>
      <v-form ref="templateFormRef">
        <NNTemplateInputField
          v-model="templateForm.name"
          :data-cy="$t('ObjectiveTemplateForm.name')"
          :label="$t('ObjectiveTemplateForm.name')"
          :items="parameterTypes"
          :rules="[formRules.required]"
          :show-drop-down-early="true"
        />
      </v-form>
    </template>
    <template #[`step.createObjective`]>
      <v-form ref="objectiveFormRef">
        <v-progress-circular
          v-if="loadingParameters"
          indeterminate
          color="secondary"
        />

        <template v-if="form.objective_template !== undefined">
          <ParameterValueSelector
            ref="paramSelector"
            :model-value="parameters"
            :template="form.objective_template.name"
            color="white"
            preview-text=" "
          />
        </template>
      </v-form>
    </template>

    <template #[`step.objectiveLevel`]>
      <v-row>
        <v-col cols="11">
          <v-select
            v-model="form.objective_level"
            :data-cy="$t('StudyObjectiveForm.objective_level')"
            :label="$t('StudyObjectiveForm.objective_level')"
            :items="studiesGeneralStore.objectiveLevels"
            item-title="sponsor_preferred_name"
            return-object
            clearable
            style="max-width: 400px"
          />
        </v-col>
      </v-row>
    </template>
  </HorizontalStepperForm>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import statuses from '@/constants/statuses'
import objectiveTemplates from '@/api/objectiveTemplates'
import templatePreInstances from '@/api/templatePreInstances'
import templateParameterTypes from '@/api/templateParameterTypes'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter.vue'
import NNTable from '@/components/tools/NNTable.vue'
import NNTemplateInputField from '@/components/tools/NNTemplateInputField.vue'
import ParameterValueSelector from '@/components/tools/ParameterValueSelector.vue'
import study from '@/api/study'
import StudySelectionTable from './StudySelectionTable.vue'
import filteringParameters from '@/utils/filteringParameters'
import constants from '@/constants/libraries'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudiesObjectivesStore } from '@/stores/studies-objectives'
import StudySelectorField from '@/components/studies/StudySelectorField.vue'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const formRules = inject('formRules')

const props = defineProps({
  currentStudyObjectives: {
    type: Array,
    default: () => [],
  },
})
const emit = defineEmits(['close', 'added'])

const studiesGeneralStore = useStudiesGeneralStore()
const studiesObjectivesStore = useStudiesObjectivesStore()
const preInstanceApi = templatePreInstances('objective')

const creationMode = ref('template')
const form = ref({})
const templateForm = ref({})
const studiesLoading = ref(false)
const loadingParameters = ref(false)
const parameters = ref([])
const parameterTypes = ref([])
const preInstanceMode = ref(true)
const selectedStudyObjectives = ref([])
const selectedTemplates = ref([])
const steps = ref(getInitialSteps())
const studies = ref([])
const templates = ref([])
const total = ref(0)
const stepper = ref()
const paramSelector = ref()
const formSelectedStudy = ref(null)
const studiesFormRef = ref()
const templateFormRef = ref()
const objectiveFormRef = ref()

let apiEndpoint = preInstanceApi
const alternateSteps = [
  { name: 'creationMode', title: t('StudyObjectiveForm.creation_mode_label') },
  { name: 'selectObjective', title: t('StudyObjectiveForm.select_objective') },
]
const scratchModeSteps = [
  { name: 'creationMode', title: t('StudyObjectiveForm.creation_mode_label') },
  {
    name: 'createTemplate',
    title: t('StudyObjectiveForm.create_template_title'),
  },
  { name: 'createObjective', title: t('StudyObjectiveForm.step2_title') },
  { name: 'objectiveLevel', title: t('StudyObjectiveForm.step3_title') },
]
const selectionHeaders = [
  { title: '', key: 'actions', width: '1%' },
  { title: t('_global.template'), key: 'name', class: 'text-center' },
]
const tplHeaders = [
  { title: '', key: 'actions', width: '1%' },
  {
    title: t('_global.sequence_number_short'),
    key: 'sequence_id',
    width: '5%',
  },
  { title: t('_global.template'), key: 'name', filteringName: 'name_plain' },
]
const defaultTplFilters = [
  { title: t('_global.sequence_number_short'), key: 'sequence_id' },
  {
    title: t('_global.indications'),
    key: 'indications',
    filteringName: 'indications.name',
  },
  {
    title: t('ObjectiveTemplateTable.objective_cat'),
    key: 'categories.name.sponsor_preferred_name',
  },
  {
    title: t('ObjectiveTemplateTable.confirmatory_testing'),
    key: 'is_confirmatory_testing',
  },
]
const objectiveHeaders = [
  { title: '', key: 'actions', width: '1%' },
  { title: t('Study.study_id'), key: 'study_id', noFilter: true },
  {
    title: t('StudyObjectiveForm.study_objective'),
    key: 'objective.name',
    filteringName: 'objective.name_plain',
  },
  {
    title: t('StudyObjectiveForm.objective_level'),
    key: 'objective_level.sponsor_preferred_name',
  },
]
const selectedObjectiveHeaders = [
  { title: '', key: 'actions', width: '1%' },
  { title: t('Study.study_id'), key: 'study_id' },
  { title: t('StudyObjectiveForm.study_objective'), key: 'objective.name' },
  {
    title: t('StudyObjectiveForm.objective_level'),
    key: 'objective_level.sponsor_preferred_name',
  },
]
const extraStudyObjectiveFilters = {
  objective_template: { v: [] },
  'objective.status': { v: [statuses.FINAL] },
}

const helpItems = [
  'StudyObjectiveForm.add_title',
  'StudyObjectiveForm.select_mode',
  'StudyObjectiveForm.template_mode',
  'StudyObjectiveForm.scratch_mode',
  'StudyObjectiveForm.select_objective_tpl',
  'StudyObjectiveForm.select_tpl_parameters_label',
  'StudyObjectiveForm.select_studies',
  'StudyObjectiveForm.study_objective',
  'StudyObjectiveForm.objective_level',
]

const title = computed(() => {
  return t('StudyObjectiveForm.add_title')
})

watch(creationMode, (value) => {
  if (value === 'template') {
    steps.value = getInitialSteps()
  } else if (value === 'select') {
    steps.value = alternateSteps
  } else {
    steps.value = scratchModeSteps
  }
})
watch(preInstanceMode, (value) => {
  apiEndpoint = value ? preInstanceApi : objectiveTemplates
  getObjectiveTemplates()
  selectedTemplates.value = []
})

onMounted(() => {
  templateParameterTypes.getTypes().then((resp) => {
    parameterTypes.value = resp.data
  })

  studiesLoading.value = true
  study
    .getSelectableStudies({ has_study_objective: true })
    .then((resp) => {
      studies.value = resp.data.filter(
        (study) => study.uid !== studiesGeneralStore.selectedStudy.uid
      )
    })
    .finally(() => {
      studiesLoading.value = false
    })
})

function close() {
  notificationHub.clearErrors()
  creationMode.value = 'template'
  form.value = {}
  templateForm.value = {}
  parameters.value = []
  stepper.value.reset()
  selectedStudyObjectives.value = []
  selectedTemplates.value = []
  apiEndpoint = preInstanceApi
  formSelectedStudy.value = null
  emit('close')
}

function getObserver(step) {
  if (creationMode.value === 'select' && step === 1) {
    return studiesFormRef.value
  }
  if (creationMode.value === 'scratch') {
    if (step === 2) {
      return templateFormRef.value
    }
    if (step === 3) {
      return objectiveFormRef.value
    }
  }
  return null
}

function getInitialSteps() {
  return [
    {
      name: 'creationMode',
      title: t('StudyObjectiveForm.creation_mode_label'),
    },
    {
      name: 'selectTemplates',
      title: t('StudyObjectiveForm.select_tpl_title'),
    },
  ]
}

function getObjectiveTemplates(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  params.status = statuses.FINAL
  if (params.filters) {
    params.filters = JSON.parse(params.filters)
  } else {
    params.filters = {}
  }
  Object.assign(params.filters, {
    'library.name': { v: [constants.LIBRARY_SPONSOR] },
  })
  apiEndpoint.get(params).then((resp) => {
    templates.value = resp.data.items
    total.value = resp.data.total
  })
}

async function loadParameters(template) {
  if (template) {
    loadingParameters.value = true
    const templateUid =
      creationMode.value !== 'scratch' && preInstanceMode.value
        ? template.template_uid
        : template.uid
    const resp = await apiEndpoint.getParameters(templateUid, {
      study_uid: studiesGeneralStore.selectedStudy.uid,
    })
    parameters.value = resp.data
    loadingParameters.value = false
  } else {
    parameters.value = []
  }
}

function selectObjectiveTemplate(template) {
  if (!selectedTemplates.value.some((el) => el.uid === template.uid)) {
    selectedTemplates.value.push(template)
  }
}
function unselectTemplate(template) {
  selectedTemplates.value = selectedTemplates.value.filter(
    (item) => item.name !== template.name
  )
}
function selectStudyObjective(studyObjective) {
  selectedStudyObjectives.value.push(studyObjective)
  form.value.objective_level = studyObjective.objective_level
}
function unselectStudyObjective(studyObjective) {
  selectedStudyObjectives.value = selectedStudyObjectives.value.filter(
    (item) => item.objective.name !== studyObjective.objective.name
  )
}
function isStudyObjectiveSelected(studyObjective) {
  let selected = selectedStudyObjectives.value.find(
    (item) => item.objective.uid === studyObjective.objective.uid
  )
  if (!selected && props.currentStudyObjectives.length) {
    selected = props.currentStudyObjectives.find(
      (item) => item.objective?.uid === studyObjective.objective.uid
    )
  }
  return selected !== undefined
}

function getCopyButtonColor(item) {
  return !isStudyObjectiveSelected(item) ? 'primary' : ''
}

async function extraStepValidation(step) {
  if (creationMode.value === 'template' && step === 2) {
    if (
      form.value.objective_template === undefined ||
      form.value.objective_template === null
    ) {
      notificationHub.add({
        msg: t('StudyObjectiveForm.template_not_selected'),
        type: 'error',
      })
      return false
    }
    return true
  }
  if (
    (creationMode.value !== 'scratch' || step !== 2) &&
    (creationMode.value !== 'clone' || step !== 1)
  ) {
    return true
  }
  if (
    form.value.objective_template &&
    form.value.objective_template.name === templateForm.value.name
  ) {
    return true
  }
  const data = {
    ...templateForm.value,
    studyUid: studiesGeneralStore.selectedStudy.uid,
  }
  data.library_name = constants.LIBRARY_USER_DEFINED
  try {
    const resp = await objectiveTemplates.create(data)
    if (resp.data.status === statuses.DRAFT)
      await objectiveTemplates.approve(resp.data.uid)
    form.value.objective_template = resp.data
  } catch (_error) {
    return false
  }
  loadParameters(form.value.objective_template)
  return true
}

async function submit() {
  notificationHub.clearErrors()

  let args = null

  if (creationMode.value === 'template') {
    if (!selectedTemplates.value.length) {
      notificationHub.add({
        msg: t('EligibilityCriteriaForm.no_template_error'),
        type: 'error',
      })
      stepper.value.loading = false
      return
    }
    const data = []
    for (const template of selectedTemplates.value) {
      data.push({
        objective_template_uid: preInstanceMode.value
          ? template.template_uid
          : template.uid,
        parameter_terms: preInstanceMode.value ? template.parameter_terms : [],
        library_name: template.library.name,
      })
    }
    await study.batchCreateStudyObjectives(
      studiesGeneralStore.selectedStudy.uid,
      data
    )
  } else if (creationMode.value === 'scratch') {
    const data = JSON.parse(JSON.stringify(form.value))
    if (preInstanceMode.value && creationMode.value !== 'scratch') {
      data.objective_template.uid = data.objective_template.template_uid
    }
    args = {
      studyUid: studiesGeneralStore.selectedStudy.uid,
      form: data,
      parameters: parameters.value,
    }
    await studiesObjectivesStore.addStudyObjectiveFromTemplate(args)
  } else {
    for (const item of selectedStudyObjectives.value) {
      args = {
        studyUid: studiesGeneralStore.selectedStudy.uid,
        objectiveUid: item.objective.uid,
      }
      if (form.value.objective_level) {
        args.objectiveLevelUid = form.value.objective_level.term_uid
      }
      await studiesObjectivesStore.addStudyObjective(args)
    }
  }
  emit('added')
  notificationHub.add({ msg: t('StudyObjectiveForm.objective_added') })
  close()
}
</script>

<style scoped>
.header-title {
  color: rgb(var(--v-theme-secondary)) !important;
  font-size: large;
}
</style>
