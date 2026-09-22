<template>
  <div>
    <div class="d-flex">
      <v-text-field
        v-model="form.value"
        class="value-selector"
        :label="label"
        type="number"
        hide-details="auto"
        :disabled="disabled"
        @update:model-value="update"
      />
      <v-autocomplete
        v-model="form.unit_definition_uid"
        class="unit-selector ml-4"
        :label="$t('DurationField.label')"
        :items="units"
        item-title="name"
        item-value="uid"
        clearable
        hide-details="auto"
        :disabled="disabled"
        @update:model-value="update"
      />
    </div>
    <div class="mt-1 v-messages theme--light">
      <div class="v-messages__message">
        {{ hint }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import unitsApi from '@/api/units'

const props = defineProps({
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
  subset: {
    type: String,
    default: '',
  },
  errors: {
    type: Array,
    default: () => [],
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})
const emit = defineEmits(['update:modelValue'])

const form = ref({})
const units = ref([])

watch(
  () => props.modelValue,
  (val) => {
    form.value = { ...val }
  }
)

form.value = { ...props.modelValue }

onMounted(() => {
  unitsApi.getBySubset(props.subset).then((resp) => {
    units.value = resp.data.items
  })
})

function update() {
  emit('update:modelValue', form.value)
}
</script>

<style>
.value-selector {
  max-width: 200px;
}
.unit-selector {
  max-width: 200px;
}
</style>
