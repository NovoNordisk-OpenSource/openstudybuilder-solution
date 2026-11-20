<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('FeatureFlagsView.title') }}
    </div>
    <v-card>
      <v-card-text>
        <v-alert
          color="nnLightBlue200"
          icon="mdi-information-outline"
          class="text-nnTrueBlue mx-4 my-2"
        >
          {{ $t('FeatureFlagsView.help') }}
        </v-alert>

        <div class="d-flex mx-4 mt-4">
          <v-spacer />
          <v-btn-toggle
            v-model="selectedSection"
            mandatory
            density="compact"
            color="nnBaseBlue"
            divided
            variant="outlined"
            class="layoutSelector"
          >
            <v-btn
              v-for="section in sections"
              :key="section.value"
              :value="section.value"
            >
              {{ section.label }}
            </v-btn>
          </v-btn-toggle>
          <v-spacer />
        </div>

        <div class="d-flex align-center mx-4 mt-4">
          <v-text-field
            v-model="search"
            clearable
            clear-icon="mdi-close"
            prepend-inner-icon="mdi-magnify"
            :label="$t('_global.search')"
            single-line
            color="nnBaseBlue"
            hide-details
            style="min-width: 240px; max-width: 300px"
            class="searchFieldLabel ml-0"
            data-cy="search-field"
          />
          <v-spacer />
          <v-btn
            class="ml-2"
            variant="outlined"
            color="nnBaseBlue"
            icon
            size="small"
            :disabled="!displayedFlags.length || !canReadAllHistory"
            :loading="historyLoading"
            data-cy="all-flags-history-button"
            @click="openAllHistory"
          >
            <v-icon>mdi-history</v-icon>
            <v-tooltip activator="parent" location="top">
              {{ $t('FeatureFlagsView.all_history') }}
            </v-tooltip>
          </v-btn>
        </div>

        <v-data-table
          v-model:search="search"
          :headers="headers"
          :items="displayedFlags"
          class="mx-4 my-6"
          items-per-page="-1"
        >
          <template #[`item.menu`]="{ item }">
            <ActionsMenu :actions="actions" :item="item" />
          </template>
          <template #[`item.actions`]="{ item }">
            <v-switch
              v-model="item.enabled"
              hide-details
              :disabled="item.status !== 'Final'"
              @update:model-value="(value) => toggleFlagState(item, value)"
            />
          </template>
          <template #[`item.status`]="{ item }">
            <StatusChip :status="item.status" />
          </template>
          <template #[`item.name`]="{ item }">
            <div class="d-flex align-center justify-space-between">
              <span>{{ item.name }}</span>
              <v-menu
                open-on-hover
                :close-on-content-click="false"
                location="top"
              >
                <template #activator="{ props }">
                  <v-icon
                    v-bind="props"
                    size="small"
                    color="nnBaseBlue"
                    class="ml-2"
                  >
                    mdi-information-outline
                  </v-icon>
                </template>
                <v-card max-width="400">
                  <v-card-text>{{ item.description }}</v-card-text>
                </v-card>
              </v-menu>
            </div>
          </template>
          <template #bottom></template>
        </v-data-table>
      </v-card-text>
    </v-card>
    <v-dialog
      v-model="showHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeHistory"
    >
      <HistoryTable
        :title="historyTitle"
        :headers="historyTableHeaders"
        :items="historyRows"
        :items-total="historyTotal"
        :loading="historyLoading"
        :with-export="!historyLoading"
        identity-key="uid"
        change-field="change_description"
        :export-name="historyExportName"
        @close="closeHistory"
        @refresh="refreshAllHistory"
      />
    </v-dialog>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  </div>
</template>

<script setup>
import { computed, inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import featureFlagsApi from '@/api/featureFlags'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import { useAccessGuard } from '@/composables/accessGuard'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const roles = inject('roles')
const accessGuard = useAccessGuard()

const flags = ref([])
const search = ref('')
const selectedSection = ref('studies')
const confirm = ref()
const showHistory = ref(false)
const historyItems = ref([])
const historyTitle = ref('')
const historyLoading = ref(false)
const historyTotal = ref(0)
// One dialog serves both the history of a single flag and of all flags.
const historyAllFlags = ref(false)
// Guards against a slow "all flags" page landing after the dialog was closed,
// reopened for something else or paged on.
let historyRequest = 0
let historyOptions = { page: 1, itemsPerPage: 10 }
let historySection = selectedSection.value

// The flags and their history are open to anyone holding any role.
const canReadAllHistory = Object.values(roles).some((role) =>
  accessGuard.checkPermission(role)
)

const displayedFlags = computed(() => {
  return flags.value.filter((flag) => flag.section === selectedSection.value)
})

const headers = [
  { key: 'menu', title: '', width: '4%' },
  { key: 'actions', title: '', width: '6%' },
  { key: 'feature', title: t('_global.feature'), width: '35%' },
  { key: 'name', title: t('_global.name'), width: '35%' },
  { key: 'status', title: t('_global.status'), width: '12%' },
]
// The visible table shows `enabled` as a switch under the `actions` key and
// hides the description behind a tooltip, so the history needs its own headers
// rather than reusing `headers` -- the keys have to match the version payload.
const historyHeaders = [
  { key: 'feature', title: t('_global.feature') },
  { key: 'name', title: t('_global.name') },
  {
    key: 'enabled_label',
    title: t('FeatureFlagsView.enabled'),
    changeKeys: ['enabled'],
  },
  { key: 'description', title: t('_global.description') },
  { key: 'status', title: t('_global.status') },
  { key: 'version', title: t('_global.version') },
]
const sections = [
  { value: 'studies', label: t('_global.studies') },
  { value: 'library', label: t('_global.library') },
  { value: 'admin', label: t('Topbar.admin') },
]
// The history of all flags mixes the three sections, so rows need to say which
// section (and, via feature/name, which flag) they belong to.
const allHistoryHeaders = [
  {
    key: 'section_label',
    title: t('FeatureFlagsView.section'),
    changeKeys: ['section'],
  },
  ...historyHeaders,
]
// The export reads raw item values and ignores header filters, so the readable
// labels are put on the rows themselves.
const historyRows = computed(() =>
  historyItems.value.map((item) => ({
    ...item,
    section_label:
      sections.find((section) => section.value === item.section)?.label ??
      item.section,
    enabled_label: item.enabled ? t('_global.yes') : t('_global.no'),
  }))
)
const historyTableHeaders = computed(() =>
  historyAllFlags.value ? allHistoryHeaders : historyHeaders
)
const historyExportName = computed(() =>
  historyAllFlags.value ? 'FeatureFlags' : 'FeatureFlag'
)

const actions = [
  {
    label: t('_global.inactivate'),
    icon: 'mdi-close-octagon-outline',
    iconColor: 'primary',
    condition: (item) => item.status === 'Final',
    accessRole: roles.ADMIN_WRITE,
    click: inactivateFlag,
  },
  {
    label: t('_global.reactivate'),
    icon: 'mdi-undo-variant',
    iconColor: 'primary',
    condition: (item) => item.status === 'Retired',
    accessRole: roles.ADMIN_WRITE,
    click: reactivateFlag,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    click: openHistory,
  },
]

async function loadFlags() {
  const resp = await featureFlagsApi.get({ include_retired: true })
  flags.value = resp.data
}

async function toggleFlagState(flag, value) {
  if (flag.status !== 'Final') {
    return
  }
  await featureFlagsApi.update(flag.uid, { enabled: value })
}

async function openHistory(flag) {
  const request = ++historyRequest
  const resp = await featureFlagsApi.getVersions(flag.uid)
  if (request !== historyRequest) {
    return
  }
  historyAllFlags.value = false
  historyTitle.value = t('FeatureFlagsView.history_title', {
    name: flag.name,
  })
  historyItems.value = resp.data
  historyTotal.value = resp.data.length
  showHistory.value = true
}

// The history of the flags in the selected section (retired included) comes
// from one paginated endpoint, newest first. The server diffs every version
// against the previous version of the same flag, also across pages.
async function openAllHistory() {
  historyAllFlags.value = true
  historySection = selectedSection.value
  historyTitle.value = t('FeatureFlagsView.all_history_title', {
    section: sections
      .find((section) => section.value === historySection)
      .label.toLowerCase(),
  })
  historyItems.value = []
  historyTotal.value = 0
  historyOptions = { page: 1, itemsPerPage: 10 }
  showHistory.value = true
  await loadAllHistory()
}

async function loadAllHistory() {
  const request = ++historyRequest
  historyLoading.value = true
  try {
    const resp = await featureFlagsApi.getAllVersions({
      page_number: historyOptions.page,
      // -1 is the "All" option of the table; the API takes 0 for all rows.
      page_size:
        historyOptions.itemsPerPage > 0 ? historyOptions.itemsPerPage : 0,
      total_count: true,
      section: historySection,
    })
    if (request !== historyRequest) {
      return
    }
    historyItems.value = resp.data.items
    historyTotal.value = resp.data.total
  } catch (_error) {
    // The request interceptor has already told the user what went wrong.
    if (request === historyRequest) {
      closeHistory()
    }
  } finally {
    if (request === historyRequest) {
      historyLoading.value = false
    }
  }
}

async function refreshAllHistory(options) {
  if (
    !historyAllFlags.value ||
    (options.page === historyOptions.page &&
      options.itemsPerPage === historyOptions.itemsPerPage)
  ) {
    return
  }
  historyOptions = { page: options.page, itemsPerPage: options.itemsPerPage }
  await loadAllHistory()
}

function closeHistory() {
  historyRequest++
  historyLoading.value = false
  showHistory.value = false
  historyItems.value = []
}

async function inactivateFlag(flag) {
  const options = {
    type: 'warning',
    cancelLabel: t('_global.cancel'),
    agreeLabel: t('_global.continue'),
  }
  if (
    !(await confirm.value.open(
      t('FeatureFlagsView.confirm_inactivate'),
      options
    ))
  ) {
    return
  }

  try {
    await featureFlagsApi.inactivate(flag.uid)
    notificationHub.add({
      msg: t('FeatureFlagsView.inactivate_success'),
      type: 'success',
    })
    await loadFlags()
  } catch (_error) {
    notificationHub.add({
      msg: t('FeatureFlagsView.lifecycle_error'),
      type: 'error',
    })
  }
}

async function reactivateFlag(flag) {
  const options = {
    type: 'warning',
    cancelLabel: t('_global.cancel'),
    agreeLabel: t('_global.continue'),
  }
  if (
    !(await confirm.value.open(
      t('FeatureFlagsView.confirm_reactivate'),
      options
    ))
  ) {
    return
  }

  try {
    await featureFlagsApi.reactivate(flag.uid)
    notificationHub.add({
      msg: t('FeatureFlagsView.reactivate_success'),
      type: 'success',
    })
    await loadFlags()
  } catch (_error) {
    notificationHub.add({
      msg: t('FeatureFlagsView.lifecycle_error'),
      type: 'error',
    })
  }
}

loadFlags()
</script>

<style scoped>
.v-data-table {
  width: auto !important;
}
</style>
