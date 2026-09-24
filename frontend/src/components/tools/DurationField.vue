<template>
  <div>
    <div
      :class="{ text_focused: text_focused, select_focused: select_focused }"
      class="d-flex"
    >
      <v-form ref="observer" class="value-selector">
        <v-text-field
          v-model="form[numericFieldName]"
          data-cy="duration-value"
          type="number"
          hide-details="auto"
          :disabled="disabled"
          bg-color="white"
          color="nnBaseBlue"
          base-color="nnBaseBlue"
          :rules="durationRules"
          @update:model-value="update(numericFieldName, $event)"
          @focus="text_focused = true"
          @blur="text_focused = false"
        />
      </v-form>
      <v-select
        v-if="withUnit"
        data-cy="duration-unit"
        class="unit-selector ml-4"
        :model-value="form[unitFieldName]"
        :placeholder="$t('DurationField.label')"
        :items="units"
        item-title="name"
        item-value="uid"
        return-object
        bg-color="white"
        color="nnBaseBlue"
        base-color="nnBaseBlue"
        clearable
        hide-details="auto"
        :disabled="disabled"
        @update:model-value="update(unitFieldName, $event)"
        @focus="select_focused = true"
        @blur="select_focused = false"
      />
    </div>
    <div class="mt-1 v-input__control theme--light">
      <v-messages :value="text_focused || select_focused ? [hint] : []" />
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  inject: ['formRules'],
  props: {
    modelValue: {
      type: Object,
      default: undefined,
    },
    label: {
      type: String,
      default: '',
    },
    hint: {
      type: String,
      default: '',
    },
    numericFieldName: {
      type: String,
      default: () => 'duration_value',
    },
    unitFieldName: {
      type: String,
      default: () => 'duration_unit_code',
    },
    withUnit: {
      type: Boolean,
      default: true,
    },
    min: {
      type: Number,
      default: 0,
    },
    max: {
      type: Number,
      default: 100,
    },
    step: {
      type: Number,
      default: 1,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['update:modelValue'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      units: computed(() => studiesGeneralStore.units),
    }
  },
  data() {
    return {
      form: {},
      select_focused: false,
      text_focused: false,
    }
  },
  computed: {
    durationRules() {
      let result = []
      if (this.min !== undefined) {
        result.push((value) => this.formRules.min_value(value, this.min))
      }
      if (this.max !== undefined) {
        result.push((value) => this.formRules.max_value(value, this.max))
      }
      return result
    },
  },
  watch: {
    modelValue: {
      handler(newValue) {
        if (newValue) {
          this.form = { ...newValue }
        }
      },
      immediate: true,
    },
  },
  methods: {
    update(key, val) {
      if (val) {
        this.$emit('update:modelValue', {
          ...this.form,
          [key]: val.uid ? { uid: val.uid, name: val.name } : val,
        })
      } else {
        this.$emit('update:modelValue', { ...this.form, [key]: undefined })
      }
    },
  },
}
</script>

<style>
.value-selector {
  width: 100px;
}
.unit-selector {
  max-width: 200px;
}
</style>
