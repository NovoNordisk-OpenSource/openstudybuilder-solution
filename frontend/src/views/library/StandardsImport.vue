<template>
  <div class="px-4">
    <div data-cy="page-title" class="page-title d-flex align-center">
      {{ $t('StandardsImport.title') }}
      <HelpButton :help-text="$t('StandardsImport.general')" />
    </div>

    <v-sheet class="mt-4" color="white" rounded="xl" elevation="0">
      <div class="d-flex align-center pa-4">
        <span class="page-title">{{
          $t('StandardsImport.releases_title')
        }}</span>
        <v-spacer />
        <v-btn
          variant="outlined"
          rounded="xl"
          class="mr-4"
          prepend-icon="mdi-cloud-download-outline"
          :loading="discovering"
          data-cy="standards-import-fetch-new-releases"
          @click="apiKeyDialogOpen = true"
        >
          {{ $t('StandardsImport.fetch_new_releases') }}
        </v-btn>
        <v-btn
          color="secondary"
          variant="flat"
          rounded="xl"
          prepend-icon="mdi-plus"
          data-cy="standards-import-start-new-release"
          @click="startNewRelease"
        >
          {{ $t('StandardsImport.start_new_release') }}
        </v-btn>
      </div>

      <v-divider />

      <v-data-table
        :headers="headers"
        :items="releases"
        :loading="loading"
        :items-per-page="-1"
        :no-data-text="$t('StandardsImport.no_releases')"
        hide-default-footer
        data-cy="standards-import-releases-table"
      >
        <template #[`item.effective_date`]="{ item }">
          <router-link
            :to="{
              name: 'StandardsImportRelease',
              params: { effective_date: item.effective_date },
            }"
          >
            {{ item.effective_date }}
          </router-link>
        </template>
        <template #[`item.status`]="{ item }">
          <v-chip
            v-if="releaseStage(item)"
            :color="releaseStatusColor(item.status)"
            size="small"
            variant="tonal"
          >
            {{ $t(`StandardsImport.stage_${releaseStage(item)}`) }}
          </v-chip>
          <EnumInfoTooltip
            enum-key="effective_date_status"
            :value="item.status"
          />
        </template>
        <template #[`item.files`]="{ item }">
          {{ (item.files || []).length }}
        </template>
        <template #[`item.open_inconsistency_count`]="{ item }">
          <span
            :class="{
              'text-error font-weight-bold': item.open_inconsistency_count > 0,
            }"
          >
            {{ item.open_inconsistency_count }}
          </span>
        </template>
        <template #[`item.analyzed_at`]="{ item }">
          {{ item.analyzed_at ? $filters.date(item.analyzed_at) : '-' }}
        </template>
        <template #[`item.imported_at`]="{ item }">
          {{ item.imported_at ? $filters.date(item.imported_at) : '-' }}
        </template>
        <template #[`item.actions`]> </template>
      </v-data-table>
    </v-sheet>
    <CdiscApiKeyForm
      :open="apiKeyDialogOpen"
      @close="apiKeyDialogOpen = false"
      @submit="fetchNewReleases"
    />
  </div>
</template>

<script setup>
import { inject, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useStandardsImportTypeDescriptionsStore } from '@/stores/standardsImportTypeDescriptions'
import HelpButton from '@/components/tools/HelpButton.vue'
import EnumInfoTooltip from '@/components/tools/EnumInfoTooltip.vue'
import CdiscApiKeyForm from '@/components/library/CdiscApiKeyForm.vue'
import effectiveDatesApi from '@/api/standardsImport/effectiveDates'
import packagesApi from '@/api/standardsImport/packages'
import jobsApi from '@/api/standardsImport/jobs'
import { releaseStage, releaseStatusColor } from '@/utils/standardsImport'

const { t } = useI18n()
const appStore = useAppStore()
const typeDescriptionsStore = useStandardsImportTypeDescriptionsStore()
const router = useRouter()
const notificationHub = inject('notificationHub')

const releases = ref([])
const loading = ref(false)
const discovering = ref(false)
const apiKeyDialogOpen = ref(false)

const headers = [
  { title: t('StandardsImport.effective_date'), key: 'effective_date' },
  { title: t('StandardsImport.status'), key: 'status' },
  { title: t('StandardsImport.files_staged'), key: 'files', sortable: false },
  {
    title: t('StandardsImport.pairing_workbooks'),
    key: 'pairing_files',
  },
  {
    title: t('StandardsImport.changelog_catalogues'),
    key: 'changelog_catalogues',
  },
  {
    title: t('StandardsImport.open_inconsistencies'),
    key: 'open_inconsistency_count',
  },
  { title: t('StandardsImport.analysed_at'), key: 'analyzed_at' },
  { title: t('StandardsImport.imported_at'), key: 'imported_at' },
  { title: '', key: 'actions', sortable: false },
]

function startNewRelease() {
  router.push({
    name: 'StandardsImportRelease',
    params: { effective_date: 'new' },
  })
}

function loadReleases() {
  loading.value = true
  return effectiveDatesApi
    .getAll()
    .then((response) => {
      releases.value = response.data || []
    })
    .finally(() => {
      loading.value = false
    })
}

// Content is never fetched here — this only tells us which releases are worth
// uploading. Staging the files is still the separate, deliberate step above.
// The mandatory catalogues are the exception: a call may have staged them already,
// even if it failed on a later release, so the table is reloaded whichever way the
// job ends rather than waiting for a page refresh.
//
// Runs as a background job on the server, same as analysis — the button's own
// loading state only covers starting it, and the outcome lands as a toast
// whenever the job actually finishes.
//
// The CDISC Library API key is asked for on every click and passed straight through:
// it is not kept in the component, a store, or the browser.
function fetchNewReleases(apiKey) {
  apiKeyDialogOpen.value = false
  discovering.value = true
  packagesApi
    .discoverNewReleases(apiKey)
    .then(({ data: job }) => {
      discovering.value = false
      return jobsApi.waitForJobCompletion(
        job.uid,
        t('StandardsImport.fetch_new_releases')
      )
    })
    .then((finishedJob) => {
      const count = finishedJob.stats?.new_release_count || 0
      notificationHub.add({
        type: count ? 'success' : 'info',
        msg: count
          ? t('StandardsImport.fetch_new_releases_success', { count })
          : t('StandardsImport.fetch_new_releases_none'),
      })
      return loadReleases()
    })
    .catch((error) => {
      discovering.value = false
      notificationHub.add({
        type: 'error',
        msg:
          error.response?.data?.message ||
          error.message ||
          t('StandardsImport.fetch_new_releases_error'),
      })
      return loadReleases()
    })
}

onMounted(() => {
  appStore.addBreadcrumbsLevel(
    t('StandardsImport.title'),
    { name: 'StandardsImport' },
    3,
    true
  )
  typeDescriptionsStore.fetchTypeDescriptions()
  loadReleases()
})
</script>
