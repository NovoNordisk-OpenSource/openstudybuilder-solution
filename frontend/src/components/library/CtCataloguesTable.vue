<template>
  <div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab
        v-for="catalogue in allCatalogues"
        :key="catalogue.name"
        :data-cy="catalogue.name"
        :value="catalogue.name"
      >
        {{ catalogue.name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab">
      <v-window-item
        v-for="catalogue in allCatalogues"
        :key="`${catalogue.name}-${tabKeys[catalogue.name]}`"
        :value="catalogue.name"
      >
        <CodelistTable
          :catalogue="catalogue.name"
          column-data-resource="ct/codelists"
          advanced-search
          @open-codelist-terms="openCodelistTerms"
        />
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup lang="js">
import { useCtCataloguesStore } from '@/stores/library-ctcatalogues'
import { ref, onMounted, watch, watchEffect } from 'vue'
import CodelistTable from './CodelistTable.vue'
import { useRouter } from 'vue-router'
import { useTabKeys } from '@/composables/tabKeys'

const props = defineProps({
  // eslint-disable-next-line vue/prop-name-casing
  catalogue_name: {
    type: String,
    default: null,
  },
})
const emit = defineEmits(['catalogueChanged'])
const router = useRouter()
const ctCataloguesStore = useCtCataloguesStore()
const { tabKeys, updateTabKey } = useTabKeys()

const allCatalogues = ref([])
const tab = ref(null)
const originalCatalogue = ref(null)

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

watch(tab, (newValue) => {
  if (newValue !== originalCatalogue.value) {
    ctCataloguesStore.currentCataloguePage = 1
  }
  updateTabKey(newValue)
  emit('catalogueChanged', newValue)
})

onMounted(() => {
  originalCatalogue.value = props.catalogue_name
  ctCataloguesStore.fetchCatalogues()
})
</script>
