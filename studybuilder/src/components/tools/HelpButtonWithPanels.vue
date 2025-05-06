<template>
  <v-menu
    v-model="open"
    persistent
    :close-on-content-click="false"
    max-height="800px"
    max-width="500px"
    location="bottom"
    no-click-animation
    content-class="right"
  >
    <template #activator="{ props }">
      <div>
        <v-btn
          icon="mdi-help-circle-outline"
          v-bind="props"
          color="primary"
          variant="text"
        />
      </div>
    </template>
    <v-card max-width="500px">
      <v-card-title class="dialog-title d-flex align-center">
        {{ $t('_global.online_help') }}
        <v-spacer />
        <v-btn
          color="secondary"
          icon="mdi-close"
          variant="text"
          @click="open = false"
        />
      </v-card-title>
      <v-divider />
      <v-list>
        <v-list-item>
          <v-expansion-panels>
            <v-expansion-panel
              v-for="item in props.items"
              :key="item.key || item"
            >
              <v-expansion-panel-title>
                {{ getItemLabel(item) }}
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <div v-html="getItemHelp(item)" />
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-list-item>
      </v-list>
    </v-card>
  </v-menu>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  items: {
    type: Array,
    default: () => [],
  },
})

const { t } = useI18n()

const open = ref(false)

function getItemLabel(item) {
  if (typeof item === 'string') {
    return t(item)
  }
  return t(item.key)
}

function getItemHelp(item) {
  if (typeof item === 'string') {
    return t(`_help.${item}`)
  }
  return t(`_help.${item.key}`, item.context())
}
</script>
<style>
.right {
  right: 10px;
  left: auto !important;
}
</style>
