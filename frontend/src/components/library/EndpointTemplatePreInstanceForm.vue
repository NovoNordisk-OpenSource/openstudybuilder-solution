<template>
  <PreInstanceForm
    object-type="endpointTemplates"
    :prepare-indexing-payload-function="prepareIndexingPayload"
    v-bind="$attrs"
  >
    <template #indexingTab="{ form, template, preInstance }">
      <EndpointTemplateIndexingForm
        v-if="template"
        ref="indexingForm"
        :form="form"
        :template="template"
      />
      <EndpointTemplateIndexingForm
        v-else
        ref="indexingForm"
        :form="form"
        :template="preInstance"
      />
    </template>
  </PreInstanceForm>
</template>

<script>
import EndpointTemplateIndexingForm from './EndpointTemplateIndexingForm.vue'
import PreInstanceForm from '@/components/library/PreInstanceForm.vue'

export default {
  components: {
    EndpointTemplateIndexingForm,
    PreInstanceForm,
  },
  methods: {
    prepareIndexingPayload(payload) {
      if (this.$refs.indexingForm) {
        Object.assign(payload, this.$refs.indexingForm.preparePayload(payload))
      }
    },
  },
}
</script>
