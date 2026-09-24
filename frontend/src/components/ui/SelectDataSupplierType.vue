<template>
  <v-autocomplete
    v-model="selectedValue"
    :label="label"
    :items="dataSupplierTypes"
    item-title="sponsor_preferred_name_sentence_case"
    item-value="term_uid"
    :rules="required ? [(v) => !!v || 'Data Supplier Type is required'] : []"
    :disabled="disabled"
    clearable
    :loading="loading"
    @update:model-value="handleChange"
  />
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import terms from '@/api/controlledTerminology/terms'

const props = defineProps({
  modelValue: {
    type: String,
    default: null,
  },
  label: {
    type: String,
    default: 'Data Supplier Type',
  },
  required: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue'])

const dataSupplierTypes = ref([])
const selectedValue = ref(props.modelValue)
const loading = ref(false)

const fetchDataSupplierTypes = async () => {
  loading.value = true
  try {
    const response = await terms.getTermsByCodelist('dataSupplierType', {
      all: true,
    })
    dataSupplierTypes.value = response.data.items || []
  } catch (error) {
    console.error('Error fetching data supplier types:', error)
  } finally {
    loading.value = false
  }
}

const handleChange = (value) => {
  emit('update:modelValue', value)
}

watch(
  () => props.modelValue,
  (newValue) => {
    selectedValue.value = newValue
  }
)

onMounted(() => {
  fetchDataSupplierTypes()
})
</script>
