<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('StudyProtocolElementsView.title') }} ({{ studyId }})
      <HelpButton :help-text="$t('_help.ProtocolElementsTable.general')" />
      <v-spacer />
      <v-btn
        v-if="tab === 'tab-1'"
        class="ml-2"
        icon
        size="small"
        variant="outlined"
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
      <v-tab v-for="item of tabs" :key="item.tab" :value="item.tab">
        {{ item.name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab" class="bg-white">
      <v-window-item value="tab-0">
        <ProtocolTitlePage :key="`tab-0-${tabKeys['tab-0']}`" />
      </v-window-item>
      <v-window-item value="tab-1">
        <ProtocolFlowchart
          :key="`tab-1-${tabKeys['tab-1']}`"
          :study-uid="selectedStudy.uid"
          :update="updateFlowchart"
        />
      </v-window-item>
      <v-window-item value="tab-2">
        <ProtocolElementsObjectiveTable
          :key="`tab-2-${tabKeys['tab-2']}`"
          :study-uid="selectedStudy.uid"
          :update="updateObjectives"
        />
      </v-window-item>
      <v-window-item value="tab-3">
        <ProtocolElementsStudyDesign
          :key="`tab-3-${tabKeys['tab-3']}`"
          :study-uid="selectedStudy.uid"
          :update="updateDesign"
        />
      </v-window-item>
      <v-window-item value="tab-4">
        <ProtocolElementsStudyPopulationSummary
          :key="`tab-4-${tabKeys['tab-4']}`"
        />
      </v-window-item>
      <v-window-item value="tab-5">
        <ProtocolElementsStudyInterventions
          :key="`tab-5-${tabKeys['tab-5']}`"
          :study-uid="selectedStudy.uid"
          :update="updateInterventions"
        />
      </v-window-item>
      <v-window-item value="tab-6">
        <ProtocolElementsProceduresAndActivities
          :key="`tab-6-${tabKeys['tab-6']}`"
        />
      </v-window-item>
    </v-window>
    <v-dialog v-model="showSoaSettings" max-width="800px">
      <SoaSettingsForm @close="closeSoaSettings" />
    </v-dialog>
  </div>
</template>

<script>
import { computed } from 'vue'
import ProtocolElementsObjectiveTable from '@/components/studies/ProtocolElementsObjectiveTable.vue'
import ProtocolElementsStudyPopulationSummary from '@/components/studies/ProtocolElementsStudyPopulationSummary.vue'
import ProtocolElementsStudyDesign from '@/components/studies/ProtocolElementsStudyDesign.vue'
import ProtocolElementsStudyInterventions from '@/components/studies/ProtocolElementsStudyIntervention.vue'
import ProtocolElementsProceduresAndActivities from '@/components/studies/ProtocolElementsProceduresAndActivities.vue'
import ProtocolFlowchart from '@/components/studies/ProtocolFlowchart.vue'
import ProtocolTitlePage from '@/components/studies/ProtocolTitlePage.vue'
import HelpButton from '@/components/tools/HelpButton.vue'
import SoaSettingsForm from '@/components/studies/SoaSettingsForm.vue'
import { useAppStore } from '@/stores/app'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useSoaContentLoadingStore } from '@/stores/soa-content-loading'
import { useAccessGuard } from '@/composables/accessGuard'
import { useTabKeys } from '@/composables/tabKeys'

export default {
  components: {
    ProtocolElementsObjectiveTable,
    ProtocolFlowchart,
    ProtocolTitlePage,
    ProtocolElementsStudyPopulationSummary,
    ProtocolElementsStudyDesign,
    ProtocolElementsStudyInterventions,
    ProtocolElementsProceduresAndActivities,
    HelpButton,
    SoaSettingsForm,
  },
  setup() {
    const appStore = useAppStore()
    const studiesGeneralStore = useStudiesGeneralStore()
    const soaContentLoadingStore = useSoaContentLoadingStore()
    const accessGuard = useAccessGuard()
    return {
      addBreadcrumbsLevel: appStore.addBreadcrumbsLevel,
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
      selectedStudyVersion: computed(
        () => studiesGeneralStore.selectedStudyVersion
      ),
      studyId: computed(() => studiesGeneralStore.studyId),
      soaContentLoadingStore,
      ...accessGuard,
      ...useTabKeys(),
    }
  },
  data() {
    return {
      tab: null,
      updateFlowchart: 0,
      updateObjectives: 0,
      updateDesign: 0,
      updateInterventions: 0,
      showSoaSettings: false,
      tabs: [
        { tab: 'tab-0', name: this.$t('Sidebar.study.protocol_title') },
        {
          tab: 'tab-1',
          name: this.$t('StudyProtocolElementsView.protocol_soa'),
        },
        {
          tab: 'tab-2',
          name: this.$t('Sidebar.study.objective_endpoints_estimands'),
        },
        { tab: 'tab-3', name: this.$t('Sidebar.study.study_design') },
        { tab: 'tab-4', name: this.$t('Sidebar.study.study_population') },
        {
          tab: 'tab-5',
          name: this.$t('Sidebar.study.study_interventions_and_therapy'),
        },
        { tab: 'tab-6', name: this.$t('Sidebar.study.study_activities') },
      ],
    }
  },
  computed: {
    lockSettings() {
      if (
        !this.checkPermission(this.$roles.STUDY_WRITE) ||
        this.selectedStudyVersion !== null
      ) {
        return true
      }
      return false
    },
  },
  watch: {
    tab(value) {
      const tabName = value
        ? this.tabs.find((el) => el.tab === value).name
        : this.tabs[0].name
      this.$router.push({
        name: 'ProtocolElements',
        params: { study_id: this.selectedStudy.uid, tab: tabName },
      })
      this.addBreadcrumbsLevel(
        tabName,
        {
          name: 'ProtocolElements',
          params: { study_id: this.selectedStudy.uid, tab: tabName },
        },
        3,
        true
      )
      localStorage.setItem('templatesTab', value)
      switch (value) {
        case 'tab-1':
          this.updateFlowchart++
          break
        case 'tab-2':
          this.updateObjectives++
          break
        case 'tab-3':
          this.updateDesign++
          break
        case 'tab-5':
          this.updateInterventions++
          break
      }
      this.updateTabKey(value)
    },
  },
  mounted() {
    this.tab = localStorage.getItem('templatesTab') || 'tab-0'
    const tabName = this.tab
      ? this.tabs.find((el) => el.tab === this.tab).name
      : this.tabs[0].name
    setTimeout(() => {
      this.addBreadcrumbsLevel(
        tabName,
        {
          name: 'ProtocolElements',
          params: { study_id: this.selectedStudy.uid, tab: tabName },
        },
        3,
        true
      )
    }, 100)
  },
  methods: {
    openSoaSettings() {
      this.showSoaSettings = true
    },
    closeSoaSettings() {
      this.updateFlowchart++
      this.showSoaSettings = false
    },
  },
}
</script>
