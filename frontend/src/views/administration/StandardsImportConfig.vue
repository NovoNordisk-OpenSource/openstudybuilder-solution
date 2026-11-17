<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('StandardsImportConfig.title') }}
    </div>
    <v-card>
      <v-card-text>
        <v-alert
          color="nnLightBlue200"
          icon="mdi-information-outline"
          class="text-nnTrueBlue mx-4 my-2"
        >
          {{ $t('StandardsImportConfig.help') }}
        </v-alert>

        <div class="text-h6 mx-4 mt-6">
          {{ $t('StandardsImportConfig.import_title') }}
        </div>
        <div class="text-body-2 text-medium-emphasis mx-4 mt-1">
          {{ $t('StandardsImportConfig.import_help') }}
        </div>
        <v-switch
          v-model="importEnabled"
          :label="$t('StandardsImportConfig.import_enabled')"
          :loading="importLoading"
          :disabled="importLoading"
          color="primary"
          hide-details
          class="mx-4 my-2"
          data-cy="import-enabled-switch"
          @update:model-value="toggleImportEnabled"
        />

        <v-divider class="my-6" />

        <div class="text-h6 mx-4">
          {{ $t('StandardsImportConfig.mandatory_title') }}
        </div>
        <div class="text-body-2 text-medium-emphasis mx-4 mt-1">
          {{ $t('StandardsImportConfig.mandatory_help') }}
        </div>
        <v-data-table
          :headers="headers"
          :items="catalogues"
          :loading="loading"
          items-per-page="-1"
          class="mx-4 my-4"
        >
          <template #[`item.actions`]="{ item }">
            <v-switch
              v-model="item.mandatory"
              hide-details
              @update:model-value="(value) => toggleMandatory(item, value)"
            />
          </template>
          <template #bottom></template>
        </v-data-table>

        <v-divider class="my-6" />

        <div class="text-h6 mx-4">
          {{ $t('StandardsImportConfig.expected_workbooks_title') }}
        </div>
        <div class="text-body-2 text-medium-emphasis mx-4 mt-1">
          {{ $t('StandardsImportConfig.expected_workbooks_help') }}
        </div>
        <v-data-table
          :headers="headers"
          :items="catalogues"
          :loading="loading"
          items-per-page="-1"
          class="mx-4 my-4"
        >
          <template #[`item.actions`]="{ item }">
            <v-switch
              v-model="item.expects_workbook"
              hide-details
              @update:model-value="
                (value) => toggleExpectedWorkbook(item, value)
              "
            />
          </template>
          <template #bottom></template>
        </v-data-table>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import configApi from '@/api/standardsImport/config'

const { t } = useI18n()
const notificationHub = inject('notificationHub')

const catalogues = ref([])
const loading = ref(false)
const importEnabled = ref(false)
const importLoading = ref(true)

const headers = [
  { key: 'actions', title: '', width: '6%' },
  { key: 'catalogue_name', title: t('StandardsImportConfig.catalogue') },
]

async function loadCatalogues() {
  loading.value = true
  try {
    const resp = await configApi.getCataloguePriority()
    catalogues.value = resp.data
  } finally {
    loading.value = false
  }
}

function mandatoryNames(withoutName, add) {
  const names = catalogues.value
    .filter((item) => item.catalogue_name !== withoutName)
    .filter((item) => item.mandatory)
    .map((item) => item.catalogue_name)
  return add ? [...names, withoutName] : names
}

function expectedWorkbookNames(withoutName, add) {
  const names = catalogues.value
    .filter((item) => item.catalogue_name !== withoutName)
    .filter((item) => item.expects_workbook)
    .map((item) => item.catalogue_name)
  return add ? [...names, withoutName] : names
}

async function toggleMandatory(item, value) {
  const previous = !value
  try {
    await configApi.setMandatoryCatalogues(
      mandatoryNames(item.catalogue_name, value)
    )
    notificationHub.add({
      msg: t('StandardsImportConfig.update_success'),
      type: 'success',
    })
  } catch (error) {
    item.mandatory = previous
    notificationHub.add({
      msg:
        error.response?.data?.message ||
        t('StandardsImportConfig.update_error'),
      type: 'error',
    })
  }
}

async function toggleExpectedWorkbook(item, value) {
  const previous = !value
  try {
    await configApi.setExpectedWorkbooks(
      expectedWorkbookNames(item.catalogue_name, value)
    )
    notificationHub.add({
      msg: t('StandardsImportConfig.update_success'),
      type: 'success',
    })
  } catch (error) {
    item.expects_workbook = previous
    notificationHub.add({
      msg:
        error.response?.data?.message ||
        t('StandardsImportConfig.update_error'),
      type: 'error',
    })
  }
}

async function loadImportEnabled() {
  try {
    const resp = await configApi.getImportEnabled()
    importEnabled.value = resp.data.enabled
  } finally {
    importLoading.value = false
  }
}

async function toggleImportEnabled(value) {
  importLoading.value = true
  try {
    await configApi.setImportEnabled(!!value)
    notificationHub.add({
      msg: t('StandardsImportConfig.update_success'),
      type: 'success',
    })
  } catch (error) {
    importEnabled.value = !value
    notificationHub.add({
      msg:
        error.response?.data?.message ||
        t('StandardsImportConfig.update_error'),
      type: 'error',
    })
  } finally {
    importLoading.value = false
  }
}

loadCatalogues()
loadImportEnabled()
</script>

<style scoped>
.v-data-table {
  width: auto !important;
}
</style>
