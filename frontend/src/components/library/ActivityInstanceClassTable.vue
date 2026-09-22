<template>
  <NNTable
    ref="topTable"
    table-id="library-activity-instance-classes-table"
    :headers="headers"
    :items="getItemsForLevel(0)"
    hide-search-field
    hide-default-switches
    disable-filtering
    show-expand
    item-value="uid"
    column-data-resource="activity-instance-classes"
    :modifiable-table="false"
    class="fixed-layout"
    :history-config="{
      dataFetcher: fetchAuditTrail,
      changeField: 'change_description',
      title: $t('_global.audit_trail'),
    }"
    :export-config="{
      objectLabel: 'ActivityInstanceClasses',
      dataUrl: 'activity-instance-classes',
    }"
  >
    <template #bottom />
    <template #item="{ item, internalItem, toggleExpand, isExpanded }">
      <tr class="level0">
        <td class="cell-expand v-data-table__td">
          <div class="d-flex align-center">
            <ActionsMenu :actions="actions" :item="item" size="small" />
            <v-btn
              v-if="isExpanded(internalItem)"
              icon="mdi-chevron-down"
              variant="text"
              size="small"
              @click="toggleExpand(internalItem)"
            />
            <v-btn
              v-else
              icon="mdi-chevron-right"
              variant="text"
              size="small"
              @click="toggleExpand(internalItem)"
            />
          </div>
        </td>
        <td :colspan="headers.length - 1" class="v-data-table__td">
          <router-link :to="getRouteForItem(item)" class="text-decoration-none">
            {{ item.name }}
          </router-link>
        </td>
      </tr>
    </template>
    <template #expanded-row="{ columns, item }">
      <tr>
        <td :colspan="columns.length" class="pa-0">
          <v-data-table
            :ref="item.uid"
            :headers="headers"
            :items="getItemsForLevel(1, item.uid)"
            item-value="uid"
            show-expand
            :search="topTable.search"
            class="fixed-layout"
          >
            <template #headers />
            <template #bottom />
            <template #item="{ item, internalItem, toggleExpand, isExpanded }">
              <tr class="level1">
                <td class="v-data-table__td cell-expand">
                  <div class="d-flex align-center">
                    <ActionsMenu :actions="actions" :item="item" size="small" />
                    <v-btn
                      v-if="isExpanded(internalItem)"
                      icon="mdi-chevron-down"
                      variant="text"
                      size="small"
                      @click="toggleExpand(internalItem)"
                    />
                    <v-btn
                      v-else
                      icon="mdi-chevron-right"
                      variant="text"
                      size="small"
                      @click="toggleExpand(internalItem)"
                    />
                  </div>
                </td>
                <td :colspan="headers.length - 1" class="v-data-table__td">
                  <router-link
                    :to="getRouteForItem(item)"
                    class="text-decoration-none"
                  >
                    {{ item.name }}
                  </router-link>
                </td>
              </tr>
            </template>
            <template #expanded-row="{ columns, item }">
              <tr>
                <td :colspan="columns.length" class="pa-0">
                  <v-data-table
                    :ref="item.uid"
                    :headers="headers"
                    :items="getItemsForLevel(2, item.uid)"
                    item-value="uid"
                    show-expand
                    class="fixed-layout"
                  >
                    <template #headers />
                    <template #bottom />
                    <template
                      #item="{ item, internalItem, toggleExpand, isExpanded }"
                    >
                      <tr class="level2">
                        <td class="v-data-table__td cell-expand">
                          <div class="d-flex align-center">
                            <ActionsMenu
                              :actions="actions"
                              :item="item"
                              size="small"
                            />
                            <v-btn
                              v-if="isExpanded(internalItem)"
                              icon="mdi-chevron-down"
                              variant="text"
                              size="small"
                              @click="toggleExpand(internalItem)"
                            />
                            <v-btn
                              v-else
                              icon="mdi-chevron-right"
                              variant="text"
                              size="small"
                              @click="toggleExpand(internalItem)"
                            />
                          </div>
                        </td>
                        <td
                          :colspan="headers.length - 1"
                          class="v-data-table__td"
                        >
                          <router-link
                            :to="getRouteForItem(item)"
                            class="text-decoration-none"
                          >
                            {{ item.name }}
                          </router-link>
                        </td>
                      </tr>
                    </template>
                    <template #expanded-row="{ columns, item }">
                      <tr>
                        <td :colspan="columns.length" class="pa-0">
                          <v-data-table
                            :ref="item.uid"
                            :headers="headers"
                            :items="getItemsForLevel(3, item.uid)"
                            :show-expand="false"
                            class="fixed-layout"
                          >
                            <template #headers />
                            <template #bottom />
                            <template #[`item.data-table-expand`]="{ item }">
                              <ActionsMenu
                                :actions="actions"
                                :item="item"
                                size="small"
                              />
                            </template>
                            <template #[`item.name`]="{ item }">
                              <router-link
                                :to="getRouteForItem(item)"
                                class="text-decoration-none"
                              >
                                {{ item.name }}
                              </router-link>
                            </template>
                            <template #[`item.is_domain_specific`]="{ item }">
                              {{ $filters.yesno(item.is_domain_specific) }}
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
                            <template #[`item.status`]="{ item }">
                              <StatusChip :status="item.status" />
                            </template>
                          </v-data-table>
                        </td>
                      </tr>
                    </template>
                  </v-data-table>
                </td>
              </tr>
            </template>
          </v-data-table>
        </td>
      </tr>
    </template>
  </NNTable>
  <ActivityInstanceClassForm
    :open="showForm"
    :edited-instance-class="activeInstanceClass"
    @close="closeForm"
    @save="updateItemInPlace"
  />
  <v-dialog
    v-model="showHistory"
    persistent
    :fullscreen="$globals.historyDialogFullscreen"
    @keydown.esc="closeHistory"
  >
    <HistoryTable
      :title="historyTitle"
      :headers="historyHeaders"
      :items="historyItems"
      :items-total="historyItems.length"
      :change-field="'change_description'"
      export-name="ActivityInstanceClass"
      @close="closeHistory"
    />
  </v-dialog>
</template>

<script setup>
import { inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '@/api/activityInstanceClasses'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ActivityInstanceClassForm from '@/components/library/ActivityInstanceClassForm.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import statuses from '@/constants/statuses'

const { t } = useI18n()
const roles = inject('roles')
const notificationHub = inject('notificationHub')

const items = ref([])
const topTable = ref()
const showForm = ref(false)
const activeInstanceClass = ref({})
const showHistory = ref(false)
const historyItems = ref([])
const historyTitle = ref('')

const historyHeaders = [
  { key: 'name', title: t('_global.name') },
  { key: 'definition', title: t('_global.definition') },
  {
    key: 'is_domain_specific',
    title: t('ActivityInstanceClassTable.domain_specific'),
    historyFilter: (value) => (value ? t('_global.yes') : t('_global.no')),
  },
  { key: 'library_name', title: t('_global.library') },
  { key: 'version', title: t('_global.version') },
  { key: 'status', title: t('_global.status') },
]

const actions = [
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: (item) => item.status === statuses.DRAFT,
    accessRole: roles.LIBRARY_WRITE,
    click: editInstanceClass,
  },
  {
    label: t('_global.approve'),
    icon: 'mdi-check-decagram',
    iconColor: 'success',
    condition: (item) => item.status === statuses.DRAFT,
    accessRole: roles.LIBRARY_WRITE,
    click: approveInstanceClass,
  },
  {
    label: t('_global.new_version'),
    icon: 'mdi-plus-circle-outline',
    iconColor: 'primary',
    condition: (item) => item.status === statuses.FINAL,
    accessRole: roles.LIBRARY_WRITE,
    click: newInstanceClassVersion,
  },
  {
    label: t('_global.inactivate'),
    icon: 'mdi-close-octagon-outline',
    iconColor: 'primary',
    condition: (item) => item.status === statuses.FINAL,
    accessRole: roles.LIBRARY_WRITE,
    click: inactivateInstanceClass,
  },
  {
    label: t('_global.reactivate'),
    icon: 'mdi-undo-variant',
    iconColor: 'primary',
    condition: (item) => item.status === statuses.RETIRED,
    accessRole: roles.LIBRARY_WRITE,
    click: reactivateInstanceClass,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    accessRole: roles.LIBRARY_READ,
    click: openHistory,
  },
]

// Update a single node in place (preserving array/object identity) so the
// expanded tree state is not lost. Falls back to a full refetch if the
// updated entity can't be matched.
function updateItemInPlace(updated) {
  if (!updated || !updated.uid) {
    fetchItems()
    return
  }
  const existing = items.value.find((ic) => ic.uid === updated.uid)
  if (existing) {
    Object.assign(existing, updated)
  } else {
    fetchItems()
  }
}

function notifyAndUpdate(key, resp) {
  notificationHub.add({ msg: t(key), type: 'success' })
  updateItemInPlace(resp.data)
}

function editInstanceClass(item) {
  activeInstanceClass.value = item
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  activeInstanceClass.value = {}
}

function approveInstanceClass(item) {
  api.approve(item.uid).then((resp) => {
    notifyAndUpdate('ActivityInstanceClassTable.approve_success', resp)
  })
}

function newInstanceClassVersion(item) {
  api.newVersion(item.uid).then((resp) => {
    notifyAndUpdate('ActivityInstanceClassTable.new_version_success', resp)
  })
}

function inactivateInstanceClass(item) {
  api.inactivate(item.uid).then((resp) => {
    notifyAndUpdate('ActivityInstanceClassTable.inactivate_success', resp)
  })
}

function reactivateInstanceClass(item) {
  api.reactivate(item.uid).then((resp) => {
    notifyAndUpdate('ActivityInstanceClassTable.reactivate_success', resp)
  })
}

async function openHistory(item) {
  historyTitle.value = t('ActivityInstanceClassTable.history_title', {
    name: item.name,
  })
  const resp = await api.getActivityInstanceClassVersions(item.uid)
  historyItems.value = resp.data
  showHistory.value = true
}

function closeHistory() {
  showHistory.value = false
  historyItems.value = []
}

const getItemsForLevel = (level, parentUid) => {
  return items.value.filter((item) => {
    // For items with null level, infer the level from their parent
    let itemLevel = item.level
    if (itemLevel === null || itemLevel === undefined) {
      if (!item.parent_class) {
        itemLevel = 0 // No parent means root level
      } else {
        // Find the parent's level and add 1
        const parent = items.value.find((p) => p.uid === item.parent_class.uid)
        if (parent) {
          itemLevel = (parent.level ?? 0) + 1
        } else {
          // If we can't find the parent, assume based on whether we have a parent
          itemLevel = 1 // Has parent but parent not in list
        }
      }
    }

    if (parentUid === undefined) {
      return itemLevel === level
    }
    return itemLevel === level && item.parent_class?.uid === parentUid
  })
}

const getRouteForItem = (item) => {
  // Check if this item has any children in the items array
  const hasChildren = items.value.some(
    (child) => child.parent_class?.uid === item.uid
  )

  return {
    name: hasChildren
      ? 'ActivityInstanceParentClassOverview'
      : 'ActivityInstanceClassOverview',
    params: { id: item.uid },
  }
}

const headers = [
  {
    key: 'data-table-expand',
    sortable: false,
    cellProps: { class: 'cell-expand' },
    headerProps: { class: 'cell-expand' },
  },
  {
    key: 'name',
    title: t('_global.name'),
    cellProps: { class: 'cell-name' },
    headerProps: { class: 'cell-name' },
    align: 'start',
    sortable: false,
  },
  {
    key: 'definition',
    title: t('_global.definition'),
    cellProps: { class: 'cell-definition' },
    headerProps: { class: 'cell-definition' },
    sortable: false,
  },
  {
    key: 'is_domain_specific',
    title: t('ActivityInstanceClassTable.domain_specific'),
    cellProps: { class: 'cell-common' },
    headerProps: { class: 'cell-common' },
    sortable: false,
  },
  {
    key: 'library_name',
    title: t('_global.library'),
    cellProps: { class: 'cell-common' },
    headerProps: { class: 'cell-common' },
    sortable: false,
  },
  {
    key: 'start_date',
    title: t('_global.modified'),
    cellProps: { class: 'cell-common' },
    headerProps: { class: 'cell-common' },
    sortable: false,
  },
  {
    key: 'author_username',
    title: t('_global.modified_by'),
    cellProps: { class: 'cell-common' },
    headerProps: { class: 'cell-common' },
    sortable: false,
  },
  {
    key: 'version',
    title: t('_global.version'),
    cellProps: { class: 'cell-common' },
    headerProps: { class: 'cell-common' },
    sortable: false,
  },
  {
    key: 'status',
    title: t('_global.status'),
    cellProps: { class: 'cell-common' },
    headerProps: { class: 'cell-common' },
    sortable: false,
  },
]

const fetchAuditTrail = async (options) => {
  const data = {
    page_number: options.page,
    page_size: options.itemsPerPage,
    total_count: true,
  }
  const resp = await api.getVersions(data)
  return resp.data
}

async function fetchItems() {
  const resp = await api.getAll({ page_size: 0, sort_by: { level: true } })
  items.value = resp.data.items
}

await fetchItems()
</script>

<style>
.level0 {
  background-color: rgb(var(--v-theme-nnSeaBlue400));
}
.level1 {
  background-color: rgb(var(--v-theme-nnSeaBlue300));
}
.level2 {
  background-color: rgb(var(--v-theme-nnSeaBlue200));
}
.fixed-layout table {
  table-layout: fixed;
  width: 100%;
}
.cell-expand {
  width: 90px !important;
}
.cell-name {
  width: 15%;
}
.cell-definition {
  width: 20%;
}
.cell-common {
  width: 10%;
}
</style>
