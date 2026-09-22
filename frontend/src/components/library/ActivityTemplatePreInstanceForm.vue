<template>
  <PreInstanceForm
    object-type="activityTemplates"
    :prepare-indexing-payload-function="prepareIndexingPayload"
    v-bind="$attrs"
  >
    <template #indexingTab="{ form, template, preInstance }">
      <ActivityTemplateIndexingForm
        v-if="template"
        ref="indexingForm"
        :form="form"
        :template="template"
      />
      <ActivityTemplateIndexingForm
        v-else
        ref="indexingForm"
        :form="form"
        :template="preInstance"
      />
    </template>
  </PreInstanceForm>
</template>

<script>
import ActivityTemplateIndexingForm from './ActivityTemplateIndexingForm.vue'
import PreInstanceForm from '@/components/library/PreInstanceForm.vue'

export default {
  components: {
    ActivityTemplateIndexingForm,
    PreInstanceForm,
  },
  props: {
    activityType: {
      type: Object,
      default: null,
    },
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
