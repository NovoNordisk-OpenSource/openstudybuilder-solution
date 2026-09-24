<template>
  <div class="px-4">
    <div data-cy="page-title" class="page-title d-flex align-center">
      {{ $t('CtPackagesView.title') }}
      <HelpButton :help-text="$t('_help.CtPackagesTable.general')" />
    </div>
    <CtPackagesTable
      :catalogue-name="route.params.catalogue_name"
      :package-name="route.params.package_name"
    />
  </div>
</template>

<script setup>
import { onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import CtPackagesTable from '@/components/library/CtPackagesTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'

const appStore = useAppStore()
const route = useRoute()

watch(
  () => route.params.catalogue_name,
  (value) => {
    updateCatalogueInBreadcrumbs(value, true)
  }
)
watch(
  () => route.params.package_name,
  (value) => {
    if (value) {
      updatePackageInBreadcrumbs(value, route.params.catalogue_name, true)
    } else {
      appStore.truncateBreadcrumbsFromLevel(4)
    }
  }
)

onMounted(() => {
  if (route.params.catalogue_name) {
    updateCatalogueInBreadcrumbs(route.params.catalogue_name)
  }
  if (route.params.package_name) {
    updatePackageInBreadcrumbs(
      route.params.package_name,
      route.params.catalogue_name
    )
  }
})

function updateCatalogueInBreadcrumbs(catalogueName, replace) {
  appStore.addBreadcrumbsLevel(
    catalogueName,
    { name: 'CtPackages', params: { catalogue_name: catalogueName } },
    3,
    replace
  )
}

function updatePackageInBreadcrumbs(packageName, catalogueName, replace) {
  appStore.addBreadcrumbsLevel(
    packageName,
    {
      name: 'CtPackages',
      params: { catalogue_name: catalogueName, package_name: packageName },
    },
    4,
    replace
  )
}
</script>
