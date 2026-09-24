<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('UsdmPage.title', { version: version }) }}
      <HelpButtonWithPanels :title="$t('_global.help')" :items="helpItems" />
      <v-spacer />
      <v-btn
        class="ml-2"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        :disabled="loading || !rawJson"
        @click="copyAll"
      >
        <v-icon>{{ copied ? 'mdi-check' : 'mdi-content-copy' }}</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ copied ? $t('UsdmPage.copied') : $t('UsdmPage.copy_json') }}
        </v-tooltip>
      </v-btn>
      <v-btn
        class="ml-2"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        :disabled="loading || !data"
        @click="toggleAll(true)"
      >
        <v-icon>mdi-unfold-more-horizontal</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ $t('UsdmPage.expand_all') }}
        </v-tooltip>
      </v-btn>
      <v-btn
        class="ml-2"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        :disabled="loading || !data"
        @click="toggleAll(false)"
      >
        <v-icon>mdi-unfold-less-horizontal</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ $t('UsdmPage.collapse_all') }}
        </v-tooltip>
      </v-btn>
      <v-menu rounded location="bottom">
        <template #activator="{ props }">
          <v-btn
            class="ml-2"
            icon
            size="small"
            variant="outlined"
            color="nnBaseBlue"
            v-bind="props"
            :loading="loading || downloadLoading"
          >
            <v-icon>mdi-download-outline</v-icon>
            <v-tooltip activator="parent" location="top">
              {{ $t('DataTableExportButton.export') }}
            </v-tooltip>
          </v-btn>
        </template>
        <v-list>
          <v-list-item link @click="downloadJSON">
            <v-list-item-title>JSON</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </div>
    <v-progress-circular
      v-if="loading"
      class="ml-6 mt-12"
      size="64"
      color="primary"
      indeterminate
    />
    <v-card v-else-if="data" variant="outlined" class="mt-4">
      <div ref="treeEl" class="json-tree pa-4">
        <JsonNode :value="data" :is-last="true" :depth="0" />
      </div>
    </v-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import study from '@/api/study'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import JsonNode from '@/components/studies/JsonNode.vue'
import exportLoader from '@/utils/exportLoader'
import { notificationHub } from '@/plugins/notificationHub'

const { t } = useI18n()

const studiesGeneralStore = useStudiesGeneralStore()

const helpItems = [
  'UsdmPage.general',
  'UsdmPage.clinical_study_def',
  'UsdmPage.official_protocol_title',
  'UsdmPage.study_protocol_version',
  'UsdmPage.protocol_status',
  'UsdmPage.study_design',
  'UsdmPage.organization_type',
  'UsdmPage.trial_type',
  'UsdmPage.intervention_model_type',
  'UsdmPage.therapeutic_areas',
  'UsdmPage.trial_blinding_schema',
  'UsdmPage.target_study_population',
]
const loading = ref(false)
const downloadLoading = ref(false)
const version = ref(null)
const data = ref(null)
const rawJson = ref('')
const copied = ref(false)
const treeEl = ref(null)

onMounted(() => {
  loading.value = true
  study
    .getDdfUsdmJson(studiesGeneralStore.selectedStudy.uid)
    .then((resp) => {
      data.value = resp.data
      rawJson.value = JSON.stringify(resp.data, null, 2)
      version.value = resp.data.usdmVersion
    })
    .catch(() => {
      notificationHub.add({ msg: t('UsdmPage.load_failed'), type: 'error' })
    })
    .finally(() => {
      loading.value = false
    })
})

function copyAll() {
  navigator.clipboard
    .writeText(rawJson.value)
    .then(() => {
      copied.value = true
      setTimeout(() => (copied.value = false), 1500)
    })
    .catch(() => {
      notificationHub.add({ msg: t('UsdmPage.copy_failed'), type: 'error' })
    })
}

function toggleAll(open) {
  if (!treeEl.value) return
  treeEl.value.querySelectorAll('details').forEach((d) => (d.open = open))
}

function downloadJSON() {
  downloadLoading.value = true
  const fileName = `Study ${studiesGeneralStore.selectedStudy.uid} USDM.json`
  exportLoader.downloadFile(rawJson.value, 'application/json', fileName)
  downloadLoading.value = false
}
</script>

<style scoped>
.json-tree {
  background-color: #f7f8fa;
  color: #001965;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
  overflow: auto;
  max-height: calc(100vh - 220px);
}
</style>
