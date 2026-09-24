<template>
  <BaseTemplateForm
    object-type="objective"
    :template="template"
    :load-form-function="loadForm"
    :prepare-indexing-payload-function="prepareIndexingPayload"
    :help-items="helpItems"
    v-bind="$attrs"
  >
    <template #indexingTab="{ form }">
      <ObjectiveTemplateIndexingForm
        ref="indexingForm"
        :form="form"
        :template="template"
      />
    </template>
  </BaseTemplateForm>
</template>

<script setup>
import { ref } from 'vue'
import BaseTemplateForm from './BaseTemplateForm.vue'
import ObjectiveTemplateIndexingForm from './ObjectiveTemplateIndexingForm.vue'

const props = defineProps({
  template: {
    type: Object,
    default: null,
  },
})

const helpItems = ref([
  'ObjectiveTemplateForm.objective_category',
  'ObjectiveTemplateForm.confirmatory_testing',
])
const indexingForm = ref()

function loadForm(form) {
  form.is_confirmatory_testing = props.template
    ? props.template.is_confirmatory_testing
    : null
  if (
    props.template &&
    props.template.categories &&
    props.template.categories.length
  ) {
    form.categories = props.template.categories
  }
}

function prepareIndexingPayload(payload) {
  // Check if form has been displayed before (possible in edit mode)
  if (indexingForm.value) {
    Object.assign(payload, indexingForm.value.preparePayload(payload))
  }
}
</script>
