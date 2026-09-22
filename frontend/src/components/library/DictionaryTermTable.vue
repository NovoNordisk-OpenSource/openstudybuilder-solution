<template>
  <NNTable
    table-id="library-dictionary-terms-table"
    :headers="actualHeaders"
    item-value="term_uid"
    :items-length="total"
    :items="items"
    :column-data-resource="columnDataResource"
    :codelist-uid="codelistUid"
    :export-config="{
      dataUrlParams: exportUrlParams,
      objectLabel: dictionaryName,
      dataUrl: columnDataResource,
    }"
    @filter="fetchTerms"
  >
    <template #actions="">
      <v-btn
        class="ml-2"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        :disabled="!checkPermission($roles.LIBRARY_WRITE)"
        @click="createTerm()"
      >
        <v-icon>mdi-plus</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ $t('DictionaryTermTable.add_title') }}
        </v-tooltip>
      </v-btn>
    </template>
    <template #[`item.status`]="{ item }">
      <StatusChip :status="item.status" />
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
    <template #[`item.actions`]="{ item }">
      <ActionsMenu :actions="actions" :item="item" />
    </template>
  </NNTable>
  <slot
    name="termForm"
    :close-form="closeForm"
    :open="showTermForm"
    :edited-term="formToEdit"
  >
    <DictionaryTermForm
      :open="showTermForm"
      :dictionary-name="dictionaryName"
      :edited-term="formToEdit"
      :edited-term-category="codelistUid"
      @close="closeForm"
      @save="fetchTerms"
    />
  </slot>
</template>

<script>
import dictionaries from '@/api/dictionaries'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import DictionaryTermForm from '@/components/library/DictionaryTermForm.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import filteringParameters from '@/utils/filteringParameters'
import { useAccessGuard } from '@/composables/accessGuard'

export default {
  components: {
    ActionsMenu,
    DictionaryTermForm,
    NNTable,
    StatusChip,
  },
  props: {
    codelistUid: {
      type: String,
      default: null,
    },
    columnDataResource: {
      type: String,
      default: null,
    },
    dictionaryName: {
      type: String,
      default: null,
    },
    headers: {
      type: Array,
      default: null,
      required: false,
    },
  },
  setup() {
    return {
      ...useAccessGuard(),
    }
  },
  data() {
    return {
      actions: [
        {
          label: this.$t('_global.approve'),
          icon: 'mdi-check-decagram',
          iconColor: 'success',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'approve'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.approveTerm,
        },
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil-outline',
          iconColor: 'primary',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'edit'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.editTerm,
        },
        {
          label: this.$t('_global.new_version'),
          icon: 'mdi-plus-circle-outline',
          iconColor: 'primary',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'new_version'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.newTermVersion,
        },
        {
          label: this.$t('_global.inactivate'),
          icon: 'mdi-close-octagon-outline',
          iconColor: 'primary',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'inactivate'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.inactivateTerm,
        },
        {
          label: this.$t('_global.reactivate'),
          icon: 'mdi-undo-variant',
          iconColor: 'primary',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'reactivate'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.reactivateTerm,
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete-outline',
          iconColor: 'error',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'delete'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.deleteTerm,
        },
      ],
      defaultHeaders: [
        { title: '', key: 'actions', width: '1%' },
        { title: this.dictionaryName, key: 'dictionary_id' },
        { title: this.$t('_global.name'), key: 'name' },
        {
          title: this.$t('DictionaryTermTable.lower_case_name'),
          key: 'name_sentence_case',
        },
        {
          title: this.$t('DictionaryTermTable.abbreviation'),
          key: 'abbreviation',
        },
        { title: this.$t('_global.status'), key: 'status' },
        { title: this.$t('_global.version'), key: 'version' },
        { title: this.$t('_global.modified'), key: 'start_date' },
      ],
      total: 0,
      items: [],
      showTermForm: false,
      formToEdit: {},
    }
  },
  computed: {
    actualHeaders() {
      return this.headers ? this.headers : this.defaultHeaders
    },
    exportUrlParams() {
      return { codelist_uid: this.codelistUid }
    },
  },
  methods: {
    fetchTerms(filters, options, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      params.codelist_uid = this.codelistUid
      if (params.codelist_uid !== null) {
        dictionaries.getTerms(params).then((resp) => {
          this.items = resp.data.items
          this.total = resp.data.total
        })
      }
    },
    inactivateTerm(item) {
      dictionaries.inactivate(item.term_uid).then(() => {
        this.fetchTerms()
      })
    },
    reactivateTerm(item) {
      dictionaries.reactivate(item.term_uid).then(() => {
        this.fetchTerms()
      })
    },
    deleteTerm(item) {
      dictionaries.delete(item.term_uid).then(() => {
        this.fetchTerms()
      })
    },
    approveTerm(item) {
      dictionaries.approve(item.term_uid).then(() => {
        this.fetchTerms()
      })
    },
    newTermVersion(item) {
      dictionaries.newVersion(item.term_uid).then(() => {
        this.fetchTerms()
      })
    },
    editTerm(item) {
      this.formToEdit = item
      this.showTermForm = true
    },
    createTerm() {
      this.formToEdit = null
      this.showTermForm = true
    },
    closeForm() {
      this.formToEdit = null
      this.showTermForm = false
    },
  },
}
</script>
