<template>
  <PackageTimelines
    :catalogue-name="route.params.catalogue_name"
    :package-name="route.params.package_name"
    @catalogue-changed="updateCatalogue"
    @package-changed="updateTerms"
  >
    <template #default="{ selectedPackage }">
      <div class="page-title">
        {{ $t('CodelistTermsView.codelist') }} {{ route.params.codelist_id }} -
        {{ codelistAttributes.submission_value }} /
        {{ $t('CodelistTermsView.terms_listing') }}
      </div>
      <CodelistTermTable
        :catalogue-name="route.params.catalogue_name"
        :codelist-uid="route.params.codelist_id"
        :package="selectedPackage"
      />
    </template>
  </PackageTimelines>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import controlledTerminology from '@/api/controlledTerminology'
import CodelistTermTable from '@/components/library/CodelistTermTable.vue'
import PackageTimelines from '@/components/library/PackageTimelines.vue'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const codelistAttributes = ref({})

watch(
  () => route.params.package_name,
  (value) => {
    if (value) {
      const to = {
        name: 'CtPackages',
        params: {
          catalogue_name: route.params.catalogue_name,
          package_name: value,
        },
      }
      appStore.addBreadcrumbsLevel(value, to, 4, true)
    } else {
      appStore.truncateBreadcrumbsFromLevel(4)
    }
  }
)

onMounted(() => {
  appStore.addBreadcrumbsLevel(
    route.params.codelist_id,
    { name: 'CtPackages', params: { package_name: route.params.package_name } },
    5
  )
  appStore.addBreadcrumbsLevel(t('CodelistTermsView.terms'), {
    name: 'CtPackageTerms',
    params: route.params,
  })
  controlledTerminology
    .getCodelistAttributes(route.params.codelist_id)
    .then((resp) => {
      codelistAttributes.value = resp.data
    })
})

function updateCatalogue(catalogueName) {
  router.push({
    name: 'CtPackages',
    params: { catalogue_name: catalogueName },
  })
}

function updateTerms(catalogueName, pkg) {
  router.push({
    name: 'CtPackageTerms',
    params: {
      codelist_id: route.params.codelist_id,
      catalogue_name: catalogueName,
      package_name: pkg ? pkg.name : '',
    },
  })
}
</script>
