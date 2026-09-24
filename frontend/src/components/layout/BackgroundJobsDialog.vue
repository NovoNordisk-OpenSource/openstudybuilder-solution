<template>
  <v-dialog
    :model-value="modelValue"
    max-width="1600px"
    hide-overlay
    class="rounded-0"
    scrollable
    @update:model-value="emit('update:modelValue', $event)"
  >
    <v-card>
      <v-card-title class="dialog-title d-flex align-center">
        {{ $t('BackgroundJobs.title') }}
        <v-btn
          icon="mdi-refresh"
          variant="text"
          :loading="loading"
          :title="$t('_global.reload')"
          class="ml-2"
          @click="refreshJobs"
        />
        <v-spacer />
        <v-btn
          icon="mdi-close"
          variant="text"
          :title="$t('_global.close')"
          @click="emit('update:modelValue', false)"
        />
      </v-card-title>
      <v-divider />
      <v-card-text>
        <NNTable
          table-id="background-jobs-table"
          :headers="headers"
          :items="jobs"
          :items-length="total"
          item-value="uid"
          hide-search-field
          hide-default-switches
          hide-actions-menu
          hide-export-button
          disable-filtering
          :modifiable-table="false"
          :disable-sort="false"
          :items-per-page-options="[10, 25, 50]"
          :loading="loading"
          @filter="fetchJobs"
        >
          <template #[`item.status`]="{ item }">
            <div class="d-flex align-center ga-1">
              <v-chip size="small" :color="statusColor(item.status)" label>
                {{ item.status }}
              </v-chip>
              <v-btn
                icon="mdi-information-outline"
                size="small"
                variant="text"
                color="grey-darken-1"
                :title="$t('BackgroundJobs.details')"
                @click="openJobDetails(item.uid)"
              />
            </div>
          </template>
          <template #[`item.started_at`]="{ item }">
            {{ $filters.date(item.started_at) }}
          </template>
          <template #[`item.ended_at`]="{ item }">
            {{
              item.ended_at ? $filters.date(item.ended_at) : $t('_global.na')
            }}
          </template>
        </NNTable>
      </v-card-text>
    </v-card>
  </v-dialog>

  <v-dialog v-model="showJobDetails" max-width="1100px" scrollable>
    <v-card>
      <v-card-title class="dialog-title d-flex align-center">
        {{ $t('BackgroundJobs.details') }}
        <v-spacer />
        <v-btn
          icon="mdi-close"
          variant="text"
          :title="$t('_global.close')"
          @click="showJobDetails = false"
        />
      </v-card-title>
      <v-divider />
      <v-card-text>
        <v-progress-linear v-if="detailsLoading" indeterminate />
        <template v-else>
          <v-row v-if="jobDetails" class="mt-0">
            <v-col cols="8">
              <div class="text-label-large text-disabled mb-1">
                {{ $t('BackgroundJobs.name') }}
              </div>
              <div class="text-body-large">{{ jobDetails.job_name }}</div>
            </v-col>
            <v-col cols="4">
              <div class="text-label-large text-disabled mb-1">
                {{ $t('_global.status') }}
              </div>
              <v-chip
                size="small"
                :color="statusColor(jobDetails.status)"
                label
              >
                {{ jobDetails.status }}
              </v-chip>
            </v-col>
            <v-col cols="12" md="4">
              <div class="text-label-large text-disabled mb-1">
                {{ $t('BackgroundJobs.started_by') }}
              </div>
              <div class="text-body-large">{{ jobDetails.author_id }}</div>
            </v-col>
            <v-col cols="12" md="4">
              <div class="text-label-large text-disabled mb-1">
                {{ $t('BackgroundJobs.started_at') }}
              </div>
              <div class="text-body-large">
                {{ $filters.date(jobDetails.started_at) }}
              </div>
            </v-col>
            <v-col cols="12" md="4">
              <div class="text-label-large text-disabled mb-1">
                {{ $t('BackgroundJobs.ended_at') }}
              </div>
              <div class="text-body-large">
                {{
                  jobDetails.ended_at
                    ? $filters.date(jobDetails.ended_at)
                    : $t('_global.na')
                }}
              </div>
            </v-col>
            <v-col cols="12">
              <div class="text-label-large text-disabled mb-1">
                {{ $t('BackgroundJobs.log') }}
              </div>
              <v-card
                variant="outlined"
                rounded="lg"
                class="pa-3 bg-grey-lighten-5"
              >
                <pre
                  class="job-details-content text-body-medium my-0"
                  v-html="formatLogHtml(jobDetails.log)"
                />
              </v-card>
            </v-col>
          </v-row>
        </template>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import jobsApi from '@/api/jobs'
import NNTable from '@/components/tools/NNTable.vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
})
const emit = defineEmits(['update:modelValue'])
const { t } = useI18n()

const jobs = ref([])
const total = ref(0)
const loading = ref(false)
const tableOptions = ref({})
const showJobDetails = ref(false)
const jobDetails = ref(null)
const detailsLoading = ref(false)

const headers = computed(() => [
  { title: t('BackgroundJobs.name'), key: 'job_name' },
  { title: t('_global.status'), key: 'status' },
  { title: t('BackgroundJobs.started_by'), key: 'author_id' },
  { title: t('BackgroundJobs.started_at'), key: 'started_at' },
  { title: t('BackgroundJobs.ended_at'), key: 'ended_at' },
])

async function fetchJobs(...args) {
  const [, options = {}] = args
  tableOptions.value = options
  const { page = 1, itemsPerPage: pageSize = 10, sortBy = [] } = options
  if (!props.modelValue) {
    return
  }

  loading.value = true
  try {
    const params = {
      page_number: page,
      page_size: pageSize,
    }
    const [sort] = sortBy
    if (sort) {
      params.sort_by = JSON.stringify({ [sort.key]: sort.order === 'asc' })
    }
    const response = await jobsApi.getJobs(params)
    jobs.value = response.data.items
    total.value = response.data.total
  } finally {
    loading.value = false
  }
}

function refreshJobs() {
  fetchJobs(null, tableOptions.value)
}

async function openJobDetails(jobUid) {
  showJobDetails.value = true
  detailsLoading.value = true
  jobDetails.value = null
  try {
    const response = await jobsApi.getJob(jobUid)
    jobDetails.value = response.data
  } finally {
    detailsLoading.value = false
  }
}

function statusColor(status) {
  if (status === 'COMPLETED') {
    return 'success'
  }
  if (status === 'FAILED') {
    return 'error'
  }
  return 'info'
}

function escapeHtml(text) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

function formatLogHtml(log) {
  const text = Array.isArray(log) ? log.join('\n') : log || t('_global.na')
  return text
    .split('\n')
    .map((line) => {
      const escaped = escapeHtml(line)
      if (line.includes(' ERROR ')) {
        return `<span style="color: red">${escaped}</span>`
      }
      if (line.includes(' WARNING ')) {
        return `<span style="color: darkorange">${escaped}</span>`
      }
      if (line.includes(' DEBUG ')) {
        return `<span style="color: gray">${escaped}</span>`
      }
      return escaped
    })
    .join('\n')
}
</script>

<style scoped>
.job-details-content {
  max-height: 320px;
  overflow: auto;
  white-space: pre-wrap;
}
</style>
