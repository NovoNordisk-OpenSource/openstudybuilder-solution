<template>
  <v-expansion-panels
    v-model="panel"
    multiple
    @update:model-value="expanded = !expanded"
  >
    <v-expansion-panel rounded="0">
      <v-expansion-panel-title :class="panelStyle">
        <p class="text-body-medium" :class="{ 'truncate-line': !expanded }">
          {{ props.item.description }}
        </p>
      </v-expansion-panel-title>
    </v-expansion-panel>
  </v-expansion-panels>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  item: {
    type: Object,
    default: undefined,
  },
})

const expanded = ref(false)
const panel = ref([])

const panelStyle = computed(() => {
  if (expanded.value) {
    return 'pa-4'
  }
  return 'pa-0 pl-2 pt-1'
})
</script>

<style scoped>
.truncate-line {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
