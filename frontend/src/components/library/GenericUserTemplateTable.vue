<template>
  <NNTable
    v-model="selected"
    table-id="library-generic-user-templates-table"
    :headers="headers"
    :items="templates"
    item-value="uid"
    :items-length="total"
    :initial-sort-by="[{ key: 'start_date' }]"
    sort-desc
    :column-data-resource="columnDataResource"
    :column-data-parameters="extendedColumnDataParameters"
    :export-config="{ objectLabel: objectType, dataUrl: urlPrefix }"
    @filter="filter"
  >
    <template v-for="(_, slot) of $slots" #[slot]="scope">
      <slot :name="slot" v-bind="scope" />
    </template>
    <template #[`item.name`]="{ item }">
      <NNParameterHighlighter :name="item.name" default-color="orange" />
    </template>
    <template #[`item.start_date`]="{ item }">
      <v-tooltip location="top">
        <template #activator="{ props }">
          <span v-bind="props">{{
            $filters.dateRelative(item.start_date)
          }}</span>
        </template>
        {{ $filters.date(item.start_date) }}
      </v-tooltip>
    </template>
    <template #[`item.status`]="{ item }">
      <StatusChip :status="item.status" />
    </template>
  </NNTable>
</template>

<script>
import libraryConstants from '@/constants/libraries'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import templates from '@/api/templates'
import filteringParameters from '@/utils/filteringParameters'

export default {
  components: {
    NNParameterHighlighter,
    NNTable,
    StatusChip,
  },
  props: {
    urlPrefix: {
      type: String,
      default: '',
    },
    translationType: {
      type: String,
      default: '',
    },
    objectType: {
      type: String,
      default: '',
    },
    columnDataResource: {
      type: String,
      default: '',
    },
    exportDataUrlParams: {
      type: Object,
      default: null,
      required: false,
    },
    columnDataParameters: {
      type: Object,
      default() {
        return { filters: {} }
      },
    },
  },
  data() {
    return {
      headers: [
        {
          title: this.$t('_global.template'),
          key: 'name',
          width: '70%',
          filteringName: 'name_plain',
        },
        { title: this.$t('_global.modified'), key: 'start_date' },
        { title: this.$t('_global.modified_by'), key: 'author_username' },
      ],
      options: {},
      selected: [],
      templates: [],
      total: 0,
      api: null,
    }
  },
  computed: {
    extendedColumnDataParameters() {
      const result = this.columnDataParameters
        ? { ...this.columnDataParameters }
        : { filters: {} }
      result.filters['library.name'] = {
        v: [libraryConstants.LIBRARY_USER_DEFINED],
      }
      return result
    },
  },
  created() {
    this.api = templates(this.urlPrefix)
  },
  methods: {
    async filter(filters, options, filtersUpdated) {
      filters = filters
        ? { ...JSON.parse(filters), ...this.columnDataParameters.filters }
        : { ...this.columnDataParameters.filters }
      filters['library.name'] = { v: [libraryConstants.LIBRARY_USER_DEFINED] }
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      this.api.get(params).then((resp) => {
        if (resp.data.items !== undefined) {
          this.templates = resp.data.items
          this.total = resp.data.total
        } else {
          this.templates = resp.data
          this.total = this.templates.length
        }
      })
    },
  },
}
</script>
