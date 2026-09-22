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
        v-for="item in items"
        :key="item.uid"
        class="crf-tree-node mb-1"
        @dragstart="onDragStartGuard"
      >
        <div
          class="node-content d-flex align-center pa-2"
          style="background-color: white"
        >
          <!-- No expand (leaf node) — placeholder for alignment -->
          <v-btn variant="text" size="x-small" class="hide" icon />

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
          <ActionsMenu :actions="actions" :item="item" />

          <!-- Icon + name -->
          <v-icon color="crfItem" size="small" class="mx-1"
            >mdi-alpha-i-circle</v-icon
          >
          <span class="font-weight-bold text-body-2 flex-grow-1 node-name">
            <v-tooltip
              v-if="item.name.length > 60"
              location="top"
              max-width="300"
              :text="item.name"
              interactive
            >
              <template #activator="{ props }">
                <span v-bind="props">{{
                  item.name.substring(0, 60) + '...'
                }}</span>
              </template>
            </v-tooltip>
            <span v-else>{{ item.name }}</span>
          </span>

          <!-- Right side: tooltips, status, version -->
          <div class="d-flex align-center">
            <CrfTreeTooltipsHandler :item="item" value="mandatory" />
            <CrfTreeTooltipsHandler :item="item" value="locked" />
            <CrfTreeTooltipsHandler :item="item" value="refAttrs" />
            <CrfTreeTooltipsHandler :item="item" value="dataType" />
            <CrfTreeTooltipsHandler :item="item" value="vendor" />
            <StatusChip :status="item.status" class="mx-1" />
            <span class="text-caption mx-2" style="min-width: 40px">{{
              item.version
            }}</span>
          </div>
        </div>
      </div>
    </div>

    <v-dialog
      v-model="showItemForm"
      persistent
      content-class="fullscreen-dialog"
    >
      <CrfItemForm
        :selected-item="selectedItem"
        :start-step="startStep"
        :form-view="false"
        :read-only-prop="selectedItem && selectedItem.status === statuses.FINAL"
        :library-name="collectionLibraryName"
        class="fullscreen-dialog"
        @close="closeDefinition"
        @update-item="updateItem"
        @link-item="linkItem"
      />
    </v-dialog>
    <v-dialog
      v-model="showExportForm"
      max-width="800px"
      persistent
      @keydown.esc="closeExportForm"
    >
      <CrfExportForm
        :item="selectedItem"
        type="item"
        @close="closeExportForm"
      />
    </v-dialog>
    <CrfReferencesForm
      :open="showAttributesForm"
      :parent="parentItemGroup"
      :element="selectedItem"
      :read-only="selectedItem.status === statuses.FINAL"
      @close="closeAttributesForm"
    />
    <CrfNewVersionSummaryConfirmDialog ref="confirmNewVersion" />
  </div>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import crfs from '@/api/crfs'
import CrfTreeTooltipsHandler from '@/components/library/crfs/CrfTreeTooltipsHandler.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import statuses from '@/constants/statuses'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import CrfItemForm from '@/components/library/crfs/CrfItemForm.vue'
import CrfExportForm from '@/components/library/crfs/CrfExportForm.vue'
import CrfReferencesForm from '@/components/library/crfs/CrfReferencesForm.vue'
import { useDragAndDrop } from '@formkit/drag-and-drop/vue'
import crfTypes from '@/constants/crfTypes'
import CrfNewVersionSummaryConfirmDialog from '@/components/library/crfs/CrfNewVersionSummaryConfirmDialog.vue'

const props = defineProps({
  parentItemGroup: {
    type: Object,
    default: null,
  },
  parentForm: {
    type: Object,
    default: null,
  },
  refreshItems: {
    type: Number,
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
  'updateParentItemGroupItem',
  'save-complete',
  'update:orderChanged',
])

const notificationHub = inject('notificationHub')
const roles = inject('roles')
const router = useRouter()
const { t } = useI18n()

const orderChanged = ref(false)

const [parent, items] = useDragAndDrop([], {
  dragHandle: '.drag-handle',
  onDragend: (event) => {
    if (event.state.targetIndex === event.state.initialIndex) return
    items.value.forEach((item, i) => {
      item.order_number = i
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
const selectedItem = ref({})
const startStep = ref(null)
const showItemForm = ref(false)
const showExportForm = ref(false)
const showAttributesForm = ref(false)

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
    label: t('CRFTree.manage_activity_instances'),
    icon: 'mdi-link',
    click: openActivityInstanceTable,
    condition: (item) => item.status === statuses.DRAFT,
    accessRole: roles.LIBRARY_READ,
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
    props.parentItemGroup?.status === statuses.DRAFT && items.value.length > 1
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
      .addItemsToItemGroup(items.value, props.parentItemGroup.uid, true)
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
    // Reset to original order by re-fetching items
    fetchItems().then(() => {
      orderChanged.value = false
      emit('update:orderChanged', false)
    })
  }
)

watch(
  () => props.refreshItems,
  () => {
    fetchItems()
  }
)

onMounted(() => {
  fetchItems()
})

async function newVersion(item) {
  if (
    await confirmNewVersion.value?.open({
      agreeLabel: t('CRFItems.create_new_version'),
      item: item,
    })
  ) {
    loading.value = true

    crfs
      .newVersion('items', item.uid)
      .then((resp) => {
        if (props.parentItemGroup?.status === statuses.DRAFT) {
          updateItem(resp.data)
        }

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
  loading.value = true

  crfs
    .approve('items', item.uid)
    .then((resp) => {
      updateItem(resp.data)

      notificationHub?.add({
        msg: t('CRFItems.approved'),
      })
    })
    .finally(() => {
      loading.value = false
    })
}

async function fetchItems() {
  if (!props.parentItemGroup) {
    return
  }

  loading.value = true
  items.value = []

  items.value = await Promise.all(
    (props.parentItemGroup.items ?? []).map((item) =>
      crfs
        .get(`items/${item.uid}`, {
          params: {
            version: item.version,
            fields:
              'uid,oid,name,datatype,status,version,mandatory,locked,order_number,vendor_attributes',
          },
        })
        .then((rs) => ({ ...item, ...rs.data }))
    )
  )
  items.value.sort((a, b) => (a.order_number ?? 0) - (b.order_number ?? 0))
  loading.value = false
}

function updateItem(item) {
  items.value = items.value.map((i) =>
    i.uid === item.uid ? { ...i, ...item } : i
  )
  emit('updateParentItemGroupItem', props.parentItemGroup, item)
}

function openDefinition(item) {
  crfs.getItem(item.uid).then((resp) => {
    selectedItem.value = resp.data
    showItemForm.value = true
  })
}

function closeDefinition() {
  selectedItem.value = {}
  startStep.value = null
  showItemForm.value = false
  fetchItems()
}

function openExportForm(item) {
  selectedItem.value = item
  showExportForm.value = true
}

function closeExportForm() {
  selectedItem.value = {}
  showExportForm.value = false
}

function editAttributes(item) {
  selectedItem.value = item
  showAttributesForm.value = true
}

function openActivityInstanceTable(item) {
  crfs.getItem(item.uid).then((resp) => {
    selectedItem.value = resp.data
    startStep.value = 'activity_instance_links'
    showItemForm.value = true
  })
}

function closeAttributesForm() {
  selectedItem.value = {}
  showAttributesForm.value = false
}

function previewODM(item) {
  router.push({
    name: 'CrfBuilder',
    params: {
      tab: 'odm-viewer',
      uid: item.uid,
      type: crfTypes.ITEM,
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
