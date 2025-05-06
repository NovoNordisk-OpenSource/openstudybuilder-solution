<template>
  <div>
    <SimpleFormDialog
      ref="form"
      :title="title"
      :open="open"
      max-width="1200px"
      no-saving
      @close="cancel"
    >
      <template #body>
        <NNTable
          :headers="headers"
          item-value="uid"
          :items-length="total"
          :items="elements"
          table-height="auto"
          hide-default-switches
          light
          disable-filtering
          hide-export-button
          :modifiable-table="false"
        >
          <template #item="{ item, internalItem, toggleExpand, isExpanded }">
            <tr :class="item.type ? '' : 'elementBackground'">
              <td width="25%">
                <v-row>
                  <v-btn
                    v-if="isExpanded(internalItem)"
                    icon="mdi-chevron-down"
                    variant="text"
                    class="mr-n2"
                    @click="toggleExpand(internalItem)"
                  />
                  <v-btn
                    v-else-if="item.attributes"
                    icon="mdi-chevron-right"
                    variant="text"
                    class="mr-n2"
                    @click="toggleExpand(internalItem)"
                  />
                  <v-btn
                    v-else
                    icon
                    variant="text" 
                    class="mr-n2"
                  />
                  <ActionsMenu :actions="actions" :item="item"/>
                  <div class="mt-3 ml-4">
                    {{
                      item.type
                        ? $t('CrfExtensions.attribute')
                        : $t('CrfExtensions.element')
                    }}
                  </div>
                </v-row>
              </td>
              <td width="25%">
                {{ item.name }}
              </td>
              <td width="25%">
                {{ item.version }}
              </td>
              <td width="25%">
                <StatusChip :status="item.status" />
              </td>
            </tr>
          </template>
          <template #expanded-row="{ columns, item }">
            <td :colspan="columns.length" class="pa-0">
              <v-data-table
                :headers="columns"
                item-value="uid"
                :items-length="total"
                :items="item.attributes"
                hide-default-switches
                disable-filtering
                hide-export-button
                :modifiable-table="false"
                hide-default-footer
                hide-default-header
              >
                <template #headers />
                <template #bottom />
                <template #item="{ item }">
                  <tr style="background-color: #d8eaf8">
                    <td width="25%">
                      <v-row>
                        <v-btn icon variant="text" />
                        <ActionsMenu :actions="actions" :item="item" />
                        <div class="mt-3 ml-4">
                          {{ $t('CrfExtensions.attribute') }}
                        </div>
                      </v-row>
                    </td>
                    <td width="25%">
                      {{ item.name }}
                    </td>
                    <td width="25%">
                      {{ item.version }}
                    </td>
                    <td width="25%">
                      <StatusChip :status="item.status" />
                    </td>
                  </tr>
                </template>
              </v-data-table>
            </td>
          </template>
          <template #actions="">
            <v-btn
              class="ml-2 mb-2"
              dark
              color="crfGroup"
              rounded
              @click="addElement"
            >
              <v-icon dark> mdi-plus </v-icon>
              {{ $t('CrfExtensions.element') }}
            </v-btn>
            <v-btn
              class="ml-2 mb-2"
              dark
              color="crfItem"
              rounded
              @click="addAttribute"
            >
              <v-icon dark> mdi-plus </v-icon>
              {{ $t('CrfExtensions.attribute') }}
            </v-btn>
          </template>
        </NNTable>
      </template>
    </SimpleFormDialog>
    <CrfAttributeForm
      :open="showAttributeForm"
      :edit-item="elementToEdit"
      :parent-uid="parentUid"
      :parent-type="parentType"
      @close="closeAttributeForm"
    />
    <CrfElementForm
      :parent-uid="editItem.uid"
      :open="showElementForm"
      :attributes="attributes"
      :edit-item="elementToEdit"
      @close="closeElementForm"
    />
  </div>
</template>

<script>
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import NNTable from '@/components/tools/NNTable.vue'
import CrfAttributeForm from '@/components/library/crfs/CrfAttributeForm.vue'
import CrfElementForm from '@/components/library/crfs/CrfElementForm.vue'
import crfs from '@/api/crfs'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import constants from '@/constants/statuses'
import StatusChip from '@/components/tools/StatusChip.vue'
import crfTypes from '@/constants/crfTypes'

export default {
  components: {
    SimpleFormDialog,
    NNTable,
    CrfAttributeForm,
    CrfElementForm,
    ActionsMenu,
    StatusChip,
  },
  props: {
    open: Boolean,
    editItem: {
      type: Object,
      default: null,
    },
  },
  emits: ['close'],
  data() {
    return {
      elements: [],
      total: 0,
      headers: [
        { title: this.$t('_global.type'), key: 'type' },
        { title: this.$t('_global.name'), key: 'name' },
        { title: this.$t('_global.version'), key: 'version' },
        { title: this.$t('_global.status'), key: 'status' },
      ],
      showAttributeForm: false,
      showElementForm: false,
      attributes: [],
      actions: [
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil-outline',
          iconColor: 'primary',
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.editElement,
        },
        {
          label: this.$t('CrfExtensions.add_new_attr'),
          icon: 'mdi-plus',
          iconColor: 'primary',
          condition: (item) => !item.type,
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.addAttribute,
        },
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
      ],
      elementToEdit: {},
      parentType: '',
      parentUid: '',
    }
  },
  computed: {
    title() {
      return this.$t('CrfExtensions.extension') + this.editItem.name
    },
  },
  watch: {
    editItem() {
      this.getNamespaceData()
    },
  },
  created() {
    this.constants = constants
  },
  mounted() {
    this.getNamespaceData()
  },
  methods: {
    approve(item) {
      const type =
        item.type === 'attr' ? 'vendor-attributes' : 'vendor-elements'
      crfs.approve(type, item.uid).then(() => {
        this.getNamespaceData()
      })
    },
    inactivate(item) {
      const type =
        item.type === 'attr' ? 'vendor-attributes' : 'vendor-elements'
      crfs.inactivate(type, item.uid).then(() => {
        this.getNamespaceData()
      })
    },
    reactivate(item) {
      const type =
        item.type === 'attr' ? 'vendor-attributes' : 'vendor-elements'
      crfs.reactivate(type, item.uid).then(() => {
        this.getNamespaceData()
      })
    },
    async newVersion(item) {
      const type =
        item.type === 'attr' ? 'vendor-attributes' : 'vendor-elements'
      crfs.newVersion(type, item.uid).then(() => {
        this.getNamespaceData()
      })
    },
    addElement() {
      this.showElementForm = true
    },
    closeElementForm() {
      this.showElementForm = false
      this.elementToEdit = {}
      this.getNamespaceData()
    },
    addAttribute(item) {
      if (item.uid) {
        this.parentType = crfTypes.ELEMENT
        this.parentUid = item.uid
      } else {
        this.parentType = crfTypes.NAMESPACE
        this.parentUid = this.editItem.uid
      }
      this.showAttributeForm = true
    },
    closeAttributeForm() {
      this.showAttributeForm = false
      this.parentType = ''
      this.parentUid = ''
      this.elementToEdit = {}
      this.getNamespaceData()
    },
    editElement(item) {
      this.elementToEdit = item
      if (item.type === 'attr') {
        this.parentType = item.vendor_namespace
          ? crfTypes.NAMESPACE
          : crfTypes.ELEMENT
        this.showAttributeForm = true
      } else {
        this.showElementForm = true
      }
    },
    delete(item) {
      if (item.type) {
        crfs.delete('vendor-attributes', item.uid).then(() => {
          this.getNamespaceData()
        })
      } else {
        crfs.delete('vendor-elements', item.uid).then(() => {
          this.getNamespaceData()
        })
      }
    },
    cancel() {
      this.close()
    },
    close() {
      this.$emit('close')
    },
    async getElementsAttributes() {
      const params = {
        page_size: 0,
        filters: {
          'vendor_element.uid': { v: this.elements.map((el) => el.uid) },
          uid: { v: this.attributes.map((attr) => attr.uid) },
        },
        operator: 'or',
      }
      await crfs.getAllAttributes(params).then((resp) => {
        this.attributes = resp.data.items
        this.attributes.forEach((attr) => (attr.type = 'attr'))
      })
    },
    async getNamespaceData() {
      this.elements = []
      this.attributes = []
      if (this.editItem.uid) {
        await crfs.getNamespace(this.editItem.uid).then((resp) => {
          this.elements = resp.data.vendor_elements
          this.attributes = resp.data.vendor_attributes
        })
        await this.getElementsAttributes()
        for (const attr of this.attributes) {
          if (attr.vendor_element) {
            const index = this.elements.indexOf(
              this.elements.find((ele) => ele.uid === attr.vendor_element.uid)
            )
            if (this.elements[index]) {
              if (!this.elements[index].attributes) {
                this.elements[index].attributes = []
              }
              this.elements[index].attributes.push(attr)
              this.attributes[this.attributes.indexOf(attr)] = null
            }
          }
        }
        this.attributes = this.attributes.filter(function (el) {
          return el != null
        })
        this.elements = [...this.elements, ...this.attributes]
      }
    },
  },
}
</script>

<style scoped>
#attr .v-table__wrapper > table > thead > tr {
  visibility: collapse;
}
.elementBackground {
  background-color: #b1d5f2;
}
</style>
