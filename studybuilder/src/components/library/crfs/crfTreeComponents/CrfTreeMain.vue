<template>
  <v-row>
    <v-switch
      v-model="sortMode"
      class="ml-6 mt-4"
      :label="$t('CrfTree.reorder')"
    />
  </v-row>
  <v-data-table-server
    ref="mainTable"
    v-model:expanded="expanded"
    :headers="headers"
    item-value="name"
    :items-length="totalTemplates"
    :items="templates"
    @update:options="getTemplates"
  >
    <template #headers="{ columns }">
      <tr class="header">
        <template v-for="column in columns" :key="column.key">
          <td>
            <span>{{ column.title }}</span>
          </td>
        </template>
      </tr>
    </template>
    <template #item="{ item, internalItem, toggleExpand, isExpanded }">
      <tr style="background-color: rgb(var(--v-theme-dfltBackgroundLight1))">
        <td width="45%" :class="'font-weight-bold'">
          <v-row class="align-center">
            <v-btn
              v-if="isExpanded(internalItem)"
              icon="mdi-chevron-down"
              variant="text"
              @click="toggleExpand(internalItem)"
            />
            <v-btn
              v-else-if="item.forms.length > 0"
              icon="mdi-chevron-right"
              variant="text"
              @click="toggleExpand(internalItem)"
            />
            <v-btn v-else variant="text" class="hide" icon />
            <ActionsMenu :actions="actions" :item="item" />
            <span class="ml-2">
              <v-icon color="crfTemplate"> mdi-alpha-t-circle-outline </v-icon>
              {{ item.name }}
            </span>
          </v-row>
        </td>
        <td width="10%" />
        <td width="10%" />
        <td width="10%">
          <StatusChip :status="item.status" />
        </td>
        <td width="10%">
          {{ item.version }}
        </td>
        <td width="15%">
          <v-menu v-if="item.status !== statuses.FINAL" offset-y>
            <template #activator="{ props }">
              <div>
                <v-btn
                  v-show="item.status !== statuses.FINAL"
                  width="150px"
                  size="small"
                  rounded
                  v-bind="props"
                  color="crfForm"
                  :title="$t('CrfTree.link_forms')"
                >
                  <v-icon icon="mdi-plus" />
                  {{ $t('CrfTree.forms') }}
                </v-btn>
              </div>
            </template>
            <v-list>
              <v-list-item @click="openLinkForm(item)">
                <template #prepend>
                  <v-icon icon="mdi-plus" />
                </template>
                <v-list-item-title>
                  {{ $t('CrfTree.link_existing') }}
                </v-list-item-title>
              </v-list-item>
              <v-list-item @click="openCreateAndAddForm(item)">
                <template #prepend>
                  <v-icon icon="mdi-pencil-outline" />
                </template>
                <v-list-item-title>
                  {{ $t('CrfTree.create_and_link') }}
                </v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
          <v-btn v-else width="150px" rounded size="small" class="hide" />
        </td>
      </tr>
    </template>
    <template #expanded-row="{ columns, item }">
      <CrfTreeForms
        :sort-mode="sortMode"
        :parent-template="item"
        :columns="columns"
        :refresh-forms="refreshForms"
        :expand-forms-for-template="expandFormsForTemplate"
      />
    </template>
  </v-data-table-server>
  <CrfTemplateForm
    :open="showTemplateForm"
    :selected-template="selectedTemplate"
    :read-only-prop="
      selectedTemplate && selectedTemplate.status === statuses.FINAL
    "
    @close="closeDefinition"
  />
  <CrfLinkForm
    :open="showLinkForm"
    :item-to-link="selectedTemplate"
    items-type="forms"
    @close="closeLinkForm"
  />
  <v-dialog
    v-model="showExportForm"
    max-width="800px"
    persistent
    @keydown.esc="closeExportForm"
  >
    <CrfExportForm
      :item="selectedTemplate"
      type="study_event"
      @close="closeExportForm"
    />
  </v-dialog>
  <v-dialog
    v-model="showCreateForm"
    persistent
    content-class="fullscreen-dialog"
  >
    <CrfFormForm
      class="fullscreen-dialog"
      @close="closeCreateAndAddForm"
      @link-form="linkForm"
    />
  </v-dialog>
</template>

<script>
import crfs from '@/api/crfs'
import CrfTreeForms from '@/components/library/crfs/crfTreeComponents/CrfTreeForms.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import statuses from '@/constants/statuses'
import CrfLinkForm from '@/components/library/crfs/CrfLinkForm.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import CrfTemplateForm from '@/components/library/crfs/CrfTemplateForm.vue'
import CrfExportForm from '@/components/library/crfs/CrfExportForm.vue'
import crfTypes from '@/constants/crfTypes'
import CrfFormForm from '@/components/library/crfs/CrfFormForm.vue'
import filteringParameters from '@/utils/filteringParameters'

export default {
  components: {
    CrfTreeForms,
    StatusChip,
    CrfLinkForm,
    ActionsMenu,
    CrfTemplateForm,
    CrfExportForm,
    CrfFormForm,
  },
  data() {
    return {
      headers: [
        { title: this.$t('CrfTree.items_for_linking'), key: 'name' },
        { title: this.$t('CrfTree.ref_attr'), key: 'refAttr' },
        { title: this.$t('CrfTree.def_attr'), key: 'defAttr' },
        { title: this.$t('_global.status'), key: 'status' },
        { title: this.$t('_global.version'), key: 'version' },
        { title: this.$t('CrfTree.link'), key: 'link' },
      ],
      actions: [
        {
          label: this.$t('CrfTree.open_def'),
          icon: 'mdi-arrow-left',
          click: this.openDefinition,
        },
        {
          label: this.$t('CrfTree.preview_odm'),
          icon: 'mdi-file-xml-box',
          click: this.previewODM,
        },
        {
          label: this.$t('_global.export'),
          icon: 'mdi-download-outline',
          click: this.openExportForm,
        },
        {
          label: this.$t('CrfTree.approve_all'),
          icon: 'mdi-check-decagram',
          click: this.approveAll,
          accessRole: this.$roles.LIBRARY_WRITE,
        },
        {
          label: this.$t('CrfTree.expand'),
          icon: 'mdi-arrow-expand-down',
          condition: (item) => item.forms.length > 0,
          click: this.expandAll,
        },
      ],
      showLinkForm: false,
      showTemplateForm: false,
      selectedTemplate: {},
      refreshForms: 0,
      expanded: [],
      expandFormsForTemplate: '',
      showExportForm: false,
      showCreateForm: false,
      sortMode: false,
      templates: [],
      totalTemplates: 0,
    }
  },
  created() {
    this.statuses = statuses
  },
  mounted() {
    this.getTemplates()
  },
  methods: {
    async getTemplates(options) {
      const params = filteringParameters.prepareParameters(options, null, null)
      if (!params) {
        params.total_count = true
      }
      return crfs.get('study-events', { params }).then((resp) => {
        this.templates = resp.data.items
        this.totalTemplates = resp.data.total
      })
    },
    openCreateAndAddForm(item) {
      this.selectedTemplate = item
      this.showCreateForm = true
    },
    closeCreateAndAddForm() {
      this.showCreateForm = false
      this.selectedTemplate = {}
    },
    linkForm(form) {
      const payload = [
        {
          uid: form.data.uid,
          order_number: this.selectedTemplate.forms.length,
          mandatory: false,
          collection_exception_condition_oid: null,
        },
      ]
      crfs
        .addFormsToTemplate(payload, this.selectedTemplate.uid, false)
        .then(() => {
          this.getTemplates().then(() => {
            this.refreshForms += 1
          })
        })
    },
    openDefinition(item) {
      this.selectedTemplate = item
      this.showTemplateForm = true
    },
    closeDefinition() {
      this.selectedTemplate = {}
      this.showTemplateForm = false
      this.getTemplates()
    },
    openLinkForm(item) {
      this.selectedTemplate = item
      this.showLinkForm = true
    },
    async closeLinkForm() {
      this.showLinkForm = false
      this.selectedTemplate = {}
      await this.getTemplates()
      this.refreshForms += 1
    },
    async expandAll(item) {
      await this.expanded.push(item.name)
      this.expandFormsForTemplate = item.uid
    },
    openExportForm(item) {
      this.selectedTemplate = item
      this.showExportForm = true
    },
    closeExportForm() {
      this.selectedTemplate = {}
      this.showExportForm = false
    },
    previewODM(item) {
      this.$router.push({
        name: 'Crfs',
        params: {
          tab: 'odm-viewer',
          uid: item.uid,
          type: crfTypes.STUDY_EVENT,
        },
      })
    },
    async approveAll(item) {
      this.expanded = this.expanded.filter((e) => e !== item.name)
      if (item.status === statuses.DRAFT) {
        item.status = statuses.FINAL
        await crfs.approve('study-events', item.uid)
      }
      let forms = []
      let params = {
        total_count: true,
        filters: JSON.stringify({
          uid: { v: item.forms.map((form) => form.uid) },
        }),
        page_size: 0,
      }
      await crfs.get('forms', { params }).then((resp) => {
        forms = resp.data.items
        for (const form of forms) {
          if (form.status === statuses.DRAFT) {
            crfs.approve('forms', form.uid)
          }
        }
      })
      let groups = []
      forms.forEach((form) => {
        groups.push(form.item_groups.map((group) => group.uid))
      })
      params.filters = JSON.stringify({ uid: { v: groups.flat(1) } })
      await crfs.get('item-groups', { params }).then((resp) => {
        groups = resp.data.items
        for (const group of groups) {
          if (group.status === statuses.DRAFT) {
            crfs.approve('item-groups', group.uid)
          }
        }
      })
      let items = []
      groups.forEach((group) => {
        items.push(group.items.map((item) => item.uid))
      })
      params.filters = JSON.stringify({ uid: { v: items.flat(1) } })
      await crfs.get('items', { params }).then((resp) => {
        items = resp.data.items
        for (const item of items) {
          if (item.status === statuses.DRAFT) {
            crfs.approve('items', item.uid)
          }
        }
      })
      this.expandAll(item)
    },
  },
}
</script>
<style>
.hide {
  opacity: 0;
}
.header {
  background-color: rgb(var(--v-theme-tableGray)) !important;
  color: rgba(26, 26, 26, 0.6) !important;
  text-align: start;
  font-weight: 500;
  font-size: 14px;
}
</style>
