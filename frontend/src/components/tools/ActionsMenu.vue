<template>
  <v-menu v-if="item && checkActionsPermissions" position="bottom">
    <template #activator="{ props }">
      <v-btn
        :disabled="disabled"
        data-cy="table-item-action-button"
        icon="mdi-dots-vertical"
        variant="plain"
        :size="size"
        v-bind="props"
        style="height: auto; z-index: 100; min-width: 0; width: 24px"
        class="pb-3 ml-n2"
      />
      <span v-if="badge" class="ml-n1 mr-2">
        <v-icon :color="badge.color">{{ badge.icon }}</v-icon>
        <v-tooltip v-if="badge.tooltip" activator="parent" location="top">{{
          badge.tooltip
        }}</v-tooltip>
      </span>
    </template>
    <v-list>
      <template v-for="(action, index) in actions">
        <v-list-item
          v-if="action.condition === undefined || action.condition(item)"
          :key="index"
          :disabled="
            action.accessRole && !accessGuard.checkPermission(action.accessRole)
          "
          @click="action.click(item, source)"
        >
          <template #prepend>
            <v-icon
              v-if="action.iconColorFunc"
              :color="action.iconColorFunc(item)"
              :icon="action.icon"
            />
            <v-icon
              v-else-if="typeof action.iconColor === 'function'"
              :color="action.iconColor(item)"
              :icon="action.icon"
            />
            <v-icon v-else :icon="action.icon" color="nnBaseBlue" />
          </template>
          <v-list-item-title
            :data-cy="
              typeof action.label === 'function'
                ? action.label(item)
                : action.label
            "
          >
            {{
              typeof action.label === 'function'
                ? action.label(item)
                : action.label
            }}
          </v-list-item-title>
        </v-list-item>
      </template>
    </v-list>
  </v-menu>
</template>

<script setup>
import { computed } from 'vue'
import { useAccessGuard } from '@/composables/accessGuard'

const accessGuard = useAccessGuard()
const props = defineProps({
  disabled: {
    type: Boolean,
    default: false,
  },
  actions: {
    type: Array,
    default: () => [],
  },
  item: {
    type: Object,
    default: undefined,
  },
  source: {
    type: String,
    default: '',
  },
  badge: {
    type: Object,
    required: false,
    default: undefined,
  },
  accessRole: {
    type: String,
    default: '',
  },
  size: {
    type: String,
    default: 'default',
  },
})

const checkActionsPermissions = computed(() => {
  return props.accessRole ? accessGuard.checkPermission(props.accessRole) : true
})
</script>
