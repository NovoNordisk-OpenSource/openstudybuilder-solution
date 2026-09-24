<template>
  <div>
    <v-progress-linear
      v-if="loading"
      indeterminate
      color="primary"
      class="mb-1"
    />

    <div ref="parent">
      <div
        v-for="itemGroup in itemGroups"
        :key="itemGroup.uid"
        class="crf-tree-node mb-1"
        @dragstart="onDragStartGuard"
      >
        <div
          class="node-content d-flex align-center pa-2"
          style="background-color: lightgrey"
        >
          <!-- Expand / collapse chevron -->
          <v-btn
            v-if="expanded.includes(itemGroup.uid)"
            icon="mdi-chevron-down"
            size="x-small"
            variant="text"
            @click="toggleExpandGroup(itemGroup)"
          />
          <v-btn
            v-else-if="itemGroup.items && itemGroup.items.length > 0"
            icon="mdi-chevron-right"
            size="x-small"
            variant="text"
            @click="toggleExpandGroup(itemGroup)"
          />
          <v-btn v-else variant="text" size="x-small" class="hide" icon />

          <!-- Drag handle -->
          <v-tooltip v-if="sortMode && !canDrag" location="top">
            <template #activator="{ props: tooltipProps }">
              <v-icon
                v-bind="tooltipProps"
                class="mx-1"
                size="small"
                color="grey-lighten-1"
              >
                mdi-drag
              </v-icon>
            </template>
            <span v-html="t('CRFTree.reordering_not_allowed')" />
          </v-tooltip>
          <v-icon v-else-if="sortMode" class="drag-handle mx-1" size="small">
            mdi-drag
          </v-icon>
          <v-icon v-else class="mx-1" size="small" style="opacity: 0">
            mdi-drag
          </v-icon>

          <!-- Actions menu -->
          <ActionsMenu :actions="actions" :item="itemGroup" />

          <!-- Icon + name -->
          <v-icon color="crfGroup" size="small" class="mx-1"
            >mdi-alpha-g-circle</v-icon
          >
          <span
            class="font-weight-bold text-body-2 node-name d-inline-flex align-center"
          >
            <v-tooltip
              v-if="itemGroup.name.length > 60"
              location="top"
              max-width="300"
              :text="itemGroup.name"
              interactive
            >
              <template #activator="{ props }">
                <span v-bind="props">{{
                  itemGroup.name.substring(0, 60) + '...'
                }}</span>
              </template>
            </v-tooltip>
            <span v-else>{{ itemGroup.name }}</span>
            <!-- Reorder buttons for items -->
            <div v-if="expanded.includes(itemGroup.uid)" class="d-inline-flex">
              <v-btn
                v-if="!sortModesItems[itemGroup.uid]"
                class="ml-2"
                prepend-icon="mdi-swap-vertical"
                color="crfGroup"
                size="x-small"
                variant="outlined"
                :loading="savingItems[itemGroup.uid]"
                :readonly="savingItems[itemGroup.uid]"
                :disabled="
                  activeReorderUid && activeReorderUid !== itemGroup.uid
                "
                @click="handleReorderClickItems(itemGroup)"
              >
                {{ $t('CRFTree.enable_reordering') }}
              </v-btn>
              <div v-else>
                <v-btn
                  class="ml-2"
                  color="error"
                  size="x-small"
                  variant="outlined"
                  prepend-icon="mdi-close"
                  :disabled="savingItems[itemGroup.uid]"
                  @click="handleDiscardReorderItems(itemGroup)"
                >
                  {{ $t('_global.discard') }}
                </v-btn>
                <v-btn
                  class="ml-2"
                  prepend-icon="mdi-content-save"
                  color="success"
                  size="x-small"
                  variant="outlined"
                  :loading="savingItems[itemGroup.uid]"
                  @click="handleReorderClickItems(itemGroup)"
                >
                  {{ $t('_global.save') }}
                </v-btn>
              </div>
            </div>
          </span>
          <span class="flex-grow-1" />

          <!-- Right side: tooltips, status, version, link button -->
          <div class="d-flex align-center">
            <CrfTreeTooltipsHandler :item="itemGroup" value="mandatory" />
            <CrfTreeTooltipsHandler :item="itemGroup" value="locked" />
            <CrfTreeTooltipsHandler :item="itemGroup" value="refAttrs" />
            <CrfTreeTooltipsHandler :item="itemGroup" value="repeating" />
            <CrfTreeTooltipsHandler
              :item="itemGroup"
              value="is_reference_data"
            />
            <CrfTreeTooltipsHandler :item="itemGroup" value="vendor" />
            <StatusChip :status="itemGroup.status" class="mx-1" />
            <span class="text-caption mx-2" style="min-width: 40px">{{
              itemGroup.version
            }}</span>
            <v-menu v-if="itemGroup.status !== statuses.FINAL" offset-y>
              <template #activator="{ props }">
                <div>
                  <v-btn
                    v-show="itemGroup.status !== statuses.FINAL"
                    width="150px"
                    size="small"
                    rounded
                    v-bind="props"
                    color="crfItem"
                    :title="$t('CRFTree.link_items')"
                  >
                    <v-icon icon="mdi-plus" />
                    {{ $t('CRFTree.items') }}
                  </v-btn>
                </div>
              </template>
              <v-list>
                <v-list-item @click="openLinkForm(itemGroup)">
                  <template #prepend>
                    <v-icon icon="mdi-plus" />
                  </template>
                  <v-list-item-title>
                    {{ $t('CRFTree.link_existing') }}
                  </v-list-item-title>
                </v-list-item>
                <v-list-item @click="openCreateAndAddForm(itemGroup)">
                  <template #prepend>
                    <v-icon icon="mdi-pencil-outline" />
                  </template>
                  <v-list-item-title>
                    {{ $t('CRFTree.create_and_link') }}
                  </v-list-item-title>
                </v-list-item>
              </v-list>
            </v-menu>
          </div>
        </div>

        <!-- Expanded children -->
        <div v-if="expanded.includes(itemGroup.uid)" class="node-children ml-6">
          <CrfTreeItems
            :sort-mode="sortModesItems[itemGroup.uid] || false"
            :save-trigger="saveTriggerItems[itemGroup.uid] || 0"
            :discard-trigger="discardTriggerItems[itemGroup.uid] || 0"
            :parent-item-group="itemGroup"
            :parent-form="parentForm"
            :collection-library-name="collectionLibraryName"
            @update-parent-item-group-item="updateItemGroupItem"
            @save-complete="handleSaveCompleteItems(itemGroup.uid)"
          />
        </div>
      </div>
    </div>

    <v-dialog
      v-model="showItemGroupForm"
      persistent
      content-class="fullscreen-dialog"
    >
      <CrfItemGroupForm
        :selected-group="selectedItemGroup"
        :read-only-prop="
          selectedItemGroup && selectedItemGroup.status === statuses.FINAL
        "
        class="fullscreen-dialog"
        @close="closeDefinition"
        @update-item-group="updateItemGroup"
        @link-group="linkGroup"
      />
    </v-dialog>
    <CrfLinkForm
      :open="showLinkForm"
      :item-to-link="selectedItemGroup"
      items-type="items"
      @close="closeLinkForm"
    />
    <v-dialog
      v-model="showExportForm"
      max-width="800px"
      persistent
      @keydown.esc="closeExportForm"
    >
      <CrfExportForm
        :item="selectedItemGroup"
        type="item_group"
        @close="closeExportForm"
      />
    </v-dialog>
    <CrfReferencesForm
      :open="showAttributesForm"
      :parent="parentForm"
      :element="selectedItemGroup"
      :read-only="selectedItemGroup.status === statuses.FINAL"
      @close="closeAttributesForm"
    />
    <v-dialog
      v-model="showCreateForm"
      persistent
      content-class="fullscreen-dialog"
    >
      <CrfItemForm
        class="fullscreen-dialog"
        :library-name="collectionLibraryName"
        @close="closeCreateAndAddForm"
        @link-item="linkItem"
      />
    </v-dialog>
    <CrfApprovalSummaryConfirmDialog ref="confirmApproval" />
    <CrfNewVersionSummaryConfirmDialog ref="confirmNewVersion" />
  </div>
</template>

<script setup>
import { computed, inject, nextTick, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import crfs from '@/api/crfs'
import CrfTreeItems from '@/components/library/crfs/crfTreeComponents/CrfTreeItems.vue'
import CrfTreeTooltipsHandler from '@/components/library/crfs/CrfTreeTooltipsHandler.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import statuses from '@/constants/statuses'
import CrfLinkForm from '@/components/library/crfs/CrfLinkForm.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import CrfItemGroupForm from '@/components/library/crfs/CrfItemGroupForm.vue'
import _isEmpty from 'lodash/isEmpty'
import CrfExportForm from '@/components/library/crfs/CrfExportForm.vue'
import CrfReferencesForm from '@/components/library/crfs/CrfReferencesForm.vue'
import crfTypes from '@/constants/crfTypes'
import CrfItemForm from '@/components/library/crfs/CrfItemForm.vue'
import parameters from '@/constants/parameters'
import { useDragAndDrop } from '@formkit/drag-and-drop/vue'
import CrfApprovalSummaryConfirmDialog from '@/components/library/crfs/CrfApprovalSummaryConfirmDialog.vue'
import CrfNewVersionSummaryConfirmDialog from '@/components/library/crfs/CrfNewVersionSummaryConfirmDialog.vue'

const props = defineProps({
  parentForm: {
    type: Object,
    default: null,
  },
  refreshItemGroups: {
    type: Number,
    default: null,
  },
  expandGroupsForForm: {
    type: Array,
    default: null,
  },
  sortMode: {
    type: Boolean,
    default: false,
  },
  collectionLibraryName: {
    type: String,
    default: null,
  },
  saveTrigger: {
    type: Number,
    default: 0,
  },
  discardTrigger: {
    type: Number,
    default: 0,
  },
})

const emit = defineEmits([
  'updateParentFormItemGroup',
  'save-complete',
  'update:orderChanged',
])

const notificationHub = inject('notificationHub')
const roles = inject('roles')
const router = useRouter()
const { t } = useI18n()

const activeReorderUid = inject('activeReorderUid')
const setActiveReorder = inject('setActiveReorder')
const clearActiveReorder = inject('clearActiveReorder')

const orderChanged = ref(false)

const sortModesItems = ref({})
const saveTriggerItems = ref({})
const discardTriggerItems = ref({})
const savingItems = ref({})

function handleReorderClickItems(itemGroup) {
  if (activeReorderUid.value && activeReorderUid.value !== itemGroup.uid) return
  if (!sortModesItems.value[itemGroup.uid]) {
    sortModesItems.value[itemGroup.uid] = true
    setActiveReorder(itemGroup.uid)
  } else {
    savingItems.value[itemGroup.uid] = true
    saveTriggerItems.value[itemGroup.uid] =
      (saveTriggerItems.value[itemGroup.uid] || 0) + 1
  }
}

function handleSaveCompleteItems(itemGroupUid) {
  sortModesItems.value[itemGroupUid] = false
  savingItems.value[itemGroupUid] = false
  clearActiveReorder()
}

function handleDiscardReorderItems(itemGroup) {
  discardTriggerItems.value[itemGroup.uid] =
    (discardTriggerItems.value[itemGroup.uid] || 0) + 1
  sortModesItems.value[itemGroup.uid] = false
  clearActiveReorder()
}

const [parent, itemGroups, updateConfig] = useDragAndDrop([], {
  dragHandle: '.drag-handle',
  onDragend: (event) => {
    if (event.state.targetIndex === event.state.initialIndex) return
    itemGroups.value.forEach((itemGroup, i) => {
      itemGroup.order_number = i
    })
    orderChanged.value = true
  },
})

function onDragStartGuard(event) {
  // Only allow dragging when the drag originates from a .drag-handle element.
  // event.target on dragstart is the element with draggable=true (the row),
  // so use the pointer coordinates to find the actual element under the cursor.
  const el = document.elementFromPoint(event.clientX, event.clientY)
  if (!el || !el.closest('.drag-handle')) {
    event.preventDefault()
    event.stopPropagation()
  }
}
const loading = ref(false)
const selectedItemGroup = ref({})
const showItemGroupForm = ref(false)
const showCreateForm = ref(false)
const showLinkForm = ref(false)
const showExportForm = ref(false)
const showAttributesForm = ref(false)
const expanded = ref([])

const refreshItems = ref(0)

const confirmApproval = ref(null)
const confirmNewVersion = ref(null)

const actions = computed(() => [
  {
    label: t('CRFTree.open_def'),
    icon: 'mdi-eye-outline',
    click: openDefinition,
  },
  {
    label: t('CRFTree.edit_reference'),
    icon: 'mdi-pencil-outline',
    click: editAttributes,
    condition: (item) => item.status === statuses.DRAFT,
    accessRole: roles.LIBRARY_WRITE,
  },
  {
    label: t('CRFTree.preview_odm'),
    icon: 'mdi-file-xml-box',
    click: previewODM,
  },
  {
    label: t('_global.approve'),
    icon: 'mdi-check-decagram',
    click: approve,
    condition: (item) => item.status === statuses.DRAFT,
    accessRole: roles.LIBRARY_WRITE,
  },
  {
    label: t('_global.new_version'),
    icon: 'mdi-plus-circle-outline',
    click: newVersion,
    condition: (item) => item.status === statuses.FINAL,
    accessRole: roles.LIBRARY_WRITE,
  },
  {
    label: t('_global.export'),
    icon: 'mdi-download-outline',
    click: openExportForm,
  },
])

const canDrag = computed(
  () =>
    props.parentForm?.status === statuses.DRAFT && itemGroups.value.length > 1
)

watch(
  () => props.saveTrigger,
  (val) => {
    if (!val) return
    if (!orderChanged.value) {
      emit('save-complete')
      return
    }
    crfs
      .addItemGroupsToForm(itemGroups.value, props.parentForm.uid, true)
      .then(() => {
        notificationHub?.add({
          msg: t('_global.order_updated'),
          timeout: 2000,
        })
        orderChanged.value = false
        emit('update:orderChanged', false)
      })
      .finally(() => {
        emit('save-complete')
      })
  }
)

watch(
  () => props.discardTrigger,
  (val) => {
    if (!val) return
    // Reset to original order by re-fetching item groups
    fetchItemGroups().then(() => {
      orderChanged.value = false
      emit('update:orderChanged', false)
    })
  }
)

watch(
  () => props.refreshItemGroups,
  () => {
    fetchItemGroups()
  }
)

watch(
  () => props.expandGroupsForForm,
  (value) => {
    if (!_isEmpty(value) && value.includes(props.parentForm?.uid)) {
      expanded.value = itemGroups.value
        .map((group) => (group.items.length > 0 ? group.uid : null))
        .filter((val) => val !== null)

      nextTick(() => updateConfig({ disabled: expanded.value.length > 0 }))
    }
  }
)

// Reinitialize drag-and-drop when expanded state changes
// Disable dragging when any item group is expanded to prevent dragging expanded nodes
watch(
  () => expanded.value.length,
  () => {
    nextTick(() => updateConfig({ disabled: expanded.value.length > 0 }))
  }
)

onMounted(() => {
  fetchItemGroups()
})

async function newVersion(item) {
  expanded.value = expanded.value.filter((e) => e !== item.uid)

  if (
    await confirmNewVersion.value?.open({
      agreeLabel: t('CRFItemGroups.create_new_version'),
      itemGroup: item,
    })
  ) {
    loading.value = true

    crfs
      .newVersion('item-groups', item.uid)
      .then((resp) => {
        if (props.parentForm?.status === statuses.DRAFT) {
          updateItemGroup(resp.data)
        }

        expandAll(item)
        notificationHub?.add({
          msg: t('_global.new_version_success'),
        })
      })
      .finally(() => {
        loading.value = false
      })
  }
}

async function approve(item) {
  expanded.value = expanded.value.filter((e) => e !== item.uid)

  if (
    await confirmApproval.value?.open({
      agreeLabel: t('CRFItemGroups.approve_group'),
      itemGroup: item,
    })
  ) {
    loading.value = true

    crfs
      .approve('item-groups', item.uid)
      .then((resp) => {
        updateItemGroup(resp.data)

        expandAll(item)
        notificationHub?.add({
          msg: t('CRFItemGroups.approved'),
        })
      })
      .finally(() => {
        loading.value = false
      })
  }
}

function updateItemGroupItem(affectedItemGroup, updatedItem) {
  if (affectedItemGroup.status == statuses.DRAFT) {
    const itemGroup = itemGroups.value.find(
      (ig) => ig.uid === affectedItemGroup.uid
    )
    if (itemGroup) {
      itemGroup.items = itemGroup.items.map((i) =>
        i.uid === updatedItem.uid ? { ...i, ...updatedItem } : i
      )
    }
  }
}

function openCreateAndAddForm(item) {
  selectedItemGroup.value = item
  showCreateForm.value = true
}

function closeCreateAndAddForm() {
  showCreateForm.value = false
  selectedItemGroup.value = {}
}

function linkItem(item) {
  const payload = [
    {
      uid: item.data.uid,
      order_number: selectedItemGroup.value.items.length,
      mandatory: 'No',
      collection_exception_condition_oid: null,
      key_sequence: parameters.NULL,
      methodOid: parameters.NULL,
      imputation_method_oid: parameters.NULL,
      role: parameters.NULL,
      role_codelist_oid: parameters.NULL,
      data_entry_required: 'No',
      sdv: 'No',
      vendor: { attributes: [] },
    },
  ]

  crfs
    .addItemsToItemGroup(payload, selectedItemGroup.value.uid, false)
    .then(() => {
      fetchItemGroups()
    })
}

async function fetchItemGroups() {
  if (!props.parentForm) {
    return
  }

  loading.value = true
  itemGroups.value = []

  const groupRefs = props.parentForm.item_groups ?? []
  itemGroups.value = await Promise.all(
    groupRefs.map((itemGroup) =>
      crfs
        .get(`item-groups/${itemGroup.uid}`, {
          params: {
            version: itemGroup.version,
            fields:
              'uid,oid,name,repeating,is_reference_data,status,version,items,mandatory,locked,order_number,vendor_attributes',
          },
        })
        .then((rs) => ({ ...itemGroup, ...rs.data }))
    )
  )
  itemGroups.value.sort((a, b) => (a.order_number ?? 0) - (b.order_number ?? 0))

  refreshItems.value += 1
  loading.value = false

  // Clean up stale reorder state for item groups no longer in the list
  const groupUids = new Set(itemGroups.value.map((ig) => ig.uid))
  for (const uid of Object.keys(sortModesItems.value)) {
    if (!groupUids.has(uid)) {
      delete sortModesItems.value[uid]
      delete saveTriggerItems.value[uid]
      delete savingItems.value[uid]
    }
  }

  if (
    !_isEmpty(props.expandGroupsForForm) &&
    props.expandGroupsForForm.includes(props.parentForm.uid)
  ) {
    expanded.value = itemGroups.value
      .map((group) => (group.items.length > 0 ? group.uid : null))
      .filter((val) => val !== null)
  }
}

function updateItemGroup(itemGroup) {
  itemGroups.value = itemGroups.value.map((ig) =>
    ig.uid === itemGroup.uid ? { ...ig, ...itemGroup } : ig
  )
  emit('updateParentFormItemGroup', props.parentForm, itemGroup)
}

function openDefinition(item) {
  crfs.getItemGroup(item.uid).then((resp) => {
    selectedItemGroup.value = resp.data
    showItemGroupForm.value = true
  })
}

function closeDefinition() {
  selectedItemGroup.value = {}
  showItemGroupForm.value = false
  fetchItemGroups()
}

function openLinkForm(item) {
  selectedItemGroup.value = item
  showLinkForm.value = true
}

function closeLinkForm() {
  showLinkForm.value = false
  selectedItemGroup.value = {}
  fetchItemGroups()
}

async function expandAll(item) {
  if (!expanded.value.includes(item.uid)) {
    expanded.value.push(item.uid)
  }
  nextTick(() => updateConfig({ disabled: expanded.value.length > 0 }))
}

function toggleExpandGroup(group) {
  const idx = expanded.value.indexOf(group.uid)
  if (idx >= 0) {
    if (sortModesItems.value[group.uid] || savingItems.value[group.uid]) return
    expanded.value.splice(idx, 1)
  } else {
    expanded.value.push(group.uid)
  }
  nextTick(() => updateConfig({ disabled: expanded.value.length > 0 }))
}

function openExportForm(item) {
  selectedItemGroup.value = item
  showExportForm.value = true
}

function closeExportForm() {
  selectedItemGroup.value = {}
  showExportForm.value = false
}

function editAttributes(item) {
  selectedItemGroup.value = item
  showAttributesForm.value = true
}

function closeAttributesForm() {
  selectedItemGroup.value = {}
  showAttributesForm.value = false
}

function previewODM(item) {
  router.push({
    name: 'CrfBuilder',
    params: {
      tab: 'odm-viewer',
      uid: item.uid,
      type: crfTypes.ITEM_GROUP,
    },
  })
}
</script>
<style scoped>
.crf-tree-node {
  margin-bottom: 4px;
}
.node-content {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  transition: all 0.2s;
}
.node-content:hover {
  border-color: #bdbdbd;
  filter: brightness(0.97);
}
.node-children {
  margin-top: 4px;
}
.drag-handle {
  cursor: grab;
}
.drag-handle:active {
  cursor: grabbing;
}
.node-name {
  min-width: 0;
}
.hide {
  opacity: 0;
  cursor: default;
}
</style>
