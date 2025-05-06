<template>
  <TemplateIndexingForm
    ref="baseForm"
    :form="form"
    :template="template"
    @emit-form="updateForm"
  >
    <template #templateIndexFields>
      <NotApplicableField
        :checked="template && checkEmpty(template.categories)"
        :clean-function="() => (localForm.categories = null)"
      >
        <template #mainField="{ notApplicable }">
          <MultipleSelect
            v-model="localForm.categories"
            :label="$t('EndpointTemplateForm.endpoint_category')"
            data-cy="template-endpoint-category"
            :items="endpointCategories"
            item-title="name.sponsor_preferred_name"
            item-value="term_uid"
            :disabled="notApplicable"
            :rules="[
              (value) => formRules.requiredIfNotNA(value, notApplicable),
            ]"
          />
        </template>
      </NotApplicableField>
      <NotApplicableField
        :checked="template && checkEmpty(template.sub_categories)"
        :clean-function="() => (localForm.sub_categories = null)"
      >
        <template #mainField="{ notApplicable }">
          <MultipleSelect
            v-model="localForm.sub_categories"
            :label="$t('EndpointTemplateForm.endpoint_sub_category')"
            data-cy="template-endpoint-sub-category"
            :items="endpointSubCategories"
            item-title="name.sponsor_preferred_name"
            item-value="term_uid"
            :disabled="notApplicable"
            :rules="[
              (value) => formRules.requiredIfNotNA(value, notApplicable),
            ]"
          />
        </template>
      </NotApplicableField>
    </template>
  </TemplateIndexingForm>
</template>

<script>
import MultipleSelect from '@/components/tools/MultipleSelect.vue'
import NotApplicableField from '@/components/tools/NotApplicableField.vue'
import TemplateIndexingForm from './TemplateIndexingForm.vue'
import terms from '@/api/controlledTerminology/terms'
import _isEmpty from 'lodash/isEmpty'

export default {
  components: {
    MultipleSelect,
    NotApplicableField,
    TemplateIndexingForm,
  },
  inject: ['formRules'],
  props: {
    form: {
      type: Object,
      default: null,
    },
    template: {
      type: Object,
      default: null,
    },
  },
  data() {
    return {
      endpointCategories: [],
      endpointSubCategories: [],
      localForm: { ...this.form },
    }
  },
  mounted() {
    terms.getByCodelist('endpointCategories').then((resp) => {
      this.endpointCategories = resp.data.items
    })
    terms.getByCodelist('endpointSubCategories').then((resp) => {
      this.endpointSubCategories = resp.data.items
    })
  },
  methods: {
    checkEmpty(value) {
      return _isEmpty(value)
    },
    updateForm(indications) {
      this.localForm = { ...this.localForm, ...indications }
    },
    preparePayload() {
      const result = {
        category_uids: [],
        sub_category_uids: [],
      }
      Object.assign(result, this.$refs.baseForm.preparePayload())
      if (this.localForm.categories) {
        for (const category of this.localForm.categories) {
          if (typeof category === 'string') {
            result.category_uids.push(category)
          } else {
            result.category_uids.push(category.term_uid)
          }
        }
      }
      if (this.localForm.sub_categories) {
        for (const subcategory of this.localForm.sub_categories) {
          if (typeof subcategory === 'string') {
            result.sub_category_uids.push(subcategory)
          } else {
            result.sub_category_uids.push(subcategory.term_uid)
          }
        }
      }
      return result
    },
  },
}
</script>
