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
            <slot name="extraActions" :item="item" />
            <template v-for="(action, pos) in actions">
              <v-btn
                v-if="
                  action.condition &&
                  !hiddenActions.includes(action.key) &&
                  (!action.accessRole || checkPermission(action.accessRole))
                "
                :key="pos"
                variant="outlined"
                class="ml-2"
                :color="action.iconColor"
                icon
                size="small"
                @click="action.click"
              >
                <v-icon left>{{ action.icon }}</v-icon>
                <v-tooltip activator="parent" location="top">
                  {{ action.label }}
                </v-tooltip>
              </v-btn>
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
              color="nnGreen1"
              class="text-white"
              icon
              size="small"
              @click="downloadYamlContent"
            >
              <v-icon>mdi-download-outline</v-icon>
              <v-tooltip activator="parent" location="top">
                {{ $t('YamlViewer.download') }}
              </v-tooltip>
            </v-btn>
            <v-btn class="ml-2" icon size="small" @click="closeYamlTab">
              <v-icon>mdi-close</v-icon>
              <v-tooltip activator="parent" location="top">
                {{ $t('YamlViewer.close_tab') }}
              </v-tooltip>
            </v-btn>
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
              color="nnGreen1"
              class="text-white"
              icon
              size="small"
              @click="downloadCosmosContent"
            >
              <v-icon>mdi-download-outline</v-icon>
              <v-tooltip activator="parent" location="top">
                {{ $t('YamlViewer.download') }}
              </v-tooltip>
            </v-btn>
            <v-btn class="ml-2" icon size="small" @click="closeYamlTab">
              <v-icon>mdi-close</v-icon>
              <v-tooltip activator="parent" location="top">
                {{ $t('YamlViewer.close_tab') }}
              </v-tooltip>
            </v-btn>
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
      :action-source="source"
      :action-subitem="resolveActionSubitem('edit')"
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
        :items-total="historyItems.length"
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
import statuses from '@/constants/statuses'

export default {
  components: {
    HistoryTable,
    YamlViewer,
  },
  inject: ['notificationHub'],
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
    actionSubitemMap: {
      type: Object,
      default: () => ({}),
    },
    hiddenActions: {
      type: Array,
      default: () => [],
    },
  },
  emits: ['closePage', 'refresh', 'approve-activity'],
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
          key: 'approve',
          label: this.$t('_global.approve'),
          icon: 'mdi-check-decagram',
          iconColor: 'success',
          condition:
            this.item &&
            this.item.status === statuses.DRAFT &&
            this.item.possible_actions.find((action) => action === 'approve'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.approveItem,
        },
        {
          key: 'edit',
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil-outline',
          iconColor: 'nnBaseBlue',
          condition:
            this.item &&
            this.item.possible_actions.find((action) => action === 'edit'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.editItem,
        },
        {
          key: 'new_version',
          label: this.$t('_global.new_version'),
          icon: 'mdi-plus-circle-outline',
          iconColor: 'nnBaseBlue',
          condition:
            this.item &&
            this.item.possible_actions.find(
              (action) => action === 'new_version'
            ),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.newItemVersion,
        },
        {
          key: 'inactivate',
          label: this.$t('_global.inactivate'),
          icon: 'mdi-close-octagon-outline',
          iconColor: 'nnBaseBlue',
          condition:
            this.item &&
            this.item.possible_actions.find(
              (action) => action === 'inactivate'
            ),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.inactivateItem,
        },
        {
          key: 'reactivate',
          label: this.$t('_global.reactivate'),
          icon: 'mdi-undo-variant',
          iconColor: 'nnBaseBlue',
          condition:
            this.item &&
            this.item.possible_actions.find(
              (action) => action === 'reactivate'
            ),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.reactivateItem,
        },
        {
          key: 'delete',
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
          key: 'history',
          label: this.$t('_global.history'),
          iconColor: 'nnBaseBlue',
          icon: 'mdi-history',
          condition: true,
          accessRole: this.$roles.LIBRARY_READ,
          click: this.openHistory,
        },
        {
          key: 'close',
          label: this.$t('_global.close'),
          iconColor: 'nnBaseBlue',
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
    resolveActionSubitem(actionName) {
      return this.actionSubitemMap?.[actionName] || null
    },
    async closeForm() {
      this.showForm = false
      this.navigateToVersion(this.item, null)
      await this.fetchItem()
    },
    closePage() {
      this.$router.go(-1)
    },
    closeYamlTab() {
      this.tab = 'html'
    },
    fetchItem() {
      return activities.getObject(this.source, this.itemUid).then((resp) => {
        this.item = resp.data
        this.transformFunc(this.item)
        this.$emit('refresh')
      })
    },
    editItem() {
      this.showForm = true
    },
    async inactivateItem() {
      await activities.inactivate(
        this.itemUid,
        this.source,
        this.resolveActionSubitem('inactivate')
      )
      this.notificationHub.add({
        msg: this.$t(`ActivitiesTable.inactivate_${this.source}_success`),
        type: 'success',
      })
      this.navigateToVersion(this.item, null)
      await this.fetchItem()
    },
    async reactivateItem() {
      await activities.reactivate(
        this.itemUid,
        this.source,
        this.resolveActionSubitem('reactivate')
      )
      this.notificationHub.add({
        msg: this.$t(`ActivitiesTable.reactivate_${this.source}_success`),
        type: 'success',
      })
      this.navigateToVersion(this.item, null)
      await this.fetchItem()
    },
    deleteItem() {
      activities.delete(this.itemUid, this.source).then(() => {
        this.notificationHub.add({
          msg: this.$t(`ActivitiesTable.delete_${this.source}_success`),
          type: 'success',
        })
        this.$router.push({ name: 'Activities', params: { tab: this.source } })
      })
    },
    async approveItem() {
      if (this.source === 'activities') {
        this.$emit('approve-activity', this.item)
        return
      }
      const options = {}
      if (
        ['activity-groups', 'activity-sub-groups'].indexOf(this.source) !== -1
      ) {
        options.cascade_edit_and_approve = true
      }
      const approveSource = this.source
      const approveSubitem = this.resolveActionSubitem('approve')
      activities
        .approve(this.itemUid, approveSource, options, approveSubitem)
        .then(async (resp) => {
          if (this.source === 'activity-sub-groups') {
            if (resp.data.was_cascade_update_performed) {
              this.notificationHub.add({
                msg: this.$t(
                  `ActivitiesTable.approve_activity-sub-groups_success_cascade`
                ),
                type: 'success',
              })
            } else {
              this.notificationHub.add({
                msg: this.$t(
                  `ActivitiesTable.approve_activity-sub-groups_success_no_cascade`
                ),
                type: 'warning',
              })
            }
          } else {
            this.notificationHub.add({
              msg: this.$t(`ActivitiesTable.approve_${this.source}_success`),
              type: 'success',
            })
          }
          this.navigateToVersion(this.item, null)
          await this.fetchItem()
        })
    },
    async newItemVersion() {
      await activities.newVersion(
        this.itemUid,
        this.source,
        this.resolveActionSubitem('newVersion')
      )
      this.notificationHub.add({
        msg: this.$t('_global.new_version_success'),
        type: 'success',
      })
      this.navigateToVersion(this.item, null)
      await this.fetchItem()
    },
    async openHistory() {
      const resp = await activities.getVersions(
        this.source,
        this.itemUid,
        this.resolveActionSubitem('history')
      )
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
