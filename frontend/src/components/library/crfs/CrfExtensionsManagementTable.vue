<template>
  <div>
    <div class="text-subtitle-1 font-weight-bold mb-2">
      {{ $t('CRFExtensions.existing_attributes') }}
    </div>
    <v-row>
      <v-col class="pt-0 mt-0">
        <NNTable
          table-id="crf-extensions-mgmt-selected"
          :headers="selectedExtensionsHeaders"
          item-value="uid"
          :items="sortedSelectedGrouped"
          :items-length="sortedSelectedGrouped.length"
          hide-export-button
          disable-filtering
          :modifiable-table="false"
          hide-default-switches
          table-height="300px"
        >
          <template #bottom />
          <template #item="{ item, internalItem, toggleExpand, isExpanded }">
            <tr v-if="item.isGroupHeader" class="namespace-group-header">
              <td colspan="6" class="namespace-group-cell">
                <strong>{{
                  item.namespace || $t('CRFExtensions.no_namespace')
                }}</strong>
              </td>
            </tr>
            <tr v-else :class="item.type ? '' : 'elementBackground'">
              <td width="12%">
                <v-row>
                  <v-btn
                    v-if="isExpanded(internalItem)"
                    icon="mdi-chevron-down"
                    data-cy="expand-item"
                    variant="text"
                    @click="toggleExpand(internalItem)"
                  />
                  <v-btn
                    v-else-if="
                      item.vendor_attributes &&
                      item.vendor_attributes.length > 0
                    "
                    icon="mdi-chevron-right"
                    data-cy="expand-item"
                    variant="text"
                    @click="toggleExpand(internalItem)"
                  />
                  <v-btn v-else icon variant="text" class="hide" />
                  <div class="mt-3">
                    {{
                      item.type
                        ? $t('CRFExtensions.attribute')
                        : $t('CRFExtensions.element')
                    }}
                  </div>
                </v-row>
              </td>
              <td width="20%">
                {{ item.name }}
              </td>
              <td width="15%">
                {{ item.vendor_namespace ? item.vendor_namespace.name : '' }}
              </td>
              <td width="12%">
                {{ item.data_type }}
              </td>
              <td width="35%">
                <div v-if="item.value_regex" class="regex-hint">
                  {{ $t('CRFExtensions.regex_expression') }}:
                  {{ item.value_regex }}
                </div>
                <v-text-field
                  v-model="item.value"
                  data-cy="selected-extensions"
                  :label="$t('_global.value')"
                  class="mt-3"
                  :readonly="readOnly"
                />
              </td>
              <td width="6%">
                <v-btn
                  icon="mdi-delete-outline"
                  data-cy="remove-extension"
                  class="mt-1"
                  variant="text"
                  :disabled="readOnly"
                  @click="removeExtension(item)"
                />
              </td>
            </tr>
          </template>
          <template #expanded-row="{ columns, item }">
            <td :colspan="columns.length" class="pa-0">
              <v-data-table
                :headers="selectedExtensionsHeaders"
                item-value="uid"
                :items="item.vendor_attributes"
                hide-default-switches
                disable-filtering
                hide-export-button
                :modifiable-table="false"
                hide-default-footer
                hide-default-header
              >
                <template #headers />
                <template #bottom />
                <template #item="{ item: attr }">
                  <tr style="background-color: #d8eaf8">
                    <td width="12%">
                      <v-row>
                        <v-btn icon variant="text" class="hide" />
                        <div class="mt-3">
                          {{ $t('CRFExtensions.attribute') }}
                        </div>
                      </v-row>
                    </td>
                    <td width="20%">
                      {{ attr.name }}
                    </td>
                    <td width="15%">
                      {{
                        attr.vendor_namespace ? attr.vendor_namespace.name : ''
                      }}
                    </td>
                    <td width="12%">
                      {{ attr.data_type }}
                    </td>
                    <td width="35%">
                      <div v-if="attr.value_regex" class="regex-hint">
                        {{ $t('CRFExtensions.regex_expression') }}:
                        {{ attr.value_regex }}
                      </div>
                      <v-text-field
                        v-model="attr.value"
                        :label="$t('_global.value')"
                        :readonly="readOnly"
                      />
                    </td>
                    <td width="6%"></td>
                  </tr>
                </template>
              </v-data-table>
            </td>
          </template>
        </NNTable>
      </v-col>
    </v-row>

    <div class="text-subtitle-1 font-weight-bold mb-2 mt-4">
      {{ $t('CRFExtensions.available_attributes') }}
    </div>
    <v-row>
      <v-col class="pt-0 mt-0">
        <NNTable
          table-id="crf-extensions-mgmt-available"
          :headers="extensionsHeaders"
          item-value="uid"
          :items="sortedAvailableGrouped"
          :items-length="availableElements.length"
          hide-export-button
          disable-filtering
          :modifiable-table="false"
          hide-default-switches
          @filter="getExtensionData"
        >
          <template #bottom />
          <template #item="{ item, internalItem, toggleExpand, isExpanded }">
            <tr v-if="item.isGroupHeader" class="namespace-group-header">
              <td colspan="5" class="namespace-group-cell">
                <strong>{{
                  item.namespace || $t('CRFExtensions.no_namespace')
                }}</strong>
              </td>
            </tr>
            <tr v-else :class="item.type ? '' : 'elementBackground'">
              <td width="12%">
                <v-row>
                  <v-btn
                    v-if="isExpanded(internalItem)"
                    data-cy="expand-item"
                    icon="mdi-chevron-down"
                    variant="text"
                    @click="toggleExpand(internalItem)"
                  />
                  <v-btn
                    v-else-if="
                      item.vendor_attributes &&
                      item.vendor_attributes.length > 0
                    "
                    icon="mdi-chevron-right"
                    data-cy="expand-item"
                    variant="text"
                    @click="toggleExpand(internalItem)"
                  />
                  <v-btn v-else icon variant="text" class="hide" />
                  <div class="mt-3">
                    {{
                      item.type
                        ? $t('CRFExtensions.attribute')
                        : $t('CRFExtensions.element')
                    }}
                  </div>
                </v-row>
              </td>
              <td width="25%">
                {{ item.name }}
              </td>
              <td width="25%">
                {{ item.vendor_namespace ? item.vendor_namespace.name : '' }}
              </td>
              <td width="25%">
                {{ item.data_type }}
              </td>
              <td width="13%">
                <v-btn
                  icon="mdi-plus"
                  :disabled="readOnly"
                  variant="text"
                  @click="addExtension(item)"
                />
              </td>
            </tr>
          </template>
          <template #expanded-row="{ columns, item }">
            <td :colspan="columns.length" class="pa-0">
              <v-data-table
                :headers="extensionsHeaders"
                item-value="uid"
                :items-length="total"
                :items="item.vendor_attributes"
                hide-default-switches
                disable-filtering
                hide-export-button
                :modifiable-table="false"
                hide-default-footer
                hide-default-header
              >
                <template #headers />
                <template #bottom />
                <template #item="{ item: attr }">
                  <tr style="background-color: #d8eaf8">
                    <td width="12%">
                      <v-row>
                        <v-btn icon variant="text" class="hide" />
                        <div class="mt-3">
                          {{ $t('CRFExtensions.attribute') }}
                        </div>
                      </v-row>
                    </td>
                    <td width="25%">
                      {{ attr.name }}
                    </td>
                    <td width="25%">
                      {{
                        attr.vendor_namespace ? attr.vendor_namespace.name : ''
                      }}
                    </td>
                    <td width="25%">
                      {{ attr.data_type }}
                    </td>
                    <td width="13%"></td>
                  </tr>
                </template>
              </v-data-table>
            </td>
          </template>
        </NNTable>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import crfs from '@/api/crfs'
import NNTable from '@/components/tools/NNTable.vue'
import filteringParameters from '@/utils/filteringParameters'

const props = defineProps({
  type: {
    type: String,
    default: null,
  },
  readOnly: Boolean,
  editExtensions: {
    type: Array,
    default: null,
  },
})

const { t } = useI18n()
const emit = defineEmits(['setExtensions'])

const elements = ref([])
const total = ref(0)
const selectedExtensions = ref([])
const extensionsHeaders = [
  { title: t('_global.type'), key: 'type' },
  { title: t('_global.name'), key: 'name' },
  { title: t('CRFExtensions.namespace'), key: 'vendor_namespace.name' },
  { title: t('CRFExtensions.data_type'), key: 'data_type' },
  { title: '', key: 'add' },
]
const selectedExtensionsHeaders = [
  { title: t('_global.type'), key: 'type' },
  { title: t('_global.name'), key: 'name' },
  { title: t('CRFExtensions.namespace'), key: 'vendor_namespace.name' },
  { title: t('CRFExtensions.data_type'), key: 'data_type' },
  { title: t('_global.value'), key: 'value' },
  { title: '', key: 'delete' },
]

function groupByNamespace(items) {
  const sorted = [...items].sort((a, b) => {
    const nsA = a.vendor_namespace?.name || ''
    const nsB = b.vendor_namespace?.name || ''
    return nsA.localeCompare(nsB)
  })
  const result = []
  let currentNs = undefined
  for (const item of sorted) {
    const ns = item.vendor_namespace?.name || ''
    if (ns !== currentNs) {
      currentNs = ns
      result.push({ isGroupHeader: true, namespace: ns, uid: `__header_${ns}` })
    }
    result.push(item)
  }
  return result
}

const sortedSelectedGrouped = computed(() =>
  groupByNamespace(selectedExtensions.value)
)

const availableElements = computed(() => {
  const selectedUids = new Set(selectedExtensions.value.map((e) => e.uid))
  return elements.value.filter((el) => !selectedUids.has(el.uid))
})

const sortedAvailableGrouped = computed(() =>
  groupByNamespace(availableElements.value)
)

watch(
  () => props.editExtensions,
  (value) => {
    selectedExtensions.value = cloneExtensions(value)
  }
)

onMounted(async () => {
  setExtensions()
})

function cloneExtensions(value) {
  return (value || []).map((ext) => ({ ...ext }))
}

function setExtensions() {
  if (props.editExtensions) {
    selectedExtensions.value = cloneExtensions(props.editExtensions)
  }
}

function addExtension(item) {
  if (!selectedExtensions.value.some((el) => el.uid === item.uid)) {
    selectedExtensions.value.push(item)
  }
  emit('setExtensions', selectedExtensions.value)
}

function removeExtension(item) {
  selectedExtensions.value = selectedExtensions.value.filter(
    (el) => el.uid !== item.uid
  )
  emit('setExtensions', selectedExtensions.value)
}

async function getExtensionData(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  await getElements(params)
  await getAttributes(params)
  enrichSelectedExtensions()
}

async function getElements(params) {
  params.filters = { compatible_types: { v: [props.type], op: 'co' } }
  params.fields =
    'uid,name,compatible_types,status,version,possible_actions,vendor_namespace,vendor_attributes'

  params.page_size = 500
  await crfs.getAllElements(params).then((resp) => {
    elements.value = resp.data.items
    total.value = resp.data.total
  })
}

async function getAttributes(params) {
  params.filters = {
    vendor_element: { v: [] },
    compatible_types: { v: [props.type], op: 'co' },
  }
  params.operator = 'and'
  params.fields =
    'uid,name,data_type,compatible_types,status,version,possible_actions,vendor_namespace,vendor_element'

  params.page_size = 500
  await crfs.getAllAttributes(params).then((resp) => {
    resp.data.items.forEach((attr) => (attr.type = 'attr'))
    elements.value = [...elements.value, ...resp.data.items]
    total.value += resp.data.total
  })
}

function enrichSelectedExtensions() {
  const lookup = new Map(elements.value.map((el) => [el.uid, el]))
  selectedExtensions.value.forEach((ext) => {
    if (!ext.vendor_namespace) {
      const match = lookup.get(ext.uid)
      if (match?.vendor_namespace) {
        ext.vendor_namespace = match.vendor_namespace
      }
    }
  })
}
</script>

<style scoped>
#attr .v-table__wrapper > table > thead > tr {
  visibility: collapse;
}
.elementBackground {
  background-color: #b1d5f2;
}
.hide {
  opacity: 0;
  cursor: default;
}
.namespace-group-header {
  background-color: #e3f0fb;
}
.namespace-group-cell {
  padding: 6px 16px !important;
  color: #1a3a5c;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.regex-hint {
  font-size: 0.72rem;
  color: rgba(0, 0, 0, 0.55);
  font-style: italic;
  margin-top: 4px;
  line-height: 1.3;
}
</style>
