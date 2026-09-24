<template>
  <PreInstanceForm
    object-type="objectiveTemplates"
    :prepare-indexing-payload-function="prepareIndexingPayload"
    v-bind="$attrs"
  >
    <template #indexingTab="{ form, template, preInstance }">
      <ObjectiveTemplateIndexingForm
        v-if="template"
        ref="indexingForm"
        :form="form"
        :template="template"
      />
      <ObjectiveTemplateIndexingForm
        v-else
        ref="indexingForm"
        :form="form"
        :template="preInstance"
      />
    </template>
  </PreInstanceForm>
</template>

<script setup>
import { ref } from 'vue'
import ObjectiveTemplateIndexingForm from './ObjectiveTemplateIndexingForm.vue'
import PreInstanceForm from '@/components/library/PreInstanceForm.vue'

const indexingForm = ref()

function prepareIndexingPayload(payload) {
  if (indexingForm.value) {
    Object.assign(payload, indexingForm.value.preparePayload(payload))
  }
}
</script>
