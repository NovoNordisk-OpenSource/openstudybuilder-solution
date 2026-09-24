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
        v-for="form in forms"
        :key="form.uid"
        class="crf-tree-node mb-1"
        @dragstart="onDragStartGuard"
      >
        <div
          class="node-content d-flex align-center pa-2"
          :style="{
            backgroundColor: 'rgb(var(--v-theme-dfltBackgroundLight2))',
          }"
        >
          <!-- Expand / collapse chevron -->
          <v-btn
            v-if="expanded.includes(form.uid)"
            icon="mdi-chevron-down"
            size="x-small"
            variant="text"
            @click="toggleExpandForm(form)"
          />
          <v-btn
            v-else-if="form.item_groups && form.item_groups.length > 0"
            icon="mdi-chevron-right"
            size="x-small"
            variant="text"
            @click="toggleExpandForm(form)"
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
          <ActionsMenu :actions="actions" :item="form" />

          <!-- Icon + name -->
          <v-icon color="crfForm" size="small" class="mx-1"
            >mdi-alpha-f-circle</v-icon
          >
          <span
            class="font-weight-bold text-body-2 node-name d-inline-flex align-center"
          >
            <v-tooltip
              v-if="form.name.length > 60"
              location="top"
              max-width="300"
              :text="form.name"
              interactive
            >
              <template #activator="{ props }">
                <span v-bind="props">{{
                  form.name.substring(0, 60) + '...'
                }}</span>
              </template>
            </v-tooltip>
            <span v-else>{{ form.name }}</span>
            <!-- Reorder buttons for item groups -->
            <div v-if="expanded.includes(form.uid)" class="d-inline-flex">
              <v-btn
                v-if="!sortModesGroups[form.uid]"
                class="ml-2"
                prepend-icon="mdi-swap-vertical"
                color="crfForm"
                size="x-small"
                variant="outlined"
                :loading="savingGroups[form.uid]"
                :readonly="savingGroups[form.uid]"
                :disabled="activeReorderUid && activeReorderUid !== form.uid"
                @click="handleReorderClickGroups(form)"
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
                  :disabled="savingGroups[form.uid]"
                  @click="handleDiscardReorderGroups(form)"
                >
                  {{ $t('_global.discard') }}
                </v-btn>
                <v-btn
                  class="ml-2"
                  prepend-icon="mdi-content-save"
                  color="success"
                  size="x-small"
                  variant="outlined"
                  :loading="savingGroups[form.uid]"
                  @click="handleReorderClickGroups(form)"
                >
                  {{ $t('_global.save') }}
                </v-btn>
              </div>
            </div>
          </span>
          <span class="flex-grow-1" />

          <!-- Right side: tooltips, status, version, link button -->
          <div class="d-flex align-center">
            <CrfTreeTooltipsHandler :item="form" value="mandatory" />
            <CrfTreeTooltipsHandler :item="form" value="locked" />
            <CrfTreeTooltipsHandler :item="form" value="repeating" />
            <StatusChip :status="form.status" class="mx-1" />
            <span class="text-caption mx-2" style="min-width: 40px">{{
              form.version
            }}</span>
            <v-menu v-if="form.status !== statuses.FINAL" offset-y>
              <template #activator="{ props }">
                <div>
                  <v-btn
                    v-show="form.status !== statuses.FINAL"
                    width="150px"
                    size="small"
                    rounded
                    v-bind="props"
                    color="crfGroup"
                    :title="$t('CRFTree.link_item_groups')"
                  >
                    <v-icon icon="mdi-plus" />
                    {{ $t('CRFTree.item_groups') }}
                  </v-btn>
                </div>
              </template>
              <v-list>
                <v-list-item @click="openLinkForm(form)">
                  <template #prepend>
                    <v-icon icon="mdi-plus" />
                  </template>
                  <v-list-item-title>
                    {{ $t('CRFTree.link_existing') }}
                  </v-list-item-title>
                </v-list-item>
                <v-list-item @click="openCreateAndAddForm(form)">
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
        <div v-if="expanded.includes(form.uid)" class="node-children ml-6">
          <CrfTreeItemGroups
            :sort-mode="sortModesGroups[form.uid] || false"
            :save-trigger="saveTriggerGroups[form.uid] || 0"
            :discard-trigger="discardTriggerGroups[form.uid] || 0"
            :parent-form="form"
            :refresh-item-groups="refreshItemGroups"
            :expand-groups-for-form="expandGroupsForForm"
            :collection-library-name="parentCollection?.library_name"
            @update-parent-form-item-group="updateFormItemGroup"
            @save-complete="handleSaveCompleteGroups(form.uid)"
          />
        </div>
      </div>
    </div>

    <v-dialog
      v-model="showFormForm"
      persistent
      content-class="fullscreen-dialog"
    >
      <CrfFormForm
        :selected-form="selectedForm"
        :read-only-prop="selectedForm && selectedForm.status === statuses.FINAL"
        class="fullscreen-dialog"
        @close="closeDefinition"
        @link-form="linkForm"
        @update-form="updateForm"
      />
    </v-dialog>
    <CrfLinkForm
      :open="showLinkForm"
      :item-to-link="selectedForm"
      items-type="item-groups"
      @close="closeLinkForm"
    />
    <v-dialog
      v-model="showExportForm"
      max-width="800px"
      persistent
      @keydown.esc="closeExportForm"
    >
      <CrfExportForm
        :item="selectedForm"
        type="form"
        @close="closeExportForm"
      />
    </v-dialog>
    <CrfReferencesForm
      :open="showAttributesForm"
      :parent="parentCollection"
      :element="selectedForm"
      :read-only="selectedForm.status === statuses.FINAL"
      @close="closeAttributesForm"
    />
    <v-dialog
      v-model="showCreateForm"
      persistent
      content-class="fullscreen-dialog"
    >
      <CrfItemGroupForm
        class="fullscreen-dialog"
        :library-name="parentCollection?.library_name"
        @close="closeCreateAndAddForm"
        @link-group="linkItemGroup"
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
import CrfTreeItemGroups from '@/components/library/crfs/crfTreeComponents/CrfTreeItemGroups.vue'
import CrfTreeTooltipsHandler from '@/components/library/crfs/CrfTreeTooltipsHandler.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import statuses from '@/constants/statuses'
import CrfLinkForm from '@/components/library/crfs/CrfLinkForm.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import CrfFormForm from '@/components/library/crfs/CrfFormForm.vue'
import _isEmpty from 'lodash/isEmpty'
import CrfExportForm from '@/components/library/crfs/CrfExportForm.vue'
import CrfReferencesForm from '@/components/library/crfs/CrfReferencesForm.vue'
import crfTypes from '@/constants/crfTypes'
import CrfItemGroupForm from '@/components/library/crfs/CrfItemGroupForm.vue'
import { useDragAndDrop } from '@formkit/drag-and-drop/vue'
import CrfApprovalSummaryConfirmDialog from '@/components/library/crfs/CrfApprovalSummaryConfirmDialog.vue'
import CrfNewVersionSummaryConfirmDialog from '@/components/library/crfs/CrfNewVersionSummaryConfirmDialog.vue'

const props = defineProps({
  parentCollection: {
    type: Object,
    default: null,
  },
  refreshForms: {
    type: Number,
    default: null,
  },
  expandFormsForCollection: {
    type: String,
    default: null,
  },
  sortMode: {
    type: Boolean,
    default: false,
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
  'updateParentCollectionForm',
  'update:orderChanged',
  'save-complete',
])

const notificationHub = inject('notificationHub')
const roles = inject('roles')
const router = useRouter()
const { t } = useI18n()

const activeReorderUid = inject('activeReorderUid')
const setActiveReorder = inject('setActiveReorder')
const clearActiveReorder = inject('clearActiveReorder')

const orderChanged = ref(false)

const sortModesGroups = ref({})
const saveTriggerGroups = ref({})
const discardTriggerGroups = ref({})
const savingGroups = ref({})

function handleReorderClickGroups(form) {
  if (activeReorderUid.value && activeReorderUid.value !== form.uid) return
  if (!sortModesGroups.value[form.uid]) {
    sortModesGroups.value[form.uid] = true
    setActiveReorder(form.uid)
  } else {
    savingGroups.value[form.uid] = true
    saveTriggerGroups.value[form.uid] =
      (saveTriggerGroups.value[form.uid] || 0) + 1
  }
}

function handleSaveCompleteGroups(formUid) {
  sortModesGroups.value[formUid] = false
  savingGroups.value[formUid] = false
  clearActiveReorder()
}

function handleDiscardReorderGroups(form) {
  discardTriggerGroups.value[form.uid] =
    (discardTriggerGroups.value[form.uid] || 0) + 1
  sortModesGroups.value[form.uid] = false
  clearActiveReorder()
}

const [parent, forms, updateConfig] = useDragAndDrop([], {
  dragHandle: '.drag-handle',
  onDragend: (event) => {
    if (event.state.targetIndex === event.state.initialIndex) return
    forms.value.forEach((form, i) => {
      form.order_number = i
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
const showFormForm = ref(false)
const showLinkForm = ref(false)
const selectedForm = ref({})
const refreshItemGroups = ref(0)
const expanded = ref([])
const expandGroupsForForm = ref([])
const showExportForm = ref(false)
const showAttributesForm = ref(false)
const showCreateForm = ref(false)

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
  {
    label: t('CRFTree.expand'),
    icon: 'mdi-arrow-expand-down',
    condition: (item) => item.item_groups.length > 0,
    click: expandAll,
  },
])

const canDrag = computed(
  () =>
    props.parentCollection?.status === statuses.DRAFT && forms.value.length > 1
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
      .addFormsToCollection(forms.value, props.parentCollection.uid, true)
      .then(() => {
        notificationHub?.add({
          msg: t('_global.order_updated'),
          timeout: 2000,
        })
        orderChanged.value = false
        emit('update:orderChanged', false)
        emit('save-complete')
      })
  }
)

watch(
  () => props.discardTrigger,
  (val) => {
    if (!val) return
    // Reset to original order by re-fetching forms
    fetchForms().then(() => {
      orderChanged.value = false
      emit('update:orderChanged', false)
    })
  }
)

watch(
  () => props.refreshForms,
  () => {
    fetchForms()
  }
)

watch(
  () => props.expandFormsForCollection,
  (value) => {
    if (!_isEmpty(value) && value === props.parentCollection?.uid) {
      expanded.value = forms.value
        .map((form) => (form.item_groups.length > 0 ? form.uid : null))
        .filter((val) => val !== null)

      expandGroupsForForm.value = forms.value
        .map((form) => (form.item_groups.length > 0 ? form.uid : null))
        .filter((val) => val !== null)

      nextTick(() => updateConfig({ disabled: expanded.value.length > 0 }))
    }
  }
)

// Reinitialize drag-and-drop when expanded state changes
// Disable dragging when any form is expanded to prevent dragging expanded nodes
watch(
  () => expanded.value.length,
  () => {
    nextTick(() => updateConfig({ disabled: expanded.value.length > 0 }))
  }
)

onMounted(() => {
  fetchForms()
})

async function newVersion(item) {
  expanded.value = expanded.value.filter((e) => e !== item.uid)

  if (
    await confirmNewVersion.value?.open({
      agreeLabel: t('CRFForms.create_new_version'),
      form: item,
    })
  ) {
    loading.value = true

    crfs
      .newVersion('forms', item.uid)
      .then((resp) => {
        if (props.parentCollection?.status === statuses.DRAFT) {
          updateForm(resp.data)
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
      agreeLabel: t('CRFForms.approve_form'),
      form: item,
    })
  ) {
    loading.value = true

    crfs
      .approve('forms', item.uid)
      .then((resp) => {
        updateForm(resp.data)

        expandAll(item)
        notificationHub?.add({
          msg: t('CRFForms.approved'),
        })
      })
      .finally(() => {
        loading.value = false
      })
  }
}

function updateFormItemGroup(affectedForm, updatedItemGroup) {
  if (affectedForm.status === statuses.DRAFT) {
    const form = forms.value.find((f) => f.uid === affectedForm.uid)

    if (form) {
      form.item_groups = form.item_groups.map((f) =>
        f.uid === updatedItemGroup.uid ? { ...f, ...updatedItemGroup } : f
      )
    }
  }
}

function openCreateAndAddForm(item) {
  selectedForm.value = item
  showCreateForm.value = true
}

function closeCreateAndAddForm() {
  showCreateForm.value = false
  selectedForm.value = {}
}

function linkItemGroup(group) {
  const payload = [
    {
      uid: group.data.uid,
      order_number: selectedForm.value.item_groups.length,
      mandatory: 'No',
      collection_exception_condition_oid: null,
      vendor: { attributes: [] },
    },
  ]

  crfs.addItemGroupsToForm(payload, selectedForm.value.uid, false).then(() => {
    fetchForms()
  })
}

async function fetchForms() {
  if (!props.parentCollection) {
    return
  }

  loading.value = true
  forms.value = []

  const formRefs = props.parentCollection.forms ?? []
  forms.value = await Promise.all(
    formRefs.map((form) =>
      crfs
        .get(`forms/${form.uid}`, {
          params: {
            version: form.version,
            fields:
              'uid,oid,name,repeating,status,version,item_groups,mandatory,locked,order_number',
          },
        })
        .then((rs) => ({ ...form, ...rs.data }))
    )
  )
  forms.value.sort((a, b) => (a.order_number ?? 0) - (b.order_number ?? 0))

  refreshItemGroups.value += 1
  loading.value = false

  // Clean up stale reorder state for forms no longer in the list
  const formUids = new Set(forms.value.map((f) => f.uid))
  for (const uid of Object.keys(sortModesGroups.value)) {
    if (!formUids.has(uid)) {
      delete sortModesGroups.value[uid]
      delete saveTriggerGroups.value[uid]
      delete savingGroups.value[uid]
    }
  }

  if (
    !_isEmpty(props.expandFormsForCollection) &&
    props.expandFormsForCollection === props.parentCollection.uid
  ) {
    expanded.value = forms.value
      .map((form) => (form.item_groups.length > 0 ? form.uid : null))
      .filter((val) => val !== null)

    expandGroupsForForm.value = forms.value
      .map((form) => (form.item_groups.length > 0 ? form.uid : null))
      .filter((val) => val !== null)
  }
}

function updateForm(form) {
  forms.value = forms.value.map((f) =>
    f.uid === form.uid ? { ...f, ...form } : f
  )
  emit('updateParentCollectionForm', props.parentCollection, form)
}

function openDefinition(item) {
  crfs.getForm(item.uid).then((resp) => {
    selectedForm.value = resp.data
    showFormForm.value = true
  })
}

function closeDefinition() {
  selectedForm.value = {}
  showFormForm.value = false
  fetchForms()
}

function openLinkForm(item) {
  selectedForm.value = item
  showLinkForm.value = true
}

function closeLinkForm() {
  showLinkForm.value = false
  selectedForm.value = {}
  fetchForms()
}

async function expandAll(item) {
  if (!expanded.value.includes(item.uid)) {
    expanded.value.push(item.uid)
  }
  expandGroupsForForm.value = [item.uid]
  nextTick(() => updateConfig({ disabled: expanded.value.length > 0 }))
}

function toggleExpandForm(form) {
  const idx = expanded.value.indexOf(form.uid)
  if (idx >= 0) {
    if (sortModesGroups.value[form.uid] || savingGroups.value[form.uid]) return
    expanded.value.splice(idx, 1)
  } else {
    expanded.value.push(form.uid)
  }
  nextTick(() => updateConfig({ disabled: expanded.value.length > 0 }))
}

function openExportForm(item) {
  selectedForm.value = item
  showExportForm.value = true
}

function closeExportForm() {
  selectedForm.value = {}
  showExportForm.value = false
}

function editAttributes(item) {
  selectedForm.value = item
  showAttributesForm.value = true
}

function closeAttributesForm() {
  selectedForm.value = {}
  showAttributesForm.value = false
}

function previewODM(item) {
  router.push({
    name: 'CrfBuilder',
    params: {
      tab: 'odm-viewer',
      uid: item.uid,
      type: crfTypes.FORM,
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
