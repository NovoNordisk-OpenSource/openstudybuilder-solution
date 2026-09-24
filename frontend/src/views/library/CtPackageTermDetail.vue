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
        {{ $t('CodelistTermDetail.term_detail') }} ({{
          $t('CodelistTermDetail.concept_id')
        }}: {{ route.params.term_id }})
      </div>
      <CodelistTermDetail
        :codelist-uid="route.params.codelist_id"
        :term-uid="route.params.term_id"
        :package-name="selectedPackage"
      />
    </template>
  </PackageTimelines>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import controlledTerminology from '@/api/controlledTerminology'
import CodelistTermDetail from '@/components/library/CodelistTermDetail.vue'
import PackageTimelines from '@/components/library/PackageTimelines.vue'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
const route = useRoute()
const router = useRouter()

const codelistAttributes = ref({})

onMounted(() => {
  appStore.addBreadcrumbsLevel(route.params.term_id, undefined, 7)
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
