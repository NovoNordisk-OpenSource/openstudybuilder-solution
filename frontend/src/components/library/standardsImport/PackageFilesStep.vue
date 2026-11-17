<template>
  <div>
    <v-row align="start">
      <v-col cols="12" md="6">
        <v-file-input
          v-model="selectedFiles"
          density="compact"
          accept=".json"
          multiple
          chips
          show-size
          prepend-icon=""
          prepend-inner-icon="mdi-paperclip"
          :label="$t('StandardsImport.choose_package_files')"
          :hint="$t('StandardsImport.package_files_hint')"
          persistent-hint
          :disabled="disabled"
        />
      </v-col>
      <v-col cols="auto">
        <v-btn
          color="secondary"
          variant="flat"
          rounded="xl"
          :loading="uploading"
          :disabled="disabled || !selectedFiles.length"
          data-cy="standards-import-upload-package-files"
          @click="uploadSelected"
        >
          {{ $t('StandardsImport.upload') }}
        </v-btn>
      </v-col>
      <v-col cols="auto">
        <v-btn variant="outlined" rounded="xl" :loading="loading" @click="load">
          {{ $t('StandardsImport.refresh') }}
        </v-btn>
      </v-col>
    </v-row>

    <v-alert
      v-for="(failure, index) in failures"
      :key="index"
      class="mt-2"
      type="error"
      variant="tonal"
      closable
      :text="`${failure.name}: ${failure.message}`"
    />

    <v-data-table
      class="mt-4"
      :headers="headers"
      :items="files"
      :loading="loading"
      item-value="uid"
      :items-per-page="-1"
      :no-data-text="$t('StandardsImport.no_package_files')"
      hide-default-footer
      data-cy="standards-import-package-files-table"
    >
      <template #[`item.catalogue`]="{ item }">
        {{ item.catalogue }}
        <v-tooltip
          v-if="item.replaced_previous_upload"
          location="top"
          :text="$t('StandardsImport.replaced_previous_upload')"
        >
          <template #activator="{ props: tooltipProps }">
            <v-icon
              v-bind="tooltipProps"
              icon="mdi-refresh"
              size="small"
              class="ml-1"
            />
          </template>
        </v-tooltip>
      </template>
      <template #[`item.size_bytes`]="{ item }">
        {{ formatSize(item.size_bytes) }}
      </template>
      <template #[`item.uploaded_at`]="{ item }">
        {{ item.uploaded_at ? $filters.date(item.uploaded_at) : '-' }}
      </template>
    </v-data-table>
  </div>
</template>

<script setup>
import { inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import packagesApi from '@/api/standardsImport/packages'

const { t } = useI18n()
const notificationHub = inject('notificationHub')

const props = defineProps({
  effectiveDate: {
    type: String,
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})
const emit = defineEmits(['effectiveDateDetected', 'uploaded'])

const headers = [
  { title: t('StandardsImport.catalogue'), key: 'catalogue' },
  { title: t('StandardsImport.package_name'), key: 'package_name' },
  { title: t('StandardsImport.codelist_count'), key: 'codelist_count' },
  { title: t('StandardsImport.term_count'), key: 'term_count' },
  { title: t('StandardsImport.size'), key: 'size_bytes' },
  { title: t('StandardsImport.uploaded_at'), key: 'uploaded_at' },
]

const files = ref([])
const selectedFiles = ref([])
const loading = ref(false)
const uploading = ref(false)
const failures = ref([])

const formatSize = (bytes) =>
  bytes === null || bytes === undefined
    ? '-'
    : `${Math.round(bytes / 1024).toLocaleString()} kB`

function load() {
  if (!props.effectiveDate) {
    files.value = []
    return
  }
  loading.value = true
  packagesApi
    .getAll({ effective_date: props.effectiveDate })
    .then((response) => {
      files.value = response.data || []
    })
    .finally(() => {
      loading.value = false
    })
}

const readAsText = (file) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = () => reject(reader.error)
    reader.readAsText(file)
  })

// The API derives both catalogue and effective date from each file's own
// contents, so files are uploaded one call at a time with nothing else to say
// about them. Sequentially, so a release's files cannot race each other into
// the staging database.
async function uploadSelected() {
  uploading.value = true
  failures.value = []
  const uploaded = []
  for (const file of selectedFiles.value) {
    try {
      const content = await readAsText(file)
      const { data } = await packagesApi.uploadFile(content)
      uploaded.push(data)
    } catch (error) {
      failures.value.push({
        name: file.name,
        message:
          error.response?.data?.message ||
          error.message ||
          t('StandardsImport.upload_error'),
      })
    }
  }
  uploading.value = false
  selectedFiles.value = []

  if (uploaded.length) {
    notificationHub.add({
      type: 'success',
      msg: t('StandardsImport.upload_success', { count: uploaded.length }),
    })
    // A brand-new release learns its effective date here, from the first file
    // that landed.
    if (!props.effectiveDate) {
      emit('effectiveDateDetected', uploaded[0].effective_date)
    }
    // Files whose own effective date is not the release on screen went
    // somewhere else entirely — say so rather than leaving them unaccounted for.
    const strays = [
      ...new Set(
        uploaded
          .map((file) => file.effective_date)
          .filter(
            (date) =>
              date !== (props.effectiveDate || uploaded[0].effective_date)
          )
      ),
    ]
    for (const date of strays) {
      notificationHub.add({
        type: 'warning',
        msg: t('StandardsImport.date_mismatch_warning', { date }),
      })
    }
    emit('uploaded')
    load()
  }
}

watch(() => props.effectiveDate, load)
onMounted(load)
</script>
