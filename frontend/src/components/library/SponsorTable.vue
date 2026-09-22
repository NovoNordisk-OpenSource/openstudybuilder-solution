<template>
  <div v-if="allCatalogues.length">
    <NavigationTabs :tabs="allCatalogues" tab-key="name">
      <template #default="{ tabKeys }">
        <v-window-item
          v-for="catalogue in allCatalogues"
          :key="`${catalogue.name}-${tabKeys[catalogue.name]}`"
          :value="catalogue.name"
        >
          <CodelistTable
            :catalogue="catalogue.name"
            column-data-resource="ct/codelists"
            library="Sponsor"
            @open-codelist-terms="openCodelistTerms"
          />
        </v-window-item>
      </template>
    </NavigationTabs>
  </div>
</template>

<script setup lang="js">
import { useCtCataloguesStore } from '@/stores/library-ctcatalogues'
import { ref, watchEffect } from 'vue'
import { useRouter } from 'vue-router'
import CodelistTable from './CodelistTable.vue'
import NavigationTabs from '@/components/tools/NavigationTabs.vue'

const router = useRouter()
const ctCataloguesStore = useCtCataloguesStore()
const allCatalogues = ref([])

watchEffect(() => {
  allCatalogues.value = [{ name: 'All' }].concat(ctCataloguesStore.catalogues)
})

const openCodelistTerms = ({ codelist, catalogueName }) => {
  router.push({
    name: 'CodelistTerms',
    params: {
      codelist_id: codelist.codelist_uid,
      catalogue_name: catalogueName,
    },
  })
}

ctCataloguesStore.fetchCatalogues()
</script>
