<template>
  <div
    v-if="label"
    class="text-nnTrueBlue mb-5"
    :class="{ 'label--disabled': disabled }"
  >
    <label>{{ label }}</label>
  </div>
  <div>
    <v-radio-group v-model="currentChoice" :inline="inline">
      <div
        v-for="(choice, index) in choices"
        :key="`choice-${index}`"
        class="choice rounded mr-3 mb-4"
        :style="props.width ? `width: ${props.width}px` : ''"
        :class="{
          'choice--disabled': disabled,
          'choice--selected': !disabled && currentChoice === choice.value,
        }"
        @click="selectChoice(choice.value)"
      >
        <div class="d-flex align-start">
          <div class="mr-2">
            <v-radio :value="choice.value" density="compact" />
          </div>
          <div class="pt-1">
            <div class="text-nnTrueBlue mb-2 font-weight-bold title">
              {{ choice.title }}
            </div>
            <div class="text-nnTrueBlue text">{{ choice.help }}</div>
          </div>
        </div>
      </div>
    </v-radio-group>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: [Boolean, Number, String], default: null },
  label: { type: String, default: '' },
  choices: { type: Array, default: () => [] },
  disabled: {
    type: Boolean,
    default: false,
  },
  inline: {
    type: Boolean,
    default: false,
  },
  width: {
    type: String,
    default: null,
  },
})

const emit = defineEmits(['update:modelValue'])

const currentChoice = computed({
  get() {
    return props.modelValue
  },
  set(value) {
    emit('update:modelValue', value)
  },
})

function selectChoice(value) {
  if (props.disabled) {
    return
  }
  currentChoice.value = value
}
</script>

<style lang="scss" scoped>
.choice {
  border: 1px solid #dbdddf;
  cursor: pointer;
  padding: 14px 16px;

  &--selected {
    background-color: rgb(var(--v-theme-nnSeaBlue100));
  }

  &--disabled {
    cursor: unset;
    opacity: 0.5;
  }

  .title {
    font-size: 14px;
  }
  .text {
    font-size: 14px;
  }
}
.label--disabled {
  opacity: 0.5;
}
</style>
