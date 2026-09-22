<template>
  <v-slide-group-item>
    <div class="mr-2">
      <v-menu v-if="isDate(item.key)" :close-on-content-click="false">
        <template #activator="{ props }">
          <v-text-field
            :label="
              data.length <= 0
                ? item.title
                : `${formatDate(data[0])} - ${formatDate(data.length - 1)}`
            "
            prepend-inner-icon="mdi-calendar-outline"
            data-cy="filter-field"
            readonly
            class="filterAutocompleteLabel ml-1"
            hide-details
            single-line
            clearable
            bg-color="nnWhite"
            v-bind="props"
          />
        </template>
        <v-date-picker
          v-model="data"
          multiple="range"
          data-cy="filter-field-datepicker"
          :selected-items-text="$t('FilterAutocomplete.range_selected')"
          @update:model-value="filterDate()"
        >
        </v-date-picker>
      </v-menu>
      <v-select
        v-else
        ref="select"
        v-model="data"
        clearable
        multiple
        :label="item.title"
        data-cy="filter-field"
        color="nnBaseBlue"
        bg-color="nnWhite"
        :items="items"
        hide-details
        single-line
        class="filterAutocompleteLabel ml-1"
        :loading="loading"
        @input="getColumnData(item.columnDataKey || item.key)"
        @update:model-value="filterTable"
      >
        <template #menu-header>
          <SelectMenuSearch
            v-model="searchString"
            :placeholder="$t('FilterAutocomplete.search')"
          />
        </template>

        <template #item="{ props }">
          <v-list-item
            class="fixed-width"
            v-bind="props"
            @click="props.onClick"
          >
            <template #prepend="{ isActive }">
              <v-list-item-action start>
                <v-checkbox-btn :model-value="isActive" />
              </v-list-item-action>
            </template>
            <template #title>
              {{
                typeof props.title === 'number'
                  ? props.title
                  : props.title.replace(/[<>]/g, '')
              }}
            </template>
            <v-tooltip activator="parent" location="bottom">
              {{ props.title.replace(/[<>]/g, '') }}
            </v-tooltip>
          </v-list-item>
        </template>

        <template #selection="{ index }">
          <div v-if="index === 0">
            <span class="items-font-size">{{
              typeof data[0] !== 'boolean' &&
              typeof data[0] !== 'number' &&
              data[0].length > 12
                ? data[0].substring(0, 12) + '...'
                : data[0]
            }}</span>
          </div>
          <span v-if="index === 1" class="text-grey text-body-small mr-1">
            (+{{ data.length - 1 }})
          </span>
        </template>
      </v-select>
    </div>
  </v-slide-group-item>
</template>

<script setup>
import { ref, watch } from 'vue'
import _isEmpty from 'lodash/isEmpty'
import columnData from '@/api/columnData'
import SelectMenuSearch from '@/components/tools/SelectMenuSearch.vue'
import { useDate } from 'vuetify'

const props = defineProps({
  item: {
    type: Object,
    default: null,
  },
  clearInput: {
    type: Number,
    default: 0,
  },
  conditional: {
    type: Boolean,
    default: false,
  },
  filters: {
    type: String,
    default: '',
  },
  resource: {
    type: Array,
    default: null,
  },
  library: {
    type: String,
    default: '',
  },
  parameters: {
    type: Object,
    default: undefined,
  },
  filtersModifyFunction: {
    type: Function,
    required: false,
    default: undefined,
  },
  initialData: {
    type: Array,
    required: false,
    default: null,
  },
  fixedData: {
    type: Array,
    required: false,
    default: null,
  },
  selectedData: {
    type: Array,
    required: false,
    default: null,
  },
  tableItems: {
    type: Array,
    required: false,
    default: null,
  },
  loadFilters: {
    type: Boolean,
    default: false,
  },
})
const emit = defineEmits(['filter'])

const data = ref([])
const items = ref([])
const searchString = ref('')
const select = ref()
const timeout = ref(null)
const adapter = useDate()
const loading = ref(false)

watch(searchString, () => {
  if (timeout.value) clearTimeout(timeout.value)
  timeout.value = setTimeout(() => {
    getColumnData(props.item.columnDataKey || props.item.key)
  }, 500)
})
watch(
  () => props.clearInput,
  () => {
    clear()
  }
)
watch(
  () => props.loadFilters,
  (value) => {
    if (value) {
      getColumnData(props.item.columnDataKey || props.item.key)
    }
  }
)

function clear() {
  data.value = []
  searchString.value = ''
  filterTable()
}

function isDate(key) {
  // Check if the column key indicates it's a date field
  // Date columns typically end with '_date' or are named 'modified' or 'created'
  if (!key) return false

  return (
    key.includes('_date') ||
    key.includes('_at') ||
    key === 'modified' ||
    key === 'created' ||
    key === 'updated'
  )
}

function getColumnData(value) {
  if (!props.resource[0]) {
    return
  }
  if (value === 'actions') {
    return []
  }
  if (value === 'add') {
    return []
  }
  loading.value = true
  let jsonFilter = JSON.parse(props.filters)
  delete jsonFilter[value]
  if (props.item.exludeFromHeader) {
    props.item.exludeFromHeader.forEach((header) => {
      delete jsonFilter[header]
    })
  }
  let params = {
    field_name: props.item.externalFilterSource
      ? props.item.externalFilterSource.substring(
          props.item.externalFilterSource.indexOf('$') + 1
        )
      : props.item.filteringName
        ? props.item.filteringName
        : value,
    search_string: searchString.value,
    page_size: 50,
  }
  if (props.parameters) {
    params = Object.assign(params, props.parameters)
  }
  if (props.item.parameters) {
    params = Object.assign(params, props.item.parameters)
  }
  if (props.filtersModifyFunction) {
    const filters = props.filtersModifyFunction(
      jsonFilter,
      params,
      props.item.externalFilterSource
    )
    jsonFilter = filters.jsonFilter
    params = filters.params
  }
  if (!_isEmpty(jsonFilter)) {
    params.filters = jsonFilter
  }
  if (props.resource[1] && props.resource[1] !== undefined) {
    params.codelist_uid = props.resource[1]
  }
  if (props.library) {
    params.library_name = props.library
  }
  let externalFilter = props.resource[0]
  if (props.item.externalFilterSource) {
    externalFilter = props.item.externalFilterSource.substring(
      0,
      props.item.externalFilterSource.indexOf('$')
    )
  }
  if (props.item.disableColumnFilters) {
    params.filters = {}
  }
  columnData.getHeaderData(params, externalFilter).then((resp) => {
    items.value = booleanValidator(resp.data)
    items.value = items.value.filter((element) => {
      return element !== ''
    })
    if (typeof items.value[0] === 'object') {
      const deconstructedItems = []
      items.value.forEach((item) => {
        if (item) {
          if (item.length > 1) {
            item.forEach((i) => {
              deconstructedItems.push(i.name)
            })
          } else if (item.length !== 0) {
            deconstructedItems.push(item[0].name)
          }
        }
      })
      items.value = Array.from(new Set(deconstructedItems))
    }
    if (props.fixedData) {
      items.value = props.fixedData.concat(items.value)
    }
    if (props.initialData) {
      items.value = items.value.filter(
        (item) => props.initialData.indexOf(item) !== -1
      )
    }
  })
  loading.value = false
}

function filterDate() {
  let dateData = [
    formatDate(data.value[0]),
    formatDate(
      data.value.length <= 1 ? data.value[0] : data.value[data.value.length - 1]
    ),
  ]
  emit('filter', {
    column: props.item.columnDataKey || props.item.key,
    data: dateData,
  })
}

function formatDate(date) {
  return adapter
    .format(date, 'keyboardDate')
    .replace(/(..).(..).(....)/, '$3-$1-$2')
}

function booleanConverter(value) {
  if (value === 'No' || value === false) {
    return value === 'No' ? false : 'No'
  } else {
    return value === 'Yes' ? true : 'Yes'
  }
}

function booleanValidator(array) {
  if (array.length <= 2 && (array[0] === false || array[0] === true)) {
    array.forEach((el) => {
      const index = array.indexOf(el)
      array[index] = booleanConverter(array[index])
    })
  }
  return array
}

function filterTable() {
  if (
    data.value.length <= 2 &&
    (data.value[0] === 'Yes' || data.value[0] === 'No')
  ) {
    const requestData = []
    data.value.forEach((el) => {
      const index = data.value.indexOf(el)
      requestData.push(booleanConverter(data.value[index]))
    })
    emit('filter', {
      column: props.item.filteringName
        ? props.item.filteringName
        : props.item.columnDataKey || props.item.key,
      data: requestData,
    })
  } else {
    emit('filter', {
      column: props.item.filteringName
        ? props.item.filteringName
        : props.item.columnDataKey || props.item.key,
      data: data.value,
    })
  }
}

if (!props.initialData && props.tableItems && props.tableItems.length) {
  getColumnData(props.item.columnDataKey || props.item.key)
} else if (props.initialData) {
  items.value = [...props.initialData]
}

if (props.selectedData) {
  data.value = props.selectedData
}
</script>

<style scoped lang="scss">
.v-list {
  max-width: 300px !important;
}
.fixed-width {
  width: 250px !important;
  max-width: 250px !important;
}
.items-font-size {
  font-size: 14px;
}
.v-select__content {
  max-width: 250px;
}
</style>
