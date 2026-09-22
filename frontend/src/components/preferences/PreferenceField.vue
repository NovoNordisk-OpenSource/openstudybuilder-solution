<template>
  <div>
    <!-- Integer field -->
    <v-text-field
      v-if="metadata.type === 'integer'"
      :model-value="value"
      :label="metadata.label"
      type="number"
      :rules="integerRules"
      hide-details="auto"
      @update:model-value="
        (val) => {
          const n = parseInt(val, 10)
          if (!isNaN(n)) $emit('update:value', n)
        }
      "
    />

    <!-- Boolean field -->
    <v-switch
      v-else-if="metadata.type === 'boolean'"
      :model-value="value"
      :label="metadata.label"
      hide-details
      @update:model-value="(val) => $emit('update:value', val)"
    />

    <!-- Theme field -->
    <v-select
      v-else-if="preferenceKey === 'theme'"
      :model-value="value"
      :label="metadata.label"
      :items="themeItems"
      item-title="title"
      item-value="value"
      hide-details="auto"
      @update:model-value="(val) => $emit('update:value', val)"
    />

    <!-- Enum field -->
    <v-select
      v-else-if="metadata.type === 'enum'"
      :model-value="value"
      :label="metadata.label"
      :items="enumItems"
      item-title="title"
      item-value="value"
      hide-details="auto"
      @update:model-value="(val) => $emit('update:value', val)"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { APP_THEMES, THEME_NAMES } from '@/plugins/vuetify'

const { t } = useI18n()

const props = defineProps({
  preferenceKey: {
    type: String,
    required: true,
  },
  value: {
    type: [String, Number, Boolean],
    required: true,
  },
  metadata: {
    type: Object,
    required: true,
  },
})

defineEmits(['update:value'])

const themeItems = computed(() => {
  return THEME_NAMES.map((name) => ({
    value: name,
    title: APP_THEMES[name].title,
  }))
})

const enumItems = computed(() => {
  return (props.metadata.allowed_values || []).map((value) => ({
    value,
    title: value,
  }))
})

const integerRules = computed(() => {
  const rules = []
  if (props.metadata.min !== undefined) {
    rules.push(
      (v) =>
        v >= props.metadata.min ||
        t('PreferenceField.min_error', { min: props.metadata.min })
    )
  }
  if (props.metadata.max !== undefined) {
    rules.push(
      (v) =>
        v <= props.metadata.max ||
        t('PreferenceField.max_error', { max: props.metadata.max })
    )
  }
  return rules
})
</script>
