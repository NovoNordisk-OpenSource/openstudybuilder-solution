<template>
  <div>
    <NNTable
      table-id="library-instances-table"
      :headers="headers"
      :items="instances"
      item-value="uid"
      v-bind="$attrs"
      :filters-modify-function="updateHeaderFilters"
      :export-config="{ dataUrl: baseUrl, objectLabel: exportObjectLabel }"
      @filter="fetchInstances"
    >
      <template #[`item.template.name`]="{ item }">
        <NNParameterHighlighter
          :name="item.template.name"
          default-color="orange"
        />
      </template>
      <template #[`item.name`]="{ item }">
        <NNParameterHighlighter
          :name="item.name"
          :show-prefix-and-postfix="false"
        />
      </template>
      <template #[`item.start_date`]="{ item }">
        <v-tooltip location="top">
          <template #activator="{ props }">
            <span v-bind="props">{{
              $filters.dateRelative(item.start_date)
            }}</span>
          </template>
          {{ $filters.date(item.start_date) }}
        </v-tooltip>
      </template>
      <template #[`item.status`]="{ item }">
        <StatusChip :status="item.status" />
      </template>
      <template #[`item.study_count`]="{ item }">
        <v-chip sizee="small" color="primary">
          {{ item.study_count }}
        </v-chip>
      </template>
      <template #[`item.actions`]="{ item }">
        <ActionsMenu :actions="actions" :item="item" />
      </template>
    </NNTable>
    <v-dialog
      v-model="showHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeHistory"
    >
      <HistoryTable
        :title="historyTitle"
        :headers="headers"
        :items="historyItems"
        :items-total="historyItems.length"
        :html-fields="historyHtmlFields"
        @close="closeHistory"
      />
    </v-dialog>
    <v-dialog
      v-model="showStudies"
      persistent
      max-width="1200px"
      @keydown.esc="closeInstanceStudies"
    >
      <InstanceStudiesDialog
        v-if="selectedInstance"
        :template="selectedInstance.template.name"
        :text="selectedInstance.name"
        :type="type"
        :studies="studies"
        @close="closeInstanceStudies"
      />
    </v-dialog>
  </div>
</template>

<script>
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import filteringParameters from '@/utils/filteringParameters'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import InstanceStudiesDialog from './InstanceStudiesDialog.vue'
import libraryObjects from '@/api/libraryObjects'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'

export default {
  components: {
    ActionsMenu,
    HistoryTable,
    InstanceStudiesDialog,
    NNParameterHighlighter,
    NNTable,
    StatusChip,
  },
  props: {
    instances: {
      type: Array,
      default: null,
    },
    fetchInstancesActionName: {
      type: String,
      default: null,
    },
    fetchingFunction: {
      type: Function,
      default: null,
    },
    fetchInstancesExtraFilters: {
      type: Object,
      default: null,
      required: false,
    },
    type: {
      type: String,
      default: null,
    },
    baseUrl: {
      type: String,
      default: null,
    },
    exportObjectLabel: {
      type: String,
      default: '',
    },
    instanceType: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      actions: [
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openHistory,
        },
        {
          label: this.$t('InstanceTable.show_studies', { type: this.type }),
          icon: 'mdi-dots-horizontal-circle-outline',
          click: this.showInstanceStudies,
        },
      ],
      headers: [
        {
          title: '',
          key: 'actions',
          width: '1%',
        },
        { title: this.$t('_global.library'), key: 'library.name' },
        {
          title: this.$t('_global.template'),
          key: 'template.name',
          width: '30%',
          filteringName: 'template.name',
        },
        {
          title: this.$t(`_global.${this.type}`),
          key: 'name',
          filteringName: 'name_plain',
        },
        { title: this.$t('_global.modified'), key: 'start_date' },
        { title: this.$t('_global.status'), key: 'status' },
        { title: this.$t('_global.version'), key: 'version' },
        { title: this.$t('ObjectiveTable.studies_count'), key: 'study_count' },
      ],
      historyItems: [],
      historyHtmlFields: [`${this.type}_template.name`, 'name'],
      studies: [],
      showStudies: false,
      showHistory: false,
      selectedInstance: null,
    }
  },
  computed: {
    historyTitle() {
      if (this.selectedInstance) {
        return this.$t('InstanceTable.item_history_title', {
          type: this.type,
          instance: this.selectedInstance.uid,
        })
      }
      return ''
    },
  },
  mounted() {
    this.api = libraryObjects(this.baseUrl)
  },
  methods: {
    closeHistory() {
      this.showHistory = false
    },
    closeInstanceStudies() {
      this.showStudies = false
    },
    fetchInstances(filters, options, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      if (this.fetchInstancesExtraFilters) {
        if (params.filters) {
          params.filters = {
            ...JSON.parse(params.filters),
            ...this.fetchInstancesExtraFilters,
          }
        } else {
          params.filters = this.fetchInstancesExtraFilters
        }
      }
      this.fetchingFunction(params)
    },
    updateHeaderFilters(jsonFilter, params) {
      if (this.instanceType) {
        jsonFilter['template.type.term_uid'] = { v: [this.instanceType] }
      }
      return {
        jsonFilter,
        params,
      }
    },
    async openHistory(instance) {
      this.selectedInstance = instance
      const resp = await this.api.getVersions(instance.uid)
      this.historyItems = resp.data
      this.showHistory = true
    },
    async showInstanceStudies(instance) {
      this.selectedInstance = instance
      const resp = await this.api.getStudies(instance.uid)
      this.studies = resp.data
      this.showStudies = true
    },
  },
}
</script>
