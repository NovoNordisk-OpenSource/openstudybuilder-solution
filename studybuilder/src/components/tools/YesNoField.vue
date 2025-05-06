<template>
  <v-radio-group
    :key="radioKey"
    v-model="value"
    density="compact"
    v-bind="$attrs"
  >
    <v-row>
      <v-col cols="12">
        <v-radio
          v-for="booleanValue in booleanValues"
          ref="radio"
          :key="booleanValue.id"
          :data-cy="'radio-' + booleanValue.label"
          class="fixed-width"
          :label="booleanValue.label"
          :value="booleanValue.value"
          color="primary"
          @mouseup="clearCurrentRadioValue(booleanValue)"
        />
      </v-col>
    </v-row>
  </v-radio-group>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  modelValue: Boolean,
})
const emit = defineEmits(['update:modelValue'])

const booleanValues = [
  { id: 1, label: t('_global.yes'), value: true },
  { id: 2, label: t('_global.no'), value: false },
]
const radioKey = ref(0)

const value = computed({
  get() {
    return props.modelValue
  },
  set(value) {
    emit('update:modelValue', value)
  },
})

function clearCurrentRadioValue(currentValue) {
  if (value.value !== null && currentValue.value === value.value) {
    emit('update:modelValue', null)
    radioKey.value += 1
  }
}
</script>
<style>
.fixed-width {
  width: 150px;
}
</style>
