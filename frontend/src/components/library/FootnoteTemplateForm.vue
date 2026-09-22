<template data-cy="template-text-part">
  <BaseTemplateForm
    object-type="footnote"
    :template="template"
    :prepare-payload-function="preparePayload"
    :prepare-indexing-payload-function="prepareIndexingPayload"
    :help-items="helpItems"
    :title-context="{ type: footnoteType.sponsor_preferred_name }"
    data-cy="template-text"
    v-bind="$attrs"
  >
    <template #indexingTab="{ form }">
      <FootnoteTemplateIndexingForm
        ref="indexingForm"
        :form="form"
        :template="template"
      />
    </template>
  </BaseTemplateForm>
</template>

<script setup>
import BaseTemplateForm from './BaseTemplateForm.vue'
import FootnoteTemplateIndexingForm from './FootnoteTemplateIndexingForm.vue'
import { ref } from 'vue'

const indexingForm = ref()

const props = defineProps({
  template: {
    type: Object,
    default: null,
  },
  footnoteType: {
    type: Object,
    default: null,
  },
})

const helpItems = [
  'FootnoteTemplateForm.indications',
  'FootnoteTemplateForm.group',
  'FootnoteTemplateForm.sub_group',
  'FootnoteTemplateForm.activity',
]

function preparePayload(payload) {
  payload.type_uid = props.footnoteType.term_uid
}

function prepareIndexingPayload(payload) {
  if (indexingForm.value) {
    Object.assign(payload, indexingForm.value.preparePayload(payload))
  }
}
</script>
