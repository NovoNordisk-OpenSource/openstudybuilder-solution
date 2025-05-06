<template>
  <v-menu v-if="item && checkActionsPermissions" position="bottom">
    <template #activator="{ props }">
      <v-btn
        v-if="!badge"
        :disabled="disabled"
        data-cy="table-item-action-button"
        icon="mdi-dots-vertical"
        variant="plain"
        :size="size"
        v-bind="props"
        style="height: auto; z-index: 100"
        class="pb-3 mr-n6 ml-n2"
      />
      <v-badge v-else :color="badge.color" :icon="badge.icon" bordered inline>
        <v-btn
          :disabled="disabled"
          icon="mdi-dots-vertical"
          v-bind="props"
          :size="size"
          class="pb-3 ml-n3"
          variant="text"
        />
      </v-badge>
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
            <v-icon v-else :icon="action.icon" color="nnBaseBlue" />
          </template>
          <v-list-item-title :data-cy="action.label">
            {{ action.label }}
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
