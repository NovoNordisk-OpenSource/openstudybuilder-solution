<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('StudyDataSpecifications.title') }} ({{
        studiesGeneralStore.studyId
      }})
      <HelpButtonWithPanels :items="helpItems" />
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
    <v-tabs v-model="tab" bg-color="white">
      <v-tab
        v-for="item of tabs"
        :key="item.tab"
        :value="item.tab"
        :loading="
          soaContentLoadingStore.loading &&
          ['operational'].indexOf(item.tab) > -1
            ? 'warning'
            : null
        "
      >
        {{ item.name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab">
      <v-window-item value="instances">
        <StudyActivityInstancesTable :key="`instances-${tabKeys.instances}`" />
      </v-window-item>
      <v-window-item value="operational">
        <OperationalSoa
          :key="`operational-${tabKeys.operational}`"
          :update="updateSoa"
        />
      </v-window-item>
      <v-window-item v-if="showAuxiliaryDevices" value="auxiliary_devices">
        <StudyAuxiliaryDeviceTable
          :key="`auxiliary_devices-${tabKeys.auxiliary_devices}`"
        />
      </v-window-item>
    </v-window>
    <v-dialog v-model="showSoaSettings" max-width="800px">
      <SoaSettingsForm @close="closeSoaSettings" />
    </v-dialog>
  </div>
</template>

<script setup>
import StudyActivityInstancesTable from '@/components/studies/StudyActivityInstancesTable.vue'
import StudyAuxiliaryDeviceTable from '@/components/studies/StudyAuxiliaryDeviceTable.vue'
import OperationalSoa from '@/components/studies/OperationalSoa.vue'
import SoaSettingsForm from '@/components/studies/SoaSettingsForm.vue'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import { useAppStore } from '@/stores/app'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useFeatureFlagsStore } from '@/stores/feature-flags'
import { useI18n } from 'vue-i18n'
import { inject, computed, watch, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAccessGuard } from '@/composables/accessGuard'
import { useSoaContentLoadingStore } from '@/stores/soa-content-loading'
import { useTabKeys } from '@/composables/tabKeys'

const appStore = useAppStore()
const studiesGeneralStore = useStudiesGeneralStore()
const featureFlagsStore = useFeatureFlagsStore()
const soaContentLoadingStore = useSoaContentLoadingStore()
const accessGuard = useAccessGuard()
const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const roles = inject('roles')
const { tabKeys, updateTabKey } = useTabKeys({ persist: true })

const tab = ref(null)

const showAuxiliaryDevices = computed(() =>
  featureFlagsStore.getFeatureFlag('study_auxiliary_devices')
)

const tabs = computed(() => {
  const allTabs = [
    { tab: 'instances', name: t('StudyDataSpecifications.tab1_title') },
    { tab: 'operational', name: t('StudyDataSpecifications.tab2_title') },
    ...(showAuxiliaryDevices.value
      ? [
          {
            tab: 'auxiliary_devices',
            name: t('StudyDataSpecifications.tab3_title'),
          },
        ]
      : []),
  ]
  return allTabs
})
const showSoaSettings = ref(false)
const updateSoa = ref(0)
const helpItems = computed(() => [
  'StudyDataSpecifications.general',
  'StudyDataSpecifications.instances_actions',
  'StudyDataSpecifications.instances_ellipsis',
  'StudyDataSpecifications.instances_exclamation',
  'StudyDataSpecifications.instances_updates',
  ...(showAuxiliaryDevices.value
    ? ['StudyDataSpecifications.auxiliary_devices']
    : []),
])

const lockSettings = computed(() => {
  if (
    !accessGuard.checkPermission(roles.STUDY_WRITE) ||
    studiesGeneralStore.selectedStudyVersion !== null
  ) {
    return true
  }
  return false
})

function openSoaSettings() {
  showSoaSettings.value = true
}

function closeSoaSettings() {
  updateSoa.value++
  showSoaSettings.value = false
}

watch(tab, (newValue) => {
  const found = newValue ? tabs.value.find((el) => el.tab === newValue) : null
  const tabName = found ? found.name : tabs.value[0].name
  router.push({
    name: 'StudyDataSpecifications',
    params: { study_id: studiesGeneralStore.selectedStudy.uid, tab: newValue },
  })
  appStore.addBreadcrumbsLevel(
    tabName,
    {
      name: 'StudyDataSpecifications',
      params: { study_id: studiesGeneralStore.selectedStudy.uid, tab: tabName },
    },
    3,
    true
  )
  updateTabKey(newValue)
})

onMounted(() => {
  const requestedTab = route.params.tab
  const knownTab = requestedTab
    ? tabs.value.find((el) => el.tab === requestedTab)
    : null
  tab.value = knownTab ? requestedTab : tabs.value[0].tab
  const tabName = knownTab ? knownTab.name : tabs.value[0].name
  setTimeout(() => {
    appStore.addBreadcrumbsLevel(
      tabName,
      {
        name: 'StudyDataSpecifications',
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
