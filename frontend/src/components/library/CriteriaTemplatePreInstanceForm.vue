<template>
  <PreInstanceForm
    object-type="criteriaTemplates"
    :prepare-payload-function="preparePayload"
    :prepare-indexing-payload-function="prepareIndexingPayload"
    v-bind="$attrs"
  >
    <template #indexingTab="{ form, template, preInstance }">
      <CriteriaTemplateIndexingForm
        v-if="template"
        ref="indexingForm"
        :form="form"
        :template="template"
      />
      <CriteriaTemplateIndexingForm
        v-else
        ref="indexingForm"
        :form="form"
        :template="preInstance"
      />
    </template>
  </PreInstanceForm>
</template>

<script>
import CriteriaTemplateIndexingForm from './CriteriaTemplateIndexingForm.vue'
import PreInstanceForm from '@/components/library/PreInstanceForm.vue'

export default {
  components: {
    CriteriaTemplateIndexingForm,
    PreInstanceForm,
  },
  props: {
    criteriaType: {
      type: Object,
      default: null,
    },
  },
  methods: {
    preparePayload(payload) {
      payload.type_uid = this.criteriaType.term_uid
    },
    prepareIndexingPayload(payload) {
      if (this.$refs.indexingForm) {
        Object.assign(payload, this.$refs.indexingForm.preparePayload(payload))
      }
    },
  },
}
</script>
