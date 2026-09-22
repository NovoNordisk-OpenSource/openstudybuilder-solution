<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('Sidebar.study.study_structure') }} ({{ studyId }})
      <HelpButtonWithPanels
        :help-text="$t('_help.StudyStructure.general')"
        :items="helpItems"
      />
    </div>
    <NavigationTabs :tabs="tabs" @tab-changed="onTabChanged">
      <template #default="{ tabKeys }">
        <v-window-item value="overview">
          <StudyStructureOverview :key="`overview-${tabKeys.overview}`" />
        </v-window-item>
        <v-window-item value="arms">
          <StudyArmsTable :key="`arms-${tabKeys.arms}`" />
        </v-window-item>
        <v-window-item value="branches">
          <StudyBranchesTable :key="`branches-${tabKeys.branches}`" />
        </v-window-item>
        <v-window-item value="cohorts">
          <StudyCohortsTable :key="`cohorts-${tabKeys.cohorts}`" />
        </v-window-item>
        <v-window-item value="epochs">
          <StudyEpochTable :key="`epochs-${tabKeys.epochs}`" />
        </v-window-item>
        <v-window-item value="elements">
          <StudyElementsTable :key="`elements-${tabKeys.elements}`" />
        </v-window-item>
        <v-window-item value="visits">
          <StudyVisitTable :key="`visits-${tabKeys.visits}`" />
        </v-window-item>
        <v-window-item value="design_matrix">
          <DesignMatrixTable :key="`design_matrix-${tabKeys.design_matrix}`" />
        </v-window-item>
        <v-window-item value="disease_milestones">
          <DiseaseMilestoneTable
            :key="`disease_milestones-${tabKeys.disease_milestones}`"
          />
        </v-window-item>
      </template>
    </NavigationTabs>
    <!-- <comment-thread-list :topicPath="topicPath" :isTransparent="true"></comment-thread-list> -->
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import DesignMatrixTable from '@/components/studies/DesignMatrixTable.vue'
import DiseaseMilestoneTable from '@/components/studies/DiseaseMilestoneTable.vue'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import NavigationTabs from '@/components/tools/NavigationTabs.vue'
import StudyEpochTable from '@/components/studies/StudyEpochTable.vue'
import StudyArmsTable from '@/components/studies/StudyArmsTable.vue'
import StudyBranchesTable from '@/components/studies/StudyBranchesTable.vue'
import StudyVisitTable from '@/components/studies/StudyVisitTable.vue'
import StudyElementsTable from '@/components/studies/StudyElementsTable.vue'
import StudyCohortsTable from '@/components/studies/StudyCohortsTable.vue'
import StudyStructureOverview from '@/components/studies/StudyStructureOverview.vue'
// import CommentThreadList from '@/components/tools/CommentThreadList.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { computed, ref } from 'vue'

const { t } = useI18n()
const studiesGeneralStore = useStudiesGeneralStore()
const selectedStudy = computed(() => studiesGeneralStore.selectedStudy)
const studyId = computed(() => studiesGeneralStore.studyId)

const helpItems = [
  'StudyStructure.study_arms',
  'StudyStructure.study_branches',
  'StudyStructure.study_cohorts',
  'StudyStructure.study_epochs',
  'StudyStructure.study_elements',
  'StudyStructure.study_visits',
  'StudyStructure.design_matrix',
  'StudyStructure.edit_visit_tableview',
]

const topicPath = ref('')

const tabs = [
  { tab: 'overview', name: t('_global.overview') },
  { tab: 'arms', name: t('Sidebar.study.study_arms') },
  { tab: 'branches', name: t('Sidebar.study.study_branches') },
  { tab: 'cohorts', name: t('Sidebar.study.study_cohorts') },
  { tab: 'epochs', name: t('Sidebar.study.study_epochs') },
  { tab: 'elements', name: t('Sidebar.study.study_elements') },
  { tab: 'visits', name: t('Sidebar.study.study_visits') },
  { tab: 'design_matrix', name: t('Sidebar.study.design_matrix') },
  {
    tab: 'disease_milestones',
    name: t('Sidebar.study.disease_milestones'),
  },
]

const onTabChanged = (value) => {
  if (value !== undefined) {
    topicPath.value =
      '/studies/' + selectedStudy.value.uid + '/study_structure/' + value
  }
}
</script>
