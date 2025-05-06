<template>
  <div>
    <v-row>
      <v-col class="pt-0 mt-0">
        <NNTable
          :headers="selectedExtensionsHeaders"
          item-value="uid"
          :items="selectedExtensions"
          hide-export-button
          disable-filtering
          :modifiable-table="false"
          hide-default-switches
          table-height="300px"
        >
          <template #bottom />
          <template
            #item="{ item, index, internalItem, toggleExpand, isExpanded }"
          >
            <tr :class="item.type ? '' : 'elementBackground'">
              <td width="25%">
                <v-row>
                  <v-btn
                    v-if="isExpanded(internalItem)"
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
                    variant="text"
                    @click="toggleExpand(internalItem)"
                  />
                  <v-btn v-else icon variant="text" class="hide" />
                  <ActionsMenu :actions="actions" :item="item" />
                  <div class="mt-3">
                    {{
                      item.type
                        ? $t('CrfExtensions.attribute')
                        : $t('CrfExtensions.element')
                    }}
                  </div>
                </v-row>
              </td>
              <td width="25%">
                {{ item.name }}
              </td>
              <td width="20%">
                {{ item.vendor_namespace ? item.vendor_namespace.name : '' }}
              </td>
              <td width="20%">
                {{ item.data_type }}
              </td>
              <td width="20%">
                <v-text-field
                  v-if="item.type"
                  v-model="selectedExtensions[index].value"
                  :label="$t('_global.value')"
                  density="compact"
                  class="mt-3"
                  :readonly="readOnly"
                />
              </td>
              <td width="20%">
                <v-btn
                  icon="mdi-delete-outline"
                  class="mt-1"
                  variant="text"
                  :disabled="readOnly"
                  @click="removeExtension(item)"
                />
              </td>
            </tr>
          </template>
          <template #expanded-row="{ columns, item, index }">
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
                <template #item="{ props }">
                  <tr style="background-color: #d8eaf8">
                    <td width="25%">
                      <v-row>
                        <v-btn icon variant="text" class="hide" />
                        <ActionsMenu :actions="actions" :item="props.item" />
                        <div class="mt-3">
                          {{ $t('CrfExtensions.attribute') }}
                        </div>
                      </v-row>
                    </td>
                    <td width="25%">
                      {{ props.item.columns.name }}
                    </td>
                    <td width="20%"></td>
                    <td width="20%">
                      {{ props.item.data_type }}
                    </td>
                    <td width="20%">
                      <v-text-field
                        v-model="
                          selectedExtensions[index].vendor_attributes[
                            props.index
                          ].value
                        "
                        :label="$t('_global.value')"
                        density="compact"
                        :readonly="readOnly"
                      />
                    </td>
                    <td width="20%"></td>
                    <td width="20%"></td>
                    <td width="20%"></td>
                  </tr>
                </template>
              </v-data-table>
            </td>
          </template>
        </NNTable>
      </v-col>
    </v-row>
    <v-row>
      <v-col class="pt-0 mt-0">
        <NNTable
          :headers="extensionsHeaders"
          item-value="uid"
          :items="elements"
          :items-length="total"
          hide-export-button
          disable-filtering
          :modifiable-table="false"
          hide-default-switches
          @filter="getExtensionData"
        >
          <template #item="{ item, internalItem, toggleExpand, isExpanded }">
            <tr :class="item.type ? '' : 'elementBackground'">
              <td width="25%">
                <v-row>
                  <v-btn
                    v-if="isExpanded(internalItem)"
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
                    variant="text"
                    @click="toggleExpand(internalItem)"
                  />
                  <v-btn v-else icon variant="text" class="hide" />
                  <ActionsMenu :actions="actions" :item="item" />
                  <div class="mt-3">
                    {{
                      item.type
                        ? $t('CrfExtensions.attribute')
                        : $t('CrfExtensions.element')
                    }}
                  </div>
                </v-row>
              </td>
              <td width="25%">
                {{ item.name }}
              </td>
              <td width="20%">
                {{ item.vendor_namespace ? item.vendor_namespace.name : '' }}
              </td>
              <td width="20%">
                {{ item.data_type }}
              </td>
              <td width="20%">
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
                <template #item="{ item }">
                  <tr style="background-color: #d8eaf8">
                    <td width="25%">
                      <v-row>
                        <v-btn icon variant="text" class="hide" />
                        <ActionsMenu :actions="actions" :item="item" />
                        <div class="mt-3">
                          {{ $t('CrfExtensions.attribute') }}
                        </div>
                      </v-row>
                    </td>
                    <td width="25%">
                      {{ item.name }}
                    </td>
                    <td width="20%">
                      {{
                        item.vendor_namespace ? item.vendor_namespace.name : ''
                      }}
                    </td>
                    <td width="20%">
                      {{ item.data_type }}
                    </td>
                    <td width="20%"></td>
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
import { onMounted, ref, watch } from 'vue'
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
  { title: t('CrfExtensions.namespace'), key: 'vendor_namespace.name' },
  { title: t('CrfExtensions.data_type'), key: 'data_type' },
  { title: '', key: 'add' },
]
const selectedExtensionsHeaders = [
  { title: t('_global.type'), key: 'type' },
  { title: t('_global.name'), key: 'name' },
  { title: t('CrfExtensions.namespace'), key: 'vendor_namespace.name' },
  { title: t('CrfExtensions.data_type'), key: 'data_type' },
  { title: t('_global.value'), key: 'value' },
  { title: '', key: 'delete' },
]

watch(
  () => props.editExtensions,
  (value) => {
    selectedExtensions.value = value
  }
)

onMounted(async () => {
  await getExtensionData()
  setExtensions()
})

function setExtensions() {
  if (props.editExtensions) {
    selectedExtensions.value = props.editExtensions
    selectedExtensions.value.forEach((ex, index) => {
      const extension = elements.value.find((el) => el.uid === ex.uid)
      if (extension) {
        const value = selectedExtensions.value[index].value
        selectedExtensions.value[index] = extension
        if (value) {
          selectedExtensions.value[index].value = value
        }
      }
    })
    selectedExtensions.value.forEach((ex, index) => {
      if (ex.vendor_attributes) {
        selectedExtensions.value[index].vendor_attributes.forEach((attr, i) => {
          selectedExtensions.value[index].vendor_attributes[i].value =
            selectedExtensions.value.find((ex) => ex.uid === attr.uid).value
        })
      }
    })
    selectedExtensions.value = selectedExtensions.value.filter((ex) => {
      return ex.library_name
    })
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
}

async function getElements(params) {
  params.filters = { compatible_types: { v: [props.type], op: 'co' } }
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
  await crfs.getAllAttributes(params).then((resp) => {
    resp.data.items.forEach((attr) => (attr.type = 'attr'))
    elements.value = [...elements.value, ...resp.data.items]
    total.value += resp.data.total
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
}
</style>
