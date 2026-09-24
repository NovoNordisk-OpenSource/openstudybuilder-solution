<template>
  <v-card color="dfltBackground">
    <v-card-actions>
      <v-card-title class="title">
        {{ $t('About.title') }}
      </v-card-title>
      <v-spacer />
      <v-btn
        variant="outlined"
        rounded
        elevation="0"
        color="nnBaseBlue"
        class="mr-4"
        @click="emit('close')"
      >
        {{ $t('_global.close') }}
      </v-btn>
    </v-card-actions>
    <v-card-text>
      <v-card rounded="lg" class="pa-4">
        <v-row>
          <v-col cols="3">
            <div class="summary-label">
              {{ $t('About.about_release_number') }}
            </div>
            <div class="summary-value">
              {{ $config.RELEASE_VERSION_NUMBER }}
            </div>
          </v-col>
          <v-col>
            <div class="summary-label">
              {{ $t('About.components_list') }}
            </div>
            <div class="summary-value">
              {{ $config.STUDYBUILDER_VERSION }}
            </div>
          </v-col>
        </v-row>
      </v-card>

      <div class="title mt-8 mb-4">{{ $t('About.components') }}</div>

      <NNTable
        table-id="about-sb-components-table"
        :headers="headers"
        :items="sbComponents"
        disable-filtering
        hide-search-field
        hide-default-switches
        hide-actions-menu
        no-title
        hide-default-footer
        table-height="500px"
      >
        <template #[`item.license`]="{ item }">
          <v-btn
            v-if="item.component"
            variant="outlined"
            rounded
            elevation="0"
            color="nnBaseBlue"
            @click="showLicenseText(item.component, item.name, 'license')"
          >
            {{ $t('_global.view') }}
          </v-btn>
          <div v-else class="ml-2">N/A</div>
        </template>
        <template #[`item.sbom`]="{ item }">
          <v-btn
            v-if="item.component"
            variant="outlined"
            rounded
            elevation="0"
            color="nnBaseBlue"
            @click="showLicenseText(item.component, item.name, 'sbom')"
          >
            {{ $t('_global.view') }}
          </v-btn>
          <div v-else class="ml-2">N/A</div>
        </template>
      </NNTable>
    </v-card-text>
    <v-dialog v-model="showLicense" scrollable max-width="1000">
      <AboutLicense
        :raw-markdown="licenseText"
        :title="licenseTitle"
        @close="showLicense = false"
      />
    </v-dialog>
  </v-card>
</template>

<script setup>
import AboutLicense from './AboutLicense.vue'
import NNTable from '@/components/tools/NNTable.vue'
import axios from 'axios'
import system from '@/api/system'
import { inject, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const emit = defineEmits(['close'])
const $config = inject('$config')

const licenses = ref({})
const licenseText = ref(null)
const licenseTitle = ref('')
const sboms = ref({})
const showLicense = ref(false)
const headers = [
  { title: t('About.component'), key: 'name', width: '1%' },
  { title: t('About.description'), key: 'description', width: '1%' },
  { title: t('About.build_number'), key: 'build_number', width: '1%' },
  { title: t('About.license'), key: 'license', width: '1%' },
  { title: t('About.sbom'), key: 'sbom', width: '1%' },
]
const sbComponents = ref([
  {
    name: t('About.studybuilder'),
    description: t('About.studybuilder_description'),
    build_number: $config.FRONTEND_BUILD_NUMBER,
    component: 'studybuilder',
  },
  {
    name: t('About.documentation-portal'),
    description: t('About.documentation-portal_description'),
    build_number: $config.DOCUMENTATION_PORTAL_BUILD_NUMBER,
    component: 'documentation-portal',
  },
  {
    name: t('About.clinical-mdr-api'),
    description: t('About.clinical-mdr-api_description'),
    build_number: $config.API_BUILD_NUMBER,
    component: 'clinical-mdr-api',
  },
  {
    name: t('About.database'),
    description: t('About.db_description'),
  },
  {
    name: t('About.import_sponsor_data'),
    description: t('About.import_sponsor_data_description'),
    build_number: $config.DATA_IMPORT_BUILD_NUMBER,
    component: 'import_sponsor_data',
  },
  {
    name: t('About.mdr-standards-import'),
    description: t('About.mdr-standards-import_description'),
    build_number: $config.STANDARDS_IMPORT_BUILD_NUMBER,
    component: 'mdr-standards-import',
  },
  {
    name: t('About.neo4j-mdr-db'),
    description: t('About.neo4j-mdr-db_description'),
    build_number: $config.NEO4J_MDR_BUILD_NUMBER,
    component: 'neo4j-mdr-db',
  },
  {
    name: t('About.studybuilder-export'),
    description: t('About.studybuilder-export_description'),
    build_number: $config.STUDYBUILDER_EXPORT_BUILD_NUMBER,
    component: 'studybuilder-export',
  },
])

onMounted(() => {
  system.getInformation().then((response) => {
    sbComponents.value[3].build_number = response.data.db_version
  })
  fetchFiles()
})

async function fetchFiles() {
  const components = [
    'studybuilder',
    'documentation-portal',
    'clinical-mdr-api',
    'import_sponsor_data',
    'mdr-standards-import',
    'neo4j-mdr-db',
    'studybuilder-export',
  ]
  const url =
    process.env.NODE_ENV === 'development'
      ? ''
      : `${location.protocol}//${location.host}`
  for (const component of components) {
    const license = await axios.get(
      `${url}/LICENSE-${component}.md?ts=${Date.now()}`
    )
    licenses.value[component] = license.data
    const sbom = await axios.get(`${url}/sbom-${component}.md?ts=${Date.now()}`)
    sboms.value[component] = sbom.data
  }
}

function showLicenseText(component, title, type) {
  licenseText.value =
    type === 'license' ? licenses.value[component] : sboms.value[component]
  showLicense.value = true
  licenseTitle.value = title
}
</script>

<style scoped>
.title {
  font-weight: 700;
  font-size: 24px;
  line-height: 32px;
  letter-spacing: -0.02em;
  color: rgb(var(--v-theme-nnTrueBlue));
}

.summary-label {
  font-size: 14px;
  color: var(--semantic-system-brand, #001965);
  margin-bottom: 4px;
  font-weight: 400;
  text-transform: none;
}

.summary-value {
  font-weight: 700;
  font-size: 18px;
  line-height: 24px;
  letter-spacing: -0.02em;
  color: var(--semantic-system-brand, #001965);
  min-height: 24px;
}
</style>
