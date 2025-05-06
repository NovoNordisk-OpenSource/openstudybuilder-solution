<template>
  <div class="pa-4 bg-white">
    <v-row>
      <v-col cols="4"> </v-col>
      <v-col cols="8" class="d-flex align-center">
        <v-spacer />
        <v-switch
          v-show="switchIsEnabled(['protocol'])"
          v-model="soaPreferences.show_epochs"
          :label="$t('ProtocolFlowchart.show_epochs')"
          hide-details
          class="mr-4"
          color="primary"
          :readonly="soaContentLoadingStore.loading"
          :loading="soaContentLoadingStore.loading ? 'warning' : null"
          @update:model-value="updateSoaPreferences('show_epochs')"
        />
        <v-switch
          v-show="switchIsEnabled(['protocol'])"
          v-model="soaPreferences.show_milestones"
          :label="$t('ProtocolFlowchart.show_milestones')"
          hide-details
          class="mr-4"
          color="primary"
          :readonly="soaContentLoadingStore.loading"
          :loading="soaContentLoadingStore.loading ? 'warning' : null"
          @update:model-value="updateSoaPreferences('show_milestones')"
        />
        <v-menu rounded location="bottom">
          <template #activator="{ props }">
            <v-btn
              class="ml-2"
              size="small"
              variant="outlined"
              color="nnBaseBlue"
              v-bind="props"
              :title="$t('DataTableExportButton.export')"
              icon="mdi-download-outline"
              :loading="soaContentLoadingStore.loading"
            />
          </template>
          <v-list>
            <v-list-item link @click="downloadCSV">
              <v-list-item-title>CSV</v-list-item-title>
            </v-list-item>
            <v-list-item link @click="downloadEXCEL">
              <v-list-item-title>EXCEL</v-list-item-title>
            </v-list-item>
            <v-list-item link @click="downloadDocx">
              <v-list-item-title>DOCX</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
      </v-col>
    </v-row>
    <div id="protocolFlowchart" class="mt-4" v-html="protocolFlowchart" />
  </div>
</template>

<script>
import { computed } from 'vue'
import study from '@/api/study'
import soaDownloads from '@/utils/soaDownloads'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useSoaContentLoadingStore } from '@/stores/soa-content-loading'
import unitConstants from '@/constants/units'
import units from '@/api/units'
import { useAccessGuard } from '@/composables/accessGuard'

export default {
  props: {
    update: {
      type: Number,
      default: 0,
    },
    layout: {
      type: String,
      default: 'protocol',
    },
  },
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    const soaContentLoadingStore = useSoaContentLoadingStore()
    return {
      ...useAccessGuard(),
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
      selectedStudyVersion: computed(
        () => studiesGeneralStore.selectedStudyVersion
      ),
      soaPreferredTimeUnit: computed(
        () => studiesGeneralStore.soaPreferredTimeUnit
      ),
      soaPreferences: computed(() => studiesGeneralStore.soaPreferences),
      setSoaPreferences: studiesGeneralStore.setSoaPreferences,
      soaContentLoadingStore,
    }
  },
  data() {
    return {
      protocolFlowchart: '',
      loadingMessage: '',
      preferredTimeUnits: [],
    }
  },
  watch: {
    layout(newVal, oldVal) {
      if (newVal !== oldVal) this.updateFlowchart()
    },
    update(newVal, oldVal) {
      if (newVal !== oldVal) this.updateFlowchart()
    },
  },
  mounted() {
    this.updateFlowchart()
    units
      .getBySubset(unitConstants.TIME_UNIT_SUBSET_STUDY_PREFERRED_TIME_UNIT)
      .then((resp) => {
        this.preferredTimeUnits = resp.data.items
      })
  },
  methods: {
    switchIsEnabled(layouts = []) {
      return (
        !this.selectedStudyVersion &&
        this.checkPermission(this.$roles.STUDY_WRITE) &&
        (!layouts || layouts.includes(this.layout))
      )
    },
    updateSoaPreferences(key) {
      this.setSoaPreferences({ [key]: this.soaPreferences[key] }).then(() => {
        this.updateFlowchart()
      })
    },
    updateFlowchart() {
      this.loadingMessage = this.$t('ProtocolFlowchart.loading')
      this.soaContentLoadingStore.changeLoadingState()
      study
        .getStudyProtocolFlowchartHtml(this.selectedStudy.uid, {
          layout: this.layout,
        })
        .then((resp) => {
          this.protocolFlowchart = resp.data
        })
        .then(this.finally)
        .catch(this.finally)
    },
    async downloadDocx() {
      this.loadingMessage = this.$t('ProtocolFlowchart.downloading')
      this.soaContentLoadingStore.changeLoadingState()
      try {
        await soaDownloads.docxDownload(this.layout)
      } finally {
        this.finally()
      }
    },
    async downloadCSV() {
      this.soaContentLoadingStore.changeLoadingState()
      try {
        await soaDownloads.csvDownload(this.layout)
      } finally {
        this.finally()
      }
    },
    async downloadEXCEL() {
      this.soaContentLoadingStore.changeLoadingState()
      try {
        await soaDownloads.excelDownload(this.layout)
      } finally {
        this.finally()
      }
    },
    finally() {
      this.loadingMessage = ''
      this.soaContentLoadingStore.changeLoadingState()
    },
  },
}
</script>

<style lang="scss">
.layoutSelect {
  max-width: 200px;
}
#protocolFlowchart {
  table {
    width: 100%;
    border-collapse: collapse;
    table-layout: auto;
    resize: both;

    &,
    & th,
    & td {
      border: 1px solid #ebe8e5;
      padding: 1px 3px;
    }

    & thead {
      background-color: rgb(var(--v-theme-tableGray));

      & th {
        border-color: white;
      }

      & .header1:nth-child(n + 2) {
        vertical-align: top;
        text-orientation: mixed;
      }

      & th:first-child {
        text-align: left;
      }
    }

    & tbody {
      & th {
        text-align: left;
        font-weight: normal;
      }

      & tr td:nth-child(n + 2) {
        text-align: center;
        vertical-align: middle;
      }

      & .soaGroup {
        background-color: #b1d5f2;
        font-weight: bold;
      }

      & .soaGroup ~ td {
        background-color: #b1d5f2;
      }

      & .group {
        background-color: #d8eaf8;
        font-weight: bold;
      }

      & .group ~ td {
        background-color: #d8eaf8;
      }

      & .subGroup:first-child {
        font-weight: bold;
        padding-left: 1em;
      }

      & .activity:first-child {
        padding-left: 1em;
      }

      & .activityInstance:first-child {
        padding-left: 2em;
        font-style: italic;
      }
    }
  }

  dl.footnotes {
    margin: 1em;

    display: grid;
    grid-template-columns: 1em auto;

    dt {
      font-size: 70%;
      vertical-align: top;
    }
  }
}
</style>
