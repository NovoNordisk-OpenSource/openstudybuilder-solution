<template>
  <div>
    <!-- <v-app-bar flat color="#e5e5e5" class="mt-2" style="height: 60px"> -->
    <v-row v-if="!doc" class="mt-2 ml-2">
      <v-col cols="2">
        <v-select
          v-model="data.target_type"
          :items="types"
          :label="$t('OdmViewer.odm_element_type')"
          density="comfortable"
          clearable
          item-title="name"
          item-value="value"
          class="mt-2"
          @update:model-value="setElements()"
        />
      </v-col>
      <v-col cols="2">
        <v-select
          v-model="data.target_uid"
          :items="elements"
          :label="$t('OdmViewer.odm_element_name')"
          density="comfortable"
          clearable
          class="mt-2"
          item-title="name"
          item-value="uid"
        />
      </v-col>
      <v-col cols="2">
        <v-select
          v-model="element_status"
          :items="elementStatuses"
          :label="$t('OdmViewer.element_status')"
          density="comfortable"
          class="mt-2"
        />
      </v-col>
    </v-row>
    <v-row v-if="!doc" class="mt-2 ml-2">
      <v-col cols="2">
        <v-row>
          <v-select
            v-model="selectedNamespaces"
            :items="allowedNamespaces"
            :label="$t('OdmViewer.allowed_namespaces')"
            density="comfortable"
            clearable
            multiple
            chips
          />
        </v-row>
      </v-col>
      <v-col cols="2">
        <v-row>
          <v-radio-group
            v-model="data.stylesheet"
            :label="$t('OdmViewer.stylesheet')"
            inline
            row
          >
            <v-radio :label="$t('OdmViewer.blank')" value="blank" />
            <v-radio :label="$t('OdmViewer.sdtm')" value="sdtm" />
          </v-radio-group>
        </v-row>
      </v-col>
      <v-col cols="2">
        <v-row justify="center">
          <v-btn
            :disabled="!data.target_uid"
            color="primary"
            :label="$t('_global.load')"
            @click="loadXml"
          >
            {{ $t('OdmViewer.load') }}
          </v-btn>
        </v-row>
      </v-col>
    </v-row>
    <v-row v-else class="mt-0 ml-2">
      <v-btn
        class="ml-2 mt-1"
        size="small"
        color="primary"
        :label="$t('_global.load')"
        @click="clearXml"
      >
        {{ $t('OdmViewer.load_another') }}
      </v-btn>
      <v-btn
        v-show="doc"
        size="small"
        color="nnGreen1"
        class="ml-4 white--text"
        :title="$t('DataTableExportButton.export_xml')"
        :loading="xmlDownloadLoading"
        icon="mdi-file-xml-box"
        @click="downloadXml"
      />
      <v-btn
        v-show="doc !== ''"
        size="small"
        color="nnGreen1"
        class="ml-4 white--text"
        :title="$t('DataTableExportButton.export_pdf')"
        :loading="pdfDownloadLoading"
        icon="mdi-file-pdf-box"
        @click="downloadPdf"
      />
      <v-btn
        v-show="doc !== ''"
        size="small"
        color="nnGreen1"
        class="ml-4 white--text"
        :title="$t('DataTableExportButton.export_html')"
        :loading="htmlDownloadLoading"
        icon="mdi-file-document-outline"
        @click="downloadHtml"
      />
    </v-row>
    <div v-show="loading">
      <v-row align="center" justify="center" style="text-align: -webkit-center">
        <v-col cols="12" sm="4">
          <div class="text-h5">
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
    <div v-show="doc" class="mt-4">
      <iframe />
    </div>
  </div>
</template>

<script setup>
import _isEmpty from 'lodash/isEmpty'
import crfs from '@/api/crfs'
import statuses from '@/constants/statuses'
import exportLoader from '@/utils/exportLoader'
import { DateTime } from 'luxon'
import { ref, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

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
const emit = defineEmits(['clearUid'])
const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const elementStatuses = [
  statuses.LATEST,
  statuses.FINAL,
  statuses.DRAFT,
  statuses.RETIRED,
]

const allowedNamespaces = ref([])
const selectedNamespaces = ref([])

const elements = ref([])
let xml = ''
const doc = ref(null)
const data = ref({
  target_type: 'study_event',
  stylesheet: 'sdtm',
  export_to: 'v1',
})
const loading = ref(false)
const xmlDownloadLoading = ref(false)
const pdfDownloadLoading = ref(false)
const htmlDownloadLoading = ref(false)
const types = [
  { name: t('OdmViewer.template'), value: 'study_event' },
  { name: t('OdmViewer.form'), value: 'form' },
  { name: t('OdmViewer.item_group'), value: 'item_group' },
  { name: t('OdmViewer.item'), value: 'item' },
]
const element_status = ref(statuses.LATEST)
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

function automaticLoad() {
  data.value.target_type = route.params.type || 'study_event'
  data.value.target_uid = route.params.uid
  setElements()
  if (_isEmpty(allowedNamespaces.value)) {
    crfs.getAllNamespaces({ page_size: 0 }).then((resp) => {
      allowedNamespaces.value = resp.data.items.map((item) => item.prefix)

      selectedNamespaces.value = allowedNamespaces.value
    })
  }
  if (data.value.target_type && data.value.target_uid) {
    loadXml()
  }
}

function setElements() {
  if (data.value.target_type) {
    const params = { page_size: 0 }
    switch (data.value.target_type) {
      case 'study_event':
        crfs.get('study-events', { params }).then((resp) => {
          elements.value = resp.data.items
        })
        return
      case 'form':
        crfs.get('forms', { params }).then((resp) => {
          elements.value = resp.data.items
        })
        return
      case 'item_group':
        crfs.get('item-groups', { params }).then((resp) => {
          elements.value = resp.data.items
        })
        return
      case 'item':
        crfs.get('items', { params }).then((resp) => {
          elements.value = resp.data.items
        })
    }
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
  doc.value = ''
  loading.value = true
  data.value.status = element_status.value.toLowerCase()
  data.value.allowed_namespaces = getAllowedNamespaces()
  crfs.getXml(data.value).then((resp) => {
    const parser = new DOMParser()
    xml = parser.parseFromString(resp.data, 'application/xml')
    const xsltProcessor = new XSLTProcessor()
    crfs.getXsl(data.value.stylesheet).then((resp) => {
      const xmlDoc = parser.parseFromString(resp.data, 'text/xml')
      xsltProcessor.importStylesheet(xmlDoc)
      doc.value = new XMLSerializer().serializeToString(
        xsltProcessor.transformToDocument(xml)
      )

      var iframe = document.createElement('iframe')
      iframe.classList.add('frame')
      document.querySelector('iframe').replaceWith(iframe)
      var iframeDoc = iframe.contentDocument
      iframeDoc.write(doc.value)
      iframeDoc.close()

      loading.value = false
    })
  })
  router.push({
    name: 'Crfs',
    params: {
      tab: 'odm-viewer',
      type: data.value.target_type,
      uid: data.value.target_uid,
    },
  })
  url = `${window.location.href}`
  emit('clearUid')
}

function getDownloadFileName() {
  const stylesheet =
    data.value.stylesheet === 'odm_template_sdtmcrf.xsl'
      ? '_sdtm_crf_'
      : '_blank_crf_'
  const templateName = elements.value.filter(
    (el) => el.uid === data.value.target_uid
  )[0].name
  return `${templateName + stylesheet + DateTime.local().toFormat('yyyy-MM-dd HH:mm')}`
}

function downloadHtml() {
  htmlDownloadLoading.value = true
  exportLoader.downloadFile(doc.value, 'text/html', getDownloadFileName())
  htmlDownloadLoading.value = false
}

function downloadXml() {
  xmlDownloadLoading.value = true
  data.value.allowed_namespaces = getAllowedNamespaces()
  crfs.getXml(data.value).then((resp) => {
    exportLoader.downloadFile(resp.data, 'text/xml', getDownloadFileName())
    xmlDownloadLoading.value = false
  })
}

function downloadPdf() {
  pdfDownloadLoading.value = true
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
  doc.value = null
  url = ''
  router.push({ name: 'Crfs', params: { tab: 'odm-viewer' } })
}
</script>
<style>
.frame {
  width: 100%;
  min-height: 1000px;
}
</style>
