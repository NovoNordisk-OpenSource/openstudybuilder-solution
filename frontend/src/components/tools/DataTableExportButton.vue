<template>
  <v-menu rounded offset-y>
    <template #activator="{ props }">
      <slot name="button" :props="props">
        <v-btn
          class="ml-2"
          icon
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          v-bind="props"
          :title="$t('DataTableExportButton.export')"
          data-cy="table-export-button"
          :loading="loading"
        >
          <v-icon>mdi-download-outline</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('DataTableExportButton.export') }}
          </v-tooltip>
        </v-btn>
      </slot>
    </template>
    <v-list>
      <v-list-item
        v-for="(format, index) in downloadFormats"
        :key="index"
        link
        color="nnBaseBlue"
        @click="exportContent(format)"
      >
        <v-list-item-title class="nnBaseBlue">
          <v-icon color="nnBaseBlue" class="mr-2">
            mdi-download-outline
          </v-icon>
          {{ format.name }}
        </v-list-item-title>
      </v-list-item>
    </v-list>
  </v-menu>
</template>

<script setup>
import { DateTime } from 'luxon'
import writeExcelFile from 'write-excel-file/browser'
import repository from '@/api/repository'
import exportLoader from '@/utils/exportLoader'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { ref } from 'vue'

const emit = defineEmits(['export'])
const studiesGeneralStore = useStudiesGeneralStore()

const props = defineProps({
  objectLabel: {
    type: String,
    default: '',
  },
  dataUrl: {
    type: String,
    default: '',
  },
  dataUrlParams: {
    type: Object,
    default: () => {},
  },
  headers: {
    type: Array,
    required: false,
    default: () => [],
  },
  items: {
    type: Array,
    required: false,
    default: () => [],
  },
  filters: {
    type: String,
    required: false,
    default: null,
  },
  includeExportFields: {
    type: Boolean,
    default: false,
  },
})

const downloadFormats = [
  { name: 'CSV', mediaType: 'text/csv', extension: 'csv' },
  { name: 'JSON', mediaType: 'application/json', extension: 'json' },
  { name: 'XML', mediaType: 'text/xml', extension: 'xml' },
  {
    name: 'EXCEL',
    mediaType:
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    extension: 'xlsx',
  },
]
const loading = ref(false)

function createDownloadLink(content, format) {
  const today = DateTime.local().toFormat('yyyy-MM-dd')
  let fileName = `${props.objectLabel} ${today}.${format.extension}`
  if (window.location.pathname.startsWith('/studies')) {
    fileName =
      `${studiesGeneralStore.selectedStudy ? studiesGeneralStore.studyId + ' ' : ''}` +
      fileName
  }
  exportLoader.downloadFile(content, format.mediaType, fileName)
}

function getValue(header, item) {
  let value = item
  header.key.split('.').forEach((part) => {
    if (value !== undefined && value !== null) {
      value = value[part]
    }
  })
  if (value !== undefined) {
    if (typeof value === 'string') {
      return value.replace(/[\n]/g, '')
    }
    return value
  }
  return ''
}

function convertHeaderLabelToName(label) {
  return label.toLowerCase().replace(/\s/g, '-')
}

function exportToCSV() {
  const delimiter = ';'
  let csv =
    props.headers
      .filter((header) => header.key !== 'actions')
      .map((header) => header.title)
      .join(delimiter) + '\n'
  props.items.forEach((item) => {
    let row = ''
    props.headers.forEach((header) => {
      if (header.key === 'actions') {
        return
      }
      if (row !== '') {
        row += delimiter
      }
      const value = getValue(header, item)
      if (value !== undefined) {
        row += `"${value}"`
      }
    })
    csv += row + '\n'
  })
  return csv
}

async function exportToXSLX() {
  const headers = props.headers
    .filter((header) => header.key !== 'actions')
    .map((header) => header.title)
  const rows = props.items.map((item) =>
    props.headers
      .filter((header) => header.key !== 'actions')
      .map((header) => getValue(header, item))
  )
  return await writeExcelFile([headers, ...rows]).toBlob()
}

/*
 ** Manual XML export.
 ** We could have used a DOM element and then use XMLSerializer() but the output is not formatted properly so...
 */
function exportToXML() {
  let result = '<items>\n'
  props.items.forEach((item) => {
    result += '  <item>\n'
    props.headers.forEach((header) => {
      if (header.key === 'actions') {
        return
      }
      const value = getValue(header, item)
      const name = convertHeaderLabelToName(header.title)
      result += `    <${name}>${value}</${name}>\n`
    })
    result += '  </item>\n'
  })
  result += '</items>\n'
  return result
}

function exportToJSON() {
  const result = []
  props.items.forEach((item) => {
    const newItem = {}
    props.headers.forEach((header) => {
      if (header.key === 'actions') {
        return
      }
      const value = getValue(header, item)
      const name = convertHeaderLabelToName(header.title)
      newItem[name] = value
    })
    result.push(newItem)
  })
  return JSON.stringify(result)
}

async function localExport(format) {
  let content = ''
  if (format.name === 'CSV') {
    content = exportToCSV()
  } else if (format.name === 'EXCEL') {
    content = await exportToXSLX()
  } else if (format.name === 'XML') {
    content = exportToXML()
  } else if (format.name === 'JSON') {
    content = exportToJSON()
  }
  createDownloadLink(content, format)
}

async function exportContent(format) {
  loading.value = true
  const result = await new Promise((resolve) => emit('export', resolve))
  if (!result) {
    loading.value = false
    return
  }
  if (props.items.length) {
    localExport(format)
    loading.value = false
    return
  }

  const headers = {}
  headers.Accept = format.mediaType
  const params = { ...props.dataUrlParams }
  if (params.page_size === undefined) {
    params.page_size = 0
  }
  if (props.filters && !params.filters) {
    params.filters = props.filters
  }
  if (props.includeExportFields && props.headers.length > 0) {
    const fieldKeys = props.headers
      .filter((h) => h.key !== 'actions')
      .map((h) => h.key)
    params.export_fields = fieldKeys.join(',')
  }
  repository
    .get(props.dataUrl, { params, headers, responseType: 'blob' })
    .then((response) => {
      createDownloadLink(response.data, format)
      loading.value = false
    })
}
</script>
