<template>
  <div>
    <v-row v-if="!doc && !loadedOnce" class="mt-2 ml-2 mr-2">
      <v-col cols="4">
        <v-select
          v-model="data.target_type"
          :items="types"
          :label="$t('OdmViewer.element_type')"
          data-cy="Level"
          density="comfortable"
          clearable
          item-title="name"
          item-value="value"
          class="mt-2"
          :class="{ shake: isShaking && !data.target_type }"
          @update:model-value="setElements()"
        />
      </v-col>
      <v-col cols="4" @click="() => activateShake(!data.target_type)">
        <v-select
          v-model="data.target_uid"
          :items="elements"
          :label="targetUidLabel"
          data-cy="form-name"
          density="comfortable"
          clearable
          class="mt-2"
          item-title="name"
          item-value="uid"
          :loading="elementLoading"
          :disabled="!data.target_type || elementLoading"
          :class="{ shake: isShaking && data.target_type && !data.target_uid }"
          @update:model-value="setElementVersions()"
        >
        </v-select>
      </v-col>
      <v-col cols="4" @click="() => activateShake(!data.target_uid)">
        <v-select
          ref="versionSelect"
          v-model="elementVersion"
          data-cy="version"
          :items="elementFinalVersions"
          :label="$t('OdmViewer.element_version')"
          density="comfortable"
          class="mt-2"
          :disabled="!data.target_uid"
        >
          <template #prepend-item>
            <v-list-item
              style="cursor: pointer"
              @click="
                () => {
                  elementVersion = $t('OdmViewer.latest_version')
                  $refs.versionSelect.blur()
                }
              "
            >
              <v-list-item-title class="ms-4">
                {{ $t('OdmViewer.latest_version') }}
              </v-list-item-title>
            </v-list-item>
            <v-divider v-if="elementFinalVersions.length > 0" />
          </template>

          <template #no-data />
        </v-select>
      </v-col>
    </v-row>
    <v-row
      v-if="!doc && !loadedOnce"
      class="mt-2 ml-2 mr-2"
      @click="() => activateShake(!data.target_uid)"
    >
      <v-col cols="4">
        <v-select
          v-model="data.selectedStylesheet"
          data-cy="stylesheet"
          :items="data.stylesheet"
          density="comfortable"
          :label="$t('OdmViewer.stylesheet')"
          :disabled="!data.target_uid"
        />
      </v-col>
      <v-col cols="4">
        <v-select
          v-model="selectedNamespaces"
          data-cy="allowed-extensions"
          :items="allowedNamespaces"
          :label="$t('OdmViewer.allowed_namespaces')"
          density="comfortable"
          clearable
          :disabled="!data.target_uid"
          multiple
        >
          <template #prepend-item>
            <v-list-item
              :title="
                allNamespacesSelected
                  ? t('_global.unselect_all')
                  : t('_global.select_all')
              "
              @click="toggleNamespace"
            >
              <template #prepend>
                <v-checkbox-btn
                  :indeterminate="
                    !allNamespacesSelected && someNamespacesSelected
                  "
                  :model-value="allNamespacesSelected"
                ></v-checkbox-btn>
              </template>
            </v-list-item>

            <v-divider class="mt-2"></v-divider>
          </template>

          <template #selection="{ internalItem: item, index }">
            <v-chip v-if="index < 2" :text="item.title" />

            <span
              v-if="index === 2"
              class="text-grey text-body-small align-self-center"
            >
              (+{{ selectedNamespaces.length - 2 }}
              {{ selectedNamespaces.length - 2 === 1 ? 'other' : 'others' }})
            </span>
          </template>
        </v-select>
      </v-col>
      <v-col cols="4">
        <v-btn
          :disabled="!data.target_uid"
          data-cy="generate"
          color="secondary"
          rounded="xl"
          :label="$t('_global.load')"
          size="large"
          block
          @click="loadXml"
        >
          {{ $t('OdmViewer.generate') }}
        </v-btn>
      </v-col>
    </v-row>
    <v-row v-else class="mt-0 ml-2">
      <v-btn
        size="small"
        color="primary"
        data-cy="clear-xml"
        class="mr-4 mt-3"
        icon="mdi-arrow-left"
        :title="$t('_global.back')"
        @click="clearXml"
      />
      <v-btn
        size="small"
        color="primary"
        data-cy="load-xml"
        class="mr-4 mt-3"
        icon="mdi-cached"
        :title="$t('_global.reload')"
        :loading="loading"
        @click="loadXml"
      />
      <v-btn
        size="small"
        color="nnGreen1"
        data-cy="download-xml"
        class="ml-4 mt-3"
        :title="$t('DataTableExportButton.export_xml')"
        :loading="xmlDownloadLoading"
        icon="mdi-file-xml-box"
        @click="downloadXml"
      />
      <v-btn
        size="small"
        color="nnGreen1"
        data-cy="download-pdf"
        class="ml-4 mt-3"
        :title="$t('DataTableExportButton.export_pdf')"
        :loading="pdfDownloadLoading"
        icon="mdi-file-pdf-box"
        @click="downloadPdf"
      />
      <v-btn
        size="small"
        color="nnGreen1"
        data-cy="download-html"
        class="ml-4 mt-3"
        :title="$t('DataTableExportButton.export_html')"
        :loading="htmlDownloadLoading"
        icon="mdi-file-document-outline"
        @click="downloadHtml"
      />
      <v-spacer />
      <v-switch
        v-model="showOdmXml"
        data-cy="switch-odm-xml"
        :label="$t('OdmViewer.source_code')"
        class="mr-6"
        inset
      ></v-switch>
    </v-row>
    <div v-show="loading">
      <v-row
        class="align-center justify-center"
        style="text-align: -webkit-center"
      >
        <v-col cols="12" sm="4">
          <div class="text-headline-medium">
            {{ $t('OdmViewer.loading_message') }}
          </div>
          <v-progress-circular
            color="primary"
            indeterminate
            size="128"
            class="ml-4"
          />
        </v-col>
      </v-row>
    </div>
    <div v-show="doc && !showOdmXml" class="mt-4">
      <iframe />
    </div>
    <div v-show="doc && showOdmXml" class="mt-4">
      <v-card color="primary" style="overflow-x: auto">
        <div class="d-flex justify-end">
          <v-btn
            icon="mdi-content-copy"
            data-cy="copy-xml"
            variant="outlined"
            border="0"
            @click="copyXML"
          />
        </div>
        <pre v-show="!loading" class="ml-6 pre" style="color: #ff0">{{
          xmlString
        }}</pre>
      </v-card>
    </div>
  </div>
</template>

<script setup>
import _isEmpty from 'lodash/isEmpty'
import crfs from '@/api/crfs'
import exportLoader from '@/utils/exportLoader'
import { DateTime } from 'luxon'
import { ref, watch, onMounted, computed, inject } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useShake } from '@/composables/shake'

const props = defineProps({
  typeProp: {
    type: String,
    default: null,
  },
  elementProp: {
    type: String,
    default: null,
  },
  refresh: {
    type: String,
    default: null,
  },
})
const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const { isShaking, activateShake } = useShake()

const elementLoading = ref(false)

const notificationHub = inject('notificationHub')

const allowedNamespaces = ref([])
const selectedNamespaces = ref([])
const showOdmXml = ref(false)

const elements = ref([])
const elementFinalVersions = ref(new Set())
let xml = ''
const xmlString = ref('')
const doc = ref(null)
const data = ref({
  target_type: 'form',
  target_uid: null,
  version: '',
  stylesheet: [
    {
      title: t('OdmViewer.html'),
      value: 'html',
    },
    {
      title: t('OdmViewer.crf_with_annotations'),
      value: 'with-annotations',
    },
    {
      title: t('OdmViewer.falcon'),
      value: 'falcon',
    },
  ],
  selectedStylesheet: 'html',
})
const loadedOnce = ref(false)
const loading = ref(false)
const xmlDownloadLoading = ref(false)
const pdfDownloadLoading = ref(false)
const htmlDownloadLoading = ref(false)
const types = [
  { name: t('OdmViewer.collection'), value: 'study_event' },
  { name: t('OdmViewer.form'), value: 'form' },
  { name: t('OdmViewer.item_group'), value: 'item_group' },
  { name: t('OdmViewer.item'), value: 'item' },
]
const elementVersion = ref(t('OdmViewer.latest_version'))
let url = ''

watch(
  () => props.refresh,
  () => {
    if (props.refresh === 'odm-viewer' && url !== '') {
      const stateObj = { id: '100' }
      window.history.replaceState(stateObj, 'Loaded CRF', url)
    }
  }
)

watch(
  () => props.elementProp,
  () => {
    automaticLoad()
  }
)

onMounted(() => {
  automaticLoad()
})

const targetUidLabel = computed(() => {
  switch (data.value.target_type) {
    case 'study_event':
      return t('OdmViewer.collection_name')
    case 'form':
      return t('OdmViewer.form_name')
    case 'item_group':
      return t('OdmViewer.item_group_name')
    case 'item':
      return t('OdmViewer.item_name')
    default:
      return t('OdmViewer.element_name')
  }
})

const allNamespacesSelected = computed(() => {
  return (
    someNamespacesSelected.value &&
    selectedNamespaces.value.length === allowedNamespaces.value.length
  )
})
const someNamespacesSelected = computed(() => {
  return selectedNamespaces.value.length > 0
})

function toggleNamespace() {
  if (allNamespacesSelected.value) {
    selectedNamespaces.value = []
  } else {
    selectedNamespaces.value = [...allowedNamespaces.value]
  }
}

function automaticLoad() {
  setElements()
  data.value.target_type = route.params.type || 'form'
  data.value.target_uid = route.params.uid || null
  if (_isEmpty(allowedNamespaces.value)) {
    crfs
      .getAllNamespaces({
        page_size: 0,
        fields: 'prefix',
      })
      .then((resp) => {
        allowedNamespaces.value = resp.data.items.map((item) => item.prefix)

        selectedNamespaces.value = allowedNamespaces.value
      })
  }
  if (data.value.target_type && data.value.target_uid) {
    loadXml()
  }
}

function setElements() {
  elementLoading.value = true
  data.value.target_uid = null

  const endpointByType = {
    study_event: 'study-events',
    form: 'forms',
    item_group: 'item-groups',
    item: 'items',
  }
  const endpoint = endpointByType[data.value.target_type]
  if (!endpoint) {
    elementLoading.value = false
    return
  }

  const params = {
    page_size: 0,
    fields: 'uid,name',
  }
  crfs
    .get(endpoint, { params })
    .then((resp) => {
      elements.value = resp.data.items
    })
    .finally(() => {
      elementLoading.value = false
    })
}

function setElementVersions() {
  const isFinalVersion = (version) => version.endsWith('.0')

  switch (data.value.target_type) {
    case 'study_event':
      crfs.getCollectionAuditTrail(data.value.target_uid).then((resp) => {
        elementFinalVersions.value = new Set(
          resp.data
            .filter((item) => isFinalVersion(item.version))
            .map((item) => item.version)
        )
      })
      return
    case 'form':
      crfs.getFormAuditTrail(data.value.target_uid).then((resp) => {
        elementFinalVersions.value = new Set(
          resp.data
            .filter((item) => isFinalVersion(item.version))
            .map((item) => item.version)
        )
      })
      return
    case 'item_group':
      crfs.getGroupAuditTrail(data.value.target_uid).then((resp) => {
        elementFinalVersions.value = new Set(
          resp.data
            .filter((item) => isFinalVersion(item.version))
            .map((item) => item.version)
        )
      })
      return
    case 'item':
      crfs.getItemAuditTrail(data.value.target_uid).then((resp) => {
        elementFinalVersions.value = new Set(
          resp.data
            .filter((item) => isFinalVersion(item.version))
            .map((item) => item.version)
        )
      })
      return
  }
}

function getAllowedNamespaces() {
  if (_isEmpty(selectedNamespaces.value)) {
    return ''
  } else if (
    allowedNamespaces.value.length == selectedNamespaces.value.length
  ) {
    return '&allowed_namespaces=*'
  } else {
    return selectedNamespaces.value
      .map((ns) => `&allowed_namespaces=${encodeURIComponent(ns)}`)
      .join('')
  }
}

async function loadXml() {
  loadedOnce.value = true
  doc.value = ''
  loading.value = true
  data.value.version =
    elementVersion.value == t('OdmViewer.latest_version')
      ? ''
      : elementVersion.value

  data.value.allowed_namespaces = getAllowedNamespaces()
  data.value.targets = `targets=${data.value.target_uid},${data.value.version}&`
  router.push({
    name: 'CrfBuilder',
    params: {
      tab: 'odm-viewer',
      type: data.value.target_type,
      uid: data.value.target_uid,
    },
  })
  url = `${window.location.href}`
  try {
    if (data.value.selectedStylesheet === 'html') {
      const resp = await crfs.getReport(data.value)
      doc.value = resp.data
      xmlString.value = resp.data

      let iframe = document.createElement('iframe')
      iframe.classList.add('frame')
      document.querySelector('iframe').replaceWith(iframe)
      let iframeDoc = iframe.contentDocument
      iframeDoc.write(doc.value)
      iframeDoc.close()
    } else {
      const resp = await crfs.getXml(data.value)
      const parser = new DOMParser()
      xmlString.value = resp.data
      xml = parser.parseFromString(resp.data, 'application/xml')
      const xsltProcessor = new XSLTProcessor()
      const xslResp = await crfs.getXsl(data.value.selectedStylesheet)
      const xmlDoc = parser.parseFromString(xslResp.data, 'text/xml')
      xsltProcessor.importStylesheet(xmlDoc)
      doc.value = new XMLSerializer().serializeToString(
        xsltProcessor.transformToDocument(xml)
      )

      let iframe = document.createElement('iframe')
      iframe.classList.add('frame')
      document.querySelector('iframe').replaceWith(iframe)
      let iframeDoc = iframe.contentDocument
      iframeDoc.write(doc.value)
      iframeDoc.close()
    }
  } finally {
    loading.value = false
  }
}

function getDownloadFileName() {
  let stylesheet = '_with_annotations_crf_'
  if (data.value.selectedStylesheet === 'falcon') {
    stylesheet = '_falcon_crf_'
  }
  const templateName = elements.value.filter(
    (el) => el.uid === data.value.target_uid
  )[0].name
  return `${templateName + stylesheet + DateTime.local().toFormat('yyyy-MM-dd HH:mm')}`
}

function downloadHtml() {
  htmlDownloadLoading.value = true
  exportLoader.downloadFile(
    doc.value,
    'text/html',
    getDownloadFileName() + '.html'
  )
  htmlDownloadLoading.value = false
}

function downloadXml() {
  xmlDownloadLoading.value = true
  data.value.allowed_namespaces = getAllowedNamespaces()
  crfs.getXml(data.value).then((resp) => {
    exportLoader.downloadFile(
      resp.data,
      'text/xml',
      getDownloadFileName() + '.xml'
    )
    xmlDownloadLoading.value = false
  })
}

function downloadPdf() {
  pdfDownloadLoading.value = true

  if (data.value.selectedStylesheet === 'html') {
    const iframe = document.querySelector('iframe')
    if (iframe && iframe.contentWindow) {
      iframe.contentWindow.print()
    }
    pdfDownloadLoading.value = false
    return
  }

  data.value.allowed_namespaces = getAllowedNamespaces()
  crfs.getPdf(data.value).then((resp) => {
    exportLoader.downloadFile(
      resp.data,
      'application/pdf',
      getDownloadFileName()
    )
    pdfDownloadLoading.value = false
  })
}

function clearXml() {
  loadedOnce.value = false
  doc.value = null
  url = ''
  router.push({ name: 'Crfs', params: { tab: 'odm-viewer' } })
}

function copyXML() {
  navigator.clipboard.writeText(xmlString.value)
  notificationHub.add({
    msg: t('OdmViewer.source_copied_to_clipboard'),
    type: 'success',
    timeout: 3000,
  })
}
</script>
<style>
.frame {
  aspect-ratio: 16 / 9;
  height: 100%;
  width: 100%;
}
</style>
