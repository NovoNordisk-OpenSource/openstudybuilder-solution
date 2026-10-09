<template>
  <v-slide-group-item>
    <div ref="rootEl" class="mr-2">
      <v-menu
        v-if="isDate(item.key)"
        v-model="menuOpen"
        :close-on-content-click="false"
        scroll-strategy="close"
      >
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
        v-model:menu="menuOpen"
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
        :menu-props="{ scrollStrategy: 'close' }"
        @input="getColumnData(item.columnDataKey || item.key)"
        @update:model-value="filterTable"
      >
        <template v-if="!booleanChoices" #menu-header>
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
              {{ displayFilterTitle(props.title) }}
            </template>
            <v-tooltip activator="parent" location="bottom">
              {{ displayFilterTitle(props.title) }}
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
import { onBeforeUnmount, ref, watch } from 'vue'
import _get from 'lodash/get'
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
const rootEl = ref()
const menuOpen = ref(false)
const timeout = ref(null)
const adapter = useDate()
const loading = ref(false)
const booleanChoices = ref(null)
let slideGroupCleanup = null
let columnDataRequestId = 0

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
  () => props.filters,
  (newFilters, oldFilters) => {
    // Only live-refresh while this column's own dropdown is open — it's the
    // only state where a stale list is visible. A closed column already gets
    // a guaranteed-fresh, non-cached fetch from the `menuOpen` watcher below
    // the next time it's opened, so refetching here too just means every
    // column re-fetches its headers on every keystroke elsewhere (e.g. the
    // table's global search box updates `filters` on every debounced
    // change), which both wastes requests and can race the request that
    // triggered the change in the first place.
    if (newFilters !== oldFilters && menuOpen.value) {
      getColumnData(props.item.columnDataKey || props.item.key, {
        useBooleanCache: false,
      })
    }
  }
)
watch(
  () => {
    const fieldKey = props.item.columnDataKey || props.item.key
    return (props.tableItems || [])
      .map((row) => `${row?.status ?? ''}:${_get(row, fieldKey) ?? ''}`)
      .join('|')
  },
  (newFingerprint, oldFingerprint) => {
    if (
      props.loadFilters &&
      newFingerprint !== oldFingerprint &&
      menuOpen.value
    ) {
      getColumnData(props.item.columnDataKey || props.item.key, {
        useBooleanCache: false,
      })
    }
  }
)

watch(menuOpen, (open) => {
  if (open) {
    if (!isDate(props.item.key)) {
      getColumnData(props.item.columnDataKey || props.item.key, {
        useBooleanCache: false,
        ignoreSearch: true,
      })
    }
    bindSlideGroupClose()
  } else {
    unbindSlideGroupClose()
  }
})

function closeMenu() {
  menuOpen.value = false
}

function bindSlideGroupClose() {
  unbindSlideGroupClose()
  // These class names are undocumented Vuetify internals, not a public API —
  // a Vuetify version bump could rename them with no compile error, only a
  // silently regressed "close on scroll" behavior.
  const group = rootEl.value?.closest('.v-slide-group')
  if (!group) {
    return
  }
  const container = group.querySelector('.v-slide-group__container')
  const next = group.querySelector('.v-slide-group__next')
  const prev = group.querySelector('.v-slide-group__prev')
  container?.addEventListener('scroll', closeMenu, { passive: true })
  next?.addEventListener('click', closeMenu)
  prev?.addEventListener('click', closeMenu)
  slideGroupCleanup = () => {
    container?.removeEventListener('scroll', closeMenu)
    next?.removeEventListener('click', closeMenu)
    prev?.removeEventListener('click', closeMenu)
    slideGroupCleanup = null
  }
}

function unbindSlideGroupClose() {
  if (slideGroupCleanup) {
    slideGroupCleanup()
  }
}

onBeforeUnmount(() => {
  unbindSlideGroupClose()
})

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

function isBooleanHeaderValues(values) {
  return (
    Array.isArray(values) &&
    values.length > 0 &&
    values.length <= 2 &&
    values.every((value) => typeof value === 'boolean')
  )
}

function isYesNoSearch(query) {
  const normalized = (query || '').trim().toLowerCase()
  return normalized === 'yes' || normalized === 'no'
}

function displayFilterTitle(title) {
  if (title == null) {
    return ''
  }
  if (typeof title === 'string') {
    return title.replace(/[<>]/g, '')
  }
  return String(title)
}

// The key this column's selection is stored under in the filters object. Both the
// read side (getColumnData) and the write side (filterTable) must agree on it, or
// the column narrows its own list of candidate values.
function ownFilterKey() {
  return props.item.filteringName || props.item.columnDataKey || props.item.key
}

function getColumnData(value, options = {}) {
  const {
    useBooleanCache = true,
    ignoreSearch = false,
    yesNoRetry = false,
  } = options
  if (!props.resource[0]) {
    return
  }
  if (value === 'actions') {
    return []
  }
  if (value === 'add') {
    return []
  }
  if (useBooleanCache && booleanChoices.value) {
    items.value = [...booleanChoices.value]
    return
  }
  loading.value = true
  items.value = []
  const requestId = ++columnDataRequestId
  let jsonFilter = JSON.parse(props.filters || '{}')
  delete jsonFilter[ownFilterKey()]
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
    search_string: ignoreSearch ? '' : searchString.value,
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
  columnData
    .getHeaderData(params, externalFilter)
    .then((resp) => {
      if (requestId !== columnDataRequestId) {
        return
      }
      const rawValues = (resp.data || []).filter((element) => element !== '')
      if (yesNoRetry && !isBooleanHeaderValues(rawValues)) {
        items.value = []
        booleanChoices.value = null
        return
      }
      // Narrow race: on a slow network, a user's "yes"/"no" search can resolve
      // before the boolean-detecting fetch fired on menu-open (see the
      // `menuOpen` watcher above). A literal "yes"/"no" search string won't
      // match real boolean values server-side, so it comes back empty; retry
      // once without the search term to get the real (boolean) header values.
      if (
        !isBooleanHeaderValues(rawValues) &&
        !ignoreSearch &&
        isYesNoSearch(searchString.value) &&
        rawValues.length === 0
      ) {
        getColumnData(value, {
          useBooleanCache: false,
          ignoreSearch: true,
          yesNoRetry: true,
        })
        return
      }
      if (isBooleanHeaderValues(rawValues)) {
        booleanChoices.value = booleanValidator(rawValues)
        searchString.value = ''
        items.value = [...booleanChoices.value]
        return
      }
      booleanChoices.value = null
      items.value = booleanValidator(rawValues)
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
    .finally(() => {
      if (requestId === columnDataRequestId) {
        loading.value = false
      }
    })
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
  if (array.length <= 2 && array.every((value) => typeof value === 'boolean')) {
    return array.map((value) => booleanConverter(value))
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
      column: ownFilterKey(),
      data: requestData,
    })
  } else {
    emit('filter', {
      column: ownFilterKey(),
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
