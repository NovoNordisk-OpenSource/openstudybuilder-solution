<template>
  <v-menu rounded offset-y>
    <template #activator="{ props }">
      <slot name="button" :props="props">
        <v-btn
          class="ml-2"
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          v-bind="props"
          :title="$t('DataTableExportButton.export')"
          data-cy="table-export-button"
          icon="mdi-download-outline"
        />
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
import ExcelJS from 'exceljs'
import repository from '@/api/repository'
import exportLoader from '@/utils/exportLoader'
import { useStudiesGeneralStore } from '@/stores/studies-general'

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

function createDownloadLink(content, format) {
  const today = DateTime.local().toFormat('yyyy-MM-dd')
  let fileName = `${props.objectLabel} ${today}.${format.extension}`
  if (window.location.pathname.startsWith('/studies')) {
    fileName =
      `${studiesGeneralStore.selectedStudy.current_metadata.identification_metadata.study_id} ` +
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
  const workbook = new ExcelJS.Workbook()
  const sheet = workbook.addWorksheet('Sheet 1')
  const headers = props.headers
    .filter((header) => header.key !== 'actions')
    .map((header) => {
      return { header: header.title, key: header.key }
    })
  const rows = []
  sheet.columns = headers
  props.items.forEach((item) => {
    const row = []
    props.headers.forEach((header) => {
      if (header.key === 'actions') {
        return
      }
      row.push(getValue(header, item))
    })
    rows.push(row)
  })
  sheet.addRows(rows)
  return await workbook.xlsx.writeBuffer()
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
  const result = await new Promise((resolve) => emit('export', resolve))
  if (!result) {
    return
  }
  if (props.items.length) {
    localExport(format)
    return
  }

  const headers = {}
  headers.Accept = format.mediaType
  const params = { ...props.dataUrlParams }
  if (params.page_size === undefined) {
    params.page_size = 0
  }
  if (props.filters) {
    params.filters = props.filters
  }
  repository
    .get(props.dataUrl, { params, headers, responseType: 'blob' })
    .then((response) => {
      createDownloadLink(response.data, format)
    })
}
</script>
