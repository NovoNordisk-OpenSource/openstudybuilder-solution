<template>
  <div>
    <v-autocomplete
      :label="$t('UCUMUnitField.label')"
      data-cy="ucum-unit-field"
      :model-value="value"
      :items="ucumUnits"
      :item-title="getUcumDisplay"
      return-object
      clearable
      v-bind="$attrs"
      @update:search-input="searchForUnit"
      @update:model-value="update"
    />
  </div>
</template>

<script>
import * as ucumlhc from '@lhncbc/ucum-lhc'

const utils = ucumlhc.UcumLhcUtils.getInstance()

export default {
  props: {
    modelValue: {
      type: Object,
      default: undefined,
    },
  },
  emits: ['update:modelValue'],
  data() {
    return {
      ucumUnits: [],
    }
  },
  methods: {
    searchForUnit(value) {
      if (!value) {
        value = ''
      }
      const result = utils.checkSynonyms(value)
      if (result.status === 'succeeded') {
        this.ucumUnits = result.units
      }
    },
    getUcumDisplay(item) {
      return `${item.code} (${item.name})`
    },
    update(value) {
      this.$emit('update:modelValue', value)
    },
  },
}
</script>
