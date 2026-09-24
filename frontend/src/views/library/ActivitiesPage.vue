<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('Sidebar.library.activities') }}
      <HelpButtonWithPanels
        :help-text="$t('_help.ActivitiesTable.general')"
        :items="helpItems"
      />
    </div>
    <NavigationTabs :tabs="tabs">
      <template #default="{ tabKeys }">
        <v-window-item value="activities">
          <ActivitiesTable
            :key="`activities-${tabKeys['activities']}`"
            source="activities"
          />
        </v-window-item>
        <v-window-item value="activity-groups">
          <ActivitiesTable
            :key="`activities-${tabKeys['activity-groups']}`"
            source="activity-groups"
          />
        </v-window-item>
        <v-window-item value="activity-subgroups">
          <ActivitiesTable
            :key="`activities-${tabKeys['activity-subgroups']}`"
            source="activity-sub-groups"
          />
        </v-window-item>
        <v-window-item value="activities-by-grouping">
          <ActivitiesTable
            :key="`activities-${tabKeys['activities-by-grouping']}`"
            source="activities-by-grouping"
          />
        </v-window-item>
        <v-window-item value="activity-instances">
          <ActivitiesTable
            :key="`activities-${tabKeys['activity-instances']}`"
            source="activity-instances"
          />
        </v-window-item>
        <v-window-item value="requested-activities">
          <ActivitiesTable
            :key="`activities-${tabKeys['requested-activities']}`"
            source="activities"
            requested
          />
        </v-window-item>
        <v-window-item value="activity-instance-classes">
          <Suspense>
            <ActivityInstanceClassTable />
          </Suspense>
        </v-window-item>
        <v-window-item value="activity-item-classes">
          <Suspense>
            <ActivityItemClassTable />
          </Suspense>
        </v-window-item>
        <v-window-item v-if="nsvsLibrary" value="non-standard-variables">
          <Suspense>
            <NonStandardVariablesTable />
          </Suspense>
        </v-window-item>
      </template>
    </NavigationTabs>
  </div>
</template>

<script setup>
import ActivitiesTable from '@/components/library/ActivitiesTable.vue'
import ActivityInstanceClassTable from '@/components/library/ActivityInstanceClassTable.vue'
import ActivityItemClassTable from '@/components/library/ActivityItemClassTable.vue'
import NonStandardVariablesTable from '@/components/library/NonStandardVariablesTable.vue'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import NavigationTabs from '@/components/tools/NavigationTabs.vue'
import { useI18n } from 'vue-i18n'
import { useFeatureFlagsStore } from '@/stores/feature-flags'
import { computed } from 'vue'

const { t } = useI18n()
const featureFlagsStore = useFeatureFlagsStore()

const streamlinePlaceholders = computed(() =>
  featureFlagsStore.getFeatureFlag('streamline_placeholder_activities')
)
const nsvsLibrary = computed(() =>
  featureFlagsStore.getFeatureFlag('nsvs_library')
)

const tabs = computed(() => {
  const allTabs = [
    { tab: 'activities', name: t('ActivityTable.activities') },
    {
      tab: 'activity-groups',
      name: t('ActivityTable.activity_groups'),
    },
    {
      tab: 'activity-subgroups',
      name: t('ActivityTable.activity_subgroups'),
    },
    {
      tab: 'activities-by-grouping',
      name: t('ActivityTable.activities_overview'),
    },
    { tab: 'activity-instances', name: t('ActivityTable.instances') },
    ...(!streamlinePlaceholders.value
      ? [
          {
            tab: 'requested-activities',
            name: t('ActivityTable.requested'),
          },
        ]
      : []),
    {
      tab: 'activity-instance-classes',
      name: t('ActivityTable.activity_instance_classes'),
    },
    {
      tab: 'activity-item-classes',
      name: t('ActivityTable.activity_item_classes'),
    },
    ...(nsvsLibrary.value
      ? [
          {
            tab: 'non-standard-variables',
            name: t('ActivityTable.non_standard_variables'),
          },
        ]
      : []),
  ]
  return allTabs
})
const helpItems = [
  'ActivityTable.activities',
  'ActivityTable.activity_groups',
  'ActivityTable.activity_subgroups',
  'ActivityTable.activities_overview',
  'ActivityTable.instances',
  'ActivityTable.requested',
  'ActivityTable.activity_name',
  'ActivityTable.sentence_case_name',
  'ActivityTable.abbreviation',
  'ActivityTable.definition',
  'ActivityTable.nci_concept_id',
  'ActivityTable.topic_code',
  'ActivityTable.adam_code',
  'ActivityTable.activity_group',
  'ActivityTable.activity_subgroup',
  'ActivityTable.is_data_collected',
  'ActivityTable.activity',
  'ActivityTable.instance',
  'ActivityTable.is_required_for_activity',
  'ActivityTable.is_default_selected_for_activity',
  'ActivityTable.is_data_sharing',
  'ActivityTable.is_legacy_usage',
  'ActivityTable.rationale_for_request',
]
</script>
