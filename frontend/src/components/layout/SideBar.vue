<!-- eslint-disable vue/v-bind-style -->
<template>
  <v-navigation-drawer
    id="sideBar"
    :key="drawerRefreshKey"
    v-model="appStore.drawer"
    :rail="mini"
    :expand-on-hover="mini"
    color="primary"
    width="290"
    @transitionend="transitionEnd"
  >
    <template #prepend="">
      <v-btn
        class="mt-1 ml-2"
        :icon="menuExpandedIcon"
        data-cy="toggle-sidebar"
        color="primary"
        size="small"
        @click="toggleMenu"
      />
    </template>
    <v-list
      v-if="appStore.menuItems"
      v-model:opened="open"
      density="compact"
      color="primary"
    >
      <template v-for="(item, pos) in selectedItems" :key="pos">
        <template v-if="!item.children">
          <v-list-item
            v-if="checkFeatureFlag(item)"
            v-bind:key="item.title"
            :data-cy="item.title"
            color="white"
            link
            :disabled="item.disabled && item.disabled()"
            :value="item.url.name"
            :to="item.url"
            @click="(event) => onMenuItemClick(event, item)"
          >
            <template v-if="item.icon" #prepend>
              <v-icon :icon="item.icon" />
            </template>
            <v-list-item-title>{{ item.title }}</v-list-item-title>
          </v-list-item>
        </template>
        <v-list-group
          v-else
          v-bind:key="item"
          color="white"
          :data-cy="item.title"
          :prepend-icon="item.icon"
          :value="item.id"
        >
          <template #activator="{ props }">
            <v-list-item v-bind="props" :title="item.title" />
          </template>

          <template v-for="subitem in item.children" :key="subitem.title">
            <v-list-item
              v-if="checkFeatureFlag(subitem)"
              class="submenu-item"
              color="white"
              :data-cy="subitem.title"
              :disabled="subitem.disabled && subitem.disabled()"
              link
              :value="subitem.url.name"
              :to="subitem.url"
              @click="(event) => onMenuItemClick(event, item, subitem)"
            >
              <template v-if="subitem.icon" #preprend>
                <v-icon :icon="subitem.icon" />
              </template>
              <v-list-item-title>{{ subitem.title }}</v-list-item-title>
            </v-list-item>
          </template>
        </v-list-group>
      </template>
    </v-list>
    <RedirectHandler :target="target" />
  </v-navigation-drawer>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useAppStore } from '@/stores/app'
import { useFeatureFlagsStore } from '@/stores/feature-flags'
import RedirectHandler from '@/components/tools/RedirectHandler.vue'

const appStore = useAppStore()
const featureFlagsStore = useFeatureFlagsStore()

onMounted(() => {
  appStore.fetchCtLibraries()
})

const drawerRefreshKey = ref(1)
const refreshNeeded = ref(false)
const mini = ref(false)
const target = ref({})
const open = ref([])

const menuExpandedIcon = computed(() => {
  return mini.value ? 'mdi-chevron-double-right' : 'mdi-chevron-double-left'
})
const selectedItems = computed(() => {
  if (
    appStore.section &&
    Object.prototype.hasOwnProperty.call(appStore.menuItems, appStore.section)
  ) {
    return appStore.menuItems[appStore.section].items
  }
  return []
})

watch(
  () => appStore.sidebarAutoMinimize,
  (val) => {
    mini.value = val
    refreshNeeded.value = true
  }
)

function onMenuItemClick(event, item, subitem) {
  // Here we only update target, the actual redirection will be
  // done by the RedirectHandler component
  event.preventDefault()
  target.value = { subitem, item }
}
function toggleMenu() {
  mini.value = !mini.value
  refreshNeeded.value = true
  localStorage.setItem('narrowMenu', JSON.stringify(mini.value))
}
function transitionEnd() {
  if (refreshNeeded.value) {
    drawerRefreshKey.value += 1
    refreshNeeded.value = false
  }
}
function checkFeatureFlag(item) {
  if (!item.featureFlag) return true
  return featureFlagsStore.getFeatureFlag(item.featureFlag) !== false
}
</script>

<style scoped lang="scss">
.top-logo {
  height: 64px;
  cursor: pointer;
}
.submenu-item {
  background-color: rgb(var(--v-theme-nnLightBlue1));
}
.v-list-item {
  &--active {
    background-color: rgb(var(--v-theme-nnLightBlue2)) !important;
    &::before {
      opacity: 0 !important;
    }
    .v-list-item-title {
      font-weight: 700 !important;
    }
  }
}
</style>
