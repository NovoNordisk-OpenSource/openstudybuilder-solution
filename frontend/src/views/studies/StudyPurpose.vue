<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('Sidebar.study.purpose') }} ({{ studyId }})
      <HelpButtonWithPanels
        :help-text="$t('_help.StudyPurposeView.general')"
        :items="helpItems"
      />
    </div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab v-for="item of tabs" :key="item.tab" :value="item.tab">
        {{ item.name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab">
      <v-window-item value="objectives">
        <ObjectiveTable :key="`objectives-${tabKeys.objectives}`" />
      </v-window-item>
      <v-window-item value="endpoints">
        <EndpointTable :key="`endpoints-${tabKeys.endpoints}`" />
      </v-window-item>
      <v-window-item value="estimands">
        <UnderConstruction />
      </v-window-item>
    </v-window>
  </div>
</template>

<script>
import EndpointTable from '@/components/studies/EndpointTable.vue'
import ObjectiveTable from '@/components/studies/ObjectiveTable.vue'
import UnderConstruction from '@/components/layout/UnderConstruction.vue'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import { useAppStore } from '@/stores/app'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { computed } from 'vue'
import { useTabKeys } from '@/composables/tabKeys'

export default {
  components: {
    EndpointTable,
    HelpButtonWithPanels,
    ObjectiveTable,
    UnderConstruction,
  },
  setup() {
    const appStore = useAppStore()
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      addBreadcrumbsLevel: appStore.addBreadcrumbsLevel,
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
      studyId: computed(() => studiesGeneralStore.studyId),
      ...useTabKeys(),
    }
  },
  data() {
    return {
      tab: null,
      helpItems: [
        'StudyPurposeView.study_objectives',
        'StudyPurposeView.study_endpoints',
        'StudyPurposeView.study_estimands',
      ],
      tabs: [
        {
          tab: 'objectives',
          name: this.$t('StudyPurposeView.study_objectives'),
        },
        { tab: 'endpoints', name: this.$t('StudyPurposeView.study_endpoints') },
        // { tab: 'estimands', name: this.$t('StudyPurposeView.study_estimands') },
      ],
    }
  },
  watch: {
    tab(newValue) {
      const tabName = newValue
        ? this.tabs.find((el) => el.tab === newValue).name
        : this.tabs[0].name
      this.$router.push({
        name: 'StudyPurpose',
        params: { tab: newValue },
      })
      this.addBreadcrumbsLevel(
        tabName,
        {
          name: 'StudyPurpose',
          params: { study_id: this.selectedStudy.uid, tab: tabName },
        },
        3,
        true
      )
      this.helpItems.splice(3, 4)
      if (newValue === 'objectives') {
        this.helpItems.push(
          'StudyObjectivesTable.objective_level',
          'StudyObjectivesTable.endpoint_count',
          'StudyObjectivesTable.objective'
        )
      } else if (newValue === 'endpoints') {
        this.helpItems.push(
          'StudyEndpointsTable.endpoint_title',
          'StudyEndpointsTable.objective',
          'StudyEndpointsTable.time_frame',
          'StudyEndpointsTable.units'
        )
      }
      this.updateTabKey(newValue)
    },
  },
  mounted() {
    this.tab = this.$route.params.tab || this.tabs[0].tab
    const tabName = this.tab
      ? this.tabs.find((el) => el.tab === this.tab).name
      : this.tabs[0].name
    setTimeout(() => {
      this.addBreadcrumbsLevel(
        tabName,
        {
          name: 'StudyPurpose',
          params: { study_id: this.selectedStudy.uid, tab: tabName },
        },
        3,
        true
      )
    }, 100)
  },
}
</script>
