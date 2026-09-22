<template>
  <v-autocomplete
    v-model="selectedValue"
    :label="label"
    :items="dataSuppliers"
    item-title="name"
    item-value="uid"
    :rules="required ? [(v) => !!v || 'Data Supplier is required'] : []"
    :disabled="disabled"
    clearable
    :loading="loading"
    @update:model-value="handleChange"
  />
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import dataSupplierApi from '@/api/dataSuppliers'

const props = defineProps({
  modelValue: {
    type: String,
    default: null,
  },
  label: {
    type: String,
    default: 'Data Supplier',
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

const dataSuppliers = ref([])
const selectedValue = ref(props.modelValue)
const loading = ref(false)

const fetchDataSuppliers = async () => {
  loading.value = true
  try {
    const response = await dataSupplierApi.get({
      params: {
        page_size: 0,
      },
    })
    dataSuppliers.value = response.data.items || []
  } catch (error) {
    console.error('Error fetching data suppliers:', error)
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
  fetchDataSuppliers()
})
</script>
