<template>
  <v-tabs v-model="tab" bg-color="white">
    <slot name="header">
      <v-tab
        v-for="item of props.tabs"
        :key="item[props.tabKey]"
        :value="item[props.tabKey]"
      >
        {{ item[props.tabTitle] }}
      </v-tab>
    </slot>
  </v-tabs>
  <v-window v-model="tab" class="bg-white">
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
const tabKeys = ref({})

const updateTabKey = (value) => {
  if (tabKeys.value[value] === undefined) {
    tabKeys.value[value] = 0
  }
  tabKeys.value[value]++
}

onMounted(() => {
  tab.value = route.params.tab || props.tabs[0].tab
})

watch(tab, (newValue) => {
  emit('tabChanged', newValue)
  const tabName = newValue
    ? props.tabs.find((el) => el.tab === newValue).name
    : props.tabs[0].name
  router.push({
    name: route.name,
    params: { ...route.params, tab: newValue },
  })
  appStore.addBreadcrumbsLevel(
    tabName,
    {
      name: route.name,
      params: { ...route.params, tab: tabName },
    },
    props.breadcrumbsLevel,
    true
  )
  updateTabKey(newValue)
})

watch(
  () => route.params.tab,
  (newValue) => {
    tab.value = newValue || props.tabs[0].tab
  }
)

defineExpose({
  tab,
})
</script>
