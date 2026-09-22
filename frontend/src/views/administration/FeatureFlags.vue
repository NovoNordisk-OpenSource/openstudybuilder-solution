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

        <div class="d-flex mx-4 mt-4">
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
        :headers="historyHeaders"
        :items="historyItems"
        :items-total="historyItems.length"
        change-field="change_description"
        export-name="FeatureFlag"
        @close="closeHistory"
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

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const roles = inject('roles')

const flags = ref([])
const search = ref('')
const selectedSection = ref('studies')
const confirm = ref()
const showHistory = ref(false)
const historyItems = ref([])
const historyTitle = ref('')

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
    key: 'enabled',
    title: t('FeatureFlagsView.enabled'),
    historyFilter: (value) => (value ? t('_global.yes') : t('_global.no')),
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
    accessRole: roles.ADMIN_READ,
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
  historyTitle.value = t('FeatureFlagsView.history_title', {
    name: flag.name,
  })
  const resp = await featureFlagsApi.getVersions(flag.uid)
  historyItems.value = resp.data
  showHistory.value = true
}

function closeHistory() {
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
