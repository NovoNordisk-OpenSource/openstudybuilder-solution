<template>
  <PackageTimelines
    :catalogue-name="props.catalogueName"
    :package-name="props.packageName"
    @catalogue-changed="updateUrl"
    @package-changed="updateUrl"
  >
    <template #default="{ catalogue_name, selectedPackage }">
      <CodelistTable
        ref="table"
        :catalogue="catalogue_name"
        :package="selectedPackage"
        read-only
        column-data-resource="ct/codelists"
        @open-codelist-terms="openCodelistTerms"
      >
        <template #extraActions>
          <v-btn
            class="ml-2"
            size="small"
            variant="outlined"
            color="nnBaseBlue"
            :title="$t('CtPackageHistory.ct_packages_history')"
            icon="mdi-calendar-clock"
            @click="goToPackagesHistory(catalogue_name)"
          />
        </template>
      </CodelistTable>
    </template>
  </PackageTimelines>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import CodelistTable from './CodelistTable.vue'
import PackageTimelines from './PackageTimelines.vue'

const props = defineProps({
  catalogueName: {
    type: String,
    default: null,
  },
  packageName: {
    type: String,
    default: null,
  },
})
const router = useRouter()

const table = ref()

function openCodelistTerms({ codelist, catalogueName, packageName }) {
  router.push({
    name: 'CtPackageTerms',
    params: {
      codelist_id: codelist.codelist_uid,
      catalogue_name: catalogueName,
      package_name: packageName,
    },
  })
}

function updateUrl(catalogueName, pkg) {
  router.push({
    name: 'CtPackages',
    params: {
      catalogue_name: catalogueName,
      package_name: pkg ? pkg.name : null,
    },
  })
  table.value.refresh()
}

function goToPackagesHistory(catalogueName) {
  router.push({
    name: 'CtPackagesHistory',
    params: { catalogue_name: catalogueName },
  })
}
</script>
