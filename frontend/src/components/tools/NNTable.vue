<template>
  <div ref="tableRoot">
    <v-card :elevation="elevation" class="rounded-0 pt-6">
      <v-card-title
        v-if="!noTitle"
        style="z-index: 3; position: relative"
        class="d-flex align-center flex-wrap ga-2"
        :class="props.noPadding ? 'pa-0' : 'pt-0'"
      >
        <div class="search-container d-flex align-center pl-0">
          <slot name="beforeSearch" />
          <SearchField
            v-if="advancedSearch && (!hideSearchField || onlyTextSearch)"
            v-model:search="search"
            v-model:match-whole-words="matchWholeWords"
          />
          <v-text-field
            v-else-if="!hideSearchField || onlyTextSearch"
            v-model="search"
            clearable
            clear-icon="mdi-close"
            prepend-inner-icon="mdi-magnify"
            :label="$t('_global.search')"
            single-line
            color="nnBaseBlue"
            hide-details
            style="min-width: 240px; max-width: 300px"
            class="searchFieldLabel ml-0"
            data-cy="search-field"
          />
          <slot name="afterSearch" />
        </div>

        <slot name="beforeSwitches" />

        <!-- Toggle switches -->
        <template v-if="!hideDefaultSwitches">
          <div
            :title="$t('NNTableTooltips.select_rows')"
            class="ml-4 selectRowsSwitch"
          >
            <v-switch
              v-model="showSelectBoxes"
              data-cy="select-rows"
              :label="$t('NNTable.show_select_boxes_label')"
              class="mr-6"
              hide-details
              :title="$t('NNTableTooltips.select_rows')"
            />
          </div>
        </template>

        <slot name="afterSwitches" />
        <slot name="headerCenter" />
        <v-spacer />

        <!-- Right-side actions -->
        <slot name="beforeActions" />
        <v-radio-group
          v-if="showColumnNamesToggleButton"
          v-model="showColumnNames"
          inline
          hide-details
        >
          <v-radio :label="$t('NNTable.column_labels')" :value="false" />
          <v-radio :label="$t('NNTable.column_names')" :value="true" />
        </v-radio-group>

        <div v-if="!hideActionsMenu" class="actions-container">
          <slot
            name="actions"
            :show-select-boxes="showSelectBoxes"
            :selected="selected"
          />
          <v-btn
            v-if="!disableFiltering && !onlyTextSearch"
            class="ml-2"
            variant="outlined"
            color="nnBaseBlue"
            icon
            size="small"
            data-cy="filters-button"
            :active="showFilterBar"
            @click="enableFiltering"
          >
            <v-icon>mdi-filter-outline</v-icon>
            <v-tooltip activator="parent" location="top">
              {{ $t('NNTableTooltips.filters') }}
            </v-tooltip>
          </v-btn>
          <v-menu rounded offset-y :close-on-content-click="false">
            <template #activator="{ props }">
              <v-btn
                v-if="(modifiableTable || modifyOnlyColumns) && !onlyTextSearch"
                class="ml-2"
                variant="outlined"
                color="nnBaseBlue"
                icon
                size="small"
                v-bind="props"
                data-cy="columns-layout-button"
              >
                <v-icon>mdi-table-column</v-icon>
                <v-tooltip activator="parent" location="top">
                  {{ $t('NNTableTooltips.select_columns') }}
                </v-tooltip>
              </v-btn>
            </template>
            <v-list data-cy="show-columns-form" class="columnList">
              <v-list-item>
                <v-list-item-title class="font-weight-bold fontSize16">{{
                  $t('NNTable.select_columns')
                }}</v-list-item-title>
              </v-list-item>
              <v-switch
                v-for="(column, index) in headers.filter((header) => {
                  return header.title !== ''
                })"
                :key="column.title"
                v-model="selectedColumns"
                :value="
                  headersHasAction() ? headers[index + 1] : headers[index]
                "
                class="ml-n3 mr-n2 scale80"
                :label="column.title"
                inset
                :disabled="disableColumnSwitch(column)"
                hide-details
              />
            </v-list>
          </v-menu>
          <DataTableExportButton
            v-if="!hideExportButton"
            class="ml-2"
            :object-label="exportConfig?.objectLabel || ''"
            :data-url="exportConfig?.dataUrl || ''"
            :data-url-params="exportConfig?.dataUrlParams"
            :headers="exportVisibleColumnsOnly ? selectedColumns : headers"
            :items="selected.length ? selected : []"
            :filters="savedFilters"
            :include-export-fields="exportVisibleColumnsOnly"
            data-cy="export-data-button"
            @export="confirmExport"
          />
          <v-btn
            v-if="historyConfig?.dataFetcher"
            class="ml-2"
            variant="outlined"
            color="nnBaseBlue"
            icon
            size="small"
            @click="openHistory"
          >
            <v-icon>mdi-history</v-icon>
            <v-tooltip activator="parent" location="top">
              {{ $t('NNTableTooltips.history') }}
            </v-tooltip>
          </v-btn>
        </div>

        <slot name="beforeTable" />
      </v-card-title>
      <v-card-text :class="{ 'pa-0': props.noPadding }">
        <slot name="customFiltering" />
        <v-fade-transition>
          <v-toolbar
            v-show="showFilterBar"
            flat
            class="filteringBar pt-1"
            color="nnGray200"
          >
            <slot name="afterFilter" />
            <v-slide-group show-arrows class="mb-5">
              <FilterAutocomplete
                v-for="item in itemsToFilter"
                :key="item.text"
                :load-filters="loadFilters"
                :clear-input="trigger"
                :item="item"
                :filters="savedFilters"
                :library="library"
                :resource="[columnDataResource, codelistUid]"
                :parameters="columnDataParameters"
                :initial-data="getColumnInitialData(item)"
                :fixed-data="getColumnFixedData(item)"
                :selected-data="getColumnSelectedData(item)"
                :filters-modify-function="filtersModifyFunction"
                :table-items="items"
                @filter="columnFilter"
              />
            </v-slide-group>
            <v-spacer />
            <v-btn
              prepend-icon="mdi-close"
              color="nnWhite"
              variant="flat"
              class="mr-3 mb-5 clearAllBtn"
              rounded
              :text="$t('NNTableTooltips.clear_filters_content')"
              @click="clearFilters()"
            />
          </v-toolbar>
        </v-fade-transition>
        <ResizingDiv>
          <template #resizing-area="areaProps">
            <v-data-table-server
              v-model="selected"
              v-model:sort-by="sortBy"
              data-cy="data-table"
              :item-value="itemValue"
              return-object
              hover
              :show-select="showSelectBoxes"
              :items-per-page="computedItemsPerPage"
              :items-per-page-options="computedItemsPerPageOptions"
              :items-per-page-text="$t('Settings.rows')"
              class="py-4 mr-0 data-table-visible"
              :row-props="rowProps"
              :loading="loading"
              :height="
                tableHeight || (props.noPadding ? 'auto' : areaProps.areaHeight)
              "
              :items="items"
              :search="search"
              :headers="shownColumns"
              :fixed-header="fixedHeader"
              :no-data-text="noDataText"
              :hide-default-footer="hideDefaultFooter"
              :items-length="
                itemsLength === -1
                  ? tablesConstants.UNKNOWN_TOTAL_PLACEHOLDER
                  : itemsLength
              "
              disable-sort
              v-bind="$attrs"
              @update:options="handleTableOptionsUpdate"
              @update:sort-by="customSort"
            >
              <template #loading>
                <v-skeleton-loader type="list-item@10"></v-skeleton-loader>
              </template>
              <template
                v-for="header in shownColumns"
                :key="header.key"
                #[getHeaderSlotName(header)]
              >
                <div class="d-flex headerRow align-center">
                  <v-chip
                    v-if="header.color"
                    size="small"
                    :color="header.color"
                    class="mt-1 mr-1"
                    variant="flat"
                  >
                    <span>&nbsp;</span>
                    <span>&nbsp;</span>
                  </v-chip>
                  <div v-if="!showColumnNames">
                    {{ header.title }}
                  </div>
                  <div v-else class="mt-1">
                    {{ header.key }}
                  </div>
                  <v-icon v-if="sortBy.length && sortBy[0].key === header.key">
                    <template v-if="sortBy[0].order === 'asc'">
                      mdi-arrow-up-thin
                    </template>
                    <template v-else> mdi-arrow-down-thin </template>
                  </v-icon>
                  <v-menu
                    v-if="
                      header.title !== '' && modifiableTable && !onlyTextSearch
                    "
                    offset-y
                  >
                    <template #activator="{ props }">
                      <v-btn
                        icon
                        v-bind="props"
                        variant="plain"
                        class="pb-1"
                        @mouseover="columnValueIndex = header.key"
                      >
                        <v-icon v-show="header.key === columnValueIndex">
                          mdi-dots-vertical
                        </v-icon>
                      </v-btn>
                    </template>
                    <v-list v-if="modifiableTable && !onlyTextSearch">
                      <template v-for="(item, index) in headerActions">
                        <v-list-item
                          v-if="item.available"
                          :key="index"
                          @mouseover="columnValueIndex = header.key"
                          @mouseleave="columnValueIndex = ''"
                        >
                          <v-btn
                            variant="text"
                            class="disableUpperCase"
                            @click="item.click(header)"
                          >
                            {{
                              itemsToFilter[
                                itemsToFilter.findIndex(
                                  (el) => el.key === header.key
                                )
                              ] && item.label === $t('NNTable.add_to_filter')
                                ? $t('NNTable.remove_from_filter')
                                : item.label
                            }}
                          </v-btn>
                        </v-list-item>
                      </template>
                    </v-list>
                  </v-menu>
                  <div v-else style="width: 50px"></div>
                </div>
              </template>
              <template
                v-for="header in shownColumns"
                #[`item.${header.key}`]="{ item }"
              >
                <template
                  v-for="(cellValue, cellIndex) in [
                    getValueByColumn(item, header.key),
                  ]"
                  :key="cellIndex"
                >
                  <v-tooltip
                    v-if="cellValue && cellValue.length > 60"
                    location="top"
                  >
                    <template #activator="{ props }">
                      <span v-bind="props">
                        {{ cellValue.substring(0, 60) + '...' }}
                      </span>
                    </template>
                    <span>{{ cellValue }}</span>
                  </v-tooltip>
                  <div v-else>{{ cellValue }}</div>
                </template>
              </template>
              <template v-for="(_, slot) of $slots" #[slot]="scope">
                <slot
                  :name="slot"
                  v-bind="scope"
                  :show-select-boxes="showSelectBoxes"
                />
              </template>
              <template #bottom="{ isDisabled }">
                <div class="v-data-table-footer">
                  <div class="v-data-table-footer__items-per-page">
                    <span>{{ $t('Settings.rows') }}:</span>
                    <v-select
                      :model-value="currentItemsPerPageValue"
                      :items="computedItemsPerPageOptions"
                      hide-details
                      :disabled="isDisabled"
                      @update:model-value="
                        (value) => updateItemsPerPage(value, currentPageNumber)
                      "
                    />
                  </div>
                  <div class="v-data-table-footer__info">
                    {{ getPaginationStartNumber() }}-{{
                      getPaginationEndNumber()
                    }}
                    of
                    {{ getPaginationTotalDisplay() }}
                  </div>
                  <div class="v-data-table-footer__pagination">
                    <v-btn
                      icon="$first"
                      variant="text"
                      :disabled="currentPageNumber === 1 || isDisabled"
                      @click="updatePage(1, currentItemsPerPageValue)"
                    />
                    <v-btn
                      icon="$prev"
                      variant="text"
                      :disabled="currentPageNumber === 1 || isDisabled"
                      @click="
                        updatePage(
                          currentPageNumber - 1,
                          currentItemsPerPageValue
                        )
                      "
                    />
                    <v-btn
                      icon="$next"
                      variant="text"
                      :disabled="
                        isDisabled ||
                        (props.itemsLength > 0 &&
                          currentPageNumber >=
                            Math.ceil(
                              props.itemsLength / currentItemsPerPageValue
                            ))
                      "
                      @click="
                        updatePage(
                          currentPageNumber + 1,
                          currentItemsPerPageValue
                        )
                      "
                    />
                    <v-btn
                      icon="$last"
                      variant="text"
                      :disabled="
                        isDisabled ||
                        props.itemsLength === -1 ||
                        (props.itemsLength > 0 &&
                          currentPageNumber >=
                            Math.ceil(
                              props.itemsLength / currentItemsPerPageValue
                            ))
                      "
                      @click="
                        updatePage(
                          Math.ceil(
                            props.itemsLength / currentItemsPerPageValue
                          ),
                          currentItemsPerPageValue
                        )
                      "
                    />
                  </div>
                </div>
              </template>
            </v-data-table-server>
          </template>
        </ResizingDiv>
      </v-card-text>
    </v-card>

    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />

    <v-dialog
      v-model="showHistory"
      :fullscreen="$globals.historyDialogFullscreen"
      persistent
      @keydown.esc="closeHistory"
    >
      <HistoryTable
        :headers="historyHeaders"
        :items="historyItems"
        :items-total="historyItemsTotal"
        :title="historyConfig?.title || ''"
        :html-fields="historyConfig?.htmlFields || []"
        :simple-styling="historyConfig?.simpleStyling || false"
        :change-field="historyConfig?.changeField || ''"
        :change-field-label="historyConfig?.changeFieldLabel || ''"
        :excluded-headers="historyConfig?.excludedHeaders || []"
        :loading="loading"
        @close="closeHistory"
        @refresh="(options) => getHistoryData(options)"
      />
    </v-dialog>
  </div>
</template>

<script>
const SEARCH_HIGHLIGHT_NAME = 'nn-search-highlight'

// A single shared Highlight object is kept in the global CSS.highlights
// registry under a constant name. Multiple NNTable instances can be rendered
// on the same page, so each instance only ever adds/removes its own Range
// objects instead of replacing or deleting the whole highlight.
function getSharedHighlight() {
  if (typeof CSS === 'undefined' || !CSS.highlights || !window.Highlight) {
    return null
  }
  let highlight = CSS.highlights.get(SEARCH_HIGHLIGHT_NAME)
  if (!highlight) {
    highlight = new window.Highlight()
    CSS.highlights.set(SEARCH_HIGHLIGHT_NAME, highlight)
  }
  return highlight
}

// Removes the given ranges from the shared Highlight and drops the shared
// object from the registry once it no longer contains any ranges.
function removeRangesFromSharedHighlight(ranges) {
  if (typeof CSS === 'undefined' || !CSS.highlights) {
    return
  }
  const highlight = CSS.highlights.get(SEARCH_HIGHLIGHT_NAME)
  if (!highlight) {
    return
  }
  ranges.forEach((range) => highlight.delete(range))
  if (highlight.size === 0) {
    CSS.highlights.delete(SEARCH_HIGHLIGHT_NAME)
  }
}
</script>

<script setup>
import { computed, onMounted, onUnmounted, onUpdated, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import { useTablesLayoutStore } from '@/stores/tables-layout'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import DataTableExportButton from '@/components/tools/DataTableExportButton.vue'
import FilterAutocomplete from './FilterAutocomplete.vue'
import HistoryTable from './HistoryTable.vue'
import ResizingDiv from './ResizingDiv.vue'
import SearchField from './SearchField.vue'
import { i18n } from '@/plugins/i18n'
import { useRoute } from 'vue-router'
import tablesConstants from '@/constants/tables'

const props = defineProps({
  // Data
  headers: {
    type: Array,
    default: () => [],
  },
  defaultHeaders: {
    type: Array,
    default: () => [],
  },
  items: {
    type: Array,
    default: () => [],
  },
  itemValue: {
    type: [String, Function],
    default: '',
  },
  itemsLength: {
    type: Number,
    default: 0,
  },

  // Layout & display
  elevation: {
    type: String,
    default: '0',
  },
  noPadding: {
    type: Boolean,
    default: false,
  },
  noTitle: {
    type: Boolean,
    default: false,
  },
  noDataText: {
    type: String,
    default: () => i18n.t('NNTable.no_data'),
  },
  fixedHeader: {
    type: Boolean,
    default: true,
  },
  tableHeight: {
    type: String,
    default: null,
  },
  subTables: {
    type: Boolean,
    default: false,
  },
  extraItemClass: {
    type: Function,
    default: undefined,
  },

  // Visibility toggles
  hideDefaultSwitches: {
    type: Boolean,
    default: false,
  },
  hideActionsMenu: {
    type: Boolean,
    default: false,
  },
  hideExportButton: {
    type: Boolean,
    default: false,
  },
  hideSearchField: {
    type: Boolean,
    default: false,
  },
  hideDefaultFooter: {
    type: Boolean,
    default: false,
  },

  // Selection
  showSelect: {
    type: Boolean,
    default: false,
  },

  // Search & filtering
  onlyTextSearch: {
    type: Boolean,
    default: false,
  },
  advancedSearch: {
    type: Boolean,
    default: false,
  },
  disableFiltering: {
    type: Boolean,
    default: false,
  },
  showFilterBarByDefault: {
    type: Boolean,
    default: false,
  },
  defaultFilters: {
    type: Array,
    default: null,
  },
  initialFilters: {
    type: Object,
    default: undefined,
  },
  library: {
    type: String,
    default: '',
  },
  columnDataResource: {
    type: String,
    default: '',
  },
  columnDataParameters: {
    type: Object,
    default: undefined,
  },
  initialColumnData: {
    type: Object,
    default: undefined,
  },
  fixedColumnData: {
    type: Object,
    default: undefined,
  },
  codelistUid: {
    type: String,
    default: undefined,
  },
  filtersModifyFunction: {
    type: Function,
    default: undefined,
  },

  // Sorting & pagination
  initialSortBy: {
    type: Array,
    default: () => [],
  },
  itemsPerPage: {
    type: Number,
    default: null,
  },
  itemsPerPageOptions: {
    type: Array,
    default: null,
  },

  // Columns
  modifiableTable: {
    type: Boolean,
    default: true,
  },
  modifyOnlyColumns: {
    type: Boolean,
    default: false,
  },
  showColumnNamesToggleButton: {
    type: Boolean,
    default: false,
  },

  // Export config: { objectLabel, dataUrl, dataUrlParams }
  exportConfig: {
    type: Object,
    default: undefined,
  },
  exportVisibleColumnsOnly: {
    type: Boolean,
    default: false,
  },

  // History config: { dataFetcher, title, htmlFields, simpleStyling, changeField, changeFieldLabel, excludedHeaders, externalHeaders }
  historyConfig: {
    type: Object,
    default: undefined,
  },

  // Loading
  loadingWatcher: {
    type: Boolean,
    required: false,
  },

  // Unique identifier for localStorage column persistence when multiple tables share the same route
  tableId: {
    type: String,
    default: '',
  },
})
const emit = defineEmits(['filter', 'customSort'])

const { t } = useI18n()
const appStore = useAppStore()
const tablesLayoutStore = useTablesLayoutStore()
const route = useRoute()
const storageKey = computed(() =>
  props.tableId ? `${route.path}::${props.tableId}` : route.path
)
const columnValueIndex = ref('')
const tableRoot = ref(null)
// Range objects contributed by this instance to the shared Highlight.
const instanceHighlightRanges = new Set()
const loading = ref(true)
const showSelectBoxes = ref(false)
const showFilterBar = ref(false)
const shownColumns = ref([])
const selected = ref([])
const search = ref('')
const matchWholeWords = ref(false)
const itemsToFilter = ref([])
const historyItems = ref([])
const historyItemsTotal = ref(0)
const apiParams = new Map()
const trigger = ref(0)
const showColumnNames = ref(false)
const showHistory = ref(false)
const sortBy = ref(props.initialSortBy)
const selectedColumnData = ref({})
const confirm = ref()
const selectedColumns = ref([])
const loadFilters = ref(false)
const externalColumns = ref([])
const currentPageNumber = ref(1)
const currentItemsPerPageValue = ref(25)

const headerActions = [
  {
    label: t('NNTable.sort_asc'),
    click: sortAscending,
    available: true,
  },
  {
    label: t('NNTable.sort_desc'),
    click: sortDescending,
    available: true,
  },
  {
    label: t('NNTable.add_to_filter'),
    click: addToFilter,
    available: Boolean(!props.disableFiltering),
  },
  {
    label: t('NNTable.hide_column'),
    click: hideColumn,
    available: true,
  },
]
let timeout
let savedOptions = {}
let savedFilters = '{}'

const computedItemsPerPage = computed(() => {
  return props.itemsPerPage ? props.itemsPerPage : appStore.rowsPerPage
})
const computedItemsPerPageOptions = computed(() => {
  return props.itemsPerPageOptions
    ? props.itemsPerPageOptions
    : tablesConstants.ITEMS_PER_PAGE_OPTIONS
})
const historyHeaders = computed(() => {
  if (props.historyConfig?.externalHeaders) {
    return props.historyConfig.externalHeaders
  }
  const result = [...props.headers]
  result.unshift({
    title: t('_global.uid'),
    key: props.itemValue,
  })
  return result
})

watch(
  () => props.headers,
  () => {
    if (externalColumns.value.length > 0) {
      shownColumns.value = externalColumns.value
      selectedColumns.value = externalColumns.value
      externalColumns.value = []
    } else {
      updateColumns()
    }
  }
)
watch(
  () => props.loadingWatcher,
  (value) => {
    loading.value = value
  }
)
watch(
  () => props.items,
  (val) => {
    if (val !== undefined) {
      loading.value = false
    }
  }
)
watch(showSelectBoxes, (val) => {
  if (!val) {
    selected.value = []
  }
})
watch(selectedColumns, () => {
  let arr
  arr = props.headers.filter(function (item) {
    return (
      item.title === '' ||
      selectedColumns.value.find((ele) => ele.key === item.key)
    )
  })
  shownColumns.value = arr.map((e) => ({ ...e, sortable: false }))
  if (props.modifiableTable || props.modifyOnlyColumns) {
    const layoutMap = new Map()
    layoutMap.set(
      storageKey.value,
      shownColumns.value.map((h) => h.key)
    )
    tablesLayoutStore.setColumns(layoutMap)
  }
})
watch(
  () => props.showSelect,
  (value) => {
    showSelectBoxes.value = value
  }
)
watch(itemsToFilter, () => {
  apiParams.forEach((value, key) => {
    const check = (obj) => obj.key === key
    if (!itemsToFilter.value.some(check)) {
      apiParams.delete(key)
    }
  })
})

watch(search, (newValue, oldValue) => {
  if (newValue !== oldValue) {
    currentPageNumber.value = 1
  }
})

watch(matchWholeWords, () => {
  currentPageNumber.value = 1
  filterTable()
})

onMounted(() => {
  showSelectBoxes.value = props.showSelect
  tablesLayoutStore.initiateColumns()
  updateColumns()

  // Initialize pagination state
  currentItemsPerPageValue.value = computedItemsPerPage.value

  if (props.showFilterBarByDefault) {
    itemsToFilter.value = props.headers.filter(
      (header) => header.key !== 'actions' && !header.noFilter
    )
  } else if (props.defaultFilters) {
    itemsToFilter.value = props.defaultFilters
  } else if (
    !props.defaultFilters &&
    !props.disableFiltering &&
    !props.onlyTextSearch
  ) {
    itemsToFilter.value = shownColumns.value.filter(
      (col) => col.key !== 'actions' && !col.noFilter
    )
  }
  if (props.items && props.items.length) {
    loading.value = false
  }
  if (props.initialFilters !== undefined) {
    selectedColumnData.value = props.initialFilters
    const filters = {}
    for (const key in props.initialFilters) {
      filters[key] = { v: props.initialFilters[key] }
      apiParams.set(key, props.initialFilters[key])
    }
    filters.value = JSON.stringify(filters)
  }
})

let cleanupHeaderListeners = null

onUpdated(() => {
  if (cleanupHeaderListeners) {
    cleanupHeaderListeners()
  }

  const headers = document.querySelectorAll(
    'div[class*="v-window-item--active"] th'
  )
  const handlers = []

  for (let index = 0; index < shownColumns.value.length; index++) {
    const header = headers[index]
    if (!header) {
      continue
    }
    const onMouseover = () => {
      const realIndex = showSelectBoxes.value ? index - 1 : index
      if (realIndex >= 0) {
        columnValueIndex.value = shownColumns.value[realIndex].key
      }
    }
    const onMouseleave = () => {
      columnValueIndex.value = ''
    }
    header.addEventListener('mouseover', onMouseover)
    header.addEventListener('mouseleave', onMouseleave)
    handlers.push({ header, onMouseover, onMouseleave })
  }

  cleanupHeaderListeners = () => {
    handlers.forEach(({ header, onMouseover, onMouseleave }) => {
      header.removeEventListener('mouseover', onMouseover)
      header.removeEventListener('mouseleave', onMouseleave)
    })
  }

  highlightSearchMatches()
})

onUnmounted(() => {
  if (cleanupHeaderListeners) {
    cleanupHeaderListeners()
  }
  removeRangesFromSharedHighlight(instanceHighlightRanges)
  instanceHighlightRanges.clear()
})

function enableFiltering() {
  showFilterBar.value = !showFilterBar.value
  loadFilters.value = true
}

// Highlights the currently searched text within the rendered table cells only
// (i.e. the data actually displayed, not the full API objects).
function highlightSearchMatches() {
  if (typeof CSS === 'undefined' || !CSS.highlights || !window.Highlight) {
    return
  }
  // Clear only this instance's previously registered ranges so other
  // NNTable instances keep their highlights intact.
  removeRangesFromSharedHighlight(instanceHighlightRanges)
  instanceHighlightRanges.clear()
  const term = (search.value || '').trim()
  if (!term || !tableRoot.value) {
    return
  }
  const lowerTerm = term.toLowerCase()
  const cells = tableRoot.value.querySelectorAll('table tbody td')
  const ranges = []
  cells.forEach((cell) => {
    const walker = document.createTreeWalker(cell, NodeFilter.SHOW_TEXT)
    let node
    while ((node = walker.nextNode())) {
      const text = node.nodeValue
      if (!text) {
        continue
      }
      const lowerText = text.toLowerCase()
      let fromIndex = 0
      let matchIndex = lowerText.indexOf(lowerTerm, fromIndex)
      while (matchIndex !== -1) {
        const range = document.createRange()
        range.setStart(node, matchIndex)
        range.setEnd(node, matchIndex + term.length)
        ranges.push(range)
        fromIndex = matchIndex + term.length
        matchIndex = lowerText.indexOf(lowerTerm, fromIndex)
      }
    }
  })
  if (ranges.length) {
    const highlight = getSharedHighlight()
    if (highlight) {
      ranges.forEach((range) => {
        highlight.add(range)
        instanceHighlightRanges.add(range)
      })
    }
  }
}

function updateColumns() {
  if (!props.modifiableTable && !props.modifyOnlyColumns) {
    if (props.defaultHeaders && props.defaultHeaders.length !== 0) {
      shownColumns.value = props.defaultHeaders
    } else {
      shownColumns.value = JSON.parse(JSON.stringify(props.headers))
    }
    return
  }
  if (
    !tablesLayoutStore.columns[storageKey.value] ||
    tablesLayoutStore.columns[storageKey.value].length === 0
  ) {
    if (props.defaultHeaders && props.defaultHeaders.length !== 0) {
      shownColumns.value = props.defaultHeaders
    } else {
      shownColumns.value = JSON.parse(JSON.stringify(props.headers))
    }
  } else {
    const savedKeys = tablesLayoutStore.columns[storageKey.value]
    const currentKeys = props.headers.map((h) => h.key)
    const validKeys = savedKeys.filter((k) => currentKeys.includes(k))
    // A saved layout goes stale when the header set changes (e.g. schema-driven
    // columns whose keys were renamed): the intersection can collapse to nothing
    // displayable, leaving only synthetic (title-less) columns like a select
    // radio and rendering the table blank. Recover by resetting to the default
    // columns and overwriting the stale entry so it stops overriding on reload.
    const survivesDisplayable = props.headers.some(
      (h) => validKeys.includes(h.key) && h.title !== ''
    )
    if (!survivesDisplayable) {
      shownColumns.value =
        props.defaultHeaders && props.defaultHeaders.length !== 0
          ? props.defaultHeaders
          : JSON.parse(JSON.stringify(props.headers))
      const layoutMap = new Map()
      layoutMap.set(
        storageKey.value,
        shownColumns.value.map((h) => h.key)
      )
      tablesLayoutStore.setColumns(layoutMap)
    } else {
      shownColumns.value = props.headers
        .filter((h) => validKeys.includes(h.key) || h.title === '')
        .map((h) => ({ ...h }))
      // Clean up stale keys that no longer exist in current headers
      if (validKeys.length !== savedKeys.length) {
        const layoutMap = new Map()
        layoutMap.set(storageKey.value, validKeys)
        tablesLayoutStore.setColumns(layoutMap)
      }
    }
  }
  selectedColumns.value = props.headers.filter((h) =>
    shownColumns.value.some((sc) => sc.key === h.key)
  )
}
function headersHasAction() {
  return Boolean(props.headers.find((ele) => ele.title === ''))
}
function getValueByColumn(item, columnName) {
  const keys = columnName.split('.')
  return keys.reduce((acc, key) => (acc ? acc[key] : undefined), item)
}
function getHeaderSlotName(header) {
  return `header.${header.key}`
}
function getColumnInitialData(column) {
  return props.initialColumnData
    ? props.initialColumnData[column.key]
    : undefined
}
function getColumnFixedData(column) {
  return props.fixedColumnData ? props.fixedColumnData[column.key] : undefined
}
function getColumnSelectedData(column) {
  return selectedColumnData.value
    ? selectedColumnData.value[column.key]
    : undefined
}
function sortAscending(header) {
  sortBy.value = [{ key: header.sortKey || header.key, order: 'asc' }]
  filterTable()
}
function sortDescending(header) {
  sortBy.value = [{ key: header.sortKey || header.key, order: 'desc' }]
  filterTable()
}
function disableColumnSwitch(column) {
  const firstHeaderIndex = headersHasAction() ? 1 : 0
  return (
    selectedColumns.value.length === 1 + firstHeaderIndex &&
    column.title === selectedColumns.value[firstHeaderIndex].title
  )
}
function addToFilter(header) {
  if (
    itemsToFilter.value[
      itemsToFilter.value.findIndex((el) => el.key === header.key)
    ]
  ) {
    itemsToFilter.value.splice(
      itemsToFilter.value.findIndex((el) => el.key === header.key),
      1
    )
  } else {
    itemsToFilter.value.push(header)
  }
  showFilterBar.value = true
}
function hideColumn(header) {
  shownColumns.value.splice(
    shownColumns.value.findIndex((el) => el.key === header.key),
    1
  )
  const layoutMap = new Map()
  layoutMap.set(
    storageKey.value,
    shownColumns.value.map((h) => h.key)
  )
  tablesLayoutStore.setColumns(layoutMap)
}
function rowProps(data) {
  let result = props.subTables ? 'subRowsTable' : ''
  if (props.extraItemClass) {
    result += props.extraItemClass(data.item)
  }
  return {
    class: result,
  }
}
function clearFilters() {
  apiParams.clear()
  search.value = null
  trigger.value += 1
  currentPageNumber.value = 1
  emit('filter')
}
function columnFilter(params) {
  apiParams.set(params.column, params.data)
  savedOptions.page = 1
  currentPageNumber.value = 1
  filterTable()
}

function filterTable(options) {
  loading.value = true
  if (timeout) clearTimeout(timeout)
  if (options) {
    savedOptions = { ...savedOptions, ...options }
  } else {
    options = savedOptions || {}
  }

  // Reset to page 1 if search term changes
  if (options.search && options.search !== (savedOptions.search || '')) {
    options.page = 1
    savedOptions.page = 1
    currentPageNumber.value = 1
  }

  // Ensure page is never less than 1, and ignore Vuetify's page calculation when itemsLength is -1
  if (options.page && options.page < 1) {
    options.page = 1
    savedOptions.page = 1
    currentPageNumber.value = 1
  } else if (
    options.page &&
    options.page !== currentPageNumber.value &&
    props.itemsLength !== -1
  ) {
    // Only sync with Vuetify's page when we have a known total
    currentPageNumber.value = options.page
  }

  apiParams.delete('*')
  if (options.search) {
    apiParams.set('*', [options.search])
  }
  timeout = setTimeout(() => {
    if (options.sortBy === undefined) {
      options.sortBy = sortBy.value
    }
    for (const elem of apiParams.entries()) {
      if (elem[1].length === 0) {
        apiParams.delete(elem[0])
      }
    }
    const filterObj = {}
    for (const [key, values] of apiParams.entries()) {
      if (values.length === 0) continue
      filterObj[key] = { v: values }
    }
    const dateKeys = [
      'start_date',
      'name.start_date',
      'attributes.start_date',
      'Timestamp',
    ]
    for (const key of dateKeys) {
      if (filterObj[key]) {
        const vals = apiParams.get(key)
        filterObj[key].op = vals[0] === vals[1] ? 'co' : 'bw'
      }
    }
    const newFilters = JSON.stringify(filterObj)
    const filtersUpdated = savedFilters && newFilters !== savedFilters
    savedFilters = newFilters
    emit('filter', savedFilters, options, filtersUpdated)
  }, 500)
}
async function confirmExport(resolve) {
  if (!selected.value.length) {
    const msg = t('NNTable.export_confirmation')
    if (!(await confirm.value.open(msg, { type: 'warning' }))) {
      return resolve(false)
    }
  }
  resolve(true)
}
async function getHistoryData(options) {
  loading.value = true
  const resp = await props.historyConfig.dataFetcher(options)
  if (resp.items) {
    historyItems.value = resp.items
    historyItemsTotal.value = resp.total
  } else {
    historyItems.value = resp
    historyItemsTotal.value = resp.length
  }
  loading.value = false
}
async function openHistory() {
  showHistory.value = true
}
function closeHistory() {
  showHistory.value = false
}
function customSort(data) {
  emit('customSort', data)
}
function setExternalColumns(columns) {
  externalColumns.value = columns
}
function updatePage(newPage, itemsPerPage) {
  // Ensure page number is never less than 1
  const validPage = Math.max(1, newPage)
  currentPageNumber.value = validPage
  currentItemsPerPageValue.value = itemsPerPage
  const newOptions = {
    ...savedOptions,
    page: validPage,
    itemsPerPage: itemsPerPage,
  }
  filterTable(newOptions)
}
function updateItemsPerPage(newItemsPerPage) {
  currentPageNumber.value = 1
  currentItemsPerPageValue.value = newItemsPerPage
  const newOptions = {
    ...savedOptions,
    page: 1,
    itemsPerPage: newItemsPerPage,
  }
  filterTable(newOptions)
}

function handleTableOptionsUpdate(options) {
  // Prevent page 0 or negative pages from ever being processed
  if (options.page && options.page < 1) {
    options.page = 1
  }

  // When itemsLength is -1, ignore Vuetify's page calculations completely
  if (props.itemsLength === -1) {
    // Only update if it's a legitimate change (search, sort, items per page)
    const legitimateUpdate =
      options.search !== undefined ||
      options.sortBy !== undefined ||
      (options.itemsPerPage &&
        options.itemsPerPage !== currentItemsPerPageValue.value)

    if (legitimateUpdate) {
      // Keep our current page unless it's a search/filter change
      if (options.search !== undefined) {
        options.page = 1
        currentPageNumber.value = 1
      } else {
        options.page = currentPageNumber.value
      }
    } else {
      // Ignore page-only updates when total is unknown
      return
    }
  }

  filterTable(options)
}

function getPaginationStartNumber() {
  return (currentPageNumber.value - 1) * currentItemsPerPageValue.value + 1
}

function getPaginationEndNumber() {
  if (currentItemsPerPageValue.value === -1) {
    return props.items.length
  }

  if (props.itemsLength === -1) {
    return currentPageNumber.value * currentItemsPerPageValue.value
  }

  return Math.min(
    currentPageNumber.value * currentItemsPerPageValue.value,
    props.itemsLength
  )
}

function getPaginationTotalDisplay() {
  return props.itemsLength === -1 ? 'many' : props.itemsLength
}

defineExpose({
  filterTable,
  clearFilters,
  selected,
  setExternalColumns,
  search,
  matchWholeWords,
  selectedColumns,
  showFilterBar,
  loadFilters,
})
</script>

<style>
.disableUpperCase {
  text-transform: capitalize;
}
::highlight(nn-search-highlight) {
  background-color: #ffe28a;
  color: rgba(0, 0, 0, 0.87);
}
.headerRow {
  flex-wrap: unset;
  max-height: 16px;
}
.fontSize16 {
  font-size: 16px !important;
}
.columnList {
  border-radius: 15px !important;
  max-height: 600px !important;
}
.filteringBar {
  height: 50px;
  border-radius: 4px;
}

.v-text-field .v-input__control .v-input__slot .v-text-field__slot {
  display: flex !important;
  min-height: 30px;
}

.v-text-field:not(.v-select--is-multi):not(.v-textarea--auto-grow)
  .v-input__control
  .v-input__slot {
  height: 30px !important;
}

.subRowsTable {
  background-color: #e3f2fd;
}

.searchFieldLabel.v-text-field label {
  font-size: 14px;
}
.scale80 {
  scale: 80%;
}
.clearAllBtn {
  color: rgb(var(--v-theme-nnBaseBlue)) !important;
}

/* Prevent the "Select rows" switch label from wrapping/shrinking */
.selectRowsSwitch {
  flex-shrink: 0;
}

.selectRowsSwitch :deep(.v-label) {
  white-space: nowrap;
}

/* Essential search container styling */
.search-container {
  min-height: 42px;
  padding-left: 0 !important;
  margin-left: 0 !important;
}

.searchFieldLabel.v-text-field {
  margin-left: 0 !important;
}

.searchFieldLabel.v-text-field :deep(.v-field__outline) {
  border-radius: 4px !important;
}

/* Only essential card styling */
:deep(.v-card) {
  border-radius: 0 !important;
  overflow: visible;
}

:deep(.v-card-title) {
  padding-left: 0 !important;
  padding-right: 16px;
}

/* Search field white background */
.searchFieldLabel.v-text-field .v-field__overlay,
[data-cy='search-field'] .v-field__overlay {
  background-color: white !important;
  opacity: 1 !important;
}

/* Ensure text remains visible */
.searchFieldLabel.v-text-field input {
  color: rgba(0, 0, 0, 0.87) !important;
}

/* Essential white background styles */
.v-field__overlay {
  background-color: white !important;
  opacity: 1 !important;
}
</style>
