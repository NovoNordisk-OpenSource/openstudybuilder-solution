<template>
  <div class="fullscreen-dialog">
    <HorizontalStepperForm
      ref="stepper"
      :title="title"
      :steps="steps"
      :form-observer-getter="getObserver"
      :help-items="helpItems"
      :editable="preInstance !== undefined && preInstance !== null"
      @close="close"
      @save="submit"
    >
      <template #[`step.setValues`]>
        <v-form ref="valuesForm">
          <ParameterValueSelector
            v-if="template"
            v-model="parameters"
            :template="template.name"
            preview-text=" "
          />
          <ParameterValueSelector
            v-else-if="preInstance"
            v-model="parameters"
            :template="preInstance.name"
            preview-text=" "
          />
        </v-form>
      </template>
      <template #[`step.indexing`]>
        <v-form ref="indexingForm">
          <slot
            name="indexingTab"
            :form="form"
            :template="template ? template : preInstance"
          />
        </v-form>
      </template>
      <template #[`step.change`]>
        <v-form ref="changeForm">
          <v-textarea
            v-model="form.change_description"
            :label="$t('HistoryTable.change_description')"
            :rows="1"
            clearable
            auto-grow
            class="white pa-5"
            :rules="[formRules.required]"
          />
        </v-form>
      </template>
    </HorizontalStepperForm>
  </div>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import _isEqual from 'lodash/isEqual'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import instances from '@/utils/instances'
import ParameterValueSelector from '@/components/tools/ParameterValueSelector.vue'
import templatesApi from '@/api/templates'
import templatePreInstancesApi from '@/api/templatePreInstances'

const notificationHub = inject('notificationHub')
const formRules = inject('formRules')
const props = defineProps({
  objectType: {
    type: String,
    default: null,
  },
  template: {
    type: Object,
    default: null,
    required: false,
  },
  preInstance: {
    type: Object,
    default: null,
    required: false,
  },
  preparePayloadFunction: {
    type: Function,
    default: null,
    required: false,
  },
  prepareIndexingPayloadFunction: {
    type: Function,
    default: null,
    required: false,
  },
})
const emit = defineEmits(['close', 'success'])
const { t } = useI18n()

const form = ref({})
const helpItems = ref([])
const originalParameters = ref([])
const parameters = ref([])
const steps = ref([
  { name: 'setValues', title: t('PreInstanceForm.step1_title') },
  { name: 'indexing', title: t('PreInstanceForm.step2_title') },
])
const stepper = ref()
const valuesForm = ref()
const indexingForm = ref()
const changeForm = ref()

let api
let originalForm = {}

const translationKey = computed(() => {
  const parts = props.objectType.split('-')
  return parts
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join('')
})
const title = computed(() => {
  const context = {}
  if (props.template) {
    return t(`${translationKey.value}PreInstanceForm.add_title`, context)
  }
  return t(`${translationKey.value}PreInstanceForm.edit_title`, context)
})

watch(
  () => props.template,
  (value) => {
    if (value) {
      form.value = { ...value }
      loadParameters(value)
    }
  },
  { immediate: true }
)

watch(
  () => props.preInstance,
  (value) => {
    if (value) {
      form.value = { ...value }
      form.value.change_description = t('_global.work_in_progress')
      originalForm = JSON.parse(JSON.stringify(form.value))
      steps.value.push({
        name: 'change',
        title: t('GenericTemplateForm.step4_title'),
      })
    }
  },
  { immediate: true }
)

function loadApi() {
  let result = props.objectType.replace('Templates', '')
  if (result === 'activity') {
    result = 'activity-instruction'
  }
  if (props.template) {
    api = templatesApi(`/${result}-templates`)
  } else {
    api = templatePreInstancesApi(result)
  }
}

onMounted(() => {
  if (props.preInstance) {
    api.getParameters(props.preInstance.template_uid).then((resp) => {
      parameters.value = resp.data
      instances.loadParameterValues(
        props.preInstance.parameter_terms,
        parameters.value
      )
      originalParameters.value = JSON.parse(JSON.stringify(parameters.value))
    })
  }
})

function close() {
  notificationHub.clearErrors()
  parameters.value = []
  form.value = {}
  stepper.value.reset()
  emit('close')
}

async function loadParameters(template) {
  if (!api) {
    let result = props.objectType.replace('Templates', '')
    if (result === 'activity') {
      result = 'activity-instruction'
    }
    api = templatesApi(`/${result}-templates`)
  }
  const resp = await api.getParameters(template.uid)
  parameters.value = resp.data
}

function getObserver(step) {
  let result
  switch (step) {
    case 1:
      result = valuesForm.value
      break
    case 2:
      result = indexingForm.value
      break
    case 3:
      result = changeForm.value
  }
  return result
}

async function preparePayload(data, creation) {
  if (props.preparePayloadFunction) {
    props.preparePayloadFunction(data)
  }
  data.parameter_terms = await instances.formatParameterValues(parameters.value)
  if (props.template) {
    data.library_name = props.template.library.name
  }
  if (creation) {
    Object.assign(data, prepareIndexingPayload())
  }
}

function prepareIndexingPayload() {
  const result = {}
  if (form.value.indications && form.value.indications.length > 0) {
    result.indication_uids = form.value.indications.map((item) => item.term_uid)
  } else {
    result.indication_uids = []
  }
  if (props.prepareIndexingPayloadFunction) {
    props.prepareIndexingPayloadFunction(result)
  }
  return result
}

async function submit() {
  notificationHub.clearErrors()

  const data = { ...form.value }
  await preparePayload(data, props.template !== undefined)
  if (props.template) {
    await api.addPreInstance(props.template.uid, data)
    emit('success')
    notificationHub.add({
      msg: t(`${translationKey.value}PreInstanceForm.add_success`),
    })
  } else {
    let updated = false
    if (!_isEqual(originalParameters.value, parameters.value)) {
      await api.update(props.preInstance.uid, data)
      updated = true
    }
    if (!_isEqual(originalForm, data)) {
      const indexingData = prepareIndexingPayload()
      await api.updateIndexings(props.preInstance.uid, indexingData)
      updated = true
    }
    if (updated) {
      emit('success')
      notificationHub.add({
        msg: t(`${translationKey.value}PreInstanceForm.update_success`),
      })
    } else {
      notificationHub.add({
        type: 'info',
        msg: t('_global.no_changes'),
      })
    }
  }
  close()
}

loadApi()
</script>
