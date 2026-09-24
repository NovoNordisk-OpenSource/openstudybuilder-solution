<template>
  <div>
    <v-row class="mt-2 ml-2 mr-2" style="display: flex">
      <v-col cols="3">
        <v-select
          v-model="selectedCollections"
          :items="collections"
          :label="$t('OdmViewer.crf_collection')"
          clearable
          multiple
          return-object
          item-title="name"
          item-value="value"
          class="mt-2"
          :loading="collectionLoading"
          :disabled="collectionLoading"
          :class="{ shake: isShaking && selectedCollections.length === 0 }"
        >
          <template v-if="collections.length > 0" #prepend-item>
            <v-list-item
              :title="
                allCollectionsSelected
                  ? t('_global.unselect_all')
                  : t('_global.select_all')
              "
              @click="toggleCollection"
            >
              <template #prepend>
                <v-checkbox-btn
                  :indeterminate="
                    !allCollectionsSelected && someCollectionsSelected
                  "
                  :model-value="allCollectionsSelected"
                ></v-checkbox-btn>
              </template>
            </v-list-item>

            <v-divider class="mt-2"></v-divider>
          </template>

          <template #selection="{ internalItem: item, index }">
            <div v-if="index === 0">
              <span>{{
                item.title.length > 25
                  ? item.title.substring(0, 25) + '...'
                  : item.title
              }}</span>
            </div>
            <span v-if="index === 1" class="grey--text text-body-small mr-1">
              (+{{ selectedCollections.length - 1 }})
            </span>
          </template>
        </v-select>
      </v-col>
      <v-col
        cols="3"
        @click="() => activateShake(selectedCollections.length === 0)"
      >
        <v-autocomplete
          v-model="selectedForms"
          :items="forms"
          :label="$t('OdmViewer.forms')"
          clearable
          multiple
          class="mt-2"
          item-title="name"
          item-value="uid"
          :disabled="selectedCollections.length === 0"
          :class="{
            shake:
              isShaking &&
              selectedCollections.length !== 0 &&
              selectedForms.length === 0,
          }"
        >
          <template v-if="forms.length > 0" #prepend-item>
            <v-list-item
              :title="
                allFormsSelected
                  ? t('_global.unselect_all')
                  : t('_global.select_all')
              "
              @click="toggleForm"
            >
              <template #prepend>
                <v-checkbox-btn
                  :indeterminate="!allFormsSelected && someFormsSelected"
                  :model-value="allFormsSelected"
                ></v-checkbox-btn>
              </template>
            </v-list-item>

            <v-divider class="mt-2"></v-divider>
          </template>

          <template #selection="{ internalItem: item, index }">
            <div v-if="index === 0">
              <span>{{
                item.title.length > 25
                  ? item.title.substring(0, 25) + '...'
                  : item.title
              }}</span>
            </div>
            <span v-if="index === 1" class="grey--text text-body-small mr-1">
              (+{{ selectedForms.length - 1 }})
            </span>
          </template>
        </v-autocomplete>
      </v-col>
      <v-col
        cols="3"
        @click="
          () =>
            activateShake(
              selectedCollections.length === 0 || selectedForms.length === 0
            )
        "
      >
        <v-select
          v-model="data.selectedStylesheet"
          :items="data.stylesheet"
          class="mt-2"
          :label="$t('OdmViewer.stylesheet')"
          :disabled="selectedForms.length === 0"
        />
      </v-col>
      <v-col
        cols="2"
        @click="
          () =>
            activateShake(
              selectedCollections.length === 0 || selectedForms.length === 0
            )
        "
      >
        <v-btn
          color="secondary"
          :label="$t('_global.load')"
          variant="flat"
          rounded="xl"
          class="mt-2"
          :disabled="selectedForms.length === 0"
          @click="loadXml"
        >
          {{ $t('OdmViewer.generate') }}
        </v-btn>
      </v-col>
      <v-col
        cols="1"
        @click="
          () =>
            activateShake(
              selectedCollections.length === 0 || selectedForms.length === 0
            )
        "
      >
        <v-menu rounded offset-y>
          <template #activator="{ props }">
            <slot name="button" :props="props">
              <v-btn
                class="mr-4 mt-2"
                size="small"
                variant="outlined"
                color="nnBaseBlue"
                v-bind="props"
                :title="$t('DataTableExportButton.export')"
                data-cy="table-export-button"
                icon="mdi-download-outline"
                :disabled="!doc"
                :loading="loading || exportLoading"
              />
            </slot>
          </template>
          <v-list>
            <v-list-item link color="nnBaseBlue" @click="downloadXml">
              <v-list-item-title class="nnBaseBlue">
                <v-icon color="nnBaseBlue" class="mr-2">
                  mdi-file-xml-box
                </v-icon>
                {{ $t('DataTableExportButton.export_xml') }}
              </v-list-item-title>
            </v-list-item>
            <v-list-item link color="nnBaseBlue" @click="downloadPdf">
              <v-list-item-title class="nnBaseBlue">
                <v-icon color="nnBaseBlue" class="mr-2">
                  mdi-file-pdf-box
                </v-icon>
                {{ $t('DataTableExportButton.export_pdf') }}
              </v-list-item-title>
            </v-list-item>
            <v-list-item link color="nnBaseBlue" @click="downloadHtml">
              <v-list-item-title class="nnBaseBlue">
                <v-icon color="nnBaseBlue" class="mr-2">
                  mdi-file-document-outline
                </v-icon>
                {{ $t('DataTableExportButton.export_html') }}
              </v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
      </v-col>
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
    <div v-show="doc" class="mt-4">
      <iframe />
    </div>
  </div>
</template>

<script setup>
import crfs from '@/api/crfs'
import exportLoader from '@/utils/exportLoader'
import { DateTime } from 'luxon'
import { ref, onMounted, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useShake } from '@/composables/shake'

const { t } = useI18n()

const { isShaking, activateShake } = useShake()

const collectionLoading = ref(false)

const selectedCollections = ref([])
const collections = ref([])
const selectedForms = ref([])
const forms = ref([])

let xml = ''
const xmlString = ref('')
const doc = ref(null)
const data = ref({
  target_type: 'form',
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
const loading = ref(false)
const exportLoading = ref(false)

onMounted(() => {
  getCollections()
})

watch(selectedCollections, () => {
  getFormsForCollections()
})

const allCollectionsSelected = computed(() => {
  return (
    someCollectionsSelected.value &&
    selectedCollections.value.length === collections.value.length
  )
})
const someCollectionsSelected = computed(() => {
  return selectedCollections.value.length > 0
})
function toggleCollection() {
  if (allCollectionsSelected.value) {
    selectedCollections.value = []
  } else {
    selectedCollections.value = [...collections.value]
  }
}

const allFormsSelected = computed(() => {
  return (
    someFormsSelected.value && selectedForms.value.length === forms.value.length
  )
})
const someFormsSelected = computed(() => {
  return selectedForms.value.length > 0
})
function toggleForm() {
  if (allFormsSelected.value) {
    selectedForms.value = []
  } else {
    selectedForms.value = forms.value.map((form) => form.uid)
  }
}

function getCollections() {
  collectionLoading.value = true
  const params = {
    page_size: 0,
    fields: 'uid,name,forms',
  }
  crfs
    .get('study-events', { params })
    .then((resp) => {
      collections.value = resp.data.items
    })
    .finally(() => {
      collectionLoading.value = false
    })
}

function getFormsForCollections() {
  try {
    forms.value = []
    selectedForms.value = []
    selectedCollections.value.forEach((collection) => {
      forms.value = [...forms.value, ...collection.forms]
    })
    forms.value = forms.value.filter(
      (form1, i, arr) => arr.findIndex((form2) => form2.uid === form1.uid) === i
    )
  } catch (error) {
    console.error(error)
  }
}

async function loadXml() {
  doc.value = ''
  loading.value = true
  data.value.allowed_namespaces = '&allowed_namespaces=*'
  data.value.targets = ''
  for (const form of selectedForms.value) {
    data.value.targets += `targets=${form}&`
  }
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
  return `${'CRF_Export' + stylesheet + DateTime.local().toFormat('yyyy-MM-dd HH:mm')}`
}

function downloadHtml() {
  exportLoading.value = true
  exportLoader.downloadFile(
    doc.value,
    'text/html',
    getDownloadFileName() + '.html'
  )
  exportLoading.value = false
}

function downloadXml() {
  exportLoading.value = true
  data.value.allowed_namespaces = '&allowed_namespaces=*'
  crfs.getXml(data.value).then((resp) => {
    exportLoader.downloadFile(
      resp.data,
      'text/xml',
      getDownloadFileName() + '.xml'
    )
    exportLoading.value = false
  })
}

function downloadPdf() {
  exportLoading.value = true
  data.value.allowed_namespaces = '&allowed_namespaces=*'
  crfs.getPdf(data.value).then((resp) => {
    exportLoader.downloadFile(
      resp.data,
      'application/pdf',
      getDownloadFileName()
    )
    exportLoading.value = false
  })
}
</script>
<style>
.frame {
  width: 100%;
  min-height: 1000px;
}
</style>
