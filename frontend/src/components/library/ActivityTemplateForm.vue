<template>
  <BaseTemplateForm
    object-type="activity-instruction"
    :template="template"
    :prepare-indexing-payload-function="prepareIndexingPayload"
    :help-items="helpItems"
    v-bind="$attrs"
  >
    <template #indexingTab="{ form }">
      <ActivityTemplateIndexingForm
        ref="indexingForm"
        :form="form"
        :template="template"
      />
    </template>
  </BaseTemplateForm>
</template>

<script>
import ActivityTemplateIndexingForm from './ActivityTemplateIndexingForm.vue'
import BaseTemplateForm from './BaseTemplateForm.vue'

export default {
  components: {
    ActivityTemplateIndexingForm,
    BaseTemplateForm,
  },
  props: {
    template: {
      type: Object,
      default: null,
    },
  },
  data() {
    return {
      activities: [],
      helpItems: [
        'ActivityInstructionTemplateForm.indications',
        'ActivityInstructionTemplateForm.group',
        'ActivityInstructionTemplateForm.sub_group',
        'ActivityInstructionTemplateForm.activity',
      ],
      libraries: [],
      parameterTypes: [],
    }
  },
  methods: {
    prepareIndexingPayload(data) {
      if (this.$refs.indexingForm) {
        Object.assign(data, this.$refs.indexingForm.preparePayload(data))
      }
    },
  },
}
</script>
