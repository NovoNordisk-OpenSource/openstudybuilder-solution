<template>
  <v-card :color="color" density="compact" rounded="lg" border="sm" flat>
    <v-card-text class="d-flex align-center pa-2 text-primary">
      <v-checkbox v-model="value" color="primary" :label="label" hide-details />
      <v-spacer />
      <v-tooltip v-if="help" v-model="showHelp" location="right">
        <template #activator="{ props }">
          <v-btn
            color="primary"
            icon="mdi-information-outline"
            variant="text"
            v-bind="props"
          />
        </template>
        <span>{{ help }}</span>
      </v-tooltip>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { computed, ref } from 'vue'

const emit = defineEmits(['update:modelValue'])
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  label: {
    type: String,
    default: null,
  },
  help: {
    type: String,
    default: null,
  },
})

const showHelp = ref(false)

const color = computed(() => {
  return props.modelValue ? 'nnLightBlue200' : ''
})
const value = computed({
  get() {
    return props.modelValue
  },
  set(newValue) {
    emit('update:modelValue', newValue)
  },
})
</script>
