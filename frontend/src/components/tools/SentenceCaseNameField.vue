<template>
  <v-form ref="observer" data-cy="sentence-case-name-class">
    <v-row>
      <v-col>
        <v-text-field
          v-model="value"
          :label="$t('ActivityForms.name_sentence_case')"
          data-cy="sentence-case-name-field"
          clearable
          :rules="[
            formRules.required,
            (value) => formRules.sameAs(value, name),
          ]"
        />
      </v-col>
    </v-row>
  </v-form>
</template>

<script>
export default {
  inject: ['formRules'],
  props: {
    modelValue: {
      type: String,
      default: '',
    },
    name: {
      type: String,
      default: '',
    },
  },
  emits: ['update:modelValue'],
  computed: {
    value: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit('update:modelValue', value)
      },
    },
  },
  watch: {
    name(value) {
      this.setSentenceCase(value)
    },
  },
  mounted() {
    this.setSentenceCase(this.name)
  },
  methods: {
    setSentenceCase(value) {
      if (value) {
        this.$emit('update:modelValue', value.toLowerCase())
      }
    },
  },
}
</script>
