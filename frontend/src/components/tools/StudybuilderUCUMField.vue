<template>
  <div>
    <v-autocomplete
      :label="$t('UCUMUnitField.label')"
      :model-value="value"
      :items="ucumUnits"
      item-value="term_uid"
      item-title="name"
      return-object
      clearable
      v-bind="$attrs"
      @update:model-value="update"
    />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import dictionaries from '@/api/dictionaries'

const props = defineProps({
  modelValue: {
    type: Object,
    default: undefined,
  },
})
const emit = defineEmits(['update:modelValue'])

const ucumUnits = ref([])
const value = ref()

onMounted(() => {
  dictionaries.getCodelists('UCUM').then((resp) => {
    const params = {
      codelist_uid: resp.data.items[0].codelist_uid,
      page_size: 0,
    }
    dictionaries.getTerms(params).then((resp) => {
      ucumUnits.value = resp.data.items
      value.value = ucumUnits.value.find(
        (ucum) => ucum.term_uid === props.modelValue
      )
    })
  })
})

function update(value) {
  emit('update:modelValue', value)
}
</script>
