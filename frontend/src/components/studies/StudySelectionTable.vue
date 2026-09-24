<template>
  <NNTable
    key="studySelectionTable"
    table-id="studies-selection-table"
    :headers="headers"
    :items="studySelectionItems"
    hide-default-switches
    hide-export-button
    :items-per-page="15"
    elevation="0"
    :items-length="total"
    :show-filter-bar-by-default="showFilterBarByDefault"
    :filters-modify-function="updateHeaderFilters"
    v-bind="$attrs"
    @filter="getStudySelection"
  >
    <template #[`item.studyUid`]="{ item }">
      {{ item.study_id }}
    </template>
    <template #[`item.actions`]="{ item }">
      <v-btn
        :data-cy="$t('StudySelectionTable.copy_item')"
        icon="mdi-content-copy"
        color="primary"
        :title="$t('StudySelectionTable.copy_item')"
        variant="text"
        @click="selectItem(item)"
      />
    </template>
    <template v-for="(_, slot) of $slots" #[slot]="scope">
      <slot :name="slot" v-bind="scope" />
    </template>
  </NNTable>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import NNTable from '@/components/tools/NNTable.vue'
import study from '@/api/study'
import filteringParameters from '@/utils/filteringParameters'

const props = defineProps({
  selectedStudy: {
    type: Object,
    default: null,
  },
  headers: {
    type: Array,
    default: () => [],
  },
  dataFetcherName: {
    type: String,
    default: '',
  },
  extraDataFetcherFilters: {
    type: Object,
    required: false,
    default: undefined,
  },
  showFilterBarByDefault: {
    type: Boolean,
    default: true,
  },
})
const emit = defineEmits(['item-selected'])

const studySelectionItems = ref([])
const total = ref(0)

watch(
  () => props.selectedStudy,
  (value) => {
    if (value && Object.keys(value).length) {
      getStudySelection()
    }
  }
)

onMounted(() => {
  studySelectionItems.value = []
})

async function getStudySelection(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  if (params.filters) {
    params.filters = JSON.parse(params.filters)
  } else {
    params.filters = {}
  }
  if (props.extraDataFetcherFilters) {
    Object.assign(params.filters, { ...props.extraDataFetcherFilters })
  }
  params.filters.study_uid = { v: [props.selectedStudy.uid] }
  study[props.dataFetcherName](params).then((resp) => {
    studySelectionItems.value = resp.data.items
    studySelectionItems.value.forEach((el) => {
      el.study_id =
        props.selectedStudy.current_metadata.identification_metadata.study_id
    })
    total.value = resp.data.total
  })
}

function selectItem(item) {
  emit('item-selected', item)
}

function updateHeaderFilters(jsonFilter, params) {
  jsonFilter.study_uid = { v: [props.selectedStudy.uid] }
  return {
    jsonFilter,
    params,
  }
}

defineExpose({
  studySelectionItems,
})
</script>
