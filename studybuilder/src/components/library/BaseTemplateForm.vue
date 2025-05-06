<template>
  <div class="fullscreen-dialog">
    <HorizontalStepperForm
      ref="stepper"
      :title="title"
      :steps="steps"
      :form-observer-getter="getObserver"
      :editable="template !== undefined && template !== null"
      :help-items="helpItems"
      :extra-step-validation="extraValidation"
      @close="close"
      @save="submit"
    >
      <template #[`step.template`]>
        <v-row>
          <v-col cols="11">
            <v-form ref="templateForm">
              <NNTemplateInputField
                v-model="form.name"
                data-cy="template-text-field"
                :items="parameterTypes"
                :show-drop-down-early="true"
                :label="$t(`${translationKey}TemplateForm.name`)"
                :rules="[formRules.required]"
              />
            </v-form>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="11">
            <p class="text-grey text-subtitle-1 font-weight-bold">
              {{ $t('_global.plain_text_version') }}
            </p>
            <div class="pa-4 bg-parameterBackground">
              {{ namePlainPreview }}
            </div>
          </v-col>
        </v-row>
        <slot name="extraFields" :form="form" />
      </template>
      <template #[`step.template.afterActions`]>
        <v-btn
          class="secondary-btn"
          data-cy="verify-syntax-button"
          color="white"
          variant="outlined"
          elevation="2"
          rounded="xl"
          @click="verifySyntax"
        >
          {{ $t('_global.verify_syntax') }}
        </v-btn>
      </template>
      <template #[`step.testTemplate`]>
        <ParameterValueSelector
          v-model="parameters"
          :template="form.name"
          load-parameter-values-from-template
          preview-text=" "
          :edit-mode="template !== undefined && template !== null"
        />
      </template>
      <template #[`step.properties`]>
        <v-form ref="propertiesForm">
          <slot name="indexingTab" :form="form" />
        </v-form>
      </template>
      <template #[`step.change`]>
        <v-form ref="changeForm">
          <v-textarea
            v-model="form.change_description"
            :label="$t('HistoryTable.change_description')"
            data-cy="template-change-description"
            :rows="1"
            density="compact"
            clearable
            auto-grow
            class="white pa-5"
            :rules="[formRules.required]"
          />
        </v-form>
      </template>
    </HorizontalStepperForm>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  </div>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import NNTemplateInputField from '@/components/tools/NNTemplateInputField.vue'
import ParameterValueSelector from '@/components/tools/ParameterValueSelector.vue'
import statuses from '@/constants/statuses'
import templateParameterTypes from '@/api/templateParameterTypes'
import templatesApi from '@/api/templates'

const eventBusEmit = inject('eventBusEmit')
const formRules = inject('formRules')
const props = defineProps({
  objectType: {
    type: String,
    default: null,
  },
  template: {
    type: Object,
    default: null,
  },
  loadFormFunction: {
    type: Function,
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
  helpItems: {
    type: Array,
    default: null,
    required: false,
  },
  titleContext: {
    type: Object,
    default: null,
    required: false,
  },
})
const emit = defineEmits(['close', 'templateAdded', 'templateUpdated'])
const { t } = useI18n()

const form = ref({})
const originalForm = ref({})
const parameters = ref([])
const parameterTypes = ref([])
const steps = ref([])
const stepper = ref()
const confirm = ref()
const templateForm = ref()
const propertiesForm = ref()
const changeForm = ref()

const api = templatesApi(`/${props.objectType}-templates`)
const createModeSteps = [
  { name: 'template', title: t('GenericTemplateForm.step1_add_title') },
  { name: 'testTemplate', title: t('GenericTemplateForm.step2_title') },
  { name: 'properties', title: t('GenericTemplateForm.step3_title') },
]
const editModeSteps = [
  { name: 'template', title: t('GenericTemplateForm.step1_edit_title') },
  { name: 'testTemplate', title: t('GenericTemplateForm.step2_title') },
  { name: 'properties', title: t('GenericTemplateForm.step3_title') },
  { name: 'change', title: t('GenericTemplateForm.step4_title') },
]

const translationKey = computed(() => {
  const parts = props.objectType.split('-')
  return parts
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join('')
})
const title = computed(() => {
  const context = props.titleContext ? props.titleContext : {}
  return props.template
    ? t(`${translationKey.value}TemplateForm.edit_title`, context)
    : t(`${translationKey.value}TemplateForm.add_title`, context)
})
const namePlainPreview = computed(() => {
  if (form.value.name) {
    const result = new DOMParser().parseFromString(form.value.name, 'text/html')
    return result.documentElement.textContent || ''
  }
  return ''
})

steps.value = createModeSteps
templateParameterTypes.getTypes().then((resp) => {
  parameterTypes.value = resp.data
})

watch(
  () => props.template,
  (value) => {
    if (value) {
      api.getTemplate(value.uid).then((resp) => {
        loadFormFromTemplate(resp.data)
        steps.value = editModeSteps
      })
    }
  },
  { immediate: true }
)

function close() {
  form.value = {}
  stepper.value.reset()
  steps.value = createModeSteps
  parameters.value = []
  emit('close')
}

function getObserver(step) {
  let result = undefined
  switch (step) {
    case 1:
      result = templateForm.value
      break
    case 3:
      result = propertiesForm.value
      break
    case 4:
      result = changeForm.value
  }
  return result
}

/**
 * Do a step by step loading of the form using the given template because we don't want to include every fields.
 */
function loadFormFromTemplate(template) {
  form.value = {
    name: template ? template.name : null,
    library: template ? template.library : { name: 'Sponsor' },
    indications: template ? template.indications : null,
  }
  if (template.status === statuses.DRAFT) {
    form.value.change_description = t('_global.work_in_progress')
  }
  if (props.loadFormFunction) {
    props.loadFormFunction(form.value)
  }
  originalForm.value = { ...form.value }
}

async function preparePayload(data, creation) {
  if (props.preparePayloadFunction) {
    props.preparePayloadFunction(data)
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

async function addTemplate() {
  const data = { ...form.value }

  await preparePayload(data, true)
  await api.create(data)
  emit('templateAdded')
  eventBusEmit('notification', {
    msg: t(`${translationKey.value}TemplateForm.add_success`),
  })
}

async function updateTemplate() {
  const data = {
    ...form.value,
    indication_uids: form.value.indications
      ? form.value.indications.map((item) => item.term_uid)
      : [],
  }

  let template
  let resp
  if (
    props.template.name !== data.name ||
    props.template.guidance_text !== data.guidance_text
  ) {
    resp = await api.update(props.template.uid, data)
    template = resp.data
  }

  const indexingData = prepareIndexingPayload()
  resp = await api.updateIndexings(props.template.uid, indexingData)
  if (!template) {
    template = resp.data
  }
  emit('templateUpdated', template)
  const key = `${translationKey.value}TemplateForm.update_success`
  eventBusEmit('notification', { msg: t(key) })
}

function verifySyntax() {
  if (!form.value.name) {
    return
  }
  const data = { name: form.value.name }
  api.preValidate(data).then(() => {
    eventBusEmit('notification', { msg: t('_global.valid_syntax') })
  })
}

async function extraValidation(step) {
  if (step !== 1) {
    return true
  }
  try {
    await api.preValidate({ name: form.value.name })
  } catch {
    return false
  }
  return true
}

async function submit() {
  try {
    if (!props.template) {
      await addTemplate()
    } else {
      await updateTemplate()
    }
    close()
  } finally {
    stepper.value.loading = false
  }
}
</script>
