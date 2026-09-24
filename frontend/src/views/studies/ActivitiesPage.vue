<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('ActivitiesView.title') }} ({{ studiesGeneralStore.studyId }})
      <HelpButtonWithPanels :title="$t('_global.help')" :items="helpItems" />
      <v-spacer />
      <v-btn
        variant="outlined"
        icon
        size="small"
        color="nnBaseBlue"
        :disabled="lockSettings"
        :loading="soaContentLoadingStore.loading"
        @click="openSoaSettings"
      >
        <v-icon left>mdi-cog-outline</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ $t('ProtocolFlowchart.soa_settings') }}
        </v-tooltip>
      </v-btn>
    </div>
    <NavigationTabs :tabs="tabs" @tab-changed="onTabChanged">
      <template #default="{ tabKeys }">
        <v-window-item value="soa">
          <ScheduleOfActivities
            :key="`soa-${tabKeys.soa}`"
            :update="updateFlowchart"
          />
        </v-window-item>
        <v-window-item value="list">
          <StudyActivityTable
            ref="activitiesTable"
            :key="`activities-${tabKeys.activities}`"
            :update="updateActivitiesTable"
          />
        </v-window-item>
      </template>
    </NavigationTabs>
    <v-dialog v-model="showSoaSettings" max-width="800px">
      <SoaSettingsForm :key="settingsFormKey" @close="closeSoaSettings" />
    </v-dialog>
  </div>
</template>

<script setup>
import ScheduleOfActivities from '@/components/studies/ScheduleOfActivities/ScheduleOfActivities.vue'
import StudyActivityTable from '@/components/studies/StudyActivityTable.vue'
import SoaSettingsForm from '@/components/studies/SoaSettingsForm.vue'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import NavigationTabs from '@/components/tools/NavigationTabs.vue'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useSoaContentLoadingStore } from '@/stores/soa-content-loading'
import { inject, computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

const studiesGeneralStore = useStudiesGeneralStore()
const soaContentLoadingStore = useSoaContentLoadingStore()
const accessGuard = useAccessGuard()
const { t } = useI18n()
const roles = inject('roles')

const loadingSoaContent = computed(() => soaContentLoadingStore.loading)
const updateFlowchart = ref(0)
const settingsFormKey = ref(0)
const tabs = ref([
  {
    tab: 'soa',
    name: t('ActivitiesView.tab1_title'),
    loading: () => (loadingSoaContent.value ? 'warning' : false),
  },
  { tab: 'list', name: t('ActivitiesView.tab2_title') },
])
const helpItems = [
  'StudyActivity.general',
  'StudyActivity.settings',
  'StudyActivity.study_activities',
  'StudyActivity.detailed_soa',
  'StudyActivity.detailed_soa_actions',
  'StudyActivity.detailed_soa_reordering',
  'StudyActivity.study_footnotes',
  'StudyActivity.hidden_activity_footnotes',
  'StudyActivity.protocol_soa',
  'StudyActivity.instructions',
]
const showSoaSettings = ref(false)
const updateActivitiesTable = ref(0)
const activitiesTable = ref()

const lockSettings = computed(() => {
  if (
    !accessGuard.checkPermission(roles.STUDY_WRITE) ||
    studiesGeneralStore.selectedStudyVersion !== null
  ) {
    return true
  }
  return false
})

const onTabChanged = () => {
  if (localStorage.getItem('open-form')) {
    updateActivitiesTable.value++
  }
  studiesGeneralStore.getSoaPreferences()
  if (localStorage.getItem('refresh-activities')) {
    activitiesTable.value.onStudyActivitiesUpdated()
    localStorage.removeItem('refresh-activities')
  }
}

function openSoaSettings() {
  settingsFormKey.value++
  showSoaSettings.value = true
}

function closeSoaSettings() {
  updateFlowchart.value++
  showSoaSettings.value = false
}
</script>
