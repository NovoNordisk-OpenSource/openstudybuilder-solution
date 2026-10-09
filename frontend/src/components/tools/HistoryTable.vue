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
                  v-html="sanitizeHTML(getDisplay(item, header))"
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
import { sanitizeHTML } from '@/utils/sanitize'

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
  comparisonItems: {
    type: Array,
    default: () => [],
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
  showChangeType: {
    type: Boolean,
    default: true,
  },
  // Field identifying the entity a row belongs to. Audit trails list several
  // entities in one table, and a row must only be diffed against an older
  // version of the same one. Auto-detected when not given.
  identityKey: {
    type: String,
    required: false,
    default: '',
  },
})
const emit = defineEmits(['close', 'refresh'])

const historyItems = ref([])
const dataOptions = ref({ itemsPerPage: 10, page: 1 })

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
  if (props.showChangeType) {
    result.push({
      title: props.changeFieldLabel
        ? props.changeFieldLabel
        : t('HistoryTable.change_type'),
      key: props.changeField !== '' ? props.changeField : 'change_type',
    })
  }
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
// Versions are listed newest first, so a row is compared with the next row
// belonging to the same entity. The oldest version of an entity has nothing to
// compare against and is never highlighted.
const decoratedItems = computed(() => {
  const items = props.items
  const comparisonItems = props.comparisonItems.length
    ? props.comparisonItems
    : items
  return items.map((item) => {
    const identity = getIdentity(item)
    const comparisonIndex = comparisonItems.findIndex(
      (candidate) =>
        getIdentity(candidate) === identity &&
        getVersionIdentity(candidate) === getVersionIdentity(item)
    )
    const previous = comparisonItems
      .slice(comparisonIndex + 1)
      .find((candidate) => getIdentity(candidate) === identity)
    const firstIdentityIndex = comparisonItems.findIndex(
      (candidate) => getIdentity(candidate) === identity
    )
    return {
      ...item,
      _changedKeys: getChangedKeys(item, previous),
      _isCurrent: comparisonIndex === firstIdentityIndex,
    }
  })
})

watch(
  () => decoratedItems.value,
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

function getIdentity(item) {
  if (props.identityKey) {
    return item[props.identityKey]
  }
  if (item.uid !== undefined) {
    return item.uid
  }
  const uidKey = Object.keys(item).find(
    (key) =>
      key !== 'study_uid' &&
      key.endsWith('_uid') &&
      typeof item[key] === 'string'
  )
  return uidKey ? item[uidKey] : null
}

function getVersionIdentity(item) {
  return item.start_date || item.version || item.change_type || item.end_date
}

function getChangedKeys(item, previous) {
  // A server computed diff covers versions that are not on this page, so it
  // wins over comparing the rows we happen to hold.
  if (Array.isArray(item.changes)) {
    return cleanedHeaders.value
      .filter(
        (header) =>
          !isTimestampColumn(header) &&
          [header.key.split('.')[0], ...(header.changeKeys ?? [])].some((key) =>
            item.changes.includes(key)
          )
      )
      .map((header) => header.key)
  }
  if (!previous) {
    return []
  }
  return cleanedHeaders.value
    .filter(
      (header) =>
        !isTimestampColumn(header) &&
        // A missing value and an empty one read the same in the table, so only
        // a real difference counts.
        (getDisplay(item, header) ?? '') !==
          (getDisplay(previous, header) ?? '')
    )
    .map((header) => header.key)
}

// Columns that differ on every version by construction, so flagging them as
// changed says nothing.
function isTimestampColumn(header) {
  return (
    header.key.indexOf('date') !== -1 ||
    header.key.indexOf('change_type') !== -1
  )
}

function refreshHistoryData(options) {
  dataOptions.value = options
  emit('refresh', options)
}

function getPaginatedHistoryData() {
  const items = decoratedItems.value
  if (items.length > dataOptions.value.itemsPerPage) {
    const sliceStart =
      dataOptions.value.itemsPerPage * (dataOptions.value.page - 1)
    let sliceEnd = dataOptions.value.itemsPerPage * dataOptions.value.page
    if (dataOptions.value.itemsPerPage === -1) {
      sliceEnd = items.length
    }
    historyItems.value = items.slice(sliceStart, sliceEnd)
  } else {
    historyItems.value = items
  }
}

function getHighlight(header, item) {
  if (!item || isTimestampColumn(header)) {
    return false
  }
  return (item._changedKeys || []).includes(header.key)
}
function getCellClasses(header, item) {
  if (props.simpleStyling) {
    return 'ml-3'
  }
  if (getHighlight(header, item)) {
    return 'bg-blue-lighten-4 difference ml-0 my-2'
  }
  return ''
}
function getTextClass(item) {
  if (props.simpleStyling) {
    return ''
  }
  if (item.change_type === 'Delete') {
    return 'text-red'
  } else if (item._isCurrent) {
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
      value = header.historyFilter(value, item)
    }
    return value ? value.toString() : value
  }
}
</script>
