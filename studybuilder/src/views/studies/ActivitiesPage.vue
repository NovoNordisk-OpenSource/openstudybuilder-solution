<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('ActivitiesView.title') }} ({{ studiesGeneralStore.studyId }})
      <HelpButtonWithPanels :title="$t('_global.help')" :items="helpItems" />
      <v-spacer />
      <v-btn
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        icon="mdi-cog-outline"
        :disabled="lockSettings"
        :loading="soaContentLoadingStore.loading"
        @click="openSoaSettings"
      />
    </div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab
        v-for="item of tabs"
        :key="item.tab"
        :value="item.tab"
        :loading="
          soaContentLoadingStore.loading &&
          ['soa', 'protocol'].indexOf(item.tab) > -1
            ? 'warning'
            : null
        "
      >
        {{ item.name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab">
      <v-window-item value="list">
        <StudyActivityTable :key="activitiesKey" />
      </v-window-item>
      <v-window-item value="soa">
        <DetailedFlowchart :update="updateFlowchart" />
      </v-window-item>
    </v-window>
    <v-dialog v-model="showSoaSettings" max-width="800px">
      <SoaSettingsForm :key="settingsFormKey" @close="closeSoaSettings" />
    </v-dialog>
  </div>
</template>

<script setup>
import DetailedFlowchart from '@/components/studies/DetailedFlowchart.vue'
import StudyActivityTable from '@/components/studies/StudyActivityTable.vue'
import SoaSettingsForm from '@/components/studies/SoaSettingsForm.vue'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import { useAccessGuard } from '@/composables/accessGuard'
import { useAppStore } from '@/stores/app'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useSoaContentLoadingStore } from '@/stores/soa-content-loading'
import { inject, computed, ref, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

const appStore = useAppStore()
const studiesGeneralStore = useStudiesGeneralStore()
const soaContentLoadingStore = useSoaContentLoadingStore()
const accessGuard = useAccessGuard()
const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const roles = inject('roles')

const activitiesKey = ref(0)
const tab = ref(null)
const updateProtocol = ref(0)
const updateFlowchart = ref(0)
const settingsFormKey = ref(0)
const tabs = [
  { tab: 'list', name: t('ActivitiesView.tab1_title') },
  { tab: 'soa', name: t('ActivitiesView.tab2_title') },
]
const helpItems = [
  'StudyActivity.general',
  'StudyActivity.settings',
  'StudyActivity.study_activities',
  'StudyActivity.detailed_soa',
  'StudyActivity.detailed_soa_actions',
  'StudyActivity.detailed_soa_reordering',
  'StudyActivity.study_footnotes',
  'StudyActivity.protocol_soa',
  'StudyActivity.instructions',
]
const showSoaSettings = ref(false)

const lockSettings = computed(() => {
  if (
    !accessGuard.checkPermission(roles.STUDY_WRITE) ||
    studiesGeneralStore.selectedStudyVersion !== null
  ) {
    return true
  }
  return false
})

watch(tab, (newValue) => {
  const tabName = newValue
    ? tabs.find((el) => el.tab === newValue).name
    : tabs[0].name
  studiesGeneralStore.getSoaPreferences()
  router.push({
    name: 'StudyActivities',
    params: { study_id: studiesGeneralStore.selectedStudy.uid, tab: newValue },
  })
  appStore.addBreadcrumbsLevel(
    tabName,
    {
      name: 'StudyActivities',
      params: { study_id: studiesGeneralStore.selectedStudy.uid, tab: tabName },
    },
    3,
    true
  )
  if (newValue === 'list') {
    activitiesKey.value++
  } else if (newValue === 'protocol') {
    updateProtocol.value++
  } else if (newValue === 'soa') {
    updateFlowchart.value++
  }
})

watch(
  () => route.params.tab,
  (newValue) => {
    tab.value = newValue
  }
)

onMounted(() => {
  tab.value = route.params.tab || tabs[0].tab
  const tabName = tab.value
    ? tabs.find((el) => el.tab === tab.value).name
    : tabs[0].name
  setTimeout(() => {
    appStore.addBreadcrumbsLevel(
      tabName,
      {
        name: 'StudyActivities',
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

function openSoaSettings() {
  settingsFormKey.value++
  showSoaSettings.value = true
}

function closeSoaSettings() {
  if (window.location.pathname.includes('protocol')) {
    updateProtocol.value++
  } else {
    updateFlowchart.value++
  }
  showSoaSettings.value = false
}
</script>
