<template>
  <NNTable
    table-id="studies-analysis-metadata-table"
    :headers="headers"
    item-value="uid"
    :items-length="total"
    :items="items"
    show-column-names-toggle-button
    :column-data-resource="exportDataUrl"
    :export-config="{ objectLabel: exportObjectLabel, dataUrl: exportDataUrl }"
    @filter="fetchData"
  >
    <template v-for="(_, slot) of $slots" #[slot]="scope">
      <slot :name="slot" v-bind="scope" />
    </template>
  </NNTable>
</template>

<script>
import { computed } from 'vue'
import filteringParameters from '@/utils/filteringParameters'
import listings from '@/api/listings'
import NNTable from '@/components/tools/NNTable.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    NNTable,
  },
  props: {
    type: {
      type: String,
      default: '',
    },
    headers: {
      type: Array,
      default: () => [],
    },
  },
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
    }
  },
  data() {
    return {
      items: [],
      total: 0,
    }
  },
  computed: {
    exportDataUrl() {
      return `listings/studies/${this.selectedStudy.uid}/adam/${this.type}`
    },
    exportObjectLabel() {
      return `adam-${this.type}`
    },
  },
  methods: {
    fetchData(filters, options, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      listings
        .getAllAdam(this.selectedStudy.uid, this.type, params)
        .then((resp) => {
          this.items = resp.data.items
          this.total = resp.data.total
        })
    },
  },
}
</script>
