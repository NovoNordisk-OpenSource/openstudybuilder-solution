<template>
  <div v-if="subgroupOverview" class="px-4">
    <div class="d-flex page-title">
      {{ subgroupOverview.activity_subgroup.name }}
      <HelpButtonWithPanels
        :help-text="$t('_help.SubgroupOverview.general')"
        :items="helpItems"
      />
    </div>
    <SubgroupOverviewComponent
      :item-overview="subgroupOverview"
      :item-uid="route.params.id"
      :yaml-version="subgroupYAML"
      :cosmos-version="subgroupCOSMoS"
      @refresh="fetchOverview"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import SubgroupOverviewComponent from '@/components/library/SubgroupOverview.vue'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import activities from '@/api/activities'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const appStore = useAppStore()
const subgroupOverview = ref(null)
const subgroupYAML = ref(null)
const subgroupCOSMoS = ref(null)

const helpItems = [
  'ActivityOverview.cosmos_yaml',
  'ActivityOverview.osb_yaml',
  'ActivityOverview.name',
  'ActivityOverview.sentence_case_name',
  'ActivityOverview.version',
  'ActivityOverview.status',
  'ActivityOverview.start_date',
  'ActivityOverview.end_date',
  'ActivityOverview.library',
  'ActivityOverview.author',
  'ActivityOverview.definition',
  'ActivityOverview.activity_groups',
  'ActivityOverview.activities',
]

const fetchOverview = async () => {
  try {
    // Fetch main overview data
    const resp = await activities.getObjectOverview(
      'activity-sub-groups',
      route.params.id,
      route.params.version
    )

    subgroupOverview.value = {
      activity_subgroup: resp.data.activity_subgroup,
      activities: resp.data.activities,
      all_versions: resp.data.all_versions,
    }

    appStore.addBreadcrumbsLevel(
      subgroupOverview.value.activity_subgroup.name,
      { name: 'SubgroupOverview', params: route.params },
      4,
      true
    )

    // Fetch YAML version
    try {
      const yamlResp = await activities.getObjectOverview(
        'activity-sub-groups',
        route.params.id,
        undefined,
        'yaml'
      )
      subgroupYAML.value = yamlResp.data
    } catch (error) {
      console.error('Error fetching YAML version:', error)
    }

    // Fetch CoSMoS version
    try {
      const cosmosResp = await activities.getCOSMoSOverview(
        'activity-sub-groups',
        route.params.id
      )
      subgroupCOSMoS.value = cosmosResp.data || ' '
    } catch (error) {
      console.error('Error fetching CoSMoS version:', error)
      subgroupCOSMoS.value = ' '
    }
  } catch (error) {
    console.error('Error fetching subgroup overview:', error)
  }
}

watch(
  () => route.params,
  () => {
    fetchOverview()
  },
  { immediate: true, deep: true }
)
</script>
