<template data-cy="template-text-part">
  <BaseTemplateForm
    object-type="criteria"
    :template="template"
    :load-form-function="loadForm"
    :prepare-payload-function="preparePayload"
    :prepare-indexing-payload-function="prepareIndexingPayload"
    :help-items="helpItems"
    :title-context="{ type: criteriaType.sponsor_preferred_name }"
    data-cy="template-text"
    v-bind="$attrs"
  >
    <template #extraFields="{ form }">
      <v-row>
        <v-col cols="11">
          <QuillEditor
            id="editor"
            ref="editor"
            v-model:content="form.guidance_text"
            data-cy="template-guidance-text"
            content-type="html"
            :toolbar="customToolbar"
            :placeholder="$t('CriteriaTemplateForm.guidance_text')"
            class="pt-4"
          />
        </v-col>
      </v-row>
    </template>
    <template #indexingTab="{ form }">
      <CriteriaTemplateIndexingForm
        ref="indexingForm"
        :form="form"
        :template="template"
      />
    </template>
  </BaseTemplateForm>
</template>

<script>
import BaseTemplateForm from './BaseTemplateForm.vue'
import CriteriaTemplateIndexingForm from './CriteriaTemplateIndexingForm.vue'
import { QuillEditor } from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css'
import { useFormStore } from '@/stores/form'

export default {
  components: {
    BaseTemplateForm,
    CriteriaTemplateIndexingForm,
    QuillEditor,
  },
  props: {
    template: {
      type: Object,
      default: null,
    },
    criteriaType: {
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
      customToolbar: [
        ['bold', 'italic', 'underline'],
        [{ script: 'sub' }, { script: 'super' }],
        [{ list: 'ordered' }, { list: 'bullet' }],
      ],
      helpItems: [
        'CriteriaTemplateForm.guidance_text',
        'CriteriaTemplateForm.indication',
        'CriteriaTemplateForm.criterion_cat',
        'CriteriaTemplateForm.criterion_sub_cat',
      ],
    }
  },
  methods: {
    loadForm(form) {
      form.guidance_text = this.template.guidance_text
      if (this.template.categories && this.template.categories.length) {
        form.categories = this.template.categories
      }
      if (this.template.sub_categories && this.template.sub_categories.length) {
        form.sub_categories = this.template.sub_categories
      }
      this.formStore.save(form)
    },
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
