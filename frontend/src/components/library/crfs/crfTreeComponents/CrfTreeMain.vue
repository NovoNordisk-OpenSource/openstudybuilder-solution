<template>
  <v-row>
    <v-col cols="auto">
      <v-select
        v-model="selectCollection"
        :items="dropdownItems"
        :item-title="(item) => item?.name || $t('CRFTree.show_all')"
        :item-value="(item) => item?.uid || null"
        :loading="dropdownLoading"
        :menu="dropdownMenuOpen"
        class="ms-4 mt-4"
        style="min-width: 300px"
        prepend-inner-icon="mdi-filter"
        hide-details
        @update:menu="dropdownMenuOpen = $event"
      >
        <template #prepend-item>
          <div v-if="dropdownItems.length > 0">
            <v-list-item @click="selectAll">
              <template #prepend>
                <v-icon icon="mdi-format-list-bulleted" size="small" />
              </template>
              <v-list-item-title class="font-weight-medium">
                {{ $t('CRFTree.show_all') }}
              </v-list-item-title>
            </v-list-item>
            <v-divider class="my-1" />
          </div>
        </template>
        <template #menu-header>
          <SelectMenuSearch
            v-model="searchQuery"
            :placeholder="$t('_global.search')"
            @clear="handleSearchClear"
          />
        </template>
        <template #append-item>
          <InfiniteScrollList
            ref="infiniteScrollList"
            v-model:search="searchQuery"
            :fetch-function="fetchCollectionsPage"
            :auto-detect-scrollable="true"
            :page-size="50"
            @items-loaded="handleItemsLoaded"
          />
        </template>

        <template #no-data>
          <v-list-item v-if="!dropdownLoading">
            <v-list-item-title class="text-center">
              {{ $t('NNTable.no_data') }}
            </v-list-item-title>
          </v-list-item>
        </template>
      </v-select>
    </v-col>
  </v-row>

  <div
    v-if="loading && collections.length === 0"
    class="d-flex justify-center align-center pb-2"
  >
    <v-progress-circular indeterminate color="primary" size="large" width="5" />
  </div>

  <div v-else class="pa-2">
    <div v-for="item in collections" :key="item.uid" class="crf-tree-node mb-1">
      <div
        class="node-content d-flex align-center pa-2"
        :style="{ backgroundColor: 'rgb(var(--v-theme-dfltBackgroundLight1))' }"
      >
        <!-- Expand / collapse chevron -->
        <v-btn
          v-if="expanded.includes(item.uid)"
          icon="mdi-chevron-down"
          size="x-small"
          variant="text"
          @click="doubleClick(item)"
        />
        <v-tooltip
          v-else-if="item.forms.length > 0"
          location="top left"
          :text="$t('CRFTree.double_click_expand')"
        >
          <template #activator="{ props }">
            <v-btn
              v-bind="props"
              icon="mdi-chevron-right"
              size="x-small"
              variant="text"
              @click="doubleClick(item)"
            />
          </template>
        </v-tooltip>
        <v-btn v-else variant="text" size="x-small" class="hide" icon />

        <!-- Actions menu -->
        <ActionsMenu :actions="actions" :item="item" />

        <!-- Icon + name -->
        <v-icon color="crfCollection" size="small" class="mx-1"
          >mdi-alpha-c-circle</v-icon
        >
        <span
          class="font-weight-bold text-body-2 node-name d-inline-flex align-center"
        >
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
          <!-- Reorder buttons -->
          <div v-if="expanded.includes(item.uid)" class="d-inline-flex">
            <v-btn
              v-if="!sortModes[item.uid]"
              class="ml-2"
              prepend-icon="mdi-swap-vertical"
              color="crfCollection"
              size="x-small"
              variant="outlined"
              :loading="savingCollections[item.uid]"
              :readonly="savingCollections[item.uid]"
              :disabled="activeReorderUid && activeReorderUid !== item.uid"
              @click="handleReorderClick(item)"
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
                :disabled="savingCollections[item.uid]"
                @click="handleDiscardReorder(item)"
              >
                {{ $t('_global.discard') }}
              </v-btn>
              <v-btn
                class="ml-2"
                prepend-icon="mdi-content-save"
                color="success"
                size="x-small"
                variant="outlined"
                :loading="savingCollections[item.uid]"
                @click="handleReorderClick(item)"
              >
                {{ $t('_global.save') }}
              </v-btn>
            </div>
          </div>
        </span>
        <span class="flex-grow-1" />

        <!-- Right side: status, version, link button -->
        <div class="d-flex align-center">
          <StatusChip :status="item.status" class="mx-1" />
          <span class="text-caption mx-2" style="min-width: 40px">{{
            item.version
          }}</span>
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
                  :title="$t('CRFTree.link_forms')"
                >
                  <v-icon icon="mdi-plus" />
                  {{ $t('CRFTree.forms') }}
                </v-btn>
              </div>
            </template>
            <v-list>
              <v-list-item @click="openLinkForm(item)">
                <template #prepend>
                  <v-icon icon="mdi-plus" />
                </template>
                <v-list-item-title>
                  {{ $t('CRFTree.link_existing') }}
                </v-list-item-title>
              </v-list-item>
              <v-list-item @click="openCreateAndAddForm(item)">
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
      <div v-if="expanded.includes(item.uid)" class="node-children ml-6">
        <CrfTreeForms
          :sort-mode="sortModes[item.uid] || false"
          :save-trigger="saveTriggers[item.uid] || 0"
          :discard-trigger="discardTriggers[item.uid] || 0"
          :parent-collection="item"
          :refresh-forms="refreshForms"
          :expand-forms-for-collection="expandFormsForCollection"
          @update:order-changed="orderChangedCollections[item.uid] = $event"
          @save-complete="handleSaveComplete(item.uid)"
          @update-parent-collection-form="updateCollectionForm"
        />
      </div>
    </div>

    <v-pagination
      v-if="totalCollections"
      v-model="pageNumber"
      :length="Math.max(1, Math.ceil(totalCollections / (pageSize || 1)))"
      :total-visible="5"
      color="nnDarkBlue1"
    ></v-pagination>
  </div>
  <v-dialog v-model="showCollectionForm" persistent>
    <CrfCollectionForm
      :selected-collection="selectedCollection"
      :read-only-prop="
        selectedCollection && selectedCollection.status === statuses.FINAL
      "
      @close="closeDefinition"
      @update-collection="updateCollection"
    />
  </v-dialog>
  <CrfLinkForm
    :open="showLinkForm"
    :item-to-link="selectedCollection"
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
      :item="selectedCollection"
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
      :library-name="selectedCollection.library_name"
      @close="closeCreateAndAddForm"
      @link-form="linkForm"
    />
  </v-dialog>
  <CrfApprovalSummaryConfirmDialog ref="confirmApproval" />
  <ConfirmDialog ref="confirmNewVersion" />
</template>

<script setup>
import {
  computed,
  inject,
  onBeforeUnmount,
  onMounted,
  provide,
  ref,
  watch,
} from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import crfs from '@/api/crfs'
import CrfApprovalSummaryConfirmDialog from '@/components/library/crfs/CrfApprovalSummaryConfirmDialog.vue'
import CrfTreeForms from '@/components/library/crfs/crfTreeComponents/CrfTreeForms.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import statuses from '@/constants/statuses'
import CrfLinkForm from '@/components/library/crfs/CrfLinkForm.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import CrfCollectionForm from '@/components/library/crfs/CrfCollectionForm.vue'
import CrfExportForm from '@/components/library/crfs/CrfExportForm.vue'
import crfTypes from '@/constants/crfTypes'
import CrfFormForm from '@/components/library/crfs/CrfFormForm.vue'
import filteringParameters from '@/utils/filteringParameters'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import isEmpty from 'lodash/isEmpty'
import SelectMenuSearch from '@/components/tools/SelectMenuSearch.vue'
import InfiniteScrollList from '@/components/tools/InfiniteScrollList.vue'

const notificationHub = inject('notificationHub')
const roles = inject('roles')
const router = useRouter()
const { t } = useI18n()

const pageNumber = ref(1)
const pageSize = ref(10)

const confirmApproval = ref(null)
const confirmNewVersion = ref(null)

const showLinkForm = ref(false)
const showCollectionForm = ref(false)
const selectedCollection = ref({})
const refreshForms = ref(0)
const expanded = ref([])
const expandFormsForCollection = ref('')
const showExportForm = ref(false)
const showCreateForm = ref(false)
const sortModes = ref({})
const orderChangedCollections = ref({})
const savingCollections = ref({})
const saveTriggers = ref({})
const discardTriggers = ref({})

const activeReorderUid = ref(null)
provide('activeReorderUid', activeReorderUid)
provide('setActiveReorder', (uid) => {
  activeReorderUid.value = uid
})
provide('clearActiveReorder', () => {
  activeReorderUid.value = null
})

function handleReorderClick(item) {
  if (activeReorderUid.value && activeReorderUid.value !== item.uid) return
  if (!sortModes.value[item.uid]) {
    sortModes.value[item.uid] = true
    activeReorderUid.value = item.uid
  } else {
    savingCollections.value[item.uid] = true
    saveTriggers.value[item.uid] = (saveTriggers.value[item.uid] || 0) + 1
  }
}

function handleSaveComplete(collectionUid) {
  sortModes.value[collectionUid] = false
  savingCollections.value[collectionUid] = false
  activeReorderUid.value = null
}

function handleDiscardReorder(item) {
  discardTriggers.value[item.uid] = (discardTriggers.value[item.uid] || 0) + 1
  sortModes.value[item.uid] = false
  activeReorderUid.value = null
}

const collections = ref([])
const totalCollections = ref(0)
const loading = ref(false)
const selectCollection = ref({})
const doubleClickCounter = ref(0)
const doubleClickTimer = ref(null)
const dropdownMenuOpen = ref(false)
const infiniteScrollList = ref(null)
const dropdownItems = ref([])
const searchQuery = ref('')
const dropdownLoading = ref(false)

// Fetch function for infinite scroll
async function fetchCollectionsPage(page, search, pageSize) {
  const params = {
    page_number: page,
    page_size: pageSize,
    total_count: true,
    fields: 'uid,name',
    sort_by: JSON.stringify({ name: true }),
  }

  if (search) {
    params.filters = { '*': { v: [search] } }
  }

  const response = await crfs.get('study-events', { params })
  return {
    items: response.data.items,
    total: response.data.total,
  }
}

// Handle items loaded from infinite scroll
function handleItemsLoaded(items) {
  dropdownItems.value = items
  if (infiniteScrollList.value) {
    dropdownLoading.value = infiniteScrollList.value.loading
  }
}

const actions = computed(() => [
  {
    label: t('CRFTree.open_def'),
    icon: 'mdi-eye-outline',
    click: openDefinition,
  },
  {
    label: t('CRFTree.preview_odm'),
    icon: 'mdi-file-xml-box',
    click: previewODM,
  },
  {
    label: t('_global.new_version'),
    icon: 'mdi-plus-circle-outline',
    click: newVersion,
    condition: (item) => item.status === statuses.FINAL,
    accessRole: roles.LIBRARY_WRITE,
  },
  {
    label: t('_global.approve'),
    icon: 'mdi-check-decagram',
    click: approve,
    condition: (item) => item.status === statuses.DRAFT,
    accessRole: roles.LIBRARY_WRITE,
  },
  {
    label: t('CRFTree.create_new_version_all'),
    icon: 'mdi-plus-circle-outline',
    click: newVersionAll,
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
    condition: (item) => item.forms.length > 0,
    click: expandAll,
  },
])

// Ensure selected collection is in the dropdown
async function ensureSelectedCollectionInDropdown() {
  if (selectCollection.value && !isEmpty(selectCollection.value)) {
    const isPresent = dropdownItems.value.find(
      (c) => c.uid === selectCollection.value
    )
    if (!isPresent) {
      // Fetch the selected collection separately and prepend it
      const resp = await crfs.getCollection(selectCollection.value)
      dropdownItems.value = [
        { uid: resp.data.uid, name: resp.data.name },
        ...dropdownItems.value,
      ]
    }
  }
}

watch(pageNumber, () => {
  getCollections(pageNumber.value)
})

watch(selectCollection, () => {
  getCollections()
})

// Sync loading state from InfiniteScrollList
watch(
  () => infiniteScrollList.value?.loading,
  (loading) => {
    if (loading !== undefined) {
      dropdownLoading.value = loading
    }
  }
)

onMounted(async () => {
  // Wait for InfiniteScrollList to initialize, then ensure selected collection
  setTimeout(async () => {
    await ensureSelectedCollectionInDropdown()
  }, 100)
  getCollections()
})

onBeforeUnmount(() => {
  if (doubleClickTimer.value) {
    clearTimeout(doubleClickTimer.value)
  }
})

function toggleExpand(item) {
  const idx = expanded.value.indexOf(item.uid)
  if (idx >= 0) {
    expanded.value.splice(idx, 1)
  } else {
    expanded.value.push(item.uid)
  }
}

function doubleClick(item) {
  doubleClickCounter.value++

  if (doubleClickCounter.value === 1) {
    doubleClickTimer.value = setTimeout(() => {
      toggleExpand(item)
      doubleClickCounter.value = 0
      expandFormsForCollection.value = ''
    }, 500)
  } else {
    expandAll(item)
    clearTimeout(doubleClickTimer.value)
    doubleClickCounter.value = 0
  }
}

async function newVersion(item) {
  expanded.value = expanded.value.filter((e) => e !== item.uid)

  if (
    await confirmNewVersion.value?.open(
      t('_global.continuation_confirmation'),
      {
        type: 'warning',
      }
    )
  ) {
    loading.value = true

    crfs
      .newVersion('study-events', item.uid)
      .then((resp) => {
        collections.value = collections.value.map((c) =>
          c.uid === resp.data.uid ? { ...c, ...resp.data } : c
        )

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

function updateCollectionForm(affectedCollection, updatedForm) {
  if (affectedCollection.status == statuses.DRAFT) {
    const collection = collections.value.find(
      (c) => c.uid === affectedCollection.uid
    )
    if (collection) {
      collection.forms = collection.forms.map((f) =>
        f.uid === updatedForm.uid ? { ...f, ...updatedForm } : f
      )
    }
  }
}

async function selectAll() {
  selectCollection.value = {}
  dropdownMenuOpen.value = false
}

async function handleSearchClear() {
  searchQuery.value = ''
  await infiniteScrollList.value?.reset()
}

async function getCollections(pageNumber = 1) {
  loading.value = true
  // If a specific collection is selected, fetch it directly by uid
  if (!isEmpty(selectCollection.value)) {
    return crfs
      .get(`study-events/${selectCollection.value}`, {
        params: {
          fields:
            'uid,oid,name,status,version,forms,effective_date,retired_date,library_name',
        },
      })
      .then((resp) => {
        collections.value = [resp.data]
        totalCollections.value = 1
      })
      .finally(() => {
        loading.value = false
      })
  }
  let options = { sortBy: [{ key: 'name', order: 'asc' }], page: pageNumber }
  let params = filteringParameters.prepareParameters(options, null, null)
  if (!params) {
    params = { total_count: true }
  } else {
    params.total_count = true
  }
  // The CRF Tree view has no pagination controls, so always fetch all
  // collections (page_size: 0 tells the API to return every row).
  params.page_size = 0
  params.fields =
    'uid,oid,name,status,version,forms,effective_date,retired_date,library_name'

  return crfs
    .get('study-events', { params })
    .then((resp) => {
      collections.value = resp.data.items
      totalCollections.value = resp.data.total
      pageSize.value = resp.data.size
    })
    .finally(() => {
      loading.value = false
    })
}

function openCreateAndAddForm(item) {
  selectedCollection.value = item
  showCreateForm.value = true
}

function closeCreateAndAddForm() {
  showCreateForm.value = false
  selectedCollection.value = {}
}

function linkForm(form) {
  const payload = [
    {
      uid: form.data.uid,
      order_number: selectedCollection.value.forms.length,
      mandatory: 'No',
      collection_exception_condition_oid: null,
    },
  ]

  crfs
    .addFormsToCollection(payload, selectedCollection.value.uid, false)
    .then(() => {
      getCollections().then(() => {
        refreshForms.value += 1
      })
    })
}

function updateCollection(collection) {
  collections.value = collections.value.map((c) =>
    c.uid === collection.uid ? { ...c, ...collection } : c
  )
}

function openDefinition(item) {
  selectedCollection.value = item
  showCollectionForm.value = true
}

function closeDefinition() {
  selectedCollection.value = {}
  showCollectionForm.value = false
  getCollections()
}

function openLinkForm(item) {
  selectedCollection.value = item
  showLinkForm.value = true
}

async function closeLinkForm() {
  showLinkForm.value = false
  selectedCollection.value = {}
  await getCollections()
  refreshForms.value += 1
}

async function expandAll(item) {
  if (!expanded.value.includes(item.uid)) {
    expanded.value.push(item.uid)
  }
  expandFormsForCollection.value = item.uid
}

function openExportForm(item) {
  selectedCollection.value = item
  showExportForm.value = true
}

function closeExportForm() {
  selectedCollection.value = {}
  showExportForm.value = false
}

function previewODM(item) {
  router.push({
    name: 'CrfBuilder',
    params: {
      tab: 'odm-viewer',
      uid: item.uid,
      type: crfTypes.STUDY_EVENT,
    },
  })
}

async function approve(item) {
  expanded.value = expanded.value.filter((e) => e !== item.uid)

  if (
    item.status === statuses.DRAFT &&
    (await confirmApproval.value?.open({
      agreeLabel: t('CRFCollections.approve_collection'),
      collection: item,
    }))
  ) {
    loading.value = true

    await crfs
      .approve('study-events', item.uid)
      .then((resp) => {
        collections.value = collections.value.map((collection) => {
          if (collection.uid === resp.data.uid) {
            return { ...collection, ...resp.data }
          }
          return collection
        })

        notificationHub?.add({
          msg: t('CRFCollections.approved'),
        })
        expandAll(item)
      })
      .finally(() => {
        loading.value = false
      })
  }
}

async function newVersionAll(item) {
  expanded.value = expanded.value.filter((e) => e !== item.uid)

  if (
    item.status === statuses.FINAL &&
    (await confirmNewVersion.value?.open(
      t('CRFTree.new_version_affecting_children_warning'),
      {
        agreeLabel: t('CRFTree.create_new_versions'),
        type: 'warning',
      }
    ))
  ) {
    loading.value = true

    await crfs
      .newVersion('study-events', item.uid, {
        params: { cascade_new_version: true },
      })
      .then((resp) => {
        collections.value = collections.value.map((collection) => {
          if (collection.uid === resp.data.uid) {
            return { ...collection, ...resp.data }
          }
          return collection
        })

        notificationHub?.add({
          msg: t('CRFCollections.new_version_all'),
        })
        expandAll(item)
      })
      .finally(() => {
        loading.value = false
      })
  }
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
.node-name {
  min-width: 0;
}
.hide {
  opacity: 0;
  cursor: default;
}
</style>
