<template>
  <v-card data-cy="version-history-window">
    <v-card-title class="d-flex align-center">
      <span class="dialog-title">{{ title }}</span>
      <v-spacer />
    </v-card-title>
    <v-card-text style="margin-bottom: 70px">
      <v-data-table-server
        :headers="cleanedHeaders"
        :items="historyItems"
        class="history_headers"
        :items-length="itemsTotal"
        disable-sort
        data-cy="data-table"
        density="compact"
        :loading="loading"
        @update:options="(options) => refreshHistoryData(options)"
      >
        <template #item="{ item }">
          <tr>
            <td
              v-for="(header, index) in cleanedHeaders"
              :key="index"
              :class="getTextClass(item)"
            >
              <div :class="getCellClasses(header, item)">
                <span
                  v-if="htmlFields && htmlFields.indexOf(header.key) !== -1"
                  v-html="getDisplay(item, header)"
                />
                <span v-else>{{ getDisplay(item, header) }}</span>
              </div>
            </td>
          </tr>
        </template>
      </v-data-table-server>
      <div v-if="!simpleStyling">
        <div>{{ $t('HistoryTable.legend') }}</div>
        <div class="ml-2 font-weight-black">
          {{ $t('HistoryTable.current_version') }}
        </div>
        <div class="ml-2">
          {{ $t('HistoryTable.older_version') }}
        </div>
        <div class="ml-2 text-red">
          {{ $t('HistoryTable.deleted_version') }}
        </div>
        <div class="ml-2 bg-blue-lighten-4 difference">
          {{ $t('HistoryTable.changed_value') }}
        </div>
      </div>
    </v-card-text>
    <v-card-actions class="bg-white fixed-actions py-6 border-t-thin">
      <v-spacer />
      <DataTableExportButton
        v-if="withExport"
        :headers="cleanedHeaders"
        :items="items"
        :object-label="exportFullName"
        @export="(resolve) => resolve(true)"
      >
        <template #button="{ props }">
          <v-btn
            class="ml-4"
            color="nnBaseBlue"
            prepend-icon="mdi-download-outline"
            v-bind="props"
            :title="$t('DataTableExportButton.export')"
            data-cy="table-export-button"
          >
            {{ $t('_global.download') }}
          </v-btn>
        </template>
      </DataTableExportButton>

      <v-btn
        color="secondary"
        data-cy="close-button"
        variant="outlined"
        rounded
        @click="emit('close')"
      >
        {{ $t('_global.close') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import DataTableExportButton from '@/components/tools/DataTableExportButton.vue'
import { DateTime } from 'luxon'

const { t } = useI18n()
const props = defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
  headers: {
    type: Array,
    default: () => [],
  },
  excludedHeaders: {
    type: Array,
    required: false,
    default: () => [],
  },
  items: {
    type: Array,
    default: () => [],
  },
  itemsTotal: {
    type: Number,
    default: 0,
  },
  title: {
    type: String,
    default: '',
  },
  withExport: {
    type: Boolean,
    default: true,
  },
  exportName: {
    type: String,
    required: false,
    default: '',
  },
  htmlFields: {
    type: Array,
    required: false,
    default: () => [],
  },
  startDateHeader: {
    type: String,
    default: 'start_date',
  },
  endDateHeader: {
    type: String,
    default: 'end_date',
  },
  changeField: {
    type: String,
    default: 'change_type',
  },
  changeFieldLabel: {
    type: String,
    required: false,
    default: '',
  },
  simpleStyling: {
    type: Boolean,
    default: false,
  },
})
const emit = defineEmits(['close', 'refresh'])

const historyItems = ref([])
const dataOptions = ref({ itemsPerPage: 10, page: 1 })

watch(
  () => props.items,
  () => {
    getPaginatedHistoryData()
  },
  { immediate: true }
)

watch(
  () => dataOptions.value,
  () => {
    getPaginatedHistoryData()
  },
  { immediate: true }
)

const cleanedHeaders = computed(() => {
  let result = []
  const excludedHeaders = ['actions', 'author_username', 'start_date']
  if (props.excludedHeaders) {
    for (const header of props.excludedHeaders) {
      excludedHeaders.push(header)
    }
  }
  for (const header of props.headers) {
    if (header.historyHeader) {
      header.key = header.historyHeader
    }
  }
  result = props.headers.filter((item) => {
    return !excludedHeaders.includes(item.key)
  })
  result.push({
    title: props.changeFieldLabel
      ? props.changeFieldLabel
      : t('HistoryTable.change_type'),
    key: props.changeField !== '' ? props.changeField : 'change_type',
  })
  result.push({
    title: t('_global.user'),
    key: 'author_username',
  })
  result.push({
    title: t('HistoryTable.start_date'),
    key: props.startDateHeader,
  })
  result.push({
    title: t('HistoryTable.end_date'),
    key: props.endDateHeader,
  })
  return result
})
const exportFullName = computed(() => {
  let result = ''
  if (props.exportName) {
    result = props.exportName + '_'
  }
  result += 'history'
  return result
})

function refreshHistoryData(options) {
  dataOptions.value = options
  emit('refresh', options)
}

function getPaginatedHistoryData() {
  if (props.items.length > dataOptions.value.itemsPerPage) {
    historyItems.value = JSON.parse(
      JSON.stringify(
        props.items.slice(
          dataOptions.value.itemsPerPage * (dataOptions.value.page - 1),
          dataOptions.value.itemsPerPage * dataOptions.value.page
        )
      )
    )
  } else {
    historyItems.value = props.items
  }
}

function getHighlight(header, item) {
  if (item) {
    if (
      header.key.indexOf('date') !== -1 ||
      header.key.indexOf('change_type') !== -1
    ) {
      return false
    } else if (item.changes) {
      let fieldName = header.key
      if (fieldName.indexOf('.') !== -1) {
        fieldName = fieldName.substring(0, fieldName.indexOf('.'))
      }
      return item.changes.indexOf(fieldName) !== -1
    } else {
      return false
    }
  }
}
function getCellClasses(header, item) {
  if (props.simpleStyling) {
    return 'ml-3'
  }
  if (getHighlight(header, item)) {
    return 'bg-blue-lighten-4 difference ml-3'
  }
  return ''
}
function getTextClass(item) {
  if (props.simpleStyling) {
    return ''
  }
  if (item.change_type === 'Delete') {
    return 'text-red'
  } else if (!item.end_date) {
    return 'font-weight-black'
  } else {
    return ''
  }
}
function getDisplay(item, header) {
  const accessor = header.key
  const accessList = accessor.split('.')
  if (item) {
    let value = item
    for (const i in accessList) {
      const label = accessList[i]
      if (value) {
        value = value[label]
      }
    }
    if (accessor.toLowerCase().indexOf('date') !== -1) {
      if (value) {
        value = DateTime.fromISO(value)
          .setLocale('en')
          .toLocaleString(DateTime.DATETIME_MED)
      }
    }
    if (header.historyFilter) {
      value = header.historyFilter(value)
    }
    return value ? value.toString() : value
  }
}
</script>
