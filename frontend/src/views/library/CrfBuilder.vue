<template>
  <div class="px-4">
    <div class="d-flex page-title">
      {{ $t('CRFBuilder.title') }}
      <HelpButton
        :title="$t('_global.definition')"
        :help-text="$t('HelpMessages.crfs')"
      />
    </div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab v-for="item of tabs" :key="item.tab" :value="item.tab">
        <v-icon
          v-if="item.icon"
          :color="item.iconColor"
          class="mr-1"
          :icon="item.icon"
        />{{ item.name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab" class="bg-white">
      <v-window-item value="collections">
        <CrfCollectionTable
          :key="`collections-${tabKeys['collections']}`"
          :element-prop="{ uid: uid, type: type, tab: tab }"
        />
      </v-window-item>
      <v-window-item value="forms">
        <CrfFormTable
          :key="`forms-${tabKeys['forms']}`"
          :element-prop="{ uid: uid, type: type, tab: tab }"
          @update-form="updateElement"
        />
      </v-window-item>
      <v-window-item value="item-groups">
        <CrfItemGroupTable
          :key="`item-groups-${tabKeys['item-groups']}`"
          :element-prop="{ uid: uid, type: type, tab: tab }"
          @update-item-group="updateElement"
        />
      </v-window-item>
      <v-window-item value="items">
        <CrfItemTable
          :key="`items-${tabKeys['items']}`"
          :element-prop="{ uid: uid, type: type, tab: tab }"
          @update-item="updateElement"
        />
      </v-window-item>
      <v-window-item value="crf-tree">
        <CrfTreeMain :key="`crf-tree-${tabKeys['crf-tree']}`" />
      </v-window-item>
      <v-window-item value="odm-viewer">
        <OdmBuildingViewer :element-prop="uid" :refresh="tab" />
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup>
import { useAppStore } from '@/stores/app'
import HelpButton from '@/components/tools/HelpButton.vue'
import CrfCollectionTable from '@/components/library/crfs/CrfCollectionTable.vue'
import CrfFormTable from '@/components/library/crfs/CrfFormTable.vue'
import CrfItemGroupTable from '@/components/library/crfs/CrfItemGroupTable.vue'
import CrfItemTable from '@/components/library/crfs/CrfItemTable.vue'
import CrfTreeMain from '@/components/library/crfs/crfTreeComponents/CrfTreeMain.vue'
import OdmBuildingViewer from '@/components/library/crfs/OdmBuildingViewer.vue'
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useTabKeys } from '@/composables/tabKeys'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const appStore = useAppStore()
const { tabKeys, updateTabKey } = useTabKeys()

const tab = ref(null)
const type = ref('')
const uid = ref('')
const updatedElement = ref({})
const tabs = [
  {
    tab: 'collections',
    name: t('CRFBuilder.tab1_title'),
    icon: 'mdi-alpha-c-circle',
    iconColor: 'crfCollection',
  },
  {
    tab: 'forms',
    name: t('CRFBuilder.tab2_title'),
    icon: 'mdi-alpha-f-circle',
    iconColor: 'crfForm',
  },
  {
    tab: 'item-groups',
    name: t('CRFBuilder.tab3_title'),
    icon: 'mdi-alpha-g-circle',
    iconColor: 'crfGroup',
  },
  {
    tab: 'items',
    name: t('CRFBuilder.tab4_title'),
    icon: 'mdi-alpha-i-circle',
    iconColor: 'crfItem',
  },
  { tab: 'crf-tree', name: t('CRFBuilder.tab5_title') },
  { tab: 'odm-viewer', name: t('CRFBuilder.tab6_title') },
]

watch(tab, (newValue) => {
  const activeTab = newValue || tabs[0].tab
  const params = { tab: activeTab }
  if (uid.value && type.value) {
    params.type = type.value
    params.value = uid.value
  }
  router.push({
    name: 'CrfBuilder',
    params: params,
  })
  const tabName = tabs.find((el) => el.tab === activeTab).name
  appStore.addBreadcrumbsLevel(
    tabName,
    { name: 'CrfBuilder', params: { tab: tabName } },
    3,
    true
  )
})

watch(
  () => route.params.tab,
  (newValue) => {
    tab.value = newValue || tabs[0].tab
    updateTabKey(newValue)
  }
)

onMounted(() => {
  if (route.params.tab) {
    tab.value = route.params.tab
  }
  type.value = route.params.type
  uid.value = route.params.uid
})

function updateElement(element) {
  updatedElement.value = element
}
</script>
