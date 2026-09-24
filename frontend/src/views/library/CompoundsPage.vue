<template>
  <div class="px-4">
    <div class="d-flex page-title">
      {{ $t('InterventionsView.title') }}
      <HelpButton
        :title="$t('_global.definition')"
        :help-text="$t('_help.InterventionsView.general')"
      />
    </div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab v-for="item of tabs" :key="item.tab" :value="item.tab">
        {{ item.name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab">
      <v-window-item value="compounds">
        <CompoundTable :tab-clicked-at="compoundsTabClickedAt" />
      </v-window-item>
      <v-window-item value="compound-aliases">
        <CompoundAliasTable :tab-clicked-at="compoundAliasesTabClickedAt" />
      </v-window-item>
      <v-window-item value="active-substances">
        <ActiveSubstancesTable :tab-clicked-at="activeSubstancesTabClickedAt" />
      </v-window-item>
      <v-window-item value="pharmaceutical-products">
        <PharmaceuticalProductTable
          :tab-clicked-at="pharmaProductsTabClickedAt"
        />
      </v-window-item>
      <v-window-item value="medicinal-products">
        <ProductsTree :tab-clicked-at="medicinalProductsTabClickedAt" />
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter, useRoute } from 'vue-router'
import ActiveSubstancesTable from '@/components/library/ActiveSubstancesTable.vue'
import CompoundAliasTable from '@/components/library/CompoundAliasTable.vue'
import CompoundTable from '@/components/library/CompoundTable.vue'
import PharmaceuticalProductTable from '@/components/library/PharmaceuticalProductTable.vue'
import ProductsTree from '@/components/library/ProductsTree.vue'
import HelpButton from '@/components/tools/HelpButton.vue'
import { useAppStore } from '@/stores/app'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const appStore = useAppStore()

const tab = ref(null)
const compoundAliasesTabClickedAt = ref(0)
const medicinalProductsTabClickedAt = ref(0)
const compoundsTabClickedAt = ref(0)
const activeSubstancesTabClickedAt = ref(0)
const pharmaProductsTabClickedAt = ref(0)

const tabs = [
  { tab: 'compounds', name: t('InterventionsView.tab1_title') },
  { tab: 'compound-aliases', name: t('InterventionsView.tab2_title') },
  { tab: 'active-substances', name: t('InterventionsView.tab3_title') },
  { tab: 'pharmaceutical-products', name: t('InterventionsView.tab4_title') },
  { tab: 'medicinal-products', name: t('InterventionsView.tab5_title') },
]
watch(tab, (newValue) => {
  switch (newValue) {
    case 'compounds':
      compoundsTabClickedAt.value = Date.now()
      break
    case 'compound-aliases':
      compoundAliasesTabClickedAt.value = Date.now()
      break
    case 'active-substances':
      activeSubstancesTabClickedAt.value = Date.now()
      break
    case 'pharmaceutical-products':
      pharmaProductsTabClickedAt.value = Date.now()
      break
    case 'medicinal-products':
      medicinalProductsTabClickedAt.value = Date.now()
      break
  }
  const newTab = newValue || tabs[0].tab
  router.push({
    name: 'Interventions',
    params: { tab: newTab },
  })
  const tabName = tabs.find((el) => el.tab === newTab).name
  appStore.addBreadcrumbsLevel(
    tabName,
    { name: 'Interventions', params: { tab: newTab } },
    3,
    true
  )
})

onMounted(() => {
  tab.value = route.params.tab ? route.params.tab : tabs[0].tab
})
</script>
