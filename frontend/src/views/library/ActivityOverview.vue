<template>
  <div v-if="activityOverview" class="px-4">
    <div class="d-flex page-title">
      {{ activityOverview.activity.name }}
      <HelpButtonWithPanels
        :help-text="$t('_help.ActivityOverview.general')"
        :items="helpItems"
      />
    </div>
    <ActivityOverview
      v-if="activityOverview"
      source="activities"
      :item-uid="$route.params.id"
      :item-overview="activityOverview"
      :yaml-version="activityYAML"
      :cosmos-version="activityCOSMoS"
      @refresh="fetchOverview"
      @close-page="closePage"
    />
  </div>
</template>

<script>
import ActivityOverview from '@/components/library/ActivityOverview.vue'
import activities from '@/api/activities'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import { useAppStore } from '@/stores/app'

export default {
  components: {
    ActivityOverview,
    HelpButtonWithPanels,
  },
  setup() {
    const appStore = useAppStore()
    return {
      addBreadcrumbsLevel: appStore.addBreadcrumbsLevel,
    }
  },
  data() {
    return {
      activityOverview: null,
      activityYAML: null,
      activityCOSMoS: null,
      helpItems: [
        'ActivityOverview.cosmos_yaml',
        'ActivityOverview.activity_groups',
        'ActivityOverview.activity_subgroups',
        'ActivityOverview.adam_code',
        'ActivityOverview.topic_code',
        'ActivityOverview.class',
        'ActivityOverview.instances',
        'ActivityOverview.is_data_collected',
        'ActivityOverview.activity_groupings',
      ],
    }
  },
  created() {
    this.fetchOverview()
  },
  methods: {
    fetchOverview() {
      activities
        .getObjectOverview(
          'activities',
          this.$route.params.id,
          this.$route.params.version
        )
        .then((resp) => {
          this.activityOverview = resp.data
          this.addBreadcrumbsLevel(
            this.activityOverview.activity.name,
            { name: 'ActivityOverview', params: this.$route.params },
            4
          )
        })
      activities
        .getObjectOverview(
          'activities',
          this.$route.params.id,
          undefined,
          'yaml'
        )
        .then((resp) => {
          this.activityYAML = resp.data
        })
      activities
        .getCOSMoSOverview('activities', this.$route.params.id)
        .then((resp) => {
          this.activityCOSMoS = resp.data
        })
    },
    closePage() {
      this.$router.go(-1)
    },
  },
}
</script>
