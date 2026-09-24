<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('ComplexityScore.admin_title') }}
    </div>

    <NavigationTabs :tabs="tabs">
      <template #default="{ tabKeys }">
        <v-window-item value="study-complexity-scores">
          <StudyComplexityScoreDetails show-study-select />
        </v-window-item>
        <v-window-item value="activity-burdens">
          <!-- Activity Subgroup Burdens Table -->
          <v-card :key="`burdens-${tabKeys['activity-burdens']}`" class="mt-0">
            <v-card-text>
              <v-alert
                color="nnLightBlue200"
                icon="mdi-information-outline"
                class="text-nnTrueBlue mx-4 my-2 mb-6"
              >
                {{ $t('ComplexityScore.admin_activity_burdens_info') }}
              </v-alert>
              <div class="d-flex justify-space-between align-center mb-4 px-4">
                <v-text-field
                  v-model="searchActivityBurdens"
                  prepend-inner-icon="mdi-magnify"
                  :label="$t('_global.search')"
                  single-line
                  hide-details
                  clearable
                  clear-icon="mdi-close"
                  class="mr-4"
                  style="max-width: 300px"
                />
                <DataTableExportButton
                  :object-label="'Activity Subgroup Burdens'"
                  :data-url="`admin/complexity-scores/activity-burdens`"
                  :headers="headersActivityBurdens"
                  data-cy="export-data-button"
                  @export="confirmExport"
                />
              </div>

              <v-data-table
                :headers="headersActivityBurdens"
                :items="activityBurdens"
                :search="searchActivityBurdens"
                class="mx-4 my-6"
                :loading="loadingActivityBurdens"
              >
              </v-data-table>
            </v-card-text>
          </v-card>
        </v-window-item>
        <v-window-item value="burdens">
          <!-- Burdens Table -->
          <v-card :key="`burdens-${tabKeys['burdens']}`" class="mt-0">
            <v-card-text>
              <v-alert
                color="nnLightBlue200"
                icon="mdi-information-outline"
                class="text-nnTrueBlue mx-4 my-2 mb-6"
              >
                {{ $t('ComplexityScore.admin_burdens_info') }}
              </v-alert>
              <div class="d-flex justify-space-between align-center mb-4 px-4">
                <v-text-field
                  v-model="searchBurdens"
                  prepend-inner-icon="mdi-magnify"
                  :label="$t('_global.search')"
                  single-line
                  hide-details
                  clearable
                  clear-icon="mdi-close"
                  class="mr-4"
                  style="max-width: 300px"
                />
                <DataTableExportButton
                  :object-label="'Burdens'"
                  :data-url="`admin/complexity-scores/burdens`"
                  :headers="headersBurdens"
                  data-cy="export-data-button"
                  @export="confirmExport"
                />
              </div>

              <v-data-table
                :headers="headersBurdens"
                :items="burdens"
                :search="searchBurdens"
                class="mx-4 my-6"
                :loading="loadingBurdens"
              >
              </v-data-table>
            </v-card-text>
          </v-card>
        </v-window-item>
      </template>
    </NavigationTabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import adminApi from '@/api/admin'
import DataTableExportButton from '@/components/tools/DataTableExportButton.vue'
import NavigationTabs from '@/components/tools/NavigationTabs.vue'
import StudyComplexityScoreDetails from '@/components/studies/StudyComplexityScoreDetails.vue'

const { t } = useI18n()
const activityBurdens = ref([])
const searchActivityBurdens = ref('')
const burdens = ref([])
const searchBurdens = ref('')
const loadingActivityBurdens = ref(false)
const loadingBurdens = ref(false)
const tabs = [
  {
    tab: 'study-complexity-scores',
    name: t('ComplexityScore.admin_study_scores_tab'),
  },
  {
    tab: 'activity-burdens',
    name: t('ComplexityScore.admin_activity_burdens_tab'),
  },
  { tab: 'burdens', name: t('ComplexityScore.admin_burdens_tab') },
]
const headersActivityBurdens = [
  {
    key: 'activity_subgroup_name',
    title: t('ComplexityScore.admin_activity_burdens_name'),
  },
  {
    key: 'burden_id',
    title: t('ComplexityScore.admin_activity_burdens_burden_id'),
  },
  { key: 'site_burden', title: t('ComplexityScore.admin_burdens_site_burden') },
  {
    key: 'patient_burden',
    title: t('ComplexityScore.admin_burdens_patient_burden'),
  },
]
const headersBurdens = [
  { key: 'burden_id', title: t('ComplexityScore.admin_burdens_id') },
  { key: 'name', title: t('ComplexityScore.admin_burdens_name') },
  { key: 'description', title: t('ComplexityScore.admin_burdens_description') },
  { key: 'site_burden', title: t('ComplexityScore.admin_burdens_site_burden') },
  {
    key: 'patient_burden',
    title: t('ComplexityScore.admin_burdens_patient_burden'),
  },
]

function fetchActivityBurdens() {
  loadingActivityBurdens.value = true
  adminApi
    .getComplexityActivityBurdens()
    .then((resp) => {
      activityBurdens.value = resp.data.sort((a, b) =>
        a.activity_subgroup_name.localeCompare(b.activity_subgroup_name)
      )
    })
    .finally(() => {
      loadingActivityBurdens.value = false
    })
}

function fetchBurdens() {
  loadingBurdens.value = true
  adminApi
    .getComplexityBurdens()
    .then((resp) => {
      burdens.value = resp.data.sort((a, b) => a.name.localeCompare(b.name))
    })
    .finally(() => {
      loadingBurdens.value = false
    })
}

async function confirmExport(resolve) {
  resolve(true)
}

fetchActivityBurdens()
fetchBurdens()
</script>

<style scoped>
.v-data-table {
  width: auto !important;
}
</style>
