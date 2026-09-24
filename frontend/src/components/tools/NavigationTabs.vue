<template>
  <v-tabs v-model="tab" bg-color="white">
    <slot name="header">
      <v-tab
        v-for="item of props.tabs"
        :key="item[props.tabKey]"
        :value="item[props.tabKey]"
        :loading="item.loading ? item.loading() : false"
      >
        {{ item[props.tabTitle] }}
      </v-tab>
    </slot>
  </v-tabs>
  <v-window :model-value="activePanel" class="bg-white">
    <slot name="default" :tab-keys="tabKeys"></slot>
  </v-window>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'

const props = defineProps({
  tabs: {
    type: Array,
    default: null,
  },
  breadcrumbsLevel: {
    type: Number,
    default: 3,
  },
  tabKey: {
    type: String,
    default: 'tab',
  },
  tabTitle: {
    type: String,
    default: 'name',
  },
})
const emit = defineEmits(['tabChanged'])

const appStore = useAppStore()
const route = useRoute()
const router = useRouter()

const tab = ref(null)
const activePanel = ref(null)
const tabKeys = ref({})

const updateTabKey = (value) => {
  if (tabKeys.value[value] === undefined) {
    tabKeys.value[value] = 0
  }
  tabKeys.value[value]++
}

// Resolve a tab key from whatever's in the URL — falls back to the first
// tab when the URL carries no tab param or an unknown one. Without this,
// a bookmarked URL like /library/activities/bogus would crash the watcher
// at find(...)[props.tabTitle].
const resolveTabKey = (raw) => {
  if (raw && props.tabs.some((el) => el[props.tabKey] === raw)) return raw
  return props.tabs[0][props.tabKey]
}

onMounted(() => {
  const initial = resolveTabKey(route.params.tab)
  tab.value = initial
  activePanel.value = initial
})

watch(tab, async (newValue) => {
  emit('tabChanged', newValue)
  // newValue should always match a tab key (resolveTabKey guards entry
  // points), but treat a miss as "drop back to the first tab" rather than
  // crashing.
  const match =
    props.tabs.find((el) => el[props.tabKey] === newValue) ?? props.tabs[0]
  const tabName = match[props.tabTitle]
  await router.push({
    name: route.name,
    params: { ...route.params, tab: newValue },
  })
  activePanel.value = newValue
  appStore.addBreadcrumbsLevel(
    tabName,
    {
      // tab in the route is the key (e.g. 'activity-subgroups'), not the
      // human label — clicking the crumb has to round-trip through the
      // same router push above.
      name: route.name,
      params: { ...route.params, tab: newValue },
    },
    props.breadcrumbsLevel,
    true
  )
  updateTabKey(newValue)
})

watch(
  () => route.params.tab,
  (newValue) => {
    const resolved = resolveTabKey(newValue)
    tab.value = resolved
    activePanel.value = resolved
  }
)

defineExpose({
  tab,
})
</script>
