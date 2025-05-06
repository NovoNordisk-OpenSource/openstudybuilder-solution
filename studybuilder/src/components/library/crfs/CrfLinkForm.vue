<template>
  <SimpleFormDialog
    ref="form"
    :title="$t('CrfTree.link') + ' ' + itemsTypeName"
    :help-items="helpItems"
    :open="open"
    max-width="1200px"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-col class="pt-0 mt-0">
        <NNTable
          :headers="availableItemsHeaders"
          item-value="uid"
          :items="items"
          hide-export-button
          hide-default-switches
          only-text-search
          column-data-resource="ct/codelists"
          :items-length="total"
          table-height="auto"
          @filter="getItems"
        >
          <template #[`item.desc`]="{ item }">
            <div v-html="getDescription(item)" />
          </template>
          <template #[`item.notes`]="{ item }">
            <div v-html="getNotes(item)" />
          </template>
          <template #[`item.add`]="{ item }">
            <v-btn
              v-if="!checkIfLinked(item)"
              icon="mdi-content-copy"
              class="mt-1 rightButtons"
              data-cy="add-item-link"
              variant="text"
              @click="addItem(item)"
            />
            <v-btn
              v-else
              icon="mdi-delete-outline"
              class="mt-1 rightButtons"
              color="error"
              data-cy="remove-item-link"
              variant="text"
              @click="removeItem(item)"
            />
          </template>
        </NNTable>
      </v-col>
    </template>
  </SimpleFormDialog>
</template>

<script>
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import crfs from '@/api/crfs'
import constants from '@/constants/parameters'
import NNTable from '@/components/tools/NNTable.vue'
import filteringParameters from '@/utils/filteringParameters'

export default {
  components: {
    SimpleFormDialog,
    NNTable,
  },
  props: {
    itemToLink: {
      type: Object,
      default: null,
    },
    itemsType: {
      type: String,
      default: null,
    },
    open: Boolean,
  },
  emits: ['close'],
  data() {
    return {
      helpItems: [],
      items: [],
      choosenItems: [],
      availableItemsHeaders: [
        { title: '', key: 'add', width: '5%' },
        { title: this.$t('_global.name'), key: 'name', width: '25%' },
        { title: this.$t('_global.description'), key: 'desc', width: '35%' },
        { title: this.$t('CrfTree.impl_notes'), key: 'notes', width: '35%' },
      ],
      total: 0,
    }
  },
  computed: {
    itemsTypeName() {
      return this.itemsType === 'forms'
        ? this.$t('CrfTree.forms')
        : this.itemsType === 'item-groups'
          ? this.$t('CrfTree.item_groups')
          : this.$t('CrfTree.items')
    },
  },
  watch: {
    itemToLink() {
      this.initForm()
    },
  },
  mounted() {
    this.initForm()
  },
  methods: {
    getDescription(item) {
      const engDesc = item.descriptions.find(
        (el) => el.language === constants.ENG
      )
      return engDesc ? engDesc.description : ''
    },
    getNotes(item) {
      const engDesc = item.descriptions.find(
        (el) => el.language === constants.ENG
      )
      return engDesc ? engDesc.sponsor_instruction : ''
    },
    submit() {
      const payload = []
      this.choosenItems.forEach((el, index) => {
        payload.push({
          uid: el.uid ? el.uid : el,
          order_number: index + 1,
          mandatory: el.mandatory ? el.mandatory : 'No',
          data_entry_required: el.data_entry_required
            ? el.data_entry_required
            : 'No',
          sdv: el.sdv ? el.sdv : 'No',
          collection_exception_condition_oid:
            el.collection_exception_condition_oid
              ? el.collection_exception_condition_oid
              : null,
          vendor: { attributes: [] },
        })
      })
      switch (this.itemsType) {
        case 'forms':
          crfs
            .addFormsToTemplate(payload, this.itemToLink.uid, true)
            .then(() => {
              this.$emit('close')
            })
          return
        case 'item-groups':
          crfs
            .addItemGroupsToForm(payload, this.itemToLink.uid, true)
            .then(() => {
              this.$emit('close')
            })
          return
        case 'items':
          payload.forEach((el) => {
            el.key_sequence = el.key_sequence ? el.key_sequence : constants.NULL
            el.method_oid = el.method_oid ? el.method_oid : constants.NULL
            el.imputation_method_oid = el.imputation_method_oid
              ? el.imputation_method_oid
              : constants.NULL
            el.role = el.role ? el.role : constants.NULL
            el.role_codelist_oid = el.role_codelist_oid
              ? el.role_codelist_oid
              : constants.NULL
          })
          crfs
            .addItemsToItemGroup(payload, this.itemToLink.uid, true)
            .then(() => {
              this.$emit('close')
            })
      }
    },
    addItem(item) {
      if (!this.choosenItems.some((el) => el.uid === item.uid)) {
        this.choosenItems.push(item)
      }
    },
    checkIfLinked(item) {
      return this.choosenItems.some((el) => el.uid === item.uid)
    },
    removeItem(item) {
      this.choosenItems = this.choosenItems.filter((el) => el.uid !== item.uid)
    },
    close() {
      this.form = {}
      this.choosenItems = []
      this.items = []
      this.$emit('close')
    },
    initForm() {
      this.choosenItems = Array.from(
        new Set(
          this.itemToLink.forms ||
            this.itemToLink.item_groups ||
            this.itemToLink.items
        )
      )
      this.getItems()
    },
    getItems(filters, options, filtersUpdated) {
      if (this.itemsType) {
        const parameters = filteringParameters.prepareParameters(
          options,
          filters,
          filtersUpdated
        )
        if (filters) {
          parameters.filters = JSON.parse(filters)
        }
        const params = {}
        params.params = parameters
        crfs.get(this.itemsType, params).then((resp) => {
          this.items = resp.data.items
          this.total = resp.data.total
        })
      }
    },
  },
}
</script>
<style scoped>
.rightButtons {
  float: right;
}
</style>
