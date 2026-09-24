<template>
  <TemplateIndexingForm
    ref="baseForm"
    :form="form"
    :template="template"
    @emit-form="updateForm"
  >
    <template #templateIndexFields>
      <NotApplicableField
        :checked="
          template && (!template.categories || !template.categories.length)
        "
        :clean-function="cleanObjectiveCategories"
      >
        <template #mainField="{ notApplicable }">
          <MultipleSelect
            v-model="localForm.categories"
            :label="$t('ObjectiveTemplateForm.objective_category')"
            data-cy="template-objective-category"
            :items="objectiveCategories"
            item-title="sponsor_preferred_name"
            item-value="term_uid"
            :disabled="notApplicable"
            :rules="[
              (value) => formRules.requiredIfNotNA(value, notApplicable),
            ]"
          />
        </template>
      </NotApplicableField>
      <YesNoField
        v-model="localForm.is_confirmatory_testing"
        :label="$t('ObjectiveTemplateForm.confirmatory_testing')"
        data-cy="template-confirmatory-testing"
      />
    </template>
  </TemplateIndexingForm>
</template>

<script setup>
import { inject, ref } from 'vue'
import MultipleSelect from '@/components/tools/MultipleSelect.vue'
import NotApplicableField from '@/components/tools/NotApplicableField.vue'
import TemplateIndexingForm from './TemplateIndexingForm.vue'
import terms from '@/api/controlledTerminology/terms'
import YesNoField from '@/components/tools/YesNoField.vue'

const formRules = inject('formRules')
const props = defineProps({
  form: {
    type: Object,
    default: null,
  },
  template: {
    type: Object,
    default: null,
  },
})

const baseForm = ref()
const objectiveCategories = ref([])
const localForm = ref({ ...props.form })

function updateForm(indications) {
  localForm.value = { ...localForm.value, ...indications }
}

function cleanObjectiveCategories(value) {
  if (value) {
    localForm.value.categories = []
  }
}

function preparePayload() {
  const result = {
    is_confirmatory_testing: localForm.value.is_confirmatory_testing,
    category_uids: [],
  }

  Object.assign(result, baseForm.value.preparePayload())
  if (localForm.value.categories) {
    for (const category of localForm.value.categories) {
      if (typeof category === 'string') {
        result.category_uids.push(category)
      } else {
        result.category_uids.push(category.term_uid)
      }
    }
  }
  return result
}

terms.getTermsByCodelist('objectiveCategories').then((resp) => {
  objectiveCategories.value = resp.data.items
})

// We get the large term model with name and attributes,
// add sponsor_preferred_name on the root.
if (localForm.value.categories) {
  for (const category of localForm.value.categories) {
    if (Object.prototype.hasOwnProperty.call(category, 'name')) {
      category.sponsor_preferred_name = category.name.sponsor_preferred_name
    }
  }
}

defineExpose({
  preparePayload,
})
</script>
