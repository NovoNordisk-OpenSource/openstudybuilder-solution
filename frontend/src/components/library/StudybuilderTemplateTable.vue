<template>
  <div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab v-for="item of tabs" :key="item.tab" :value="item.tab">
        {{ item.name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab">
      <v-window-item :key="`parent-${tabKeys.parent}`" value="parent">
        <GenericSponsorTemplateTable
          ref="sponsorTable"
          key="sponsorTable"
          :headers="headers"
          v-bind="$attrs"
          :url-prefix="urlPrefix"
          :object-type="objectType"
          :history-excluded-headers="historyExcludedHeaders"
          @refresh="$emit('refresh')"
        >
          <template v-for="(_, slot) of $slots" #[slot]="scope">
            <slot :name="slot" v-bind="scope" />
          </template>
        </GenericSponsorTemplateTable>
      </v-window-item>
      <v-window-item
        :key="`pre-instances-${tabKeys['pre-instances']}`"
        value="pre-instances"
      >
        <GenericSponsorTemplateTable
          ref="preInstanceTable"
          key="preInstanceTable"
          :headers="headers"
          v-bind="$attrs"
          pre-instance-mode
          :url-prefix="preInstanceUrlPrefix"
          :export-object-label="preInstanceExportLabel"
          :object-type="objectType"
          :history-excluded-headers="historyExcludedHeaders"
        >
          <template v-for="(_, slot) of $slots" #[slot]="scope">
            <slot :name="slot" v-bind="scope" />
          </template>
        </GenericSponsorTemplateTable>
      </v-window-item>
      <v-window-item :key="`user-${tabKeys.user}`" value="user">
        <GenericUserTemplateTable :url-prefix="urlPrefix" v-bind="$attrs" />
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useTabKeys } from '@/composables/tabKeys'
import GenericSponsorTemplateTable from './GenericSponsorTemplateTable.vue'
import GenericUserTemplateTable from './GenericUserTemplateTable.vue'
import { useAppStore } from '@/stores/app'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const { tabKeys, updateTabKey } = useTabKeys()
const props = defineProps({
  headers: {
    type: Array,
    default: () => {
      const { t } = useI18n()
      return [
        {
          title: '',
          key: 'actions',
          width: '1%',
        },
        { title: t('_global.sequence_number'), key: 'sequence_id' },
        {
          title: t('_global.template'),
          key: 'name',
          width: '30%',
          filteringName: 'name_plain',
        },
        { title: t('_global.modified'), key: 'start_date' },
        { title: t('_global.status'), key: 'status' },
        { title: t('_global.version'), key: 'version' },
      ]
    },
  },
  withPreInstances: {
    type: Boolean,
    default: true,
  },
  doubleBreadcrumb: {
    type: Boolean,
    default: false,
  },
  urlPrefix: {
    type: String,
    default: '',
  },
  objectType: {
    type: String,
    default: '',
  },
  historyExcludedHeaders: {
    type: Array,
    default: null,
    required: false,
  },
  extraRouteParams: {
    type: Object,
    default: () => {},
    required: false,
  },
})
const emit = defineEmits(['refresh'])
const appStore = useAppStore()

const tab = ref()
const tabs = ref([
  { tab: 'parent', name: t('GenericTemplateTable.sponsor_tab') },
  { tab: 'user', name: t('GenericTemplateTable.user_tab') },
])
const sponsorTable = ref(null)
const preInstanceTable = ref(null)

if (props.withPreInstances) {
  tabs.value.splice(1, 0, {
    tab: 'pre-instances',
    name: t('GenericTemplateTable.pre_instances_tab'),
  })
}

const preInstanceUrlPrefix = computed(() => {
  return props.urlPrefix.replace('-templates', '-pre-instances')
})
const preInstanceExportLabel = computed(() => {
  let result = props.objectType.replace('Templates', '')
  if (result === 'activity') {
    result = 'activity-instruction'
  }
  return result + 'PreInstances'
})

watch(tab, (newValue) => {
  const params = { ...route.params, ...props.extraRouteParams }
  params.tab = newValue
  router.push({
    name: route.name,
    params,
  })
  updateTabKey(newValue)
  if (!props.doubleBreadcrumb) {
    const tabName = newValue
      ? tabs.value.find((el) => el.tab === newValue).name
      : tabs.value[0].name
    appStore.addBreadcrumbsLevel(tabName, undefined, 3, true)
  } else {
    let tabName = ''
    if (tabs.value.find((el) => el.tab === newValue)) {
      tabName = tabs.value.find((el) => el.tab === newValue).name
    } else {
      tabName = tabs.value[0].name
    }
    appStore.addBreadcrumbsLevel(tabName, undefined, 4, true)
  }
  emit('refresh', newValue)
})

onMounted(() => {
  if (route.params.tab) {
    tab.value = route.params.tab
  } else {
    tab.value = tabs.value[0].tab
  }
  if (!props.doubleBreadcrumb) {
    const tabName = tab.value
      ? tabs.value.find((el) => el.tab === tab.value).name
      : tabs.value[0].name
    setTimeout(() => {
      appStore.addBreadcrumbsLevel(tabName, undefined, 3, true)
    }, 100)
  } else {
    setTimeout(() => {
      let tabName = ''
      if (tabs.value.find((el) => el.tab === tab.value)) {
        tabName = tabs.value.find((el) => el.tab === tab.value).name
      } else {
        tabName = tabs.value[0].name
      }
      appStore.addBreadcrumbsLevel(tabName, undefined, 4, true)
    }, 100)
  }
})

function restoreTab() {
  tab.value = tabs.value[0].tab
}

defineExpose({
  restoreTab,
  tab,
  sponsorTable,
  preInstanceTable,
})
</script>
