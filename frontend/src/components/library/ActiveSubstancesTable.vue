<template>
  <NNTable
    table-id="library-active-substances-table"
    :headers="headers"
    :items="formattedActiveSubstances"
    :items-length="total"
    item-value="uid"
    density="compact"
    column-data-resource="concepts/active-substances"
    :history-config="{
      dataFetcher: fetchGlobalAuditTrail,
      changeField: 'change_description',
      title: $t('_global.audit_trail'),
    }"
    :export-config="{
      objectLabel: 'active-substances',
      dataUrl: 'concepts/active-substances',
    }"
    @filter="fetchItems"
  >
    <template #actions="">
      <v-btn
        color="nnBaseBlue"
        :disabled="!checkPermission($roles.LIBRARY_WRITE)"
        variant="outlined"
        icon
        size="small"
        @click.stop="showForm = true"
      >
        <v-icon>mdi-plus</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ $t('ActiveSubstanceForm.add_title') }}
        </v-tooltip>
      </v-btn>
    </template>
    <template #[`item.actions`]="{ item }">
      <ActionsMenu :actions="actions" :item="item" />
    </template>
    <template #[`item.is_preferred_synonym`]="{ item }">
      {{ $filters.yesno(item.is_preferred_synonym) }}
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
  </NNTable>
  <v-dialog
    v-model="showForm"
    fullscreen
    persistent
    content-class="fullscreen-dialog"
  >
    <ActiveSubstanceForm
      :active-substance-uid="selectedItem ? selectedItem.uid : null"
      :open="showForm"
      @close="closeForm"
      @created="fetchItems"
      @updated="fetchItems"
    />
  </v-dialog>
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
      @close="closeHistory"
    />
  </v-dialog>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
</template>

<script>
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ActiveSubstanceForm from './ActiveSubstanceForm.vue'
import activeSubstances from '@/api/concepts/activeSubstances'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import { useAccessGuard } from '@/composables/accessGuard'
import filteringParameters from '@/utils/filteringParameters'

export default {
  components: {
    ActionsMenu,
    ActiveSubstanceForm,
    ConfirmDialog,
    HistoryTable,
    NNTable,
    StatusChip,
  },
  inject: ['notificationHub'],
  props: {
    tabClickedAt: {
      type: Number,
      default: null,
    },
  },
  setup() {
    const accessGuard = useAccessGuard()
    return {
      ...accessGuard,
    }
  },
  data() {
    return {
      actions: [
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil-outline',
          iconColor: 'primary',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'edit'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.editItem,
        },
        {
          label: this.$t('_global.approve'),
          icon: 'mdi-check-decagram',
          iconColor: 'success',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'approve'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.approveItem,
        },
        {
          label: this.$t('_global.new_version'),
          icon: 'mdi-plus-circle-outline',
          iconColor: 'primary',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'new_version'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.createNewVersion,
        },
        {
          label: this.$t('_global.inactivate'),
          icon: 'mdi-close-octagon-outline',
          iconColor: 'primary',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'inactivate'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.inactivateItem,
        },
        {
          label: this.$t('_global.reactivate'),
          icon: 'mdi-undo-variant',
          iconColor: 'primary',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'reactivate'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.reactivateItem,
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete-outline',
          iconColor: 'error',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'delete'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.deleteItem,
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openHistory,
        },
      ],
      activeSubstances: [],
      filters: {},
      headers: [
        { title: '', key: 'actions', width: '5%' },
        {
          title: this.$t('ActiveSubstance.inn'),
          key: 'inn',
        },
        {
          title: this.$t('ActiveSubstance.analyte_number'),
          key: 'analyte_number',
        },
        { title: this.$t('ActiveSubstance.short_number'), key: 'short_number' },
        { title: this.$t('ActiveSubstance.long_number'), key: 'long_number' },
        { title: this.$t('ActiveSubstance.unii'), key: 'unii', noFilter: true },
        {
          title: this.$t('CompoundTable.pharmacological_class'),
          key: 'pclass',
          noFilter: true,
        },
        { title: this.$t('_global.modified'), key: 'start_date' },
        { title: this.$t('_global.version'), key: 'version' },
        { title: this.$t('_global.status'), key: 'status' },
      ],
      historyItems: [],
      options: {},
      selectedItem: null,
      showForm: false,
      showHistory: false,
      total: 0,
    }
  },
  computed: {
    historyTitle() {
      if (this.selectedItem) {
        return this.$t('CompoundAliasTable.history_title', {
          compoundAlias: this.selectedItem.uid,
        })
      }
      return ''
    },
    formattedActiveSubstances() {
      return this.transformItems(this.activeSubstances)
    },
  },
  watch: {
    tabClickedAt() {
      this.fetchItems()
    },
    options: {
      handler() {
        this.fetchItems()
      },
      deep: true,
    },
  },
  methods: {
    fetchItems(filters, options, filtersUpdated) {
      if (filters !== undefined) {
        this.filters = filters
      }
      const params = filteringParameters.prepareParameters(
        options,
        this.filters,
        filtersUpdated
      )
      activeSubstances.getFiltered(params).then((resp) => {
        this.activeSubstances = resp.data.items
        this.total = resp.data.total
      })
    },
    closeForm() {
      this.showForm = false
      this.selectedItem = null
    },
    editItem(item) {
      this.selectedItem = item
      this.showForm = true
    },
    approveItem(item) {
      activeSubstances.approve(item.uid).then(() => {
        this.fetchItems()
        this.notificationHub.add({
          msg: this.$t('ActiveSubstanceTable.approve_success'),
          type: 'success',
        })
      })
    },
    async deleteItem(item) {
      const options = { type: 'warning' }
      const compoundAlias = item.name
      if (
        await this.$refs.confirm.open(
          this.$t('ActiveSubstanceTable.confirm_delete', { compoundAlias }),
          options
        )
      ) {
        await activeSubstances.deleteObject(item.uid)
        this.fetchItems()
        this.notificationHub.add({
          msg: this.$t('ActiveSubstanceTable.delete_success'),
          type: 'success',
        })
      }
    },
    createNewVersion(item) {
      activeSubstances.newVersion(item.uid).then(() => {
        this.fetchItems()
        this.notificationHub.add({
          msg: this.$t('ActiveSubstanceTable.new_version_success'),
          type: 'success',
        })
      })
    },
    inactivateItem(item) {
      activeSubstances.inactivate(item.uid).then(() => {
        this.fetchItems()
        this.notificationHub.add({
          msg: this.$t('ActiveSubstanceTable.inactivate_success'),
          type: 'success',
        })
      })
    },
    reactivateItem(item) {
      activeSubstances.reactivate(item.uid).then(() => {
        this.fetchItems()
        this.notificationHub.add({
          msg: this.$t('ActiveSubstanceTable.reactivate_success'),
          type: 'success',
        })
      })
    },
    async openHistory(item) {
      this.selectedItem = item
      const resp = await activeSubstances.getVersions(this.selectedItem.uid)
      this.historyItems = this.transformItems(resp.data)
      this.showHistory = true
    },
    closeHistory() {
      this.showHistory = false
    },
    transformItems(items) {
      const result = []
      for (const item of items) {
        const newItem = { ...item }
        newItem.unii = item.unii?.substance_unii
          ? item.unii?.substance_unii
          : '-'
        newItem.pclass = item.unii?.pclass_id
          ? `${item.unii?.pclass_name} (${item.unii?.pclass_id})`
          : '-'
        result.push(newItem)
      }
      return result
    },
    async fetchGlobalAuditTrail(options) {
      const resp = await activeSubstances.getAllVersions(options)
      return this.transformItems(resp.data.items)
    },
  },
}
</script>
