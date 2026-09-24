<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('Sidebar.study.study_interventions') }} ({{
        studiesGeneralStore.studyId
      }})
      <HelpButton :help-text="$t('_help.StudyInterventionsTable.general')" />
    </div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab v-for="item of tabs" :key="item.tab" :value="item.tab">
        {{ item.name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab" class="bg-white">
      <v-window-item value="overview">
        <InterventionOverview />
      </v-window-item>
      <v-window-item value="study_compounds">
        <CompoundTable />
      </v-window-item>
      <v-window-item value="study_compound_dosings">
        <CompoundDosingTable />
      </v-window-item>
      <v-window-item value="other_interventions">
        <UnderConstruction />
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import CompoundDosingTable from '@/components/studies/CompoundDosingTable.vue'
import CompoundTable from '@/components/studies/CompoundTable.vue'
import InterventionOverview from '@/components/studies/InterventionOverview.vue'
import UnderConstruction from '@/components/layout/UnderConstruction.vue'
import HelpButton from '@/components/tools/HelpButton.vue'
import { useAppStore } from '@/stores/app'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const studiesGeneralStore = useStudiesGeneralStore()

const tab = ref(null)

const tabs = [
  {
    tab: 'overview',
    name: t('Sidebar.study.study_intervention_overview'),
  },
  { tab: 'study_compounds', name: t('Sidebar.study.compounds') },
  {
    tab: 'study_compound_dosings',
    name: t('Sidebar.study.compound_dosings'),
  },
  {
    tab: 'other_interventions',
    name: t('Sidebar.study.other_interventions'),
  },
]

watch(tab, (newValue) => {
  const tabName = newValue
    ? tabs.find((el) => el.tab === newValue).name
    : tabs[0].name
  router.push({
    name: 'StudyInterventions',
    params: { tab: newValue },
  })
  appStore.addBreadcrumbsLevel(
    tabName,
    {
      name: 'StudyInterventions',
      params: {
        study_id: studiesGeneralStore.selectedStudy.uid,
        tab: tabName,
      },
    },
    3,
    true
  )
})

onMounted(() => {
  tab.value = route.params.tab || tabs[0].tab
  const tabName = tab.value
    ? tabs.find((el) => el.tab === tab.value).name
    : tabs[0].name
  setTimeout(() => {
    appStore.addBreadcrumbsLevel(
      tabName,
      {
        name: 'StudyInterventions',
        params: {
          study_id: studiesGeneralStore.selectedStudy.uid,
          tab: tabName,
        },
      },
      3,
      true
    )
  }, 100)
})
</script>
