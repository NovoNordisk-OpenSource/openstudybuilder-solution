<template>
  <div class="px-4">
    <div class="page-title">
      {{ $t('CtPackagesHistoryView.title') }}
    </div>
    <v-tabs v-model="tab" bg-color="dfltBackground">
      <v-tab
        v-for="catalogue in catalogues"
        :key="catalogue.name"
        :value="catalogue.name"
        :data-cy="catalogue.name"
      >
        {{ catalogue.name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab">
      <v-window-item
        v-for="catalogue in catalogues"
        :id="catalogue.name"
        :key="catalogue.name"
        :value="catalogue.name"
      >
        <CtPackageHistory :catalogue="catalogue" />
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import controlledTerminology from '@/api/controlledTerminology'
import CtPackageHistory from '@/components/library/CtPackageHistory.vue'

const appStore = useAppStore()
const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const catalogues = ref([])
const tab = ref(route.params.catalogue_name)

watch(tab, (newValue) => {
  router.push({
    name: 'CtPackagesHistory',
    params: { catalogue_name: newValue },
  })
})

onMounted(() => {
  appStore.addBreadcrumbsLevel(
    route.params.catalogue_name,
    { name: 'CtPackages', params: route.params },
    3
  )
  appStore.addBreadcrumbsLevel(t('_global.history'), {
    name: 'CtPackagesHistory',
    params: route.params,
  })

  controlledTerminology.getCatalogues().then((resp) => {
    catalogues.value = resp.data
  })
})
</script>
