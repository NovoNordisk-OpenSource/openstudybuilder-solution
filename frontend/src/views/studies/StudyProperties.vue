<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('Sidebar.study.study_properties') }} ({{ studyId }})
      <HelpButtonWithPanels
        :help-text="$t('_help.StudyProperties.general')"
        :items="helpItems"
      />
    </div>
    <NavigationTabs :tabs="tabs">
      <template #default="{ tabKeys }">
        <v-window-item value="type">
          <StudyTypeSummary :key="`type-${tabKeys.type}`" />
        </v-window-item>
        <v-window-item value="attributes">
          <InterventionTypeSummary :key="`attributes-${tabKeys.attributes}`" />
        </v-window-item>
        <v-window-item value="other_study_attributes">
          <OtherStudyAttributesTable
            :key="`other_study_attributes-${tabKeys.other_study_attributes}`"
          />
        </v-window-item>
        <v-window-item value="age_rules">
          <StudyAgeRulesSummary :key="`age_rules-${tabKeys.age_rules}`" />
        </v-window-item>
      </template>
    </NavigationTabs>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import InterventionTypeSummary from '@/components/studies/InterventionTypeSummary.vue'
import NavigationTabs from '@/components/tools/NavigationTabs.vue'
import OtherStudyAttributesTable from '@/components/studies/OtherStudyAttributesTable.vue'
import StudyAgeRulesSummary from '@/components/studies/StudyAgeRulesSummary.vue'
import StudyTypeSummary from '@/components/studies/StudyTypeSummary.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const { t } = useI18n()
const studiesGeneralStore = useStudiesGeneralStore()

const helpItems = ['StudyProperties.study_type']
const tabs = [
  { tab: 'type', name: t('Sidebar.study.study_type') },
  { tab: 'attributes', name: t('Sidebar.study.study_attributes') },
  {
    tab: 'other_study_attributes',
    name: t('Sidebar.study.other_study_attributes'),
  },
  { tab: 'age_rules', name: t('Sidebar.study.age_rules') },
]

const studyId = computed(() => studiesGeneralStore.studyId)
</script>
