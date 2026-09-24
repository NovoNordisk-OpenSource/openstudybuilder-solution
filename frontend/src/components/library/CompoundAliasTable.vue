<template>
  <div>
    <NNTable
      table-id="library-compound-aliases-table"
      :headers="headers"
      :items="compoundAliases"
      :items-length="total"
      item-value="uid"
      density="compact"
      column-data-resource="concepts/compound-aliases"
      :history-config="{
        dataFetcher: fetchGlobalAuditTrail,
        changeField: 'change_description',
        title: $t('_global.audit_trail'),
      }"
      :export-config="{
        objectLabel: 'compound-aliases',
        dataUrl: 'concepts/compound-aliases',
      }"
      @filter="fetchItems"
    >
      <template #actions="">
        <v-btn
          class="ml-2"
          icon
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          :disabled="!checkPermission($roles.LIBRARY_WRITE)"
          @click.stop="showForm = true"
        >
          <v-icon>mdi-plus</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('CompoundAliasForm.add_title') }}
          </v-tooltip>
        </v-btn>
      </template>
      <template #[`item.actions`]="{ item }">
        <ActionsMenu :actions="actions" :item="item" />
      </template>
      <template #[`item.is_preferred_synonym`]="{ item }">
        {{ $filters.yesno(item.is_preferred_synonym) }}
      </template>
      <template #[`item.compound.name`]="{ item }">
        <router-link
          :to="{ name: 'CompoundOverview', params: { id: item.compound.uid } }"
        >
          {{ item.compound.name }}
        </router-link>
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
      <CompoundAliasForm
        :compound-alias-uid="selectedItem ? selectedItem.uid : null"
        :form-shown="showForm"
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
  </div>
</template>

<script>
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import CompoundAliasForm from './CompoundAliasForm.vue'
import compoundAliases from '@/api/concepts/compoundAliases'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import dataFormating from '@/utils/dataFormating'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import { useAccessGuard } from '@/composables/accessGuard'
import filteringParameters from '@/utils/filteringParameters'

export default {
  components: {
    ActionsMenu,
    CompoundAliasForm,
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
      compoundAliases: [],
      filters: {},
      headers: [
        { title: '', key: 'actions', width: '1%' },
        {
          title: this.$t('CompoundAliasTable.compound_name'),
          key: 'compound.name',
        },
        { title: this.$t('CompoundAliasTable.compound_alias'), key: 'name' },
        {
          title: this.$t('_global.sentence_case_name'),
          key: 'name_sentence_case',
        },
        {
          title: this.$t('CompoundAliasTable.is_preferred_synonym'),
          key: 'is_preferred_synonym',
        },
        { title: this.$t('_global.definition'), key: 'definition' },
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
  mounted() {
    this.fetchItems()
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
      compoundAliases.getFiltered(params).then((resp) => {
        this.compoundAliases = resp.data.items
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
      compoundAliases.approve(item.uid).then(() => {
        this.fetchItems()
        this.notificationHub.add({
          msg: this.$t('CompoundAliasTable.approve_success'),
          type: 'success',
        })
      })
    },
    async deleteItem(item) {
      const options = { type: 'warning' }
      const compoundAlias = item.name
      if (
        await this.$refs.confirm.open(
          this.$t('CompoundAliasTable.confirm_delete', { compoundAlias }),
          options
        )
      ) {
        await compoundAliases.deleteObject(item.uid)
        this.fetchItems()
        this.notificationHub.add({
          msg: this.$t('CompoundAliasTable.delete_success'),
          type: 'success',
        })
      }
    },
    createNewVersion(item) {
      compoundAliases.newVersion(item.uid).then(() => {
        this.fetchItems()
        this.notificationHub.add({
          msg: this.$t('CompoundAliasTable.new_version_success'),
          type: 'success',
        })
      })
    },
    inactivateItem(item) {
      compoundAliases.inactivate(item.uid).then(() => {
        this.fetchItems()
        this.notificationHub.add({
          msg: this.$t('CompoundAliasTable.inactivate_success'),
          type: 'success',
        })
      })
    },
    reactivateItem(item) {
      compoundAliases.reactivate(item.uid).then(() => {
        this.fetchItems()
        this.notificationHub.add({
          msg: this.$t('CompoundAliasTable.reactivate_success'),
          type: 'success',
        })
      })
    },
    transformItems(items) {
      const result = []
      for (const item of items) {
        const newItem = { ...item }
        if (newItem.is_preferred_synonym !== undefined) {
          newItem.is_preferred_synonym = dataFormating.yesno(
            newItem.is_preferred_synonym
          )
        }
        result.push(newItem)
      }
      return result
    },
    async openHistory(item) {
      this.selectedItem = item
      const resp = await compoundAliases.getVersions(this.selectedItem.uid)
      this.historyItems = this.transformItems(resp.data)
      this.showHistory = true
    },
    closeHistory() {
      this.showHistory = false
    },
    async fetchGlobalAuditTrail(options) {
      const resp = await compoundAliases.getAllVersions(options)
      return this.transformItems(resp.data.items)
    },
  },
}
</script>
