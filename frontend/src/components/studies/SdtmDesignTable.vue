<template>
  <NNTable
    table-id="studies-sdtm-design-table"
    :headers="headers"
    item-value="uid"
    :items-length="total"
    :items="items"
    show-column-names-toggle-button
    disable-filtering
    :export-config="{ objectLabel: type, dataUrl: exportDataUrl }"
    @filter="fetchData"
  />
</template>

<script>
import _isEmpty from 'lodash/isEmpty'
import NNTable from '@/components/tools/NNTable.vue'
import listings from '@/api/listings'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { computed } from 'vue'
import filteringParameters from '@/utils/filteringParameters'

export default {
  components: {
    NNTable,
  },
  props: {
    type: {
      type: String,
      default: 'TA',
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
      headers: [],
      taHeaders: [
        { title: this.$t('SdtmDesignTable.study_id'), key: 'STUDYID' },
        { title: this.$t('SdtmDesignTable.domain_abbr'), key: 'DOMAIN' },
        { title: this.$t('SdtmDesignTable.planned_arm'), key: 'ARMCD' },
        { title: this.$t('SdtmDesignTable.arm_desc'), key: 'ARM' },
        {
          title: this.$t('SdtmDesignTable.planned_order_of_elem'),
          key: 'TAETORD',
        },
        { title: this.$t('SdtmDesignTable.elem_code'), key: 'ETCD' },
        { title: this.$t('SdtmDesignTable.elem_desc'), key: 'ELEMENT' },
        { title: this.$t('SdtmDesignTable.branch'), key: 'TABRANCH' },
        { title: this.$t('SdtmDesignTable.transition_rule'), key: 'TATRANS' },
        { title: this.$t('SdtmDesignTable.epoch'), key: 'EPOCH' },
      ],
      tvHeaders: [
        { title: this.$t('SdtmDesignTable.study_id'), key: 'STUDYID' },
        { title: this.$t('SdtmDesignTable.domain_abbr'), key: 'DOMAIN' },
        { title: this.$t('SdtmDesignTable.visit_number'), key: 'VISITNUM' },
        { title: this.$t('SdtmDesignTable.visit_name'), key: 'VISIT' },
        { title: this.$t('SdtmDesignTable.planned_study_day'), key: 'VISITDY' },
        { title: this.$t('SdtmDesignTable.planned_arm_code'), key: 'ARMCD' },
        { title: this.$t('SdtmDesignTable.planned_arm_desc'), key: 'ARM' },
        { title: this.$t('SdtmDesignTable.visit_start_rule'), key: 'TVSTRL' },
        { title: this.$t('SdtmDesignTable.visit_end_rule'), key: 'TVENRL' },
      ],
      teHeaders: [
        { title: this.$t('SdtmDesignTable.study_id'), key: 'STUDYID' },
        { title: this.$t('SdtmDesignTable.domain_abbr'), key: 'DOMAIN' },
        { title: this.$t('SdtmDesignTable.elem_code'), key: 'ETCD' },
        { title: this.$t('SdtmDesignTable.elem_desc'), key: 'ELEMENT' },
        { title: this.$t('SdtmDesignTable.elem_start_rule'), key: 'TESTRL' },
        { title: this.$t('SdtmDesignTable.elem_end_rule'), key: 'TEENRL' },
        {
          title: this.$t('SdtmDesignTable.elem_planned_duration'),
          key: 'TEDUR',
        },
      ],
      tiHeaders: [
        { title: this.$t('SdtmDesignTable.study_id'), key: 'STUDYID' },
        { title: this.$t('SdtmDesignTable.domain_abbr'), key: 'DOMAIN' },
        {
          title: this.$t('SdtmDesignTable.incl_excl_short_name'),
          key: 'IETESTCD',
        },
        {
          title: this.$t('SdtmDesignTable.incl_excl_criterion'),
          key: 'IETEST',
        },
        { title: this.$t('SdtmDesignTable.incl_excl_cat'), key: 'IECAT' },
        { title: this.$t('SdtmDesignTable.incl_excl_subcat'), key: 'IESCAT' },
        {
          title: this.$t('SdtmDesignTable.incl_excl_criterion_rule'),
          key: 'TIRL',
        },
        {
          title: this.$t('SdtmDesignTable.protocol_criteria_versions'),
          key: 'TIVERS',
        },
      ],
      tsHeaders: [
        { title: this.$t('SdtmDesignTable.study_id'), key: 'STUDYID' },
        { title: this.$t('SdtmDesignTable.domain_abbr'), key: 'DOMAIN' },
        { title: this.$t('SdtmDesignTable.sequence_number'), key: 'TSSEQ' },
        { title: this.$t('SdtmDesignTable.group_id'), key: 'TSGRPID' },
        {
          title: this.$t('SdtmDesignTable.trial_summary_short_name'),
          key: 'TSPARMCD',
        },
        {
          title: this.$t('SdtmDesignTable.trial_summary_param'),
          key: 'TSPARM',
        },
        { title: this.$t('SdtmDesignTable.param_value'), key: 'TSVAL' },
        { title: this.$t('SdtmDesignTable.param_null'), key: 'TSVALNF' },
        { title: this.$t('SdtmDesignTable.param_value_code'), key: 'TSVALCD' },
        {
          title: this.$t('SdtmDesignTable.reference_term_name'),
          key: 'TSVCDREF',
        },
        {
          title: this.$t('SdtmDesignTable.reference_term_version'),
          key: 'TSVCDVER',
        },
      ],
      tdmHeaders: [
        { title: this.$t('SdtmDesignTable.study_id'), key: 'STUDYID' },
        { title: this.$t('SdtmDesignTable.domain_abbr'), key: 'DOMAIN' },
        {
          title: this.$t('SdtmDesignTable.disease_milestone_type'),
          key: 'MIDSTYPE',
        },
        {
          title: this.$t('SdtmDesignTable.disease_milestone_definition'),
          key: 'TMDEF',
        },
        {
          title: this.$t('SdtmDesignTable.disease_milestone_rep_ind'),
          key: 'TMRPT',
        },
      ],
      items: [],
      total: 0,
    }
  },
  computed: {
    exportDataUrl() {
      return `listings/studies/${this.selectedStudy.uid}/sdtm/${this.type.toLowerCase()}`
    },
  },
  watch: {
    options() {
      this.fetchData()
    },
    type() {
      if (this.type === 'TA') {
        this.headers = this.taHeaders
      } else if (this.type === 'TV') {
        this.headers = this.tvHeaders
      } else if (this.type === 'TE') {
        this.headers = this.teHeaders
      } else if (this.type === 'TI') {
        this.headers = this.tiHeaders
      } else if (this.type === 'TS') {
        this.headers = this.tsHeaders
      } else if (this.type === 'TDM') {
        this.headers = this.tdmHeaders
      }
    },
  },
  mounted() {
    if (this.type === 'TA') {
      this.headers = this.taHeaders
    } else if (this.type === 'TV') {
      this.headers = this.tvHeaders
    } else if (this.type === 'TE') {
      this.headers = this.teHeaders
    } else if (this.type === 'TI') {
      this.headers = this.tiHeaders
    } else if (this.type === 'TS') {
      this.headers = this.tsHeaders
    } else if (this.type === 'TDM') {
      this.headers = this.tdmHeaders
    }
  },
  methods: {
    fetchData(filters, options, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      if (this.type === 'TV' && _isEmpty(options.sortBy)) {
        params.sort_by = JSON.stringify({ VISITNUM: true })
      }
      listings
        .getAllSdtm(this.selectedStudy.uid, params, this.type)
        .then((resp) => {
          this.items = resp.data.items
          this.total = resp.data.total
        })
    },
  },
}
</script>
