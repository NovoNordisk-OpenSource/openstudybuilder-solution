<template>
  <div class="px-4">
    <div data-cy="page-title" class="page-title d-flex align-center">
      {{ $t('CtCataloguesView.title') }}
      <HelpButton :help-text="$t('_help.CtCataloguesTable.general')" />
    </div>
    <CtCataloguesTable
      :catalogue_name="$route.params.catalogue_name"
      @catalogue-changed="updateCatalogue"
    />
  </div>
</template>

<script setup>
import { onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import CtCataloguesTable from '@/components/library/CtCataloguesTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'

const appStore = useAppStore()
const route = useRoute()
const router = useRouter()

watch(
  () => route.params.catalogue_name,
  (value) => {
    appStore.addBreadcrumbsLevel(
      value,
      { name: 'CtCatalogues', params: { catalogue_name: value } },
      3,
      true
    )
  }
)

onMounted(() => {
  if (route.params.catalogue_name) {
    appStore.addBreadcrumbsLevel(
      route.params.catalogue_name,
      { name: 'CtCatalogues', params: route.params },
      3
    )
  }
})

function updateCatalogue(catalogueName) {
  router.push({
    name: 'CtCatalogues',
    params: { catalogue_name: catalogueName },
  })
}
</script>
