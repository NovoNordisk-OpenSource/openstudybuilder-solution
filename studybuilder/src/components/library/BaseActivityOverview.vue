<template>
  <div>
    <v-tabs v-model="tab">
      <v-tab value="html">
        {{ $t('_global.overview') }}
      </v-tab>
      <v-tab value="yaml">
        {{ $t('ActivityOverview.osb_yaml') }}
      </v-tab>
      <v-tab v-if="cosmosVersion" value="cosmos">
        {{ $t('ActivityOverview.cosmos_yaml') }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab">
      <v-window-item value="html">
        <v-card elevation="0" class="rounded-0">
          <v-card-title class="d-flex">
            <v-spacer />
            <template v-for="(action, pos) in actions">
              <v-btn
                v-if="
                  action.condition &&
                  (!action.accessRole || checkPermission(action.accessRole))
                "
                :key="pos"
                size="small"
                :title="action.label"
                class="ml-2"
                :color="action.iconColor"
                :icon="action.icon"
                @click="action.click"
              />
            </template>
          </v-card-title>
          <v-card-text>
            <slot
              name="htmlContent"
              :item-overview="itemOverview"
              :item="item"
            />
          </v-card-text>
        </v-card>
      </v-window-item>
      <v-window-item value="yaml">
        <v-card elevation="0" class="rounded-0">
          <v-card-title class="d-flex">
            <v-spacer />
            <v-btn
              size="small"
              color="nnGreen1"
              class="text-white"
              :title="$t('YamlViewer.download')"
              icon="mdi-download-outline"
              @click="downloadYamlContent"
            />
            <v-btn
              size="small"
              :title="$t('YamlViewer.close_tab')"
              class="ml-2"
              icon="mdi-close"
              @click="closeYamlTab"
            />
          </v-card-title>
          <v-card-text>
            <YamlViewer :content="yamlVersion" />
          </v-card-text>
        </v-card>
      </v-window-item>
      <v-window-item v-if="cosmosVersion" value="cosmos">
        <v-card elevation="0" class="rounded-0">
          <v-card-title class="d-flex">
            <v-spacer />
            <v-btn
              size="small"
              color="nnGreen1"
              class="text-white"
              :title="$t('YamlViewer.download')"
              icon="mdi-download-outline"
              @click="downloadCosmosContent"
            />
            <v-btn
              size="small"
              :title="$t('YamlViewer.close_tab')"
              class="ml-2"
              icon="mdi-close"
              @click="closeYamlTab"
            />
          </v-card-title>
          <v-card-text>
            <YamlViewer :content="cosmosVersion" />
          </v-card-text>
        </v-card>
      </v-window-item>
    </v-window>
    <slot
      v-if="showForm"
      name="itemForm"
      :show="showForm"
      :item="item"
      :close="closeForm"
    />
    <v-dialog
      v-model="showHistory"
      persistent
      :max-width="$globals.historyDialogMaxWidth"
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeHistory"
    >
      <HistoryTable
        :title="historyTitle"
        :headers="historyHeaders"
        :items="historyItems"
        @close="closeHistory"
      />
    </v-dialog>
  </div>
</template>

<script>
import { useAccessGuard } from '@/composables/accessGuard'
import activities from '@/api/activities'
import exportLoader from '@/utils/exportLoader'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import YamlViewer from '@/components/tools/YamlViewer.vue'

export default {
  components: {
    HistoryTable,
    YamlViewer,
  },
  inject: ['eventBusEmit'],
  props: {
    itemUid: {
      type: String,
      default: null,
    },
    source: {
      type: String,
      default: null,
    },
    itemOverview: {
      type: Object,
      default: null,
    },
    yamlVersion: {
      type: String,
      default: null,
    },
    transformFunc: {
      type: Function,
      default: null,
    },
    navigateToVersion: {
      type: Function,
      default: null,
    },
    historyHeaders: {
      type: Array,
      default: null,
    },
    cosmosVersion: {
      type: String,
      default: null,
      required: false,
    },
  },
  emits: ['closePage', 'refresh'],
  setup() {
    const accessGuard = useAccessGuard()
    return {
      ...accessGuard,
    }
  },
  data() {
    return {
      item: null,
      historyItems: [],
      showForm: false,
      showHistory: false,
      tab: null,
    }
  },
  computed: {
    actions() {
      return [
        {
          label: this.$t('_global.approve'),
          icon: 'mdi-check-decagram',
          iconColor: 'success',
          condition:
            this.item &&
            this.item.possible_actions.find((action) => action === 'approve'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.approveItem,
        },
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil-outline',
          iconColor: 'primary',
          condition:
            this.item &&
            this.item.possible_actions.find((action) => action === 'edit'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.editItem,
        },
        {
          label: this.$t('_global.new_version'),
          icon: 'mdi-plus-circle-outline',
          iconColor: 'primary',
          condition:
            this.item &&
            this.item.possible_actions.find(
              (action) => action === 'new_version'
            ),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.newItemVersion,
        },
        {
          label: this.$t('_global.inactivate'),
          icon: 'mdi-close-octagon-outline',
          iconColor: 'primary',
          condition:
            this.item &&
            this.item.possible_actions.find(
              (action) => action === 'inactivate'
            ),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.inactivateItem,
        },
        {
          label: this.$t('_global.reactivate'),
          icon: 'mdi-undo-variant',
          iconColor: 'primary',
          condition:
            this.item &&
            this.item.possible_actions.find(
              (action) => action === 'reactivate'
            ),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.reactivateItem,
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete-outline',
          iconColor: 'error',
          condition:
            this.item &&
            this.item.possible_actions.find((action) => action === 'delete'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.deleteItem,
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          condition: true,
          accessRole: this.$roles.LIBRARY_READ,
          click: this.openHistory,
        },
        {
          label: this.$t('_global.close'),
          icon: 'mdi-close',
          condition: true,
          accessRole: this.$roles.LIBRARY_READ,
          click: this.closePage,
        },
      ]
    },
    historyTitle() {
      if (this.source === 'activities') {
        return this.$t('ActivityOverview.history_title', { uid: this.itemUid })
      } else if (this.source === 'activity-sub-groups') {
        return this.$t('SubgroupOverview.history_title', { uid: this.itemUid })
      } else if (this.source === 'activity-groups') {
        return this.$t('GroupOverview.history_title', { uid: this.itemUid })
      } else {
        return this.$t('ActivityInstanceOverview.history_title', {
          uid: this.itemUid,
        })
      }
    },
  },
  mounted() {
    this.fetchItem()
  },
  methods: {
    closeForm() {
      this.showForm = false
      this.navigateToVersion(this.item, null)
      this.fetchItem()
    },
    closePage() {
      this.$router.go(-1)
    },
    closeYamlTab() {
      this.tab = 'html'
    },
    fetchItem() {
      activities.getObject(this.source, this.itemUid).then((resp) => {
        this.item = resp.data
        this.transformFunc(this.item)
        this.$emit('refresh')
      })
    },
    editItem() {
      this.showForm = true
    },
    inactivateItem() {
      activities.inactivate(this.itemUid, this.source).then(() => {
        this.eventBusEmit('notification', {
          msg: this.$t(`ActivitiesTable.inactivate_${this.source}_success`),
          type: 'success',
        })
        this.navigateToVersion(this.item, null)
        this.fetchItem()
      })
    },
    reactivateItem() {
      activities.reactivate(this.itemUid, this.source).then(() => {
        this.eventBusEmit('notification', {
          msg: this.$t(`ActivitiesTable.reactivate_${this.source}_success`),
          type: 'success',
        })
        this.navigateToVersion(this.item, null)
        this.fetchItem()
      })
    },
    deleteItem() {
      activities.delete(this.itemUid, this.source).then(() => {
        this.eventBusEmit('notification', {
          msg: this.$t(`ActivitiesTable.delete_${this.source}_success`),
          type: 'success',
        })
        this.$router.push({ name: 'Activities', params: { tab: this.source } })
      })
    },
    approveItem() {
      const options = {}
      if (this.source === 'activities') {
        options.cascade_edit_and_approve = true
      }
      activities.approve(this.itemUid, this.source, options).then(() => {
        this.eventBusEmit('notification', {
          msg: this.$t(`ActivitiesTable.approve_${this.source}_success`),
          type: 'success',
        })
        this.navigateToVersion(this.item, null)
        this.fetchItem()
      })
    },
    newItemVersion() {
      activities.newVersion(this.itemUid, this.source).then(() => {
        this.eventBusEmit('notification', {
          msg: this.$t('_global.new_version_success'),
          type: 'success',
        })
        this.navigateToVersion(this.item, null)
        this.fetchItem()
      })
    },
    async openHistory() {
      const resp = await activities.getVersions(this.source, this.itemUid)
      this.historyItems = this.transformItems(resp.data)
      this.showHistory = true
    },
    closeHistory() {
      this.showHistory = false
    },
    transformItems(items) {
      const result = []
      for (const item of items) {
        if (this.source === 'activities') {
          // For activities, check activity_groupings
          if (item.activity_groupings && item.activity_groupings.length > 0) {
            this.transformFunc(item)
            result.push(item)
          }
        } else if (this.source === 'activity-sub-groups') {
          // For subgroups, check activity_groups
          if (item.activity_groups && item.activity_groups.length >= 0) {
            this.transformFunc(item)
            result.push(item)
          }
        } else if (this.source === 'activity-groups') {
          this.transformFunc(item)
          result.push(item)
        } else {
          this.transformFunc(item)
          result.push(item)
        }
      }
      return result
    },
    downloadYamlContent() {
      exportLoader.downloadFile(
        this.yamlVersion,
        'application/yaml',
        'overview.yml'
      )
    },
    downloadCosmosContent() {
      exportLoader.downloadFile(
        this.cosmosVersion,
        'application/yaml',
        'COSMoS-overview.yml'
      )
    },
  },
}
</script>
