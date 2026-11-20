<template>
  <v-tooltip v-if="text" location="top">
    <template #activator="{ props }">
      <v-icon v-bind="props" size="14" class="ml-1" color="medium-emphasis">
        mdi-information-outline
      </v-icon>
    </template>
    {{ text }}
  </v-tooltip>
</template>

<script setup>
import { computed } from 'vue'
import { useStandardsImportTypeDescriptionsStore } from '@/stores/standardsImportTypeDescriptions'

const props = defineProps({
  enumKey: {
    type: String,
    required: true,
  },
  value: {
    type: String,
    required: true,
  },
})

const store = useStandardsImportTypeDescriptionsStore()
const text = computed(() =>
  store.getValueDescription(props.enumKey, props.value)
)
</script>
