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
      </template>
    </NavigationTabs>
  </div>
</template>

<script setup>
import ActivitiesTable from '@/components/library/ActivitiesTable.vue'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import NavigationTabs from '@/components/tools/NavigationTabs.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const tabs = [
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
  {
    tab: 'requested-activities',
    name: t('ActivityTable.requested'),
  },
]
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
