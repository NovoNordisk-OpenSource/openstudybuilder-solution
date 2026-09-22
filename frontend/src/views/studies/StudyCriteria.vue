<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('Sidebar.study.study_criteria') }} ({{
        studiesGeneralStore.studyId
      }})
      <HelpButtonWithPanels :items="helpItems" />
    </div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab
        v-for="type in criteriaTypes"
        :key="type.term_uid"
        :value="type.sponsor_preferred_name"
      >
        {{ type.sponsor_preferred_name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab">
      <v-window-item
        v-for="type in criteriaTypes"
        :key="type.term_uid"
        :value="type.sponsor_preferred_name"
      >
        <EligibilityCriteriaTable
          :key="`${type.sponsor_preferred_name}-${tabKeys[type.sponsor_preferred_name]}`"
          :criteria-type="type"
        />
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import EligibilityCriteriaTable from '@/components/studies/EligibilityCriteriaTable.vue'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import terms from '@/api/controlledTerminology/terms'
import { useAppStore } from '@/stores/app'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useTabKeys } from '@/composables/tabKeys'

const router = useRouter()
const route = useRoute()
const appStore = useAppStore()
const studiesGeneralStore = useStudiesGeneralStore()
const { tabKeys, updateTabKey } = useTabKeys()

const selectedStudy = computed(() => studiesGeneralStore.selectedStudy)

const criteriaTypes = ref([])
const tab = ref(null)

const helpItems = [
  'StudyCriteriaTable.general',
  'StudyCriteriaTable.study_criteria',
]

watch(tab, (newValue) => {
  router.push({
    name: 'StudySelectionCriteria',
    params: { study_id: selectedStudy.value.uid, tab: newValue },
  })
  appStore.addBreadcrumbsLevel(
    newValue,
    {
      name: 'StudySelectionCriteria',
      params: { study_id: selectedStudy.value.uid, tab: newValue },
    },
    3,
    true
  )
  updateTabKey(newValue)
})

onMounted(() => {
  terms.getTermsByCodelist('criteriaTypes', { unSorted: true }).then((resp) => {
    criteriaTypes.value = resp.data.items
    tab.value =
      route.params.tab || criteriaTypes.value[0].sponsor_preferred_name
  })
})
</script>

<style scoped>
.v-window {
  min-height: 50vh;
}
</style>
