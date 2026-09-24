<template>
  <PreInstanceForm
    object-type="footnoteTemplates"
    :prepare-payload-function="preparePayload"
    :prepare-indexing-payload-function="prepareIndexingPayload"
    v-bind="$attrs"
  >
    <template #indexingTab="{ form, template }">
      <FootnoteTemplateIndexingForm
        ref="indexingForm"
        :form="form"
        :template="template"
      />
    </template>
  </PreInstanceForm>
</template>

<script>
import FootnoteTemplateIndexingForm from './FootnoteTemplateIndexingForm.vue'
import PreInstanceForm from '@/components/library/PreInstanceForm.vue'

export default {
  components: {
    FootnoteTemplateIndexingForm,
    PreInstanceForm,
  },
  props: {
    footnoteType: {
      type: Object,
      default: null,
    },
  },
  methods: {
    preparePayload(payload) {
      payload.type_uid = this.footnoteType.term_uid
      Object.assign(payload, this.$refs.indexingForm.preparePayload(payload))
    },
    prepareIndexingPayload(payload) {
      if (this.$refs.indexingForm) {
        Object.assign(payload, this.$refs.indexingForm.preparePayload(payload))
      }
    },
  },
}
</script>
