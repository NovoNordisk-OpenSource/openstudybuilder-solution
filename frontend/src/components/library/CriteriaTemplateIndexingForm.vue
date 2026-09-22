<template>
  <TemplateIndexingForm
    ref="baseForm"
    :form="localForm"
    :template="template"
    @emit-form="updateForm"
  >
    <template #templateIndexFields>
      <NotApplicableField
        class="mt-4"
        :checked="
          template && (!template.categories || !template.categories.length)
        "
        :clean-function="() => (localForm.categories = null)"
      >
        <template #mainField="{ notApplicable }">
          <MultipleSelect
            v-model="localForm.categories"
            :label="$t('CriteriaTemplateForm.criterion_cat')"
            data-cy="template-criterion-category"
            :items="categories"
            item-title="sponsor_preferred_name"
            item-value="term_uid"
            :disabled="notApplicable"
            :rules="[
              (value) => formRules.requiredIfNotNA(value, notApplicable),
            ]"
          />
        </template>
      </NotApplicableField>
      <NotApplicableField
        class="mt-4"
        :checked="
          template &&
          (!template.sub_categories || !template.sub_categories.length)
        "
        :clean-function="() => (localForm.sub_categories = null)"
      >
        <template #mainField="{ notApplicable }">
          <MultipleSelect
            v-model="localForm.sub_categories"
            :label="$t('CriteriaTemplateForm.criterion_sub_cat')"
            data-cy="template-criterion-sub-category"
            :items="subCategories"
            item-title="sponsor_preferred_name"
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
      categories: [],
      subCategories: [],
      localForm: { ...this.form },
      key: 0,
    }
  },
  mounted() {
    // We get the large term model with name and attributes,
    // add sponsor_preferred_name on the root.
    if (this.localForm.categories) {
      for (const category of this.localForm.categories) {
        if (Object.prototype.hasOwnProperty.call(category, 'name')) {
          category.sponsor_preferred_name = category.name.sponsor_preferred_name
        }
      }
    }
    if (this.localForm.sub_categories) {
      for (const subcategory of this.localForm.sub_categories) {
        if (Object.prototype.hasOwnProperty.call(subcategory, 'name')) {
          subcategory.sponsor_preferred_name =
            subcategory.name.sponsor_preferred_name
        }
      }
    }
    terms.getTermsByCodelist('criteriaCategories').then((resp) => {
      this.categories = resp.data.items
    })
    terms.getTermsByCodelist('criteriaSubCategories').then((resp) => {
      this.subCategories = resp.data.items
    })
  },
  methods: {
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
