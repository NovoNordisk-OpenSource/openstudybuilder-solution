<template>
  <v-expansion-panels
    v-model="panel"
    multiple
    @update:model-value="expanded = !expanded"
  >
    <v-expansion-panel rounded="0">
      <v-expansion-panel-title :class="panelStyle">
        <template
          v-if="
            !expanded &&
            props.item.description &&
            props.item.description.length > 30
          "
        >
          <p class="subtitle-1">
            {{ props.item.description.substring(0, 30) + '...' }}
          </p>
        </template>
        <template v-else>
          <p class="subtitle-1">
            {{ props.item.description }}
          </p>
        </template>
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
