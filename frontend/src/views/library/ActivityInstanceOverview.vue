<template>
  <div v-if="activityInstanceOverview" class="px-4">
    <div class="d-flex page-title">
      {{ activityInstanceOverview.activity_instance.name }}
      <HelpButtonWithPanels
        :help-text="$t('_help.ActivityInstanceOverview.general')"
        :items="helpItems"
      />
    </div>
    <ActivityInstanceOverview
      v-if="activityInstanceOverview"
      source="activity-instances"
      :item-uid="route.params.id"
      :item-overview="activityInstanceOverview"
      :yaml-version="activityInstanceYAML"
      :cosmos-version="activityInstanceCOSMoS"
      @refresh="fetchOverview"
      @close-page="closePage"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ActivityInstanceOverview from '@/components/library/ActivityInstanceOverview.vue'
import activities from '@/api/activities'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()

const activityInstanceOverview = ref(null)
const activityInstanceYAML = ref(null)
const activityInstanceCOSMoS = ref(null)

const helpItems = [
  'ActivityInstanceOverview.cosmos_yaml',
  'ActivityInstanceOverview.class',
  'ActivityInstanceOverview.adam_code',
  'ActivityInstanceOverview.topic_code',
  'ActivityInstanceOverview.activity_group',
  'ActivityInstanceOverview.activity_subgroup',
  'ActivityInstanceOverview.activity',
  'ActivityInstanceOverview.activity_groupings',
  'ActivityInstanceOverview.is_required_for_activity',
  'ActivityInstanceOverview.is_default_selected_for_activity',
  'ActivityInstanceOverview.is_data_sharing',
  'ActivityInstanceOverview.is_legacy_usage',
  'ActivityInstanceOverview.item_type',
  'ActivityInstanceOverview.items',
  'ActivityInstanceOverview.item_class',
]
const fetchOverview = async () => {
  try {
    // Fetch main overview data
    const resp = await activities.getObjectOverview(
      'activity-instances',
      route.params.id,
      route.params.version
    )

    activityInstanceOverview.value = resp.data

    appStore.addBreadcrumbsLevel(
      activityInstanceOverview.value.activity_instance.name,
      { name: 'ActivityInstanceOverview', params: route.params },
      4,
      true
    )

    // Fetch YAML version
    try {
      const yamlResp = await activities.getObjectOverview(
        'activity-instances',
        route.params.id,
        route.params.version,
        'yaml'
      )
      activityInstanceYAML.value = yamlResp.data
    } catch (error) {
      console.error('Error fetching YAML version:', error)
    }

    // Fetch CoSMoS version
    try {
      const cosmosResp = await activities.getCOSMoSOverview(
        'activity-instances',
        route.params.id
      )
      activityInstanceCOSMoS.value = cosmosResp.data || ' '
    } catch (error) {
      console.error('Error fetching CoSMoS version:', error)
      activityInstanceCOSMoS.value = ' '
    }
  } catch (error) {
    console.error('Error fetching activity instance overview:', error)
  }
}
const closePage = () => {
  router.push({
    name: 'Activities',
    params: { tab: 'activity-instances' },
  })
}

watch(
  () => route.params,
  () => {
    fetchOverview()
  },
  { immediate: true, deep: true }
)
</script>
