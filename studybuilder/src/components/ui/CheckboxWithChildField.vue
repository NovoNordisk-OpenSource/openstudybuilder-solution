<template>
  <v-card color="#f7f8fa" rounded="lg" flat>
    <v-card-text class="pa-0">
      <slot :update-child-display="updateChildDisplay"></slot>
      <v-switch
        v-if="showChild"
        v-model="value"
        :label="props.label"
        color="primary"
        hide-details
        class="mx-6"
      />
    </v-card-text>
  </v-card>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  label: {
    type: String,
    default: null,
  },
})
const emit = defineEmits(['update:modelValue'])

const value = computed({
  get() {
    return props.modelValue
  },
  set(newValue) {
    emit('update:modelValue', newValue)
  },
})

const showChild = ref(false)

function updateChildDisplay(newValue) {
  showChild.value = newValue
}
</script>
