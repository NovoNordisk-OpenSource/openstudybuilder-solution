<template>
  <div>
    <v-row>
      <v-col cols="3">
        <v-card rounded="lg" variant="flat" class="timeline-height">
          <v-card-text>
            <template
              v-for="(groupModels, qualifier) in groupedModels"
              :key="qualifier"
            >
              <div
                class="text-caption font-weight-bold text-medium-emphasis text-uppercase mt-3 mb-1 pl-2"
              >
                {{ qualifier || 'Sponsor' }}
              </div>
              <v-divider class="mb-1" />
              <v-timeline density="compact">
                <v-timeline-item
                  v-for="model of groupModels"
                  :key="model.name"
                  :dot-color="
                    activeModel?.name === model.name ? 'primary' : 'grey'
                  "
                  size="small"
                  right
                >
                  <v-btn
                    variant="text"
                    :color="
                      activeModel?.name === model.name ? 'primary' : 'default'
                    "
                    @click="activeModel = model"
                  >
                    {{ model.extended_implementation_guide || model.name }} -
                    {{ model.version }}
                  </v-btn>
                </v-timeline-item>
              </v-timeline>
            </template>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="9">
        <v-card v-if="activeModel" rounded="lg" variant="flat">
          <v-card-title>
            {{ $t('SponsorDataModels.datasets') }} - {{ activeModel.name }}
          </v-card-title>
          <v-card-text>
            <NNTable
              ref="datasetTable"
              key="datasetTable"
              table-id="sponsor-models-datasets"
              :headers="datasetHeaders"
              :default-headers="datasetDefaultHeaders"
              :items="datasets"
              :items-length="totalDatasets"
              :items-per-page="itemsPerPage"
              :page="currentDatasetPage"
              :loading="loadingDatasets"
              :row-props="getRowProps"
              density="compact"
              no-padding
              :disable-filtering="!FILTERING_ENABLED"
              hide-search-field
              hide-default-switches
              export-visible-columns-only
              :export-config="datasetExportConfig"
              @filter="fetchDatasets"
            >
              <template #[`item.select`]="{ item }">
                <v-radio-group v-model="selectedDataset" hide-details>
                  <v-radio :value="item.uid" />
                </v-radio-group>
              </template>
              <template
                v-for="header in datasetFormattableHeaders"
                #[`item.${header.key}`]="{ item }"
                :key="header.key"
              >
                {{ formatCell(item[header.key], header._type) }}
              </template>
            </NNTable>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-card v-if="selectedDataset" rounded="lg" variant="flat">
          <v-card-text>
            <NNTable
              ref="variableTable"
              key="variableTable"
              table-id="sponsor-models-variables"
              :headers="variableHeaders"
              :default-headers="variableDefaultHeaders"
              :items="variables"
              :items-length="totalVariables"
              :page="currentVariablePage"
              :loading="loadingVariables"
              :row-props="getRowProps"
              density="compact"
              no-padding
              :disable-filtering="!FILTERING_ENABLED"
              hide-search-field
              hide-default-switches
              export-visible-columns-only
              :export-config="variableExportConfig"
              @filter="fetchVariables"
            >
              <template #[`item.label`]="{ item }">
                {{ item.label }}
                <v-icon
                  v-if="item.dataset.key_order"
                  icon="mdi-key-outline"
                  :title="item.dataset.key_order"
                />
              </template>
              <template #[`item.order`]="{ item }">
                {{ item.dataset?.ordinal }}
              </template>
              <template
                v-for="header in variableFormattableHeaders"
                #[`item.${header.key}`]="{ item }"
                :key="header.key"
              >
                {{ formatCell(item[header.key], header._type) }}
              </template>
              <template #[`item.referenced_codelists`]="{ item }">
                <template v-if="item.referenced_codelists">
                  <v-btn
                    v-for="codelist in item.referenced_codelists"
                    :key="codelist.uid"
                    variant="text"
                    @click="openCodelistDialog(codelist.uid)"
                  >
                    {{ codelist.submission_value }}
                  </v-btn>
                </template>
              </template>
            </NNTable>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <v-dialog v-model="showCodelistDialog" persistent>
      <StandardsCodelistTermsDialog
        :codelist-uid="selectedCodelistUid"
        @close="closeCodelistDialog"
      />
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, watch, computed, inject } from 'vue'
import { useI18n } from 'vue-i18n'
import standardsApi from '@/api/standards'
import NNTable from '@/components/tools/NNTable.vue'
import filteringParameters from '@/utils/filteringParameters'
import StandardsCodelistTermsDialog from '@/components/library/StandardsCodelistTermsDialog.vue'
import { useSponsorModelSchemasStore } from '@/stores/sponsor-model-schemas'
import dataFormating from '@/utils/dataFormating'

const props = defineProps({
  uid: {
    type: String,
    default: null,
  },
})

const { t, te } = useI18n()
const notificationHub = inject('notificationHub')
const schemasStore = useSponsorModelSchemasStore()

// FILTERING SEAM: per-column filtering is disabled for Sponsor Models because
// the API cannot reliably filter on sponsor-specific fields yet. Flip this to
// true to re-enable filtering once server-side support lands.
const FILTERING_ENABLED = false

// Legacy Sponsor Models without a schema_version follow schema version 1.
const DEFAULT_SCHEMA_VERSION = 1

// Columns rendered by bespoke slots below - excluded from the generic
// type-aware formatting slot loop so their custom markup wins.
const DATASET_CUSTOM_KEYS = ['select']
// `order` is rendered from `item.dataset.ordinal`: the schema's `order`
// api_field is an import-time (write) field only, the read model nests the
// actual value under `dataset.ordinal` (see SponsorModelDatasetVariable in
// the API).
const VARIABLE_CUSTOM_KEYS = ['label', 'referenced_codelists', 'order']

// The dataset table's radio-select column is synthetic (not part of the schema).
const DATASET_SELECT_HEADER = { key: 'select', title: '', width: '5%' }

// The identity column the page always shows. The schema declares this field as
// `dataset_uid` / `dataset_variable_uid`, but the list endpoints project it onto
// the row as `uid`, so we pin it as a fixed leading column keyed to `uid` rather
// than resolving it from the schema's structural list.
const UID_HEADER = { key: 'uid', title: 'UID', sortable: false }

// Minimal, always-safe columns used when a schema cannot be loaded.
const DATASET_FALLBACK_HEADERS = [
  DATASET_SELECT_HEADER,
  { key: 'uid', title: 'UID', sortable: false },
  { key: 'label', title: t('_global.label'), sortable: false },
]
const VARIABLE_FALLBACK_HEADERS = [
  { key: 'uid', title: 'UID', sortable: false },
  { key: 'label', title: t('_global.label'), sortable: false },
]

const activeModel = ref(null)
const currentDatasetPage = ref(1)
const currentVariablePage = ref(1)
const datasets = ref([])
const datasetTable = ref()
const variableTable = ref()
const itemsPerPage = ref(5)
const loadingDatasets = ref(false)
const loadingVariables = ref(false)
const models = ref([])
const selectedCodelistUid = ref(null)
const selectedDataset = ref(null)
const showCodelistDialog = ref(false)
const totalDatasets = ref(0)
const totalVariables = ref(0)
const variables = ref([])
const activeSchema = ref(null)

// --- Schema-driven header construction -------------------------------------

// Humanize an api_field for display when no i18n title is available,
// e.g. 'map_domain_flag' -> 'Map domain flag'.
function humanize(apiField) {
  if (!apiField) return ''
  return apiField
    .split('_')
    .map((word, index) =>
      index === 0 && word ? word.charAt(0).toUpperCase() + word.slice(1) : word
    )
    .join(' ')
}

// ui.column_title is an i18n key that may not exist in our locales. Resolve it
// when present, otherwise fall back to a humanized api_field.
function resolveTitle(field) {
  const key = field.ui?.column_title
  if (key && te(key)) {
    return t(key)
  }
  return humanize(field.api_field)
}

// Column sort: by ui.order ascending; fields without an order go last, tie-
// broken stably by api_field.
function compareColumnOrder(a, b) {
  const aOrder = a.ui?.order
  const bOrder = b.ui?.order
  const aHas = aOrder !== undefined && aOrder !== null
  const bHas = bOrder !== undefined && bOrder !== null
  if (aHas && bHas) return aOrder - bOrder
  if (aHas) return -1
  if (bHas) return 1
  return a.api_field.localeCompare(b.api_field)
}

function fieldToHeader(field) {
  return {
    key: field.api_field,
    title: resolveTitle(field),
    sortable: false,
    _type: field.type,
  }
}

// Some schema fields are declared more than once under the same api_field with
// mutually-exclusive `condition`s (e.g. `is_cdisc_std` is derived from a
// different source column depending on the CSV layout - see
// how_to_customize_sponsor_model.md). Those are import-time alternatives for
// the SAME field, not separate columns, so collapse them to one entry per
// api_field. Prefer whichever entry carries a `ui` block, since that's the one
// with column metadata (title/order/visibility) when only one of them declares it.
function dedupeByApiField(fields) {
  const byApiField = new Map()
  for (const field of fields) {
    const existing = byApiField.get(field.api_field)
    if (!existing || (!existing.ui && field.ui)) {
      byApiField.set(field.api_field, field)
    }
  }
  return [...byApiField.values()]
}

// Build the header set for an entity from its schema: the `leadingHeaders`
// (synthetic/identity columns the page always shows, e.g. select + uid)
// followed by the displayable schema fields sorted by column order.
//
// Most structural fields are the injected relationship backbone and are not
// surfaced as columns, but some (e.g. `label`) are structural purely so they
// are filterable while still belonging in the table. A `ui` block is the
// schema's signal that a field is displayable, so structural fields that
// declare one are merged in with the extensible fields and ordered together.
function buildHeaders(
  schema,
  entity,
  { leadingHeaders = [], defaultOnly = false } = {}
) {
  const entitySchema = schema?.entities?.[entity]
  const structural = entitySchema?.structural ?? []
  const extensible = entitySchema?.extensible ?? []

  let fields = dedupeByApiField([
    ...structural.filter((field) => field.ui),
    ...extensible,
  ])
  if (defaultOnly) {
    fields = fields.filter((field) => field.ui?.default_visible === true)
  }
  // ORDERING SEAM: rows are rendered in API order for now. Schema-driven row
  // ordering (one extensible field flagged as the ordering source) is a
  // follow-up; it does not affect column ordering computed here.
  fields.sort(compareColumnOrder)

  return [...leadingHeaders, ...fields.map(fieldToHeader)]
}

const datasetHeaders = computed(() => {
  if (!activeSchema.value) return DATASET_FALLBACK_HEADERS
  return buildHeaders(activeSchema.value, 'dataset', {
    leadingHeaders: [DATASET_SELECT_HEADER, UID_HEADER],
  })
})

const datasetDefaultHeaders = computed(() => {
  if (!activeSchema.value) return DATASET_FALLBACK_HEADERS
  return buildHeaders(activeSchema.value, 'dataset', {
    leadingHeaders: [DATASET_SELECT_HEADER, UID_HEADER],
    defaultOnly: true,
  })
})

const variableHeaders = computed(() => {
  if (!activeSchema.value) return VARIABLE_FALLBACK_HEADERS
  return buildHeaders(activeSchema.value, 'dataset_variable', {
    leadingHeaders: [UID_HEADER],
  })
})

const variableDefaultHeaders = computed(() => {
  if (!activeSchema.value) return VARIABLE_FALLBACK_HEADERS
  return buildHeaders(activeSchema.value, 'dataset_variable', {
    leadingHeaders: [UID_HEADER],
    defaultOnly: true,
  })
})

// Boolean and list-like columns need custom rendering; string/integer columns
// fall through to NNTable's default cell rendering (which already renders
// null as blank and truncates long text). Columns with their own bespoke slots
// are excluded so their interactive markup wins. List types come in variants
// (e.g. `list`, `list_space_separated`), so match any `list*` type.
function needsCustomFormat(type) {
  return (
    type === 'boolean' || (typeof type === 'string' && type.startsWith('list'))
  )
}

const datasetFormattableHeaders = computed(() =>
  datasetHeaders.value.filter(
    (h) => needsCustomFormat(h._type) && !DATASET_CUSTOM_KEYS.includes(h.key)
  )
)
const variableFormattableHeaders = computed(() =>
  variableHeaders.value.filter(
    (h) => needsCustomFormat(h._type) && !VARIABLE_CUSTOM_KEYS.includes(h.key)
  )
)

// Type-aware cell rendering. null/absent -> blank, booleans -> yes/no, lists
// joined (space-separated variants use a space), everything else as-is.
function formatCell(value, type) {
  if (value === null || value === undefined) return ''
  if (type === 'boolean') return dataFormating.yesno(value)
  if (typeof type === 'string' && type.startsWith('list')) {
    if (!Array.isArray(value)) return value
    const separator = type.includes('space') ? ' ' : ', '
    return value.join(separator)
  }
  return value
}

// Resolve and cache the schema for the given Sponsor Model. Degrades to a
// minimal safe column set (via activeSchema = null) on failure.
async function resolveSchema(model) {
  const version = model?.schema_version ?? DEFAULT_SCHEMA_VERSION
  const libraryName = model?.library_name
  try {
    activeSchema.value = await schemasStore.fetchSchema(version, libraryName)
  } catch (error) {
    activeSchema.value = null
    console.warn(
      `Failed to load Sponsor Model schema version ${version}; falling back to minimal columns.`,
      error
    )
    notificationHub.add({
      type: 'warning',
      msg: t('SponsorDataModels.schema_load_failed'),
    })
  }
}

const groupedModels = computed(() => {
  const groups = {}
  for (const model of models.value) {
    const key = model.name_qualifier ?? ''
    if (!groups[key]) groups[key] = []
    groups[key].push(model)
  }
  return groups
})

const datasetExportConfig = computed(() => {
  if (!activeModel.value) return {}
  return {
    objectLabel: 'Datasets',
    dataUrl: 'standards/sponsor-models/datasets',
    dataUrlParams: {
      sponsor_model_name: activeModel.value.name,
      sponsor_model_version: activeModel.value.version,
    },
  }
})

const variableExportConfig = computed(() => {
  if (!activeModel.value || !selectedDataset.value) return {}
  return {
    objectLabel: 'DatasetVariables',
    dataUrl: 'standards/sponsor-models/dataset-variables',
    dataUrlParams: {
      sponsor_model_name: activeModel.value.name,
      sponsor_model_version: activeModel.value.version,
      filters: {
        'dataset.uid': { v: [selectedDataset.value] },
      },
    },
  }
})

async function fetchDatasets(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  if (!options) {
    params.page_size = itemsPerPage.value
    params.page_number = currentDatasetPage.value
  }
  if (!params.filters) {
    params.filters = {}
  }
  params.sponsor_model_name = activeModel.value.name
  params.sponsor_model_version = activeModel.value.version
  loadingDatasets.value = true
  try {
    const resp = await standardsApi.getSponsorModelDatasets(params)
    datasets.value = resp.data.items
    totalDatasets.value = resp.data.total
  } finally {
    loadingDatasets.value = false
  }
}

async function fetchVariables(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  if (!options) {
    variables.value = []
    currentVariablePage.value = 1
    params.page_number = currentVariablePage.value
  }
  if (!params.filters) {
    params.filters = {}
  }
  params.sponsor_model_name = activeModel.value.name
  params.sponsor_model_version = activeModel.value.version
  params.filters['dataset.uid'] = { v: [selectedDataset.value] }
  loadingVariables.value = true
  try {
    const resp = await standardsApi.getSponsorModelDatasetVariables(params)
    variables.value = resp.data.items
    totalVariables.value = resp.data.total
  } finally {
    loadingVariables.value = false
  }
}

function getRowProps(data) {
  const result = {}
  if (!data.item.is_basic_std) {
    result.class = 'bg-nnLightBlue200'
  }
  return result
}

function openCodelistDialog(codelistUid) {
  selectedCodelistUid.value = codelistUid
  showCodelistDialog.value = true
}

function closeCodelistDialog() {
  showCodelistDialog.value = false
}

watch(activeModel, (value) => {
  currentDatasetPage.value = 1
  currentVariablePage.value = 1
  datasets.value = []
  variables.value = []
  selectedDataset.value = null
  resolveSchema(value)
  datasetTable.value?.filterTable()
})

// flush: 'post' ensures this runs after the variables table (re)mounts -
// the table is only rendered while a dataset is selected (see the v-card's
// v-if="selectedDataset" above)
watch(
  selectedDataset,
  (value) => {
    if (value) {
      variableTable.value?.filterTable()
    }
  },
  { flush: 'post' }
)

const resp = await standardsApi.getSponsorModels({
  filters: { uid: { v: [props.uid] } },
  page_size: 0,
})
models.value = resp.data.items
if (models.value.length) {
  await resolveSchema(models.value[0])
  activeModel.value = models.value[0]
}
</script>

<style>
.timeline-height {
  height: auto !important;
}
</style>
