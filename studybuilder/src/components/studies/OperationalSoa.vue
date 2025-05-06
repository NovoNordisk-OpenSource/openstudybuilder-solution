<template>
  <div v-resize="onResize" class="pa-4 bg-white" style="overflow-x: auto">
    <div class="d-flex align-center mb-4">
      <v-switch
        v-model="expandAllRows"
        :label="$t('DetailedFlowchart.expand_all')"
        hide-details
        class="ml-2 flex-grow-0"
        color="primary"
        @update:model-value="toggleAllRowState"
      />
      <v-switch
        v-model="showFlowchartGroups"
        :label="$t('DetailedFlowchart.show_flowchart_groups')"
        hide-details
        class="ml-6 flex-grow-0"
        color="primary"
        :disabled="selectedStudyVersion !== null"
      />
      <v-spacer />
      <v-menu rounded location="bottom">
        <template #activator="{ props }">
          <v-btn
            size="small"
            color="nnGreen1"
            class="ml-2 text-white"
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
          <v-list-item link @click="downloadDOCX">
            <v-list-item-title>DOCX</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </div>
    <div
      ref="tableContainer"
      class="sticky-header"
      :style="`height: ${tableHeight}px`"
    >
      <table :aria-label="$t('DetailedFlowchart.table_caption')">
        <thead>
          <tr ref="firstHeader">
            <th width="2%" rowspan="4" scope="col" />
            <th width="25%" rowspan="4" scope="col">
              {{ $t('DetailedFlowchart.activities') }}
            </th>
            <th width="10%" scope="col">
              {{ $t('DetailedFlowchart.study_epoch') }}
            </th>
            <template v-if="soaContent">
              <th
                v-for="(cell, index) in soaEpochRow"
                :key="`epoch-${index}`"
                class="text-vertical"
                scope="col"
              >
                {{ cell.text }}
              </th>
            </template>
            <template v-else>
              <th colspan="2" scope="col" />
            </template>
          </tr>
          <tr ref="secondHeader">
            <th :style="`top: ${firstHeaderHeight}px`" scope="col">
              {{ $t('DetailedFlowchart.visit_short_name') }}
            </th>
            <template v-if="soaContent">
              <th
                v-for="(cell, index) in soaVisitRow"
                :key="`shortName-${index}`"
                :style="`top: ${firstHeaderHeight}px`"
                scope="col"
              >
                <div class="d-flex align-center">
                  {{ cell.text }}
                </div>
              </th>
            </template>
            <template v-else>
              <th
                colspan="2"
                :style="`top: ${firstHeaderHeight}px`"
                scope="col"
              />
            </template>
          </tr>
          <tr ref="thirdHeader">
            <template v-if="soaContent">
              <th
                v-for="(cell, index) in soaDayRow"
                :key="`week-${index}`"
                :style="`top: ${thirdHeaderRowTop}px`"
                scope="col"
              >
                {{ cell.text }}
              </th>
            </template>
            <template v-else>
              <th
                colspan="2"
                :style="`top: ${thirdHeaderRowTop}px`"
                scope="col"
              />
            </template>
          </tr>
          <tr>
            <th :style="`top: ${fourthHeaderRowTop}px`" scope="col">
              {{ $t('DetailedFlowchart.visit_window') }}
            </th>
            <template v-if="soaContent">
              <th
                v-for="(cell, index) in soaWindowRow"
                :key="`window-${index}`"
                :style="`top: ${fourthHeaderRowTop}px`"
                scope="col"
              >
                {{ cell.text }}
              </th>
            </template>
            <template v-else>
              <th
                colspan="2"
                :style="`top: ${fourthHeaderRowTop}px`"
                scope="col"
              />
            </template>
          </tr>
        </thead>
        <tbody>
          <template v-for="(row, index) in soaRows">
            <tr
              v-if="showSoaRow(index, row)"
              :key="`row-${index}`"
              :class="getSoaRowClasses(row)"
            >
              <td>
                <v-btn
                  v-if="getSoaRowType(row) !== 'activityInstance'"
                  :icon="getDisplayButtonIcon(`row-${index}`)"
                  variant="text"
                  class="expand-btn"
                  @click="toggleRowState(`row-${index}`)"
                />
              </td>
              <td :class="getSoaFirstCellClasses(row.cells[0])">
                <div v-if="row.cells[0].style !== 'activityInstance'">
                  {{ row.cells[0].text }}
                </div>
                <a
                  v-else
                  href="#"
                  class="font-weight-regular"
                  @click="redirectToActivityInstance(row.cells[0].refs[0].uid)"
                >
                  {{ row.cells[0].text }}
                </a>
              </td>
              <td />
              <td
                v-for="(subrow, subindex) in row.cells.slice(1)"
                :key="`row-${subindex}`"
              >
                {{ subrow.text }}
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import study from '@/api/study'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useSoaContentLoadingStore } from '@/stores/soa-content-loading'
import soaDownloads from '@/utils/soaDownloads'

export default {
  props: {
    update: {
      type: Number,
      default: 0,
    },
  },
  setup() {
    const accessGuard = useAccessGuard()
    const studiesGeneralStore = useStudiesGeneralStore()
    const soaContentLoadingStore = useSoaContentLoadingStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
      selectedStudyVersion: computed(
        () => studiesGeneralStore.selectedStudyVersion
      ),
      studyPreferredTimeUnit: computed(
        () => studiesGeneralStore.studyPreferredTimeUnit
      ),
      ...accessGuard,
      soaContentLoadingStore,
    }
  },
  data() {
    return {
      currentSelectionMatrix: {},
      rowsDisplayState: {},
      tableHeight: 500,
      soaContent: null,
      expandAllRows: false,
      firstHeaderHeight: 0,
      secondHeaderHeight: 0,
      thirdHeaderHeight: 0,
      showFlowchartGroups: false,
    }
  },
  computed: {
    soaEpochRow() {
      if (this.soaContent) {
        return this.soaContent.rows[0].cells.slice(1)
      }
      return []
    },
    soaVisitRow() {
      if (this.soaContent) {
        return this.soaContent.rows[1].cells.slice(1)
      }
      return []
    },
    soaDayRow() {
      if (this.soaContent) {
        return this.soaContent.rows[2].cells
      }
      return []
    },
    soaWindowRow() {
      if (this.soaContent) {
        return this.soaContent.rows[3].cells.slice(1)
      }
      return []
    },
    soaRows() {
      if (this.soaContent) {
        return this.soaContent.rows.slice(4)
      }
      return []
    },
    thirdHeaderRowTop() {
      return this.firstHeaderHeight + this.secondHeaderHeight
    },
    fourthHeaderRowTop() {
      return (
        this.firstHeaderHeight +
        this.secondHeaderHeight +
        this.thirdHeaderHeight
      )
    },
  },
  watch: {
    update(newVal, oldVal) {
      if (newVal !== oldVal) this.loadSoaContent()
    },
  },
  updated() {
    this.firstHeaderHeight = this.$refs.firstHeader.clientHeight
    this.secondHeaderHeight = this.$refs.secondHeader.clientHeight
    this.thirdHeaderHeight = this.$refs.thirdHeader.clientHeight
  },
  mounted() {
    this.loadSoaContent()
  },
  methods: {
    async redirectToActivityInstance(instanceUid) {
      const resp = await study.getStudyActivityInstance(
        this.selectedStudy.uid,
        instanceUid
      )
      this.$router.push({
        name: 'ActivityInstanceOverview',
        params: { id: resp.data.activity_instance.uid },
      })
    },
    toggleAllRowState(value) {
      for (const key in this.rowsDisplayState) {
        this.rowsDisplayState[key].value = value
      }
    },
    showSoaRow(index, row) {
      let key = `row-${index}`
      let result = true

      // prettier-ignore
      while (true) { // eslint-disable-line no-constant-condition
        if (
          this.rowsDisplayState[key] &&
          this.rowsDisplayState[key].parent !== undefined &&
          this.rowsDisplayState[key].parent !== null
        ) {
          const parentIndex = this.rowsDisplayState[key].parent
          key = `row-${parentIndex}`
          if (this.rowsDisplayState[key]) {
            const parentHasParent =
              this.rowsDisplayState[key].parent !== undefined &&
              this.rowsDisplayState[key].parent !== null
            if (
              (this.showFlowchartGroups ||
                (!this.showFlowchartGroups && parentHasParent)) &&
              !this.rowsDisplayState[key].value
            ) {
              result = false
              break
            }
          } else {
            console.log(`Warning: key ${key} not found in displayState!!`)
          }
          continue
        }
        break
      }
      if (row.cells && row.cells.length) {
        if (row.cells[0].style === 'soaGroup') {
          return this.showFlowchartGroups
        }
        if (row.cells[0].style === 'group') {
          return !this.showFlowchartGroups || result
        }
      }
      return result
    },
    onResize() {
      this.tableHeight =
        window.innerHeight -
        this.$refs.tableContainer.getBoundingClientRect().y -
        60
    },
    async loadSoaContent(keepDisplayState) {
      this.soaContentLoadingStore.changeLoadingState()
      const resp = await study.getStudyProtocolFlowchart(
        this.selectedStudy.uid,
        { layout: 'operational' }
      )
      let currentSoaGroup
      let currentGroup
      let currentSubGroup
      let currentActivity

      this.soaContent = resp.data
      if (!keepDisplayState) {
        this.rowsDisplayState = {}
        this.expandAllRows = false
      }
      for (const [index, row] of this.soaRows.entries()) {
        const key = `row-${index}`
        if (row.cells && row.cells.length) {
          if (row.cells[0].style === 'soaGroup') {
            this.rowsDisplayState[key] = { value: false }
            currentGroup = null
            currentSubGroup = null
            currentSoaGroup = index
          } else if (row.cells[0].style === 'group') {
            if (!keepDisplayState) {
              this.rowsDisplayState[key] = {
                value: false,
                parent: currentSoaGroup,
              }
            }
            currentSubGroup = null
            currentGroup = index
          } else if (row.cells[0].style === 'subGroup') {
            if (!keepDisplayState) {
              this.rowsDisplayState[key] = {
                value: false,
                parent: currentGroup,
              }
            }
            currentSubGroup = index
          } else if (row.cells[0].style === 'activity') {
            if (!keepDisplayState) {
              this.rowsDisplayState[key] = {
                value: false,
                parent: currentSubGroup,
              }
            }
            currentActivity = index
          } else if (row.cells[0].style === 'activityInstance') {
            if (!keepDisplayState) {
              this.rowsDisplayState[key] = {
                value: false,
                parent: currentActivity,
              }
            }
          }
        }
      }
      this.soaContentLoadingStore.changeLoadingState()
    },
    getSoaFirstCellClasses(cell) {
      if (cell.style === 'soaGroup' || cell.style === 'group') {
        return 'text-strong'
      }
      if (cell.style === 'subGroup') {
        return 'subgroup'
      }
      if (cell.style === 'activity') {
        return 'activity'
      }
      return 'activityInstance'
    },
    getSoaRowClasses(row) {
      if (row.cells && row.cells.length) {
        if (row.cells[0].style === 'soaGroup') {
          return 'flowchart text-uppercase'
        }
        if (row.cells[0].style === 'group') {
          return 'group'
        }
      }
      return ''
    },
    getSoaRowType(row) {
      return row.cells[0].style
    },
    getCurrentDisplayValue(rowKey) {
      const currentValue = this.rowsDisplayState[rowKey]
        ? this.rowsDisplayState[rowKey].value
        : undefined
      if (currentValue === undefined) {
        return false
      }
      return currentValue
    },
    getDisplayButtonIcon(rowKey) {
      return this.getCurrentDisplayValue(rowKey)
        ? 'mdi-chevron-down'
        : 'mdi-chevron-right'
    },
    toggleRowState(rowKey) {
      const currentValue = this.getCurrentDisplayValue(rowKey)
      this.rowsDisplayState[rowKey].value = !currentValue
    },
    async downloadCSV() {
      this.soaContentLoadingStore.changeLoadingState()
      try {
        await soaDownloads.csvDownload('operational')
      } finally {
        this.soaContentLoadingStore.changeLoadingState()
      }
    },
    async downloadEXCEL() {
      this.soaContentLoadingStore.changeLoadingState()
      try {
        await soaDownloads.excelDownload('operational')
      } finally {
        this.soaContentLoadingStore.changeLoadingState()
      }
    },
    async downloadDOCX() {
      this.soaContentLoadingStore.changeLoadingState()
      try {
        await soaDownloads.docxDownload('operational')
      } finally {
        this.soaContentLoadingStore.changeLoadingState()
      }
    },
  },
}
</script>

<style lang="scss" scoped>
table {
  width: 100%;
  text-align: left;
  border-spacing: 0px;
  border-collapse: collapse;
}
thead {
  background-color: rgb(var(--v-theme-tableGray));
  font-weight: 600;
}
tr {
  padding: 4px;
  &.section {
    background-color: rgb(var(--v-theme-tableGray));
    font-weight: 600;
  }
}
tbody tr {
  border-bottom: 1px solid rgb(var(--v-theme-greyBackground));
}
th {
  vertical-align: bottom;
  background-color: rgb(var(--v-theme-tableGray));
}
th,
td {
  padding: 6px;
  font-size: 14px !important;
}
.sticky-header {
  overflow-y: auto;

  thead th {
    position: sticky;
    top: 0;
    z-index: 3;
  }
}
.flowchart {
  background-color: rgb(var(--v-theme-dfltBackgroundLight1));
}
.group {
  background-color: rgb(var(--v-theme-dfltBackgroundLight2));
}
.subgroup {
  font-weight: 600;
  padding-left: 20px;
}
.activity {
  padding-left: 30px;
}
.activityInstance {
  padding-left: 40px;
  font-style: italic;
}
.text-vertical {
  text-orientation: mixed;
}
.text-strong {
  font-weight: 600;
}
.visitFootnote {
  margin-bottom: 8px;
}
.expand-btn {
  height: 30px;
  width: 10px;
}
</style>
