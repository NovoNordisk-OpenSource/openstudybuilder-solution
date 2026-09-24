<template>
  <StudySelectionEditForm
    ref="formRef"
    :title="$t('StudyEndpointEditForm.title')"
    :study-selection="editedObject"
    :template="template"
    :library-name="library.name"
    object-type="endpoint"
    :open="open"
    :get-object-from-selection="(selection) => selection.endpoint"
    :with-unformatted-version="false"
    @init-form="initForm"
    @submit="submit"
    @close="close"
  >
    <template #formFields="{ editTemplate, form }">
      <v-form ref="observer">
        <p class="mt-6 text-secondary text-headline-small">
          {{ $t('StudyEndpointEditForm.units_section') }}
        </p>
        <v-row>
          <v-col cols="9">
            <MultipleSelect
              v-model="form.endpoint_units.units"
              :label="$t('StudyEndpointEditForm.unit')"
              :items="studiesGeneralStore.allUnits"
              :rules="[(value) => formRules.requiredIfNotNA(value, skipUnits)]"
              item-title="name"
              return-object
              :disabled="skipUnits || editTemplate"
            />
          </v-col>
          <v-col cols="3">
            <v-select
              v-if="form.endpoint_units.units.length > 1"
              v-model="form.endpoint_units.separator"
              :label="$t('ParameterValueSelector.separator')"
              :items="separators"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <p class="mt-6 text-secondary text-headline-small">
          {{ $t('StudyEndpointEditForm.timeframe_section') }}
        </p>
        <v-row>
          <v-col cols="11">
            <v-autocomplete
              v-model="timeframeTemplate"
              :label="$t('StudyEndpointEditForm.timeframe')"
              :items="timeframeTemplates"
              item-title="name_plain"
              return-object
              :rules="[formRules.required]"
              :disabled="editTemplate"
            />
          </v-col>
        </v-row>
        <div v-if="timeframeTemplate" class="mt-2">
          <v-progress-circular
            v-if="loadingParameters"
            indeterminate
            color="secondary"
          />

          <template v-else>
            <ParameterValueSelector
              ref="timeframeParamSelector"
              key="timeframeParameters"
              :model-value="timeframeTemplateParameters"
              :template="timeframeTemplate.name"
              color="white"
              stacked
              :disabled="editTemplate"
              :with-unformatted-version="false"
            />
          </template>
        </div>
        <p class="mt-6 text-secondary text-headline-small">
          {{ $t('StudyEndpointEditForm.level_section') }}
        </p>
        <v-row>
          <v-col cols="6">
            <v-select
              v-model="form.endpoint_level"
              :label="$t('StudyEndpointForm.endpoint_level')"
              :items="studiesGeneralStore.endpointLevels"
              item-title="term_name"
              return-object
              clearable
              :disabled="editTemplate"
            />
          </v-col>
          <v-col cols="6">
            <v-select
              v-model="form.endpoint_sublevel"
              :label="$t('StudyEndpointForm.endpoint_sub_level')"
              :items="studiesGeneralStore.endpointSubLevels"
              item-title="term_name"
              return-object
              clearable
              :disabled="editTemplate"
            />
          </v-col>
        </v-row>
        <p class="mt-6 text-secondary text-headline-small">
          {{ $t('StudyEndpointEditForm.objective_section') }}
        </p>
        <v-row>
          <v-col cols="11">
            <v-autocomplete
              v-model="form.study_objective"
              :label="$t('StudyEndpointForm.objective')"
              :items="studyObjectives"
              item-title="objective.name_plain"
              return-object
              clearable
              :disabled="editTemplate"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </StudySelectionEditForm>
</template>

<script setup>
import _isEmpty from 'lodash/isEmpty'
import constants from '@/constants/libraries'
import formUtils from '@/utils/forms'
import instances from '@/utils/instances'
import MultipleSelect from '@/components/tools/MultipleSelect.vue'
import ParameterValueSelector from '@/components/tools/ParameterValueSelector.vue'
import statuses from '@/constants/statuses'
import study from '@/api/study'
import StudySelectionEditForm from './StudySelectionEditForm.vue'
import timeframes from '@/api/timeframes'
import timeframeTemplatesApi from '@/api/timeframeTemplates'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudiesEndpointsStore } from '@/stores/studies-endpoints'
import { inject, ref, watch, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  studyEndpoint: {
    type: Object,
    default: undefined,
  },
  open: Boolean,
})
const { t } = useI18n()
const emit = defineEmits(['close', 'updated'])
const notificationHub = inject('notificationHub')
const formRules = inject('formRules')
const studiesGeneralStore = useStudiesGeneralStore()
const studiesEndpointsStore = useStudiesEndpointsStore()
const loadingParameters = ref(false)
const skipUnits = ref(false)
const studyObjectives = ref([])
const timeframeTemplate = ref(null)
const timeframeTemplates = ref([])
const originalForm = ref({})
const timeframeTemplateParameters = ref([])
const separators = ref([' and ', ' or ', ' and/or '])
const formRef = ref()
const observer = ref()
const editedObject = ref({})

const template = computed(() => {
  return editedObject.value.endpoint
    ? editedObject.value.endpoint.template
    : editedObject.value.template
})
const library = computed(() => {
  return (
    editedObject.value.endpoint?.library ??
    editedObject.value.template?.library ??
    {}
  )
})

watch(timeframeTemplate, (value) => {
  if (!value) {
    return
  }
  if (
    editedObject.value.timeframe &&
    editedObject.value.timeframe.template.uid === value.uid
  ) {
    return
  }
  loadingParameters.value = true
  timeframeTemplatesApi
    .getParameters(value.uid, {
      study_uid: studiesGeneralStore.selectedStudy.uid,
    })
    .then((resp) => {
      timeframeTemplateParameters.value = resp.data
      loadingParameters.value = false
    })
})

watch(
  () => props.studyEndpoint,
  (value) => {
    if (value) {
      study
        .getStudyEndpoint(
          studiesGeneralStore.selectedStudy.uid,
          value.study_endpoint_uid
        )
        .then((resp) => {
          editedObject.value = resp.data
        })
    }
  },
  { immediate: true }
)

onMounted(() => {
  getTimeframeTemplates()
  study
    .getStudyObjectives(studiesGeneralStore.selectedStudy.uid, {
      page_size: 0,
    })
    .then((resp) => {
      studyObjectives.value = resp.data.items.filter((obj) => obj.objective)
    })
})

function close() {
  notificationHub.clearErrors()
  timeframeTemplate.value = null
  emit('close')
}

function initForm(form) {
  form.endpoint_units = editedObject.value.endpoint_units
  form.endpoint_level = editedObject.value.endpoint_level
  form.endpoint_sublevel = editedObject.value.endpoint_sublevel
  if (editedObject.value.timeframe) {
    timeframeTemplate.value = editedObject.value.timeframe.template
    timeframes
      .getObjectParameters(editedObject.value.timeframe.uid, {
        study_uid: studiesGeneralStore.selectedStudy.uid,
      })
      .then((resp) => {
        timeframeTemplateParameters.value = resp.data
        instances.loadParameterValues(
          editedObject.value.timeframe.parameter_terms,
          timeframeTemplateParameters.value
        )
      })
  }
  if (editedObject.value.study_objective) {
    form.study_objective = editedObject.value.study_objective
  }
  originalForm.value = JSON.parse(JSON.stringify(form))
}

async function getStudyEndpointNamePreview(parameters) {
  const endpointData = {
    endpoint_template_uid: editedObject.value.endpoint.template.uid,
    parameter_terms: await instances.formatParameterValues(parameters),
    library_name: editedObject.value.endpoint.library.name,
  }
  const resp = await study.getStudyEndpointPreview(
    studiesGeneralStore.selectedStudy.uid,
    { endpoint_data: endpointData }
  )
  return resp.data.endpoint.name
}

async function getTimeframeNamePreview(parameters) {
  const data = {
    timeframe_template_uid: editedObject.value.timeframe.template.uid,
    parameter_terms: await instances.formatParameterValues(parameters),
    library_name: constants.LIBRARY_USER_DEFINED,
  }
  const resp = await timeframes.getPreview(data)
  return resp.data.name
}

function getTimeframeTemplates() {
  const params = {
    filters: { 'library.name': { v: [constants.LIBRARY_SPONSOR] } },
    page_size: 0,
    status: statuses.FINAL,
  }
  timeframeTemplatesApi.get(params).then((resp) => {
    timeframeTemplates.value = resp.data.items
  })
}

async function submit(newTemplate, form, parameters) {
  const { valid } = await observer.value.validate()
  if (!valid) {
    formRef.value.$refs.form.working = false
    return
  }

  notificationHub.clearErrors()

  const data = formUtils.getDifferences(originalForm.value, form)

  if (newTemplate) {
    data.endpoint_template = newTemplate
    data.endpoint_parameters = parameters
  } else if (!editedObject.value.endpoint) {
    data.endpoint_template = editedObject.value.template
    data.endpoint_parameters = parameters
  } else {
    const namePreview = await getStudyEndpointNamePreview(parameters)
    if (namePreview !== editedObject.value.endpoint.name) {
      data.endpoint_template = editedObject.value.endpoint.endpoint_template
        ? editedObject.value.endpoint.endpoint_template
        : editedObject.value.endpoint.template
      // Hotfix because we don't have the template library here...
      data.endpoint_template.library = {
        name: constants.LIBRARY_SPONSOR,
      }
      data.endpoint_parameters = parameters
    }
  }
  if (!editedObject.value.timeframe) {
    if (timeframeTemplate.value) {
      data.timeframe_template = timeframeTemplate.value
      data.timeframe_parameters = timeframeTemplateParameters.value
      data.timeframe_template.library = {
        name: constants.LIBRARY_USER_DEFINED,
      }
    }
  } else {
    const namePreview = await getTimeframeNamePreview(
      timeframeTemplateParameters.value
    )
    if (namePreview !== editedObject.value.timeframe.name) {
      data.timeframe_template = timeframeTemplate.value
      // Hotfix because we don't have the template library here...
      data.timeframe_template.library = {
        name: constants.LIBRARY_USER_DEFINED,
      }
      data.timeframe_parameters = timeframeTemplateParameters.value
    }
  }
  if (_isEmpty(data)) {
    notificationHub.add({ msg: t('_global.no_changes'), type: 'info' })
    formRef.value.close()
    return
  }
  const args = {
    studyUid: studiesGeneralStore.selectedStudy.uid,
    studyEndpointUid: editedObject.value.study_endpoint_uid,
    form: data,
    library_name: constants.LIBRARY_USER_DEFINED,
  }
  studiesEndpointsStore
    .updateStudyEndpoint(args)
    .then(() => {
      notificationHub.add({
        msg: t('StudyEndpointEditForm.endpoint_updated'),
      })
      emit('updated')
      formRef.value.close()
    })
    .catch((err) => {
      formRef.value.$refs.form.working = false
      console.log(err)
    })
}
</script>
