<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('StudyPopulationView.title') }} ({{ studiesGeneralStore.studyId }})
      <HelpButton :help-text="$t('_help.StudyPopulationTable.general')" />
    </div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab value="general-population-attributes">
        {{ $t('StudyPopulationView.tab_general') }}
      </v-tab>
      <v-tab value="study-design-population">
        {{ $t('StudyPopulationView.tab_design_population') }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab">
      <v-window-item
        :key="`general-${tabKeys['general-population-attributes']}`"
        value="general-population-attributes"
      >
        <StudyPopulationSummary />
      </v-window-item>
      <v-window-item
        :key="`design-${tabKeys['study-design-population']}`"
        value="study-design-population"
      >
        <StudyDesignPopulationTable />
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import StudyPopulationSummary from '@/components/studies/StudyPopulationSummary.vue'
import StudyDesignPopulationTable from '@/components/studies/StudyDesignPopulationTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useAppStore } from '@/stores/app'
import { useTabKeys } from '@/composables/tabKeys'

const studiesGeneralStore = useStudiesGeneralStore()
const appStore = useAppStore()
const router = useRouter()
const route = useRoute()
const { tabKeys, updateTabKey } = useTabKeys()

const tab = ref(route.params.tab || 'general-population-attributes')

watch(tab, (newValue) => {
  router.push({
    name: 'StudyPopulation',
    params: { study_id: studiesGeneralStore.selectedStudy.uid, tab: newValue },
  })
  appStore.addBreadcrumbsLevel(
    newValue,
    {
      name: 'StudyPopulation',
      params: {
        study_id: studiesGeneralStore.selectedStudy.uid,
        tab: newValue,
      },
    },
    3,
    true
  )
  updateTabKey(newValue)
})
</script>

<style scoped>
.v-window {
  min-height: 50vh;
}
</style>
