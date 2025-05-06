<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('UsdmPage.title', { version: version }) }}
      <HelpButtonWithPanels :title="$t('_global.help')" :items="helpItems" />
      <v-spacer />
      <v-menu rounded location="bottom">
        <template #activator="{ props }">
          <v-btn
            class="ml-2"
            size="small"
            variant="outlined"
            color="nnBaseBlue"
            v-bind="props"
            :title="$t('DataTableExportButton.export')"
            icon="mdi-download-outline"
            :loading="loading || downloadLoading"
          />
        </template>
        <v-list>
          <v-list-item link @click="downloadJSON">
            <v-list-item-title>JSON</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </div>
    <v-row>
      <v-col cols="5"></v-col>
      <v-col>
        <v-progress-circular
          v-if="loading"
          class="ml-6 mt-12"
          size="128"
          color="primary"
          indeterminate
        />
      </v-col>
    </v-row>
    <v-card color="primary">
      <pre v-show="!loading" id="json-data" class="ml-6 mt-6 pre" />
    </v-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import study from '@/api/study'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import exportLoader from '@/utils/exportLoader'

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

onMounted(() => {
  loading.value = true
  const preElement = document.getElementById('json-data')
  study.getDdfUsdmJson(studiesGeneralStore.selectedStudy.uid).then((resp) => {
    preElement.innerText = JSON.stringify(resp.data.study, null, 2)
    version.value = resp.data.usdmVersion
    loading.value = false
  })
})

function downloadJSON() {
  downloadLoading.value = true
  study.getDdfUsdmJson(studiesGeneralStore.selectedStudy.uid).then((resp) => {
    download(JSON.stringify(resp.data))
  })
}

function download(response) {
  const fileName = `Study ${studiesGeneralStore.selectedStudy.uid} USDM.json`
  exportLoader.downloadFile(response, 'application/json', fileName)
  downloadLoading.value = false
}
</script>

<style scoped>
.pre {
  white-space: pre-wrap;
  font-size: 18px;
  color: yellow;
}
</style>
