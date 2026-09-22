<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      CT {{ $route.params.library_name }}
      <HelpButton :help-text="$t('_help.CtLibraryTable.general')" />
    </div>
    <CtLibraryTable
      :key="$route.params.library_name"
      :library="$route.params.library_name"
    />
  </div>
</template>

<script setup>
import { onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import CtLibraryTable from '@/components/library/CtLibraryTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'

const appStore = useAppStore()
const route = useRoute()

// The router guard's beforeEach derives the level-2 breadcrumb by matching
// subitem.url.name against the current route name, but every CT library
// shares the same route name ('CtLibrary') with only params.library_name
// differing — so the guard always picks the title of whichever library
// happens to be first in the sidebar list. Override it here with the
// actual library from the route.
watch(
  () => route.params.library_name,
  (value) => {
    appStore.addBreadcrumbsLevel(
      value,
      { name: 'CtLibrary', params: { library_name: value } },
      2,
      true
    )
  }
)

onMounted(() => {
  if (route.params.library_name) {
    appStore.addBreadcrumbsLevel(
      route.params.library_name,
      { name: 'CtLibrary', params: route.params },
      2
    )
  }
})
</script>
