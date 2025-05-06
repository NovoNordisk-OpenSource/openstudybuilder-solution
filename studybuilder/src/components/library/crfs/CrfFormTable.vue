<template>
  <div>
    <NNTable
      ref="table"
      :headers="headers"
      :items="forms"
      item-value="uid"
      :items-length="total"
      column-data-resource="concepts/odms/forms"
      export-data-url="concepts/odms/forms"
      export-object-label="CRFForms"
      @filter="getForms"
    >
      <template #actions="">
        <v-btn
          class="ml-2"
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          :title="$t('CRFForms.add_form')"
          data-cy="add-crf-form"
          :disabled="!checkPermission($roles.LIBRARY_WRITE)"
          icon="mdi-plus"
          @click.stop="openForm"
        />
      </template>
      <template #[`item.name`]="{ item }">
        <v-tooltip bottom>
          <template #activator="{ props }">
            <div v-bind="props">
              {{
                item.name.length > 40
                  ? item.name.substring(0, 40) + '...'
                  : item.name
              }}
            </div>
          </template>
          <span>{{ item.name }}</span>
        </v-tooltip>
      </template>
      <template #[`item.description`]="{ item }">
        <v-tooltip bottom>
          <template #activator="{ props }">
            <div v-bind="props" v-html="getDescription(item, true)" />
          </template>
          <span>{{ getDescription(item, false) }}</span>
        </v-tooltip>
      </template>
      <template #[`item.notes`]="{ item }">
        <v-tooltip bottom>
          <template #activator="{ props }">
            <div v-bind="props" v-html="getNotes(item, true)" />
          </template>
          <span>{{ getNotes(item, false) }}</span>
        </v-tooltip>
      </template>
      <template #[`item.repeating`]="{ item }">
        {{ item.repeating }}
      </template>
      <template #[`item.activity_groups`]="{ item }">
        <v-tooltip bottom>
          <template #activator="{ props }">
            <div v-bind="props">
              {{
                item.activity_groups[0]
                  ? item.activity_groups.length > 1
                    ? item.activity_groups[0].name + '...'
                    : item.activity_groups[0].name
                  : ''
              }}
            </div>
          </template>
          <span>{{ $filters.names(item.activity_groups) }}</span>
        </v-tooltip>
      </template>
      <template #[`item.status`]="{ item }">
        <StatusChip :status="item.status" />
      </template>
      <template #[`item.actions`]="{ item }">
        <ActionsMenu :actions="actions" :item="item" />
      </template>
    </NNTable>
    <v-dialog v-model="showForm" persistent content-class="fullscreen-dialog">
      <CrfFormForm
        :selected-form="selectedForm"
        class="fullscreen-dialog"
        :read-only-prop="selectedForm && selectedForm.status === statuses.FINAL"
        @close="closeForm"
        @approve="approve"
      />
    </v-dialog>
    <v-dialog
      v-model="showFormHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeFormHistory"
    >
      <HistoryTable
        :title="formHistoryTitle"
        :headers="headers"
        :items="formHistoryItems"
        @close="closeFormHistory"
      />
    </v-dialog>
    <CrfActivitiesModelsLinkForm
      :open="linkForm"
      :item-to-link="selectedForm"
      item-type="form"
      @close="closeLinkForm"
    />
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  </div>
</template>

<script>
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import crfs from '@/api/crfs'
import CrfFormForm from '@/components/library/crfs/CrfFormForm.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import CrfActivitiesModelsLinkForm from '@/components/library/crfs/CrfActivitiesModelsLinkForm.vue'
import statuses from '@/constants/statuses'
import filteringParameters from '@/utils/filteringParameters'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import crfTypes from '@/constants/crfTypes'
import parameters from '@/constants/parameters'
import dataFormating from '@/utils/dataFormating'
import { useAccessGuard } from '@/composables/accessGuard'
import { useCrfsStore } from '@/stores/crfs'
import { computed } from 'vue'

export default {
  components: {
    NNTable,
    StatusChip,
    ActionsMenu,
    CrfFormForm,
    HistoryTable,
    CrfActivitiesModelsLinkForm,
    ConfirmDialog,
  },
  props: {
    elementProp: {
      type: Object,
      default: null,
    },
  },
  emits: ['updateForm', 'clearUid'],
  setup() {
    const crfsStore = useCrfsStore()

    return {
      fetchForms: crfsStore.fetchForms,
      total: computed(() => crfsStore.totalForms),
      forms: computed(() => crfsStore.forms),
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
          click: this.approve,
        },
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil-outline',
          iconColor: 'primary',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'edit'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.edit,
        },
        {
          label: this.$t('_global.view'),
          icon: 'mdi-eye-outline',
          iconColor: 'primary',
          condition: (item) => item.status === statuses.FINAL,
          click: this.view,
        },
        {
          label: this.$t('_global.new_version'),
          icon: 'mdi-plus-circle-outline',
          iconColor: 'primary',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'new_version'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.newVersion,
        },
        {
          label: this.$t('_global.inactivate'),
          icon: 'mdi-close-octagon-outline',
          iconColor: 'primary',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'inactivate'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.inactivate,
        },
        {
          label: this.$t('_global.reactivate'),
          icon: 'mdi-undo-variant',
          iconColor: 'primary',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'reactivate'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.reactivate,
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete-outline',
          iconColor: 'error',
          condition: (item) =>
            item.possible_actions.find((action) => action === 'delete'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.delete,
        },
        {
          label: this.$t('CrfLinikingForm.link_activity_groups'),
          icon: 'mdi-plus',
          iconColor: 'primary',
          condition: (item) => item.status === statuses.DRAFT,
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.openLinkForm,
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openFormHistory,
        },
      ],
      headers: [
        { title: '', key: 'actions', width: '1%' },
        { title: this.$t('CRFForms.oid'), key: 'oid' },
        { title: this.$t('_global.name'), key: 'name' },
        {
          title: this.$t('_global.description'),
          key: 'description',
          filteringName: 'descriptions.description',
        },
        {
          title: this.$t('CRFItems.impl_notes'),
          key: 'notes',
          filteringName: 'descriptions.sponsor_instruction',
        },
        {
          title: this.$t('CrfFormTable.repeating'),
          key: 'repeating',
          width: '1%',
        },
        {
          title: this.$t('_global.links'),
          key: 'activity_groups',
          filteringName: 'activity_groups.name',
        },
        { title: this.$t('_global.version'), key: 'version', width: '1%' },
        { title: this.$t('_global.status'), key: 'status', width: '1%' },
      ],
      showForm: false,
      showHistory: false,
      selectedForm: null,
      filters: '',
      showFormHistory: false,
      linkForm: false,
      formHistoryItems: [],
    }
  },
  computed: {
    formHistoryTitle() {
      if (this.selectedForm) {
        return this.$t('CrfFormTable.form_history_title', {
          formUid: this.selectedForm.uid,
        })
      }
      return ''
    },
  },
  watch: {
    elementProp(value) {
      if (value.tab === 'forms' && value.type === crfTypes.FORM && value.uid) {
        this.edit({ uid: value.uid })
      }
    },
  },
  mounted() {
    if (
      this.elementProp.tab === 'forms' &&
      this.elementProp.type === crfTypes.FORM &&
      this.elementProp.uid
    ) {
      this.edit({ uid: this.elementProp.uid })
    }
  },
  created() {
    this.statuses = statuses
  },
  methods: {
    getDescription(item, short) {
      const engDesc = item.descriptions.find(
        (el) => el.language === parameters.ENG
      )
      if (engDesc && engDesc.description) {
        return short
          ? engDesc.description.length > 40
            ? engDesc.description.substring(0, 40) + '...'
            : engDesc.description
          : engDesc.description
      }
      return ''
    },
    getNotes(item, short) {
      const engDesc = item.descriptions.find(
        (el) => el.language === parameters.ENG
      )
      if (engDesc && engDesc.sponsor_instruction) {
        return short
          ? engDesc.sponsor_instruction.length > 40
            ? engDesc.sponsor_instruction.substring(0, 40) + '...'
            : engDesc.sponsor_instruction
          : engDesc.sponsor_instruction
      }
      return ''
    },
    async delete(item) {
      let relationships = 0
      await crfs.getRelationships(item.uid, 'forms').then((resp) => {
        if (resp.data.OdmTemplate && resp.data.OdmTemplate.length > 0) {
          relationships = resp.data.OdmTemplate.length
        }
      })
      const options = {
        type: 'warning',
        cancelLabel: this.$t('_global.cancel'),
        agreeLabel: this.$t('_global.continue'),
      }
      if (
        relationships > 0 &&
        (await this.$refs.confirm.open(
          `${this.$t('CRFForms.delete_warning_1')} ${relationships} ${this.$t('CRFForms.delete_warning_2')}`,
          options
        ))
      ) {
        crfs.delete('forms', item.uid).then(() => {
          this.$refs.table.filterTable()
        })
      } else if (relationships === 0) {
        crfs.delete('forms', item.uid).then(() => {
          this.$refs.table.filterTable()
        })
      }
    },
    approve(item) {
      crfs.approve('forms', item.uid).then((resp) => {
        this.$emit('updateForm', { type: crfTypes.FORM, element: resp.data })
        this.$refs.table.filterTable()
      })
    },
    inactivate(item) {
      crfs.inactivate('forms', item.uid).then((resp) => {
        this.$emit('updateForm', { type: crfTypes.FORM, element: resp.data })
        this.$refs.table.filterTable()
      })
    },
    reactivate(item) {
      crfs.reactivate('forms', item.uid).then((resp) => {
        this.$emit('updateForm', { type: crfTypes.FORM, element: resp.data })
        this.$refs.table.filterTable()
      })
    },
    async newVersion(item) {
      let relationships = 0
      await crfs.getRelationships(item.uid, 'forms').then((resp) => {
        if (resp.data.OdmTemplate && resp.data.OdmTemplate.length > 0) {
          relationships = resp.data.OdmTemplate.length
        }
      })
      const options = {
        type: 'warning',
        cancelLabel: this.$t('_global.cancel'),
        agreeLabel: this.$t('_global.continue'),
      }
      if (
        relationships > 1 &&
        (await this.$refs.confirm.open(
          `${this.$t('CRFForms.new_version_warning')}`,
          options
        ))
      ) {
        crfs.newVersion('forms', item.uid).then((resp) => {
          this.$emit('updateForm', { type: crfTypes.FORM, element: resp.data })
          this.$refs.table.filterTable()
        })
      } else if (relationships <= 1) {
        crfs.newVersion('forms', item.uid).then((resp) => {
          this.$emit('updateForm', { type: crfTypes.FORM, element: resp.data })
          this.$refs.table.filterTable()
        })
      }
    },
    edit(item) {
      crfs.getForm(item.uid).then((resp) => {
        this.selectedForm = resp.data
        this.showForm = true
        this.$emit('clearUid')
      })
    },
    view(item) {
      crfs.getForm(item.uid).then((resp) => {
        this.selectedForm = resp.data
        this.showForm = true
      })
    },
    openForm() {
      this.selectedForm = null
      this.showForm = true
    },
    async closeForm() {
      this.showForm = false
      this.selectedForm = null
      this.$refs.table.filterTable()
    },
    async openFormHistory(form) {
      this.selectedForm = form
      const resp = await crfs.getFormAuditTrail(form.uid)
      this.formHistoryItems = this.transformItems(resp.data)
      this.showFormHistory = true
    },
    closeFormHistory() {
      this.selectedForm = null
      this.showFormHistory = false
    },
    transformItems(items) {
      const result = []
      for (const item of items) {
        const newItem = { ...item }
        if (newItem.activity_groups) {
          newItem.activity_groups = dataFormating.names(newItem.activity_groups)
        } else {
          newItem.activity_groups = ''
        }
        result.push(newItem)
      }
      return result
    },
    openLinkForm(item) {
      this.selectedForm = item
      this.linkForm = true
    },
    closeLinkForm() {
      this.linkForm = false
      this.selectedForm = null
      this.$refs.table.filterTable()
    },
    async getForms(filters, options, filtersUpdated) {
      if (filters) {
        this.filters = filters
      }
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      this.fetchForms(params)
    },
  },
}
</script>
