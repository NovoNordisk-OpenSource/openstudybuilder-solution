<template>
  <div class="border-b w-100 pa-2" @keydown.stop>
    <v-text-field
      :model-value="modelValue"
      :placeholder="placeholder"
      :loading="loading"
      prepend-inner-icon="mdi-magnify"
      hide-details
      clearable
      @update:model-value="$emit('update:modelValue', $event)"
      @click:clear="($emit('update:modelValue', ''), $emit('clear'))"
    />
  </div>
</template>

<script setup>
defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  placeholder: {
    type: String,
    default: '',
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['update:modelValue', 'clear'])
</script>
