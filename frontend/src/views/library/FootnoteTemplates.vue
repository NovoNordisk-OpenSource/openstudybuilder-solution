<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('FootnoteTemplatesView.title') }}
      <HelpButton :help-text="$t('_help.FootnotesTemplatesTable.general')" />
    </div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab
        v-for="type in footnoteTypes"
        :key="type.term_uid"
        :value="type.sponsor_preferred_name"
      >
        {{ type.sponsor_preferred_name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab">
      <v-window-item
        v-for="type in footnoteTypes"
        :key="type.term_uid"
        :value="type.sponsor_preferred_name"
      >
        <FootnoteTemplateTable :key="type.term_uid" :footnote-type="type" />
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import FootnoteTemplateTable from '@/components/library/FootnoteTemplateTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'
import terms from '@/api/controlledTerminology/terms'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
const route = useRoute()
const router = useRouter()

const footnoteTypes = ref([])
const tab = ref(null)

watch(tab, (newValue) => {
  const params = { ...route.params }
  params.type = newValue
  router.push({
    name: 'FootnoteTemplates',
    params,
  })
  appStore.addBreadcrumbsLevel(newValue, undefined, 3, true)
})

watch(
  () => route.params.type,
  (newValue) => {
    tab.value = newValue
  }
)

onMounted(() => {
  terms.getTermsByCodelist('footnoteTypes').then((resp) => {
    footnoteTypes.value = resp.data.items
    tab.value = footnoteTypes.value[0].sponsor_preferred_name
    setTimeout(() => {
      appStore.addBreadcrumbsLevel(tab.value, undefined, 3, true)
    }, 100)
  })
})
</script>
