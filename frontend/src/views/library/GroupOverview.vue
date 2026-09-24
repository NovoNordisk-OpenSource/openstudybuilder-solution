<template>
  <div v-if="groupOverview" class="px-4">
    <div class="d-flex page-title">
      {{ groupOverview.group.name }}
      <HelpButtonWithPanels
        :help-text="$t('_help.GroupOverview.general')"
        :items="helpItems"
      />
    </div>
    <GroupOverviewComponent
      :item-overview="groupOverview"
      :item-uid="route.params.id"
      :yaml-version="groupYAML"
      :cosmos-version="groupCOSMoS"
      @refresh="fetchOverview"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import GroupOverviewComponent from '@/components/library/GroupOverview.vue'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import activities from '@/api/activities'
import { useAppStore } from '@/stores/app'

const { t } = useI18n()

const route = useRoute()
const appStore = useAppStore()
const groupOverview = ref(null)
const groupYAML = ref(null)
const groupCOSMoS = ref(null)

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
  'ActivityOverview.activity_subgroups',
]

const fetchOverview = async () => {
  try {
    let groupData, allVersions

    try {
      const detailsResp = await activities.getActivityGroupDetails(
        route.params.id,
        route.params.version
      )

      if (detailsResp.data) {
        if (detailsResp.data.group) {
          groupData = detailsResp.data.group
          allVersions = detailsResp.data.all_versions || []
        } else {
          groupData = detailsResp.data
          allVersions = detailsResp.data.all_versions || []
        }
      }
    } catch (detailsError) {
      console.error('Error fetching group details:', detailsError)
    }

    if (!groupData || !groupData.name) {
      appStore.addBreadcrumbsLevel(
        t('_global.loading'),
        { name: 'GroupOverview', params: route.params },
        4,
        true
      )
    } else {
      appStore.addBreadcrumbsLevel(
        groupData.name,
        { name: 'GroupOverview', params: route.params },
        4,
        true
      )
    }

    if (!groupData) {
      try {
        console.warn('Falling back to original overview endpoint')
        const resp = await activities.getObjectOverview(
          'activity-groups',
          route.params.id,
          route.params.version
        )

        groupOverview.value = resp.data

        if (groupOverview.value?.group?.name) {
          appStore.addBreadcrumbsLevel(
            groupOverview.value.group.name,
            { name: 'GroupOverview', params: route.params },
            4,
            true
          )
        }

        return
      } catch (fallbackError) {
        console.error(
          'Error with fallback to original endpoint:',
          fallbackError
        )
        throw fallbackError
      }
    }

    groupOverview.value = {
      group: groupData,
      all_versions: allVersions || [],
      subgroups: null, // Let the component fetch its own subgroups
    }

    try {
      const yamlResp = await activities.getObjectOverview(
        'activity-groups',
        route.params.id,
        undefined,
        'yaml'
      )
      groupYAML.value = yamlResp.data
    } catch (error) {
      console.error('Error fetching YAML version:', error)
    }

    // Fetch CoSMoS version
    try {
      const cosmosResp = await activities.getCOSMoSOverview(
        'activity-groups',
        route.params.id
      )
      groupCOSMoS.value = cosmosResp.data || ' '
    } catch (error) {
      console.error('Error fetching CoSMoS version:', error)
      groupCOSMoS.value = ' '
    }
  } catch (error) {
    console.error('Error fetching group overview:', error)
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
