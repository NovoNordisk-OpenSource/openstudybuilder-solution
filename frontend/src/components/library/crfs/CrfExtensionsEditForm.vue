<template>
  <div>
    <SimpleFormDialog
      ref="form"
      :title="title"
      :open="open"
      max-width="1200px"
      no-saving
      :cancel-label="$t('_global.close')"
      @close="close"
    >
      <template #body>
        <NNTable
          ref="table"
          table-id="crf-extensions-edit-form"
          :headers="headers"
          item-value="uid"
          :items-length="total"
          :items="tableElements"
          table-height="auto"
          hide-default-switches
          hide-search-field
          light
          disable-filtering
          hide-export-button
          :modifiable-table="false"
          @filter="paginateResults"
        >
          <template #item="{ item, internalItem, toggleExpand, isExpanded }">
            <tr :class="item.type ? '' : 'elementBackground'">
              <td width="20%">
                <v-row>
                  <v-btn
                    v-if="isExpanded(internalItem)"
                    icon="mdi-chevron-down"
                    data-cy="expand-item"
                    variant="text"
                    class="mr-n2"
                    @click="toggleExpand(internalItem)"
                  />
                  <v-btn
                    v-else-if="item.attributes"
                    icon="mdi-chevron-right"
                    data-cy="expand-item"
                    variant="text"
                    class="mr-n2"
                    @click="toggleExpand(internalItem)"
                  />
                  <v-btn v-else icon variant="text" class="mr-n2" />
                  <ActionsMenu :actions="actions" :item="item" />
                  <div class="mt-3 ml-4">
                    {{
                      item.type
                        ? $t('CRFExtensions.attribute')
                        : $t('CRFExtensions.element')
                    }}
                  </div>
                </v-row>
              </td>
              <td width="20%">
                {{ item.name }}
              </td>
              <td width="20%">
                <ul>
                  <li
                    v-for="compatible_type in item.compatible_types"
                    :key="compatible_type"
                  >
                    {{ compatible_type }}
                  </li>
                </ul>
              </td>
              <td width="20%">
                {{ item.version }}
              </td>
              <td width="20%">
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
                    <td width="20%">
                      <v-row>
                        <v-btn icon variant="text" />
                        <ActionsMenu :actions="actions" :item="item" />
                        <div class="mt-3 ml-4">
                          {{ $t('CRFExtensions.attribute') }}
                        </div>
                      </v-row>
                    </td>
                    <td width="20%">
                      {{ item.name }}
                    </td>
                    <td width="20%"></td>
                    <td width="20%">
                      {{ item.version }}
                    </td>
                    <td width="20%">
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
              color="crfGroup"
              data-cy="add-element"
              rounded
              :disabled="!accessGuard.checkPermission($roles.LIBRARY_WRITE)"
              @click="addElement"
            >
              <v-icon left> mdi-plus </v-icon>
              <span class="label">{{ $t('CRFExtensions.element') }}</span>
            </v-btn>
            <v-btn
              class="ml-2 mb-2"
              color="crfItem"
              data-cy="add-atribute"
              rounded
              :disabled="!accessGuard.checkPermission($roles.LIBRARY_WRITE)"
              @click="addAttribute"
            >
              <v-icon left> mdi-plus </v-icon>
              <span class="label">{{ $t('CRFExtensions.attribute') }}</span>
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
      :edit-item="elementToEdit"
      @close="closeElementForm"
    />
  </div>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import NNTable from '@/components/tools/NNTable.vue'
import CrfAttributeForm from '@/components/library/crfs/CrfAttributeForm.vue'
import CrfElementForm from '@/components/library/crfs/CrfElementForm.vue'
import crfs from '@/api/crfs'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import crfTypes from '@/constants/crfTypes'
import { useAccessGuard } from '@/composables/accessGuard'

const roles = inject('roles')
const { t } = useI18n()
const emit = defineEmits(['close'])
const accessGuard = useAccessGuard()

const props = defineProps({
  open: Boolean,
  editItem: {
    type: Object,
    default: null,
  },
})

const table = ref()

const elements = ref([])
const total = ref(0)
const headers = [
  { title: t('_global.type'), key: 'type' },
  { title: t('_global.name'), key: 'name' },
  { title: t('CRFExtensions.compatible_types'), key: 'compatible_types' },
  { title: t('_global.version'), key: 'version' },
  { title: t('_global.status'), key: 'status' },
]
const showAttributeForm = ref(false)
const showElementForm = ref(false)
const attributes = ref([])
const actions = [
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'edit'),
    accessRole: roles.LIBRARY_WRITE,
    click: editElement,
  },
  {
    label: t('CRFExtensions.add_new_attr'),
    icon: 'mdi-plus',
    iconColor: 'primary',
    condition: (item) =>
      !item.type && item.possible_actions.find((action) => action === 'edit'),
    accessRole: roles.LIBRARY_WRITE,
    click: addAttribute,
  },
  {
    label: t('_global.approve'),
    icon: 'mdi-check-decagram',
    iconColor: 'success',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'approve'),
    accessRole: roles.LIBRARY_WRITE,
    click: approve,
  },
  {
    label: t('_global.new_version'),
    icon: 'mdi-plus-circle-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'new_version'),
    accessRole: roles.LIBRARY_WRITE,
    click: newVersion,
  },
  {
    label: t('_global.inactivate'),
    icon: 'mdi-close-octagon-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'inactivate'),
    accessRole: roles.LIBRARY_WRITE,
    click: inactivate,
  },
  {
    label: t('_global.reactivate'),
    icon: 'mdi-undo-variant',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'reactivate'),
    accessRole: roles.LIBRARY_WRITE,
    click: reactivate,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'delete'),
    accessRole: roles.LIBRARY_WRITE,
    click: remove,
  },
]
const elementToEdit = ref({})
const parentType = ref('')
const parentUid = ref('')
const tableElements = ref([])

const title = computed(() => {
  return t('CRFExtensions.extension') + props.editItem.name
})

watch(
  () => props.editItem,
  () => {
    getNamespaceData()
  }
)

onMounted(() => {
  getNamespaceData()
})

function paginateResults(filters, options) {
  const firstIndex = (options.page - 1) * options.itemsPerPage
  const lastIndex = options.page * options.itemsPerPage
  tableElements.value = elements.value.slice(firstIndex, lastIndex)
}

function approve(item) {
  const type = item.type === 'attr' ? 'vendor-attributes' : 'vendor-elements'
  crfs.approve(type, item.uid).then(() => {
    getNamespaceData()
  })
}

function inactivate(item) {
  const type = item.type === 'attr' ? 'vendor-attributes' : 'vendor-elements'
  crfs.inactivate(type, item.uid).then(() => {
    getNamespaceData()
  })
}

function reactivate(item) {
  const type = item.type === 'attr' ? 'vendor-attributes' : 'vendor-elements'
  crfs.reactivate(type, item.uid).then(() => {
    getNamespaceData()
  })
}

async function newVersion(item) {
  const type = item.type === 'attr' ? 'vendor-attributes' : 'vendor-elements'
  crfs.newVersion(type, item.uid).then(() => {
    getNamespaceData()
  })
}

function addElement() {
  showElementForm.value = true
}

function closeElementForm() {
  showElementForm.value = false
  elementToEdit.value = {}
  getNamespaceData()
}

function addAttribute(item) {
  if (item.uid) {
    parentType.value = crfTypes.ELEMENT
    parentUid.value = item.uid
  } else {
    parentType.value = crfTypes.NAMESPACE
    parentUid.value = props.editItem.uid
  }
  showAttributeForm.value = true
}

function closeAttributeForm() {
  showAttributeForm.value = false
  parentType.value = ''
  parentUid.value = ''
  elementToEdit.value = {}
  getNamespaceData()
}

function editElement(item) {
  elementToEdit.value = item
  if (item.type === 'attr') {
    parentType.value = item.vendor_namespace
      ? crfTypes.NAMESPACE
      : crfTypes.ELEMENT
    showAttributeForm.value = true
  } else {
    showElementForm.value = true
  }
}

function remove(item) {
  if (item.type) {
    crfs.delete('vendor-attributes', item.uid).then(() => {
      getNamespaceData()
    })
  } else {
    crfs.delete('vendor-elements', item.uid).then(() => {
      getNamespaceData()
    })
  }
}

function close() {
  emit('close')
}

async function getElementsAttributes() {
  const params = {
    page_size: 0,
    filters: {
      'vendor_element.uid': { v: elements.value.map((el) => el.uid) },
      uid: { v: attributes.value.map((attr) => attr.uid) },
    },
    operator: 'or',
  }
  await crfs.getAllAttributes(params).then((resp) => {
    attributes.value = resp.data.items
    attributes.value.forEach((attr) => (attr.type = 'attr'))
  })
}

async function getNamespaceData() {
  elements.value = []
  attributes.value = []
  if (props.editItem.uid) {
    await crfs.getNamespace(props.editItem.uid).then((resp) => {
      elements.value = resp.data.vendor_elements
      attributes.value = resp.data.vendor_attributes
    })
    await getElementsAttributes()
    for (const attr of attributes.value) {
      if (attr.vendor_element) {
        const index = elements.value.indexOf(
          elements.value.find((ele) => ele.uid === attr.vendor_element.uid)
        )
        if (elements.value[index]) {
          if (!elements.value[index].attributes) {
            elements.value[index].attributes = []
          }
          elements.value[index].attributes.push(attr)
          attributes.value[attributes.value.indexOf(attr)] = null
        }
      }
    }
    attributes.value = attributes.value.filter(function (el) {
      return el != null
    })
    elements.value = [...elements.value, ...attributes.value]
    total.value = elements.value.length
    table.value.filterTable()
  }
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
