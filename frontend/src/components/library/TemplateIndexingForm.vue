<template>
  <NotApplicableField
    :clean-function="
      () => {
        ;((localForm.indications = []), emitFormUpdate('indications'))
      }
    "
    :checked="
      template && (!template.indications || !template.indications.length)
    "
  >
    <template #mainField="{ notApplicable }">
      <MultipleSelect
        v-model="localForm.indications"
        :label="$t('GenericTemplateForm.study_indication')"
        data-cy="template-indication-dropdown"
        :items="indications"
        item-title="name"
        return-object
        :disabled="notApplicable"
        :rules="[(value) => formRules.requiredIfNotNA(value, notApplicable)]"
        @update:model-value="emitFormUpdate('indications')"
      />
    </template>
  </NotApplicableField>
  <slot name="templateIndexFields" />
</template>

<script>
import dictionaries from '@/api/dictionaries'
import MultipleSelect from '@/components/tools/MultipleSelect.vue'
import NotApplicableField from '@/components/tools/NotApplicableField.vue'

export default {
  components: {
    MultipleSelect,
    NotApplicableField,
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
  emits: ['emit-form'],
  data() {
    return {
      indications: [],
      localForm: { ...this.form },
    }
  },
  created() {
    dictionaries.getCodelists('SNOMED').then((resp) => {
      /* FIXME: we need a direct way to retrieve the terms here */
      dictionaries
        .getTerms({
          codelist_uid: resp.data.items[0].codelist_uid,
          page_size: 0,
        })
        .then((resp) => {
          this.indications = resp.data.items
          this.indications.sort((a, b) => a.name.localeCompare(b.name))
        })
    })
  },
  methods: {
    emitFormUpdate(fieldName) {
      this.$emit('emit-form', { [fieldName]: this.localForm[fieldName] })
    },
    preparePayload() {
      const data = {}
      data.indication_uids = this.localForm.indications.length
        ? this.localForm.indications.map((item) => item.term_uid)
        : []
      return data
    },
  },
}
</script>
