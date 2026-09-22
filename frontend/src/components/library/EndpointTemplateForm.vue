<template>
  <BaseTemplateForm
    object-type="endpoint"
    :template="template"
    :load-form-function="loadForm"
    :prepare-indexing-payload-function="prepareIndexingPayload"
    :help-items="helpItems"
    v-bind="$attrs"
  >
    <template #indexingTab="{ form }">
      <EndpointTemplateIndexingForm
        ref="indexingForm"
        :form="form"
        :template="template"
      />
    </template>
  </BaseTemplateForm>
</template>

<script>
import BaseTemplateForm from './BaseTemplateForm.vue'
import EndpointTemplateIndexingForm from './EndpointTemplateIndexingForm.vue'
import { useFormStore } from '@/stores/form'

export default {
  components: {
    BaseTemplateForm,
    EndpointTemplateIndexingForm,
  },
  props: {
    template: {
      type: Object,
      default: null,
    },
  },
  setup() {
    const formStore = useFormStore()
    return {
      formStore,
    }
  },
  data() {
    return {
      helpItems: [
        'EndpointTemplateForm.endpoint_category',
        'EndpointTemplateForm.endpoint_sub_category',
      ],
    }
  },
  methods: {
    loadForm(form) {
      if (this.template.categories && this.template.categories.length) {
        form.categories = this.template.categories
      }
      if (this.template.sub_categories && this.template.sub_categories.length) {
        form.sub_categories = this.template.sub_categories
      }
      this.formStore.save(form)
    },
    prepareIndexingPayload(payload) {
      if (this.$refs.indexingForm) {
        Object.assign(payload, this.$refs.indexingForm.preparePayload(payload))
      }
    },
  },
}
</script>
