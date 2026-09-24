<template>
  <div
    v-show="!loadingSoaContent"
    v-resize="onResize"
    class="pa-4 bg-white"
    style="overflow-x: auto"
  >
    <v-row style="justify-content: center" class="my-2">
      <v-btn-toggle
        v-model="layout"
        mandatory
        density="compact"
        color="nnBaseBlue"
        divided
        variant="outlined"
        class="layoutSelector text-body-medium"
        :disabled="sortMode || soaRows.length === 0"
      >
        <v-btn value="detailed">
          {{ $t('DetailedFlowchart.detailed') }}
        </v-btn>
        <v-btn value="protocol">
          {{ $t('DetailedFlowchart.protocol') }}
        </v-btn>
        <v-btn
          v-if="
            featureFlagsStore.getFeatureFlag('soa_protocol_lab_table') === true
          "
          value="protocol_lab_table"
        >
          {{ $t('DetailedFlowchart.protocol_lab_table') }}
        </v-btn>
      </v-btn-toggle>
    </v-row>
    <ProtocolFlowchart
      v-if="
        ['operational', 'protocol', 'protocol_lab_table'].indexOf(layout) > -1
      "
      :layout="layout"
      :study-visits="studyVisits"
      :style="`max-height: ${tableHeight + 150}px;`"
    />
    <div v-else>
      <div class="d-flex align-center mb-4">
        <v-text-field
          v-model="search"
          :label="$t('_global.search')"
          clearable
          clear-icon="mdi-close"
          prepend-inner-icon="mdi-magnify"
          class="ml-2 mr-6 mt-5"
          style="max-width: 300px"
          :disabled="sortMode"
          @click:clear="search = ''"
        />
        <v-switch
          v-model="expandAllRows"
          :label="$t('DetailedFlowchart.expand_all')"
          hide-details
          class="flex-grow-0"
          :disabled="sortMode"
          @update:model-value="toggleAllRowState"
        />
        <v-spacer />

        <div
          v-if="
            featureFlagsStore.getFeatureFlag('complexity_score_calculation') ===
            true
          "
          style="width: 280px"
        >
          {{ $t('DetailedFlowchart.complexity_score') }}
          <b v-if="!complexityScoreLoading" class="pl-1">{{
            complexityScore
          }}</b>
          <v-progress-circular
            v-else
            color="primary"
            indeterminate
            size="24"
            class="ml-2"
          />
          <v-btn
            v-if="
              featureFlagsStore.getFeatureFlag('complexity_score_details') ===
              true
            "
            icon
            size="x-small"
            variant="text"
            class="ml-0 mt-n1"
            color="primary"
            @click="openComplexityDetails"
          >
            <v-icon size="small">mdi-information-outline</v-icon>
          </v-btn>
        </div>
        <template v-if="!props.readOnly">
          <v-btn
            v-show="multipleVisitsSelected()"
            class="ml-2"
            icon
            size="small"
            variant="outlined"
            color="nnBaseBlue"
            :disabled="
              footnoteMode ||
              !accessGuard.checkPermission($roles.STUDY_WRITE) ||
              studiesGeneralStore.selectedStudyVersion !== null ||
              sortMode
            "
            :loading="soaContentLoadingStore.loading"
            @click="groupSelectedVisits()"
          >
            <v-icon>mdi-arrow-expand-horizontal</v-icon>
            <v-tooltip activator="parent" location="top">
              {{ $t('GroupStudyVisits.title') }}
            </v-tooltip>
          </v-btn>
          <v-menu
            :disabled="
              footnoteMode ||
              !accessGuard.checkPermission($roles.STUDY_WRITE) ||
              studiesGeneralStore.selectedStudyVersion !== null ||
              sortMode
            "
            rounded
            location="bottom"
          >
            <template #activator="{ props }">
              <v-btn
                :disabled="
                  footnoteMode ||
                  !accessGuard.checkPermission($roles.STUDY_WRITE) ||
                  studiesGeneralStore.selectedStudyVersion !== null ||
                  sortMode
                "
                class="ml-2"
                icon
                size="small"
                variant="outlined"
                color="nnBaseBlue"
                v-bind="props"
                :loading="soaContentLoadingStore.loading"
              >
                <v-icon>mdi-folder-multiple-outline</v-icon>
                <v-tooltip activator="parent" location="top">
                  {{ $t('DetailedFlowchart.bulk_actions') }}
                </v-tooltip>
              </v-btn>
            </template>

            <v-list density="compact" rounded="xl">
              <v-list-item
                prepend-icon="mdi-pencil-outline"
                @click="openBatchEditForm"
              >
                <v-list-item-title>{{
                  $t('DetailedFlowchart.bulk_edit')
                }}</v-list-item-title>
              </v-list-item>
              <v-list-item
                prepend-icon="mdi-delete-outline"
                link
                @click="batchRemoveStudyActivities"
              >
                <v-list-item-title>{{
                  $t('DetailedFlowchart.bulk_remove')
                }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
          <v-menu rounded location="bottom" :disabled="sortMode">
            <template #activator="{ props }">
              <v-btn
                class="ml-2"
                icon
                size="small"
                variant="outlined"
                color="nnBaseBlue"
                v-bind="props"
                data-cy="table-export-button"
                :disabled="sortMode"
                :loading="soaContentLoadingStore.loading"
              >
                <v-icon>mdi-download-outline</v-icon>
                <v-tooltip activator="parent" location="top">
                  {{ $t('DataTableExportButton.export') }}
                </v-tooltip>
              </v-btn>
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
          <v-btn
            class="ml-2"
            icon
            size="small"
            variant="outlined"
            color="nnBaseBlue"
            :disabled="sortMode"
            @click="openHistory"
          >
            <v-icon>mdi-history</v-icon>
            <v-tooltip activator="parent" location="top">
              {{ $t('NNTableTooltips.history') }}
            </v-tooltip>
          </v-btn>
        </template>
      </div>
      <div
        ref="tableContainer"
        class="sticky-header"
        :style="`max-height: ${tableHeight}px; min-height: 500px; border-radius: 15px;`"
      >
        <table :aria-label="$t('DetailedFlowchart.table_caption')">
          <thead>
            <tr ref="firstHeader">
              <th
                ref="firstCol"
                scope="col"
                class="header zindex25 pl-6 pt-3"
                style="left: 0px; min-width: 120px"
              >
                {{ $t('DetailedFlowchart.study_epoch') }}
              </th>
              <th
                v-if="soaVisitRow.length === 0"
                :rowspan="numHeaderRows"
                scope="col"
                class="header zindex25"
              />
              <template v-if="soaContent">
                <th
                  v-for="(cell, index) in soaEpochRow"
                  :key="`epoch-${index}`"
                  class="header"
                  scope="col"
                  style="min-width: 110px"
                >
                  <div style="width: max-content" class="mt-3">
                    <v-row>
                      <v-badge
                        color="transparent"
                        text-color="nnWhite"
                        floating
                        :content="
                          cell.refs
                            ? scheduleMethods.getElementFootnotesLetters(
                                cell.refs[0].uid
                              )
                            : ''
                        "
                        class="mt-3 mr-1 ml-5 mb-5"
                      >
                        {{ cell.text }}
                      </v-badge>
                      <v-btn
                        v-if="
                          footnoteMode &&
                          cell.text !== '' &&
                          !checkIfElementHasFootnote(cell.refs[0].uid)
                        "
                        size="x-small"
                        icon="mdi-plus-circle-outline"
                        :title="$t('DetailedFlowchart.add_footnote')"
                        class="mr-1 mt-1"
                        color="nnWhite"
                        variant="text"
                        @click="
                          addElementForFootnote(
                            cell.refs[0].uid,
                            'StudyEpoch',
                            cell.text
                          )
                        "
                      />
                      <v-btn
                        v-else-if="
                          footnoteMode &&
                          cell.text !== '' &&
                          checkIfElementHasFootnote(cell.refs[0].uid)
                        "
                        size="x-small"
                        icon="mdi-minus-circle"
                        color="nnWhite"
                        class="mx-0 px-0"
                        variant="text"
                        :title="$t('DetailedFlowchart.remove_footnote')"
                        @click="removeElementForFootnote(cell.refs[0].uid)"
                      />
                    </v-row>
                  </div>
                </th>
              </template>
              <template v-else>
                <th colspan="2" scope="col" />
              </template>
            </tr>
            <tr v-if="soaMilestoneRow.length" ref="milestoneHeader">
              <th
                width="10%"
                scope="col"
                :style="`top: ${firstHeaderHeight}px;`"
                class="header zindex25 pl-6"
              >
                {{ $t('DetailedFlowchart.study_milestone') }}
              </th>
              <th
                v-for="(cell, index) in soaMilestoneRow"
                :key="`milestone-${index}`"
                class="header ml-2"
                scope="col"
                :style="`top: ${firstHeaderHeight}px`"
              >
                <div class="ml-2">
                  {{ cell.text }}
                </div>
              </th>
            </tr>
            <tr ref="secondHeader">
              <th
                :style="`top: ${firstHeaderHeight + milestoneHeaderHeight}px; align-content: center;`"
                scope="col"
                class="header zindex25 pl-6"
              >
                {{ $t('DetailedFlowchart.visit_short_name') }}
              </th>
              <template v-if="soaContent">
                <th
                  v-for="(cell, index) in soaVisitRow"
                  :key="`shortName-${index}`"
                  :style="`top: ${firstHeaderHeight + milestoneHeaderHeight}px;`"
                  scope="col"
                >
                  <div class="d-flex align-center mt-1">
                    <v-badge
                      color="transparent"
                      text-color="secondary"
                      floating
                      :content="
                        cell.refs.length
                          ? scheduleMethods.getElementFootnoteLettersForMultipleRefs(
                              cell.refs
                            )
                          : ''
                      "
                      class="visitFootnote ml-2"
                    >
                      {{ cell.text }}
                    </v-badge>
                    <v-btn
                      v-if="
                        footnoteMode &&
                        !checkIfElementHasFootnote(cell.refs[0].uid)
                      "
                      size="small"
                      icon="mdi-plus-circle-outline"
                      :title="$t('DetailedFlowchart.add_footnote')"
                      class="mb-1 mx-0 px-0"
                      variant="text"
                      @click="
                        addVisitForFootnote(cell.refs, 'StudyVisit', cell.text)
                      "
                    />
                    <v-btn
                      v-else-if="
                        footnoteMode &&
                        checkIfElementHasFootnote(cell.refs[0].uid)
                      "
                      size="small"
                      icon="mdi-minus-circle"
                      color="nnBaseBlue"
                      class="mb-1 mx-0 px-0"
                      variant="text"
                      :title="$t('DetailedFlowchart.remove_footnote')"
                      @click="removeElementForFootnote(cell.refs[0].uid)"
                    />
                    <v-checkbox
                      v-if="cell.refs.length === 1 && !footnoteMode"
                      v-model="selectedVisitIndexes"
                      :value="index"
                      hide-details
                      class="mt-n2 scale75"
                      multiple
                      :disabled="
                        footnoteMode ||
                        !accessGuard.checkPermission($roles.STUDY_WRITE) ||
                        studiesGeneralStore.selectedStudyVersion !== null
                      "
                    />
                    <v-btn
                      v-else-if="!footnoteMode"
                      icon="mdi-delete-outline"
                      color="error"
                      size="x-small"
                      class="mb-1"
                      :title="$t('GroupStudyVisits.delete_title')"
                      :disabled="
                        footnoteMode ||
                        !accessGuard.checkPermission($roles.STUDY_WRITE) ||
                        studiesGeneralStore.selectedStudyVersion !== null
                      "
                      variant="text"
                      @click="deleteVisitGroup(cell)"
                    />
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
                  :class="
                    cell.text.includes('Study') ? 'header zindex25 pl-6' : ''
                  "
                >
                  <div :class="cell.text.includes('Study') ? '' : 'ml-2'">
                    {{ cell.text }}
                  </div>
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
              <template v-if="soaContent">
                <th
                  v-for="(cell, index) in soaWindowRow"
                  :key="`window-${index}`"
                  :style="`top: ${fourthHeaderRowTop}px`"
                  scope="col"
                  :class="
                    cell.text.includes('Visit window')
                      ? 'header zindex25 pl-6'
                      : ''
                  "
                >
                  <div
                    :class="cell.text.includes('Visit window') ? '' : 'ml-2'"
                  >
                    {{ cell.text }}
                  </div>
                </th>
              </template>
              <template v-else>
                <th
                  colspan="2"
                  :style="`top: ${fourthHeaderRowTop}px`"
                  scope="col"
                ></th>
              </template>
            </tr>
          </thead>
          <EmptySoATbody
            v-if="soaRows.length === 0"
            :messages="emptyStateMessages"
            :visits-redirect="Boolean(soaVisitRow.length === 0)"
          />
          <ReorderingDetailedSoATbody
            v-if="sortMode"
            :soa-rows="soaRows"
            :soa-visit-row="soaVisitRow"
            :current-selection-matrix="currentSelectionMatrix"
            :selected-reorder-item="selectedReorderItem"
          />
          <tbody v-if="!sortMode">
            <template v-for="(row, index) in visibleRows">
              <tr
                v-if="row.cells"
                :id="`row-scroll-${row.cells[0].refs[0]?.uid}`"
                :key="`row-${row.cells[0].refs[0]?.uid}`"
                :class="scheduleMethods.getSoaRowClasses(row)"
                style="height: 35px"
              >
                <td class="sticky-column" style="min-width: 320px">
                  <div class="d-flex align-center justify-start">
                    <div class="row-fixed-width">
                      <v-btn
                        v-if="
                          !props.readOnly && !scheduleMethods.isActivityRow(row)
                        "
                        :icon="
                          getDisplayButtonIcon(
                            `row-${row.cells[0].refs[0]?.uid}`
                          )
                        "
                        variant="text"
                        size="x-small"
                        @click="
                          toggleRowState(`row-${row.cells[0].refs[0]?.uid}`)
                        "
                      />
                    </div>
                    <div class="row-fixed-width">
                      <ActionsMenu
                        v-if="row.order"
                        v-model="actionMenuStates[index]"
                        size="small"
                        :actions="actions"
                        :item="{ row: row, index: index }"
                        :disabled="
                          Boolean(studiesGeneralStore.selectedStudyVersion)
                        "
                        @update:model-value="highlightRow(row)"
                      />
                    </div>
                    <v-checkbox
                      v-if="
                        !props.readOnly && scheduleMethods.isActivityRow(row)
                      "
                      hide-details
                      :model-value="
                        studyActivitySelection.findIndex(
                          (cell) =>
                            cell.refs[0].uid === row.cells[0].refs[0].uid
                        ) !== -1
                      "
                      :disabled="
                        !accessGuard.checkPermission($roles.STUDY_WRITE) ||
                        studiesGeneralStore.selectedStudyVersion !== null
                      "
                      :style="footnoteMode ? 'visibility: hidden;' : ''"
                      class="flex-grow-0 ml-12 scale75"
                      @update:model-value="
                        (value) => toggleActivitySelection(row, value)
                      "
                    />
                    <v-checkbox
                      v-if="
                        !props.readOnly &&
                        scheduleMethods.getSoaRowType(row) === 'subGroup'
                      "
                      true-icon="mdi-checkbox-multiple-marked-outline"
                      false-icon="mdi-checkbox-multiple-blank-outline"
                      hide-details
                      :disabled="
                        !accessGuard.checkPermission($roles.STUDY_WRITE) ||
                        studiesGeneralStore.selectedStudyVersion !== null
                      "
                      :style="footnoteMode ? 'visibility: hidden;' : ''"
                      class="flex-grow-0 scale75 ml-4"
                      @update:model-value="
                        (value) => toggleSubgroupActivitiesSelection(row, value)
                      "
                    />

                    <div class="ml-4 row-label-wrapper">
                      <span class="row-label-activator">
                        <span class="row-label-text">
                          <template
                            v-for="(
                              segment, segmentIndex
                            ) in getSearchHighlightedSegments(
                              row.cells[0].text
                            )"
                            :key="`row-${row.cells[0].refs[0]?.uid}-segment-${segmentIndex}`"
                          >
                            <span
                              :class="{
                                'search-match-cell': segment.match,
                              }"
                            >
                              {{ segment.text }}
                            </span>
                          </template>
                        </span>
                        <v-tooltip
                          v-if="row.cells[0].text"
                          activator="parent"
                          location="top"
                        >
                          {{ row.cells[0].text }}
                        </v-tooltip>
                      </span>
                      <span
                        v-if="
                          scheduleMethods.getElementFootnotesLetters(
                            row.cells[0]?.refs[0]?.uid
                          )
                        "
                        class="badgeActivities"
                      >
                        {{
                          scheduleMethods.getElementFootnotesLetters(
                            row.cells[0]?.refs[0]?.uid
                          )
                        }}
                      </span>
                    </div>
                    <v-btn
                      v-if="
                        footnoteMode &&
                        row.cells[0].refs[0] &&
                        !checkIfElementHasFootnote(row.cells[0].refs[0].uid)
                      "
                      icon="mdi-plus-circle-outline"
                      :title="$t('DetailedFlowchart.add_footnote')"
                      class="mx-0 px-0"
                      size="x-small"
                      variant="text"
                      @click="
                        addElementForFootnote(
                          row.cells[0].refs[0].uid,
                          row.cells[0].refs[0].type,
                          row.cells[0].text
                        )
                      "
                    />
                    <v-btn
                      v-else-if="
                        footnoteMode &&
                        row.cells[0].refs[0] &&
                        checkIfElementHasFootnote(row.cells[0].refs[0].uid)
                      "
                      icon="mdi-minus-circle"
                      size="x-small"
                      class="mx-0 px-0"
                      color="nnBaseBlue"
                      variant="text"
                      :title="$t('DetailedFlowchart.remove_footnote')"
                      @click="
                        removeElementForFootnote(row.cells[0].refs[0].uid)
                      "
                    />
                    <v-spacer />
                    <v-btn
                      v-if="!props.readOnly"
                      icon
                      :disabled="
                        footnoteMode ||
                        !accessGuard.checkPermission($roles.STUDY_WRITE) ||
                        studiesGeneralStore.selectedStudyVersion !== null
                      "
                      variant="text"
                      style="height: auto"
                      :loading="row.loading"
                      @click="toggleLevelDisplay(row)"
                    >
                      <v-tooltip activator="parent" location="right">
                        {{
                          $t('DetailedFlowchart.toggle_soa_group_display', {
                            type: getProtocolSoaTypeLabel(row.cells[0].style),
                          })
                        }}
                      </v-tooltip>
                      <v-icon
                        v-if="getLevelDisplayState(row)"
                        size="x-small"
                        color="success"
                      >
                        mdi-eye-outline
                      </v-icon>
                      <v-icon v-else size="x-small">
                        mdi-eye-off-outline
                      </v-icon>
                      <template #loader>
                        <v-progress-linear
                          style="width: 75%"
                          rounded
                          indeterminate
                        />
                      </template>
                    </v-btn>
                  </div>
                </td>
                <td
                  v-if="!scheduleMethods.isActivityRow(row)"
                  :colspan="soaVisitRow.length"
                />
                <td
                  v-for="(visitCell, visitIndex) in soaVisitRow"
                  v-else
                  :key="`row-${index}-cell-${visitIndex}`"
                >
                  <div
                    v-if="leftIndex <= visitIndex <= rightIndex"
                    class="mb-n1 footnote-cell"
                  >
                    <input
                      v-model="
                        currentSelectionMatrix[row.cells[0].refs[0].uid][
                          visitCell.refs[0].uid
                        ].value
                      "
                      :disabled="
                        isCheckboxDisabled(
                          row.cells[0].refs[0].uid,
                          visitCell.refs[0].uid
                        ) ||
                        footnoteMode ||
                        !accessGuard.checkPermission($roles.STUDY_WRITE) ||
                        studiesGeneralStore.selectedStudyVersion !== null
                      "
                      class="mx-0 mt-2 ml-6 mb-3"
                      type="checkbox"
                      @update:model-value="
                        (value) =>
                          updateSchedule(
                            value,
                            row.cells[0].refs[0].uid,
                            visitCell
                          )
                      "
                    />
                    <div class="badgeSchedules">
                      {{
                        row?.cells[visitIndex - leftIndex + 1]?.footnotes?.join(
                          ', '
                        )
                      }}
                    </div>
                    <div class="actionButtons">
                      <v-btn
                        v-if="
                          !footnoteMode &&
                          !props.readOnly &&
                          row.cells[visitIndex - leftIndex + 1]?.refs &&
                          row.cells[visitIndex - leftIndex + 1]?.refs.length &&
                          Boolean(
                            scheduleMethods.getElementFootnotesLetters(
                              row.cells[visitIndex - leftIndex + 1]?.refs[0].uid
                            )
                          )
                        "
                        key="2"
                        class="mr-n2 mb-n2 scale50"
                        size="x-small"
                        variant="outlined"
                        color="nnBaseBlue"
                        icon="mdi-minus"
                        :title="$t('DetailedFlowchart.remove_footnote')"
                        @click="
                          openRemoveFootnoteForm(
                            row.cells[visitIndex - leftIndex + 1],
                            row.cells[0].refs[0].uid
                          )
                        "
                      />
                    </div>
                    <v-btn
                      v-if="
                        footnoteMode &&
                        currentSelectionMatrix[row.cells[0].refs[0].uid][
                          visitCell.refs[0].uid
                        ].uid &&
                        !checkIfElementHasFootnote(
                          currentSelectionMatrix[row.cells[0].refs[0].uid][
                            visitCell.refs[0].uid
                          ].uid
                        )
                      "
                      size="x-small"
                      icon="mdi-plus-circle-outline"
                      :title="$t('DetailedFlowchart.add_footnote')"
                      class="actionButtons mx-0 px-0 ml-n3 mt-2 mb-4 mr-n4"
                      variant="text"
                      @click="
                        addElementForFootnote(
                          currentSelectionMatrix[row.cells[0].refs[0].uid][
                            visitCell.refs[0].uid
                          ].uid,
                          'StudyActivitySchedule',
                          undefined,
                          row?.cells[visitIndex - leftIndex + 1]
                        )
                      "
                    />
                    <v-btn
                      v-else-if="
                        footnoteMode &&
                        currentSelectionMatrix[row.cells[0].refs[0].uid][
                          visitCell.refs[0].uid
                        ].uid &&
                        checkIfElementHasFootnote(
                          currentSelectionMatrix[row.cells[0].refs[0].uid][
                            visitCell.refs[0].uid
                          ].uid
                        )
                      "
                      size="x-small"
                      icon="mdi-minus-circle"
                      class="mx-0 px-0 ml-n3 mt-2 mb-4 mr-n4"
                      color="nnBaseBlue"
                      variant="text"
                      :title="$t('DetailedFlowchart.remove_footnote')"
                      @click="
                        removeElementForFootnote(
                          currentSelectionMatrix[row.cells[0].refs[0].uid][
                            visitCell.refs[0].uid
                          ].uid,
                          row?.cells[visitIndex - leftIndex + 1]
                        )
                      "
                    />
                  </div>
                </td>
              </tr>
              <tr v-else :key="index" style="height: 35px">
                -
              </tr>
            </template>
          </tbody>
        </table>
      </div>
      <div class="mt-8 ml-n4 mr-n4">
        <StudyFootnoteTable
          ref="footnoteTable"
          @update="loadSoaContent()"
          @enable-footnote-mode="enableFootnoteMode"
          @remove-element-from-footnote="removeElementForFootnote"
        />
      </div>
    </div>
    <v-card v-if="sortMode" id="bottomCard" elevation="1" class="bottomCard">
      <v-row>
        <v-col cols="8">
          <v-card
            color="nnLightBlue200"
            class="ml-4"
            style="width: fit-content"
          >
            <v-card-text>
              <v-icon class="pb-1 mr-2">mdi-information-outline</v-icon>
              <div>
                {{ $t('DetailedFlowchart.reordering_help_msg') }}
              </div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col style="align-content: center; text-align-last: end">
          <v-btn
            color="nnBaseBlue"
            variant="outlined"
            size="large"
            rounded
            class="mr-4"
            :text="$t('DetailedFlowchart.finish_reordering_btn')"
            @click="finishReordering"
          />
        </v-col>
      </v-row>
    </v-card>
    <v-card
      v-if="footnoteMode"
      id="bottomCard"
      elevation="1"
      class="bottomCard"
    >
      <v-row>
        <v-col cols="8">
          <v-card
            color="nnLightBlue200"
            class="ml-4"
            style="width: fit-content"
          >
            <v-card-text>
              <v-icon class="pb-1 mr-2">mdi-information-outline</v-icon>
              <div
                v-if="activeFootnote"
                v-html="
                  sanitizeHTML(
                    $t('StudyFootnoteEditForm.select_footnote_items', {
                      footnote: escapeHTML(
                        activeFootnote.template
                          ? activeFootnote.template.name_plain
                          : activeFootnote.footnote.name_plain
                      ),
                    })
                  )
                "
              />
              <div v-else>
                {{
                  $t('StudyFootnoteEditForm.select_to_create_footnote_items')
                }}
              </div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="4" style="align-content: center; text-align-last: end">
          <v-btn
            color="nnBaseBlue"
            variant="outlined"
            size="large"
            rounded
            :text="$t('_global.cancel')"
            @click="disableFootnoteMode"
          />
          <v-btn
            color="nnBaseBlue"
            class="ml-2 mr-4"
            size="large"
            rounded
            :loading="footnoteUpdateLoading"
            :text="
              activeFootnote
                ? $t('StudyFootnoteEditForm.save_linking')
                : $t('_global.continue')
            "
            @click="saveElementsForFootnote"
          />
        </v-col>
      </v-row>
    </v-card>
    <v-dialog v-model="showActivityEditForm" max-width="600px">
      <StudyActivityEditForm
        :study-activity="selectedStudyActivity"
        @close="closeEditForm"
        @updated="loadSoaContent(true)"
      />
    </v-dialog>
    <v-dialog v-model="showDraftedActivityEditForm" max-width="600px">
      <StudyDraftedActivityEditForm
        :study-activity="selectedStudyActivity"
        @close="closeEditForm"
        @updated="loadSoaContent(true)"
      />
    </v-dialog>
    <RemoveFootnoteForm
      :open="showRemoveFootnoteForm"
      :item-uid="removeItemUid"
      @close="closeRemoveFootnoteForm"
    />
    <StudyActivityScheduleBatchEditForm
      v-if="showBatchEditForm"
      :open="showBatchEditForm"
      :selection="formattedStudyActivitySelection"
      :current-selection-matrix="currentSelectionMatrix"
      :study-visits="studyVisits"
      @updated="() => loadSoaContent(true)"
      @close="showBatchEditForm = false"
      @remove="unselectItem"
    />
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
    <v-dialog
      v-model="showComplexityDetails"
      max-width="900px"
      max-height="90vh"
      scrollable
    >
      <StudyComplexityScoreDetails
        v-if="showComplexityDetails"
        :study-uid="studiesGeneralStore.selectedStudy?.uid"
        :show-close="true"
        @close="showComplexityDetails = false"
      />
    </v-dialog>
    <CollapsibleVisitDisplaySelectForm
      :open="showCollapsibleGroupForm"
      :visits="selectedVisits"
      :are-consecutive-visits-selected="areConsecutiveVisitsSelected"
      @close="closeCollapsibleVisitGroupForm"
      @created="collapsibleVisitGroupCreated"
    />
    <v-dialog
      v-model="showFootnoteForm"
      persistent
      fullscreen
      content-class="fullscreen-dialog"
    >
      <StudyFootnoteForm
        :current-study-footnotes="footnotesStore.studyFootnotes"
        :selected-elements="elementsForFootnote"
        class="fullscreen-dialog"
        @close="closeFootnoteForm"
        @added="onFootnoteAdded()"
      />
    </v-dialog>
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
        :title="historyTitle"
        change-field="action"
        @close="closeHistory"
        @refresh="(options) => getHistoryData(options)"
      />
    </v-dialog>
    <v-dialog
      v-model="showActivityForm"
      persistent
      fullscreen
      content-class="fullscreen-dialog"
    >
      <StudyActivityForm
        :exchange-mode="activityExchangeMode"
        :exchange-activity-uid="selectedStudyActivity"
        :order="flowchartActivityOrder"
        @close="closeActivityForm"
        @added="onActivityExchanged"
      />
    </v-dialog>
  </div>
  <v-skeleton-loader
    v-if="loadingSoaContent"
    class="mt-6 mx-auto"
    max-width="800px"
    type="table-heading, table-thead, table-tbody"
  />
</template>

<script setup>
import {
  nextTick,
  computed,
  inject,
  ref,
  watch,
  onUpdated,
  onMounted,
  onBeforeUnmount,
} from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import CollapsibleVisitDisplaySelectForm from '../CollapsibleVisitDisplaySelectForm.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import study from '@/api/study'
import StudyActivityScheduleBatchEditForm from '../StudyActivityScheduleBatchEditForm.vue'
import StudyFootnoteTable from '../StudyFootnoteTable.vue'
import studyEpochs from '@/api/studyEpochs'
import StudyFootnoteForm from '@/components/studies/StudyFootnoteForm.vue'
import _isEmpty from 'lodash/isEmpty'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useFootnotesStore } from '@/stores/studies-footnotes'
import { useSoaContentLoadingStore } from '@/stores/soa-content-loading'
import { useSoaExpandStateStore } from '@/stores/soa-expand-state'
import soaDownloads from '@/utils/soaDownloads'
import ProtocolFlowchart from '../ProtocolFlowchart.vue'
import RemoveFootnoteForm from '../RemoveFootnoteForm.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import StudyActivityEditForm from '../StudyActivityEditForm.vue'
import StudyDraftedActivityEditForm from '../StudyDraftedActivityEditForm.vue'
import StudyActivityForm from '../StudyActivityForm.vue'
import libraries from '@/constants/libraries.js'
import ReorderingDetailedSoATbody from './ReorderingDetailedSoATbody.vue'
import scheduleMethods from '@/utils/scheduleMethods'
import EmptySoATbody from './EmptySoATbody.vue'
import StudyComplexityScoreDetails from '@/components/studies/StudyComplexityScoreDetails.vue'
import { escapeHTML, sanitizeHTML } from '@/utils/sanitize'
import { useFeatureFlagsStore } from '@/stores/feature-flags'
import dataFormating from '@/utils/dataFormating'

const featureFlagsStore = useFeatureFlagsStore()
const { t } = useI18n()
const notificationHub = inject('notificationHub')
const roles = inject('roles')
const studiesGeneralStore = useStudiesGeneralStore()
const footnotesStore = useFootnotesStore()
const soaContentLoadingStore = useSoaContentLoadingStore()
const soaExpandStateStore = useSoaExpandStateStore()
const accessGuard = useAccessGuard()
const router = useRouter()
const route = useRoute()

const props = defineProps({
  readOnly: {
    type: Boolean,
    default: false,
  },
  update: {
    type: Number,
    default: 0,
  },
})

const firstHeader = ref()
const secondHeader = ref()
const thirdHeader = ref()
const milestoneHeader = ref()
const firstCol = ref()
const secondCol = ref()
const footnoteTable = ref()
const confirm = ref()
const tableContainer = ref()
const complexityScore = ref(0)
const complexityScoreLoading = ref(false)
const showComplexityDetails = ref(false)

const actionMenuStates = ref({})
const currentSelectionMatrix = ref({})
const expandAllRows = ref(false)
const rowsDisplayState = ref({})
const firstHeaderHeight = ref(0)
const secondHeaderHeight = ref(0)
const thirdHeaderHeight = ref(0)
const firstColWidth = ref(0)
const secondColWidth = ref(0)
const milestoneHeaderHeight = ref(0)
const selectedVisitIndexes = ref([])
const showBatchEditForm = ref(false)
const showCollapsibleGroupForm = ref(false)
const showFootnoteForm = ref(false)
const studyActivitySelection = ref([])
const tableHeight = ref(700)
const activeFootnote = ref(null)
const footnoteMode = ref(false)
const elementsForFootnote = ref({
  referenced_items: [],
})
const loadingSoaContent = ref(false)
const showHistory = ref(false)
const footnoteUpdateLoading = ref(false)
const historyHeaders = [
  {
    title: t('DetailedFlowchart.history_object_type'),
    key: 'object_type',
  },
  { title: t('_global.description'), key: 'description' },
  { title: t('_global.modified_by'), key: 'author_username' },
]
const historyItems = ref([])
const historyItemsTotal = ref(0)
const soaContent = ref(null)
const layout = ref('detailed')
const soaLayoutStorageKey = computed(
  () => `soa-layout-${studiesGeneralStore.selectedStudy.uid}`
)
const showRemoveFootnoteForm = ref(false)
const removeItemUid = ref('')
const actions = [
  {
    label: t('DetailedFlowchart.edit_activity'),
    icon: 'mdi-pencil-outline',
    condition: (item) =>
      scheduleMethods.isActivityRow(item.row) &&
      !studiesGeneralStore.selectedStudyVersion,
    click: editStudyActivity,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('DetailedFlowchart.bulk_edit'),
    icon: 'mdi-pencil-outline',
    condition: (item) =>
      scheduleMethods.isActivityRow(item.row) &&
      studyActivitySelection.value.length > 1 &&
      !studiesGeneralStore.selectedStudyVersion,
    click: openBatchEditForm,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('DetailedFlowchart.add_activity'),
    icon: 'mdi-plus-circle-outline',
    condition: (item) =>
      scheduleMethods.isActivityRow(item.row) &&
      !studiesGeneralStore.selectedStudyVersion,
    click: addStudyActivity,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('DetailedFlowchart.exchange_activity'),
    icon: 'mdi-autorenew',
    condition: (item) =>
      scheduleMethods.isActivityRow(item.row) &&
      !studiesGeneralStore.selectedStudyVersion,
    click: exchangeStudyActivity,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('DetailedFlowchart.reorder'),
    icon: 'mdi-sort',
    condition: (item) =>
      !studiesGeneralStore.selectedStudyVersion &&
      item.row.order &&
      !search.value,
    click: initiateReorder,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('DetailedFlowchart.remove_activity'),
    icon: 'mdi-minus-circle-outline',
    condition: (item) =>
      scheduleMethods.isActivityRow(item.row) &&
      !studiesGeneralStore.selectedStudyVersion,
    click: removeActivity,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('DetailedFlowchart.bulk_remove'),
    icon: 'mdi-minus-circle-outline',
    condition: (item) =>
      scheduleMethods.isActivityRow(item.row) &&
      studyActivitySelection.value.length > 1 &&
      !studiesGeneralStore.selectedStudyVersion,
    click: batchRemoveStudyActivities,
    accessRole: roles.STUDY_WRITE,
  },
]
const showActivityEditForm = ref(false)
const showDraftedActivityEditForm = ref(false)
const selectedStudyActivity = ref(null)
const activityExchangeMode = ref(false)
const showActivityForm = ref(false)
const flowchartActivityOrder = ref(null)
const sortMode = ref(false)
const scrollItemId = ref('')
const selectedReorderItem = ref({})
const search = ref('')
const studyVisits = ref([])

const soaRows = computed(() => {
  // Hierarchical search handler for SoA table rows.
  // Rules:
  // 1) SoA group match => whole SoA subtree.
  // 2) Group match => whole group subtree + SoA parent.
  // 3) Subgroup/activity match => matching subgroup subtree + parents.
  const searchTerm = String(search.value ?? '')
    .trim()
    .toLowerCase()
  if (searchTerm.length >= 3) {
    // We search only data rows (header rows are excluded).
    const itemsToSearch =
      soaContent.value?.rows.slice(soaContent.value.num_header_rows) || []
    const result = []
    const getRowStyle = (row) => row?.cells?.[0]?.style
    const rowMatchesSearch = (row) => {
      const rowText = row?.cells?.[0]?.text
      return (
        typeof rowText === 'string' &&
        rowText.toLowerCase().includes(searchTerm)
      )
    }

    let index = 0
    // Walk top-level blocks from one SoA group to the next.
    while (index < itemsToSearch.length) {
      const soaGroupRow = itemsToSearch[index]
      const soaGroupStyle = getRowStyle(soaGroupRow)

      // Fallback for unexpected data shape: still allow search to return matching rows.
      if (soaGroupStyle !== 'soaGroup') {
        if (rowMatchesSearch(soaGroupRow)) {
          result.push(soaGroupRow)
        }
        index += 1
        continue
      }

      const soaGroupStartIndex = index
      index += 1

      // If SoA group itself matches, include full branch until next SoA group.
      if (rowMatchesSearch(soaGroupRow)) {
        while (
          index < itemsToSearch.length &&
          getRowStyle(itemsToSearch[index]) !== 'soaGroup'
        ) {
          index += 1
        }
        result.push(...itemsToSearch.slice(soaGroupStartIndex, index))
        continue
      }

      const soaChildrenToInclude = []

      // Evaluate all rows that belong to this SoA group.
      while (
        index < itemsToSearch.length &&
        getRowStyle(itemsToSearch[index]) !== 'soaGroup'
      ) {
        const currentRow = itemsToSearch[index]

        // Fallback inside SoA group for unexpected non-group rows.
        if (getRowStyle(currentRow) !== 'group') {
          if (rowMatchesSearch(currentRow)) {
            soaChildrenToInclude.push(currentRow)
          }
          index += 1
          continue
        }

        const groupStart = index
        index += 1
        while (index < itemsToSearch.length) {
          const currentStyle = getRowStyle(itemsToSearch[index])
          if (currentStyle === 'soaGroup' || currentStyle === 'group') {
            break
          }
          index += 1
        }

        const groupRows = itemsToSearch.slice(groupStart, index)
        const groupRow = groupRows[0]

        // Group match => include full group subtree (all its subgroups/activities).
        if (rowMatchesSearch(groupRow)) {
          soaChildrenToInclude.push(...groupRows)
          continue
        }

        // No group match: keep only matching subgroup branches (with full children)
        // and matching direct children that are not under a subgroup.
        const subgroupOrChildRowsToInclude = []
        let localIndex = 1

        // Scan inside one group, subgroup-by-subgroup.
        while (localIndex < groupRows.length) {
          const row = groupRows[localIndex]
          if (getRowStyle(row) === 'subGroup') {
            const subGroupStart = localIndex
            localIndex += 1
            // Collect rows until next subgroup; this is one subgroup subtree.
            while (
              localIndex < groupRows.length &&
              getRowStyle(groupRows[localIndex]) !== 'subGroup'
            ) {
              localIndex += 1
            }
            const subGroupRows = groupRows.slice(subGroupStart, localIndex)
            // If subgroup or any child matches, include entire subgroup subtree.
            if (subGroupRows.some((subRow) => rowMatchesSearch(subRow))) {
              subgroupOrChildRowsToInclude.push(...subGroupRows)
            }
            continue
          }

          if (rowMatchesSearch(row)) {
            subgroupOrChildRowsToInclude.push(row)
          }
          localIndex += 1
        }

        if (subgroupOrChildRowsToInclude.length) {
          soaChildrenToInclude.push(groupRow, ...subgroupOrChildRowsToInclude)
        }
      }

      // Add SoA parent only when something inside it matched.
      if (soaChildrenToInclude.length) {
        result.push(soaGroupRow, ...soaChildrenToInclude)
      }
    }

    return result
  }
  const result = []
  soaContent.value?.rows
    .slice(soaContent.value.num_header_rows)
    .forEach((row) => {
      row.class = scheduleMethods.getSoaRowClasses(row)
      result.push(row)
    })
  return result
})

const scrollTop = ref(0)
const scrollLeft = ref(0)
const rowHeight = 35
const tableWidth = ref(0)
const overscan = 10

const visibleRows = computed(() => {
  const rowsToDisplay = soaRows.value
    .filter((row) => showSoaRow(row.cells?.[0]?.refs?.[0]?.uid, row))
    .map((row) => {
      const cells = row.cells || []
      const first = cells[0]
      const rest = cells.slice(
        Math.max(1, leftIndex.value + 1),
        rightIndex.value
      )
      return { ...row, cells: first ? [first, ...rest] : rest }
    })
  if (rowsToDisplay.length <= 50) {
    return rowsToDisplay
  }
  const emptyObjects = Array.from({ length: rowsToDisplay.length }, () => ({}))

  const result = [
    ...emptyObjects.slice(0, startIndex.value),
    ...rowsToDisplay.slice(startIndex.value, endIndex.value + 1),
    ...emptyObjects.slice(endIndex.value + 1),
  ]
  return result
})

const startIndex = computed(() => {
  return Math.max(0, Math.floor(scrollTop.value / rowHeight) - overscan)
})

const endIndex = computed(() => {
  return Math.min(
    soaRows.value.length,
    Math.ceil((scrollTop.value + tableHeight.value) / rowHeight) + overscan
  )
})

const leftIndex = computed(() => {
  return Math.max(0, Math.floor(scrollLeft.value / 110))
})

const rightIndex = computed(() => {
  return Math.min(
    soaRows.value.length,
    Math.ceil((scrollLeft.value + tableWidth.value) / 110)
  )
})

let rafId = null
function onScroll(e) {
  const st = e.target.scrollTop
  const sl = e.target.scrollLeft
  if (rafId) cancelAnimationFrame(rafId)
  rafId = requestAnimationFrame(() => {
    nextTick(() => {
      scrollTop.value = Math.ceil(st)
      scrollLeft.value = Math.ceil(sl)
    })
  })
}

const numHeaderRows = computed(() => {
  return soaContent.value?.num_header_rows || 4
})
const soaEpochRow = computed(() => {
  return soaContent.value?.rows[0].cells.slice(1) || []
})
const soaMilestoneRow = computed(() => {
  if (soaContent.value && soaContent.value.num_header_rows > 4) {
    return soaContent.value.rows[1].cells.slice(1)
  }
  return []
})
const soaVisitRow = computed(() => {
  return (
    soaContent.value?.rows[soaContent.value.num_header_rows - 3].cells.slice(
      1
    ) || []
  )
})
const soaDayRow = computed(() => {
  return (
    soaContent.value?.rows[soaContent.value.num_header_rows - 2].cells || []
  )
})
const soaWindowRow = computed(() => {
  return (
    soaContent.value?.rows[soaContent.value.num_header_rows - 1].cells || []
  )
})
const thirdHeaderRowTop = computed(() => {
  return (
    firstHeaderHeight.value +
    secondHeaderHeight.value +
    milestoneHeaderHeight.value
  )
})
const fourthHeaderRowTop = computed(() => {
  return (
    firstHeaderHeight.value +
    secondHeaderHeight.value +
    milestoneHeaderHeight.value +
    thirdHeaderHeight.value
  )
})
const formattedStudyActivitySelection = computed(() => {
  return studyActivitySelection.value.map((cell) => {
    return {
      study_activity_uid: cell.refs[0].uid,
      activity: { name: cell.text },
    }
  })
})
const historyTitle = computed(() => {
  return t('DetailedFlowchart.history_title', {
    study: studiesGeneralStore.selectedStudy.uid,
  })
})
const selectedVisits = computed(() => {
  return selectedVisitIndexes.value.map((cell) => soaVisitRow.value[cell])
})
const emptyStateMessages = computed(() => {
  const type =
    soaRows.value.length === 0 && soaVisitRow.value.length === 0 ? 1 : 2
  return {
    title: t(`DetailedFlowchart.empty_soa_title_${type}`),
    text: t(`DetailedFlowchart.empty_soa_text_${type}`),
  }
})

watch(
  () => props.update,
  () => {
    loadSoaContent()
  }
)
watch(layout, (value) => {
  localStorage.setItem(soaLayoutStorageKey.value, value)
})
watch(
  () => '$route.params.footnote',
  (value) => {
    if (value && !_isEmpty(value)) {
      enableFootnoteMode(value)
    }
  }
)
watch(
  () => tableContainer.value,
  (value) => {
    if (!value) {
      return
    }
    scrollTop.value = value.scrollTop || 0
    if (tableContainer.value?.getBoundingClientRect().width > 0) {
      tableWidth.value = tableContainer.value?.getBoundingClientRect().width
    }
    value.addEventListener('scroll', onScroll, { passive: true })
  }
)

onMounted(() => {
  restoreLayout()
  loadSoaContent()
  getStudyVisits()
})

function restoreLayout() {
  const savedLayout = localStorage.getItem(soaLayoutStorageKey.value)
  if (!savedLayout) {
    return
  }
  const allowedLayouts = ['detailed', 'protocol', 'protocol_lab_table']
  if (allowedLayouts.includes(savedLayout)) {
    layout.value = savedLayout
  }
}

onUpdated(() => {
  observeWidth()
  if (!firstHeader.value) {
    return
  }
  firstHeaderHeight.value = firstHeader.value.clientHeight
  if (secondHeader.value) {
    secondHeaderHeight.value = secondHeader.value.clientHeight
  }
  if (thirdHeader.value) {
    thirdHeaderHeight.value = thirdHeader.value.clientHeight
  }
  if (milestoneHeader.value) {
    milestoneHeaderHeight.value = milestoneHeader.value.clientHeight
  }
  if (firstCol.value) {
    firstColWidth.value = firstCol.value.clientWidth
  }
  if (secondCol.value) {
    secondColWidth.value = secondCol.value.clientWidth
  }
})

function onFootnoteAdded() {
  footnoteTable.value.filterTable()
  loadSoaContent(true)
}

function initiateReorder(item) {
  const selectedUid = item.row.cells[0].refs[0]?.uid
  scrollItemId.value = `row-scroll-${selectedUid}`
  selectedReorderItem.value = item.row.cells[0]
  selectedReorderItem.value.order = item.row.order

  const fullRowIndex = soaRows.value.findIndex(
    (row) => row?.cells?.[0]?.refs?.[0]?.uid === selectedUid
  )
  selectedReorderItem.value.tableIndex =
    fullRowIndex !== -1 ? fullRowIndex : item.index
  sortMode.value = true
}

function finishReordering() {
  sortMode.value = false
  loadSoaContent(true)
}

let resizeObserver = null

function observeWidth() {
  if (resizeObserver) {
    return
  }
  resizeObserver = new ResizeObserver(function (el) {
    if (
      el[0].target.offsetWidth &&
      document.getElementById('bottomCard') &&
      document.getElementById('bottomCard').style
    ) {
      document.getElementById('bottomCard').style.left =
        el[0].target.offsetWidth + 'px'
    }
  })
  const sideBar = document.getElementById('sideBar')
  if (sideBar) {
    resizeObserver.observe(sideBar)
  }
}

onBeforeUnmount(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (tableContainer.value) {
    tableContainer.value.removeEventListener('scroll', onScroll)
  }
  soaExpandStateStore.save(
    studiesGeneralStore.selectedStudy.uid,
    snapshotExpandState()
  )
})

function snapshotExpandState() {
  const rowsDisplayStateSnapshot = {}
  for (const key in rowsDisplayState.value) {
    rowsDisplayStateSnapshot[key] = rowsDisplayState.value[key].value
  }
  return {
    rowsDisplayState: rowsDisplayStateSnapshot,
    expandAllRows: expandAllRows.value,
  }
}

function getStudyVisits() {
  const params = {
    page_size: 0,
    lite: true,
  }
  studyEpochs
    .getStudyVisits(studiesGeneralStore.selectedStudy.uid, params)
    .then((resp) => {
      studyVisits.value = resp.data.items
    })
}

async function removeActivity(item) {
  localStorage.setItem('refresh-activities', true)
  highlightRow(item.row)
  const activity = item.row.cells[0].refs[0]
  const options = { type: 'warning' }
  if (
    !(await confirm.value.open(
      t('DetailedFlowchart.remove_activity_msg'),
      options
    ))
  ) {
    highlightRow(item.row)
    return
  }
  loadingSoaContent.value = true
  study
    .deleteStudyActivity(studiesGeneralStore.selectedStudy.uid, activity.uid)
    .then(() => {
      notificationHub.add({
        type: 'success',
        msg: t('DetailedFlowchart.remove_activity_success'),
      })
      loadSoaContent(true)
    })
}

function addStudyActivity(item) {
  localStorage.setItem('refresh-activities', true)
  item = item.row.cells[0].refs[0]
  scrollItemId.value = `row-scroll-${item?.uid}`
  study
    .getStudyActivity(studiesGeneralStore.selectedStudy.uid, item.uid)
    .then((resp) => {
      flowchartActivityOrder.value = resp.data.order
      showActivityForm.value = true
    })
}

function exchangeStudyActivity(item) {
  localStorage.setItem('refresh-activities', true)
  item = item.row.cells[0].refs[0]
  selectedStudyActivity.value = item.uid
  activityExchangeMode.value = true
  showActivityForm.value = true
}

function closeActivityForm() {
  notificationHub.clearErrors()
  selectedStudyActivity.value = null
  activityExchangeMode.value = false
  flowchartActivityOrder.value = null
  showActivityForm.value = false
  loadSoaContent(true)
}

function onActivityExchanged() {
  showActivityForm.value = false
  activityExchangeMode.value = false
  loadSoaContent(true)
}

function editStudyActivity(item) {
  localStorage.setItem('refresh-activities', true)
  highlightRow(item.row)
  try {
    item = item.row.cells[0].refs[0]
    scrollItemId.value = `row-scroll-${item?.uid}`
  } catch (error) {
    console.error(error)
  }
  study
    .getStudyActivity(studiesGeneralStore.selectedStudy.uid, item.uid)
    .then((resp) => {
      selectedStudyActivity.value = resp.data
      if (
        resp.data.activity.library_name === libraries.LIBRARY_REQUESTED &&
        !resp.data.activity.is_request_final
      ) {
        showDraftedActivityEditForm.value = true
      } else {
        showActivityEditForm.value = true
      }
    })
}

function closeEditForm() {
  notificationHub.clearErrors()
  showActivityEditForm.value = false
  showDraftedActivityEditForm.value = false
  selectedStudyActivity.value = null
  loadSoaContent(true)
}

function openRemoveFootnoteForm(ele, rowUid) {
  scrollItemId.value = `row-scroll-${rowUid}`
  removeItemUid.value = ele.refs[0].uid
  showRemoveFootnoteForm.value = true
}

function closeRemoveFootnoteForm() {
  notificationHub.clearErrors()
  removeItemUid.value = null
  showRemoveFootnoteForm.value = false
  loadSoaContent(true)
}

function showSoaRow(index, row) {
  try {
    const searchTerm = String(search.value ?? '').trim()
    if (searchTerm.length >= 3) {
      return true
    }

    let key = `row-${index}`
    let result = true

    // prettier-ignore
    while (true) {  
      if (
        rowsDisplayState.value[key] &&
        rowsDisplayState.value[key].parent !== undefined &&
        rowsDisplayState.value[key].parent !== null
      ) {
        const parentIndex = rowsDisplayState.value[key].parent
        key = `row-${parentIndex}`
        if (rowsDisplayState.value[key]) {
          // We want to check if parent is an soaGroup or not (not parent === soaGroup)
          if (!rowsDisplayState.value[key].value) {
            result = false
            break
          }
        } else {
          console.warn(`Warning: key ${key} not found in displayState!!`)
        }
        continue
      }
      break
    }
    if (row.cells && row.cells.length) {
      if (row.cells[0].style === 'soaGroup') {
        return true
      }
      if (row.cells[0].style === 'group') {
        return result
      }
    }
    return result
  } catch (error) {
    console.error(error)
  }
}

function getStudyActivitiesForSubgroup(subgroupUid) {
  let subgroupFound = false
  const result = []
  for (const row of soaRows.value) {
    if (
      row.cells[0].style === 'subGroup' &&
      row.cells[0].refs?.[0]?.uid === subgroupUid
    ) {
      subgroupFound = true
    } else if (subgroupFound) {
      if (scheduleMethods.isActivityRow(row)) {
        result.push(row.cells[0])
      } else {
        break
      }
    }
  }
  return result
}

function enableFootnoteMode(footnote) {
  if (footnote) {
    activeFootnote.value = footnote
    elementsForFootnote.value.referenced_items = footnote.referenced_items
  }
  footnoteMode.value = true
}

function disableFootnoteMode() {
  if (route.params.footnote) {
    router.push({
      name: 'StudyActivities',
      params: { tab: 'footnotes' },
    })
    route.params.footnote = null
  }
  activeFootnote.value = null
  elementsForFootnote.value.referenced_items = []
  footnoteMode.value = false
  footnoteTable.value.disableFootnoteMode()
}

function addVisitForFootnote(refs, type, name) {
  if (!name) {
    name = type
  }
  if (refs.length > 1) {
    this.notificationHub.add({
      msg: t('DetailedFlowchart.footnote_added_to_visit_group'),
      type: 'warning',
    })
  }
  refs.forEach((ref) => {
    elementsForFootnote.value.referenced_items.push({
      item_uid: ref.uid,
      item_type: ref.type,
      item_name: name,
    })
  })
}

function addElementForFootnote(uid, type, name, schedule) {
  try {
    if (schedule && activeFootnote.value) {
      if (!schedule.footnotes) schedule.footnotes = []
      schedule.footnotes.push(
        dataFormating.footnoteSymbol(activeFootnote.value.order)
      )
    }
    if (!name) {
      name = type
    }
    if (typeof uid !== 'string') {
      uid.forEach((u) => {
        elementsForFootnote.value.referenced_items.push({
          item_uid: u,
          item_type: type,
          item_name: name,
        })
      })
    } else {
      elementsForFootnote.value.referenced_items.push({
        item_uid: uid,
        item_type: type,
        item_name: name,
      })
    }
  } catch (error) {
    console.error(error)
  }
}

function removeFootnote(uid) {
  const indexToRemove = elementsForFootnote.value.referenced_items.findIndex(
    (item) => item.item_uid === uid
  )
  if (indexToRemove !== -1) {
    elementsForFootnote.value.referenced_items.splice(indexToRemove, 1)
  }
}

function removeElementForFootnote(uid, schedule) {
  try {
    if (schedule && activeFootnote.value) {
      schedule.footnotes = schedule.footnotes?.filter(
        (s) => s !== dataFormating.footnoteSymbol(activeFootnote.value.order)
      )
    }
    if (typeof uid !== 'string') {
      uid.forEach((u) => {
        removeFootnote(u)
      })
    } else {
      removeFootnote(uid)
    }
  } catch (error) {
    console.error(error)
  }
}

function saveElementsForFootnote() {
  notificationHub.clearErrors()

  if (activeFootnote.value) {
    footnoteUpdateLoading.value = true
    study
      .updateStudyFootnote(
        studiesGeneralStore.selectedStudy.uid,
        activeFootnote.value.uid,
        elementsForFootnote.value
      )
      .then(() => {
        footnoteUpdateLoading.value = false
        disableFootnoteMode()
        loadSoaContent(true)
        notificationHub.add({
          msg: t('StudyFootnoteEditForm.update_success'),
        })
      })
  } else {
    showFootnoteForm.value = true
  }
}

function closeFootnoteForm() {
  notificationHub.clearErrors()
  showFootnoteForm.value = false
  disableFootnoteMode()
  footnoteTable.value.filterTable()
}

function checkIfElementHasFootnote(elUid) {
  if (elUid && typeof elUid === 'string') {
    return elementsForFootnote.value.referenced_items.find(
      (item) => item.item_uid === elUid
    )
  } else if (elUid) {
    return elementsForFootnote.value.referenced_items.find(
      (item) => item.item_uid === elUid[0]
    )
  }
}

function getComplexityScore() {
  if (
    featureFlagsStore.getFeatureFlag('complexity_score_calculation') === true
  ) {
    complexityScoreLoading.value = true
    study
      .getComplexityScore(studiesGeneralStore.selectedStudy.uid)
      .then((resp) => {
        complexityScore.value = resp.data
        complexityScoreLoading.value = false
      })
  }
}

function openComplexityDetails() {
  showComplexityDetails.value = true
}

function isCheckboxDisabled(studyActivityUid, studyVisitUid) {
  const state = currentSelectionMatrix.value[studyActivityUid][studyVisitUid]
  return (
    props.readOnly ||
    (state.value && !state.uid) ||
    (!state.value && state.uid !== null)
  )
}

function getCurrentDisplayValue(rowKey) {
  const currentValue = rowsDisplayState?.value[rowKey]?.value
  if (currentValue === undefined) {
    return false
  }
  return currentValue
}

function getDisplayButtonIcon(rowKey) {
  return getCurrentDisplayValue(rowKey)
    ? 'mdi-chevron-down'
    : 'mdi-chevron-right'
}

function getLevelDisplayState(row) {
  return !row.hide
}

function getProtocolSoaTypeLabel(style) {
  if (style === 'soaGroup') {
    return 'SoA group'
  }
  if (style === 'subGroup') {
    return 'Subgroup'
  }
  return style.charAt(0).toUpperCase() + style.slice(1)
}

function highlightRow(row) {
  if (!scheduleMethods.isActivityRow(row)) {
    return
  }
  const rowId = `row-scroll-${row.cells[0].refs[0]?.uid}`
  const el = document.getElementById(rowId)
  el.classList.toggle('bg-nnBaseHeavy')
}

function toggleRowState(rowKey) {
  try {
    const currentValue = getCurrentDisplayValue(rowKey)
    rowsDisplayState.value[rowKey].value = !currentValue
  } catch (error) {
    console.error(error)
  }
}

function toggleAllRowState(value) {
  for (const key in rowsDisplayState.value) {
    rowsDisplayState.value[key].value = value
  }
}

async function toggleLevelDisplay(row) {
  const firstCell = row.cells?.[0]
  if (!firstCell) {
    row.loading = false
    return
  }

  const key = firstCell.refs?.[0]?.uid

  const soaRow = soaRows.value.find((r) => {
    const fc = r.cells?.[0]
    return fc && fc.refs?.[0]?.uid === key
  })
  soaRow.hide = !soaRow.hide

  let action
  let field
  if (scheduleMethods.isActivityRow(soaRow)) {
    field = 'show_activity_in_protocol_flowchart'
    action = 'updateStudyActivity'
  } else if (firstCell.style === 'subGroup') {
    field = 'show_activity_subgroup_in_protocol_flowchart'
    action = 'updateStudyActivitySubGroup'
  } else if (firstCell.style === 'group') {
    field = 'show_activity_group_in_protocol_flowchart'
    action = 'updateStudyActivityGroup'
  } else if (firstCell.style === 'soaGroup') {
    field = 'show_soa_group_in_protocol_flowchart'
    action = 'updateStudySoaGroup'
  }

  const payload = {}
  payload[field] = !soaRow.hide

  try {
    await study[action](
      studiesGeneralStore.selectedStudy.uid,
      firstCell.refs[0].uid,
      payload
    )
  } catch (err) {
    soaRow.hide = !soaRow.hide
    console.error(err)
  }
}

function updateGroupedSchedule(value, studyActivityUid, studyVisitCell) {
  if (value) {
    const data = []
    for (const visitRef of studyVisitCell.refs) {
      data.push({
        method: 'POST',
        content: {
          study_activity_uid: studyActivityUid,
          study_visit_uid: visitRef.uid,
        },
      })
    }
    study
      .studyActivityScheduleBatchOperations(
        studiesGeneralStore.selectedStudy.uid,
        data
      )
      .then((resp) => {
        const scheduleUids = []
        for (const subResp of resp.data) {
          if (subResp.response_code >= 400) {
            notificationHub.add({
              msg: subResp.content.message,
              type: 'error',
              timeout: 0,
            })
          } else {
            scheduleUids.push(subResp.content.study_activity_schedule_uid)
          }
        }
        currentSelectionMatrix.value[studyActivityUid][
          studyVisitCell.refs[0].uid
        ].uid = scheduleUids
        getComplexityScore()
      })
  } else {
    const data = []
    for (const scheduleUid of currentSelectionMatrix.value[studyActivityUid][
      studyVisitCell.refs[0].uid
    ].uid) {
      data.push({
        method: 'DELETE',
        content: {
          uid: scheduleUid,
        },
      })
    }
    study
      .studyActivityScheduleBatchOperations(
        studiesGeneralStore.selectedStudy.uid,
        data
      )
      .then((resp) => {
        const errors = []
        for (const subResp of resp.data) {
          if (subResp.response_code >= 400) {
            errors.push(subResp.content.message)
            notificationHub.add({
              msg: subResp.content.message,
              type: 'error',
              timeout: 0,
            })
          }
        }
        if (!errors.length) {
          currentSelectionMatrix.value[studyActivityUid][
            studyVisitCell.refs[0].uid
          ].uid = null
          getComplexityScore()
        }
      })
  }
}

function updateSchedule(value, studyActivityUid, studyVisitCell) {
  notificationHub.clearErrors()

  complexityScoreLoading.value = true
  if (studyVisitCell.refs.length > 1) {
    updateGroupedSchedule(value, studyActivityUid, studyVisitCell)
    return
  }
  if (value) {
    const data = {
      study_activity_uid: studyActivityUid,
      study_visit_uid: studyVisitCell.refs[0].uid,
    }
    study
      .createStudyActivitySchedule(studiesGeneralStore.selectedStudy.uid, data)
      .then((resp) => {
        currentSelectionMatrix.value[studyActivityUid][
          studyVisitCell.refs[0].uid
        ].uid = resp.data.study_activity_schedule_uid
        getComplexityScore()
      })
  } else {
    const scheduleUid =
      currentSelectionMatrix.value[studyActivityUid][studyVisitCell.refs[0].uid]
        .uid
    study
      .deleteStudyActivitySchedule(
        studiesGeneralStore.selectedStudy.uid,
        scheduleUid
      )
      .then(() => {
        currentSelectionMatrix.value[studyActivityUid][
          studyVisitCell.refs[0].uid
        ].uid = null
        getComplexityScore()
      })
  }
}

async function openBatchEditForm() {
  localStorage.setItem('refresh-activities', true)
  if (!studyActivitySelection.value.length) {
    notificationHub.add({
      type: 'warning',
      msg: t('DetailedFlowchart.batch_edit_no_selection'),
    })
    return
  }
  showBatchEditForm.value = true
}

function unselectItem(item) {
  studyActivitySelection.value = studyActivitySelection.value.filter(
    (sa) => sa.refs[0].uid !== item.study_activity_uid
  )
}

async function batchRemoveStudyActivities() {
  localStorage.setItem('refresh-activities', true)
  if (!studyActivitySelection.value.length) {
    notificationHub.add({
      type: 'warning',
      msg: t('DetailedFlowchart.batch_remove_no_selection'),
    })
    return
  }
  const data = []
  for (const cell of studyActivitySelection.value) {
    data.push({
      method: 'DELETE',
      content: {
        study_activity_uid: cell.refs[0].uid,
      },
    })
  }
  const options = { type: 'warning' }
  if (
    !(await confirm.value.open(
      t('DetailedFlowchart.remove_multiple_activities_msg', {
        activities: studyActivitySelection.value.length,
      }),
      options
    ))
  ) {
    return
  }
  loadingSoaContent.value = true
  study
    .studyActivityBatchOperations(studiesGeneralStore.selectedStudy.uid, data)
    .then(() => {
      notificationHub.add({
        msg: t('DetailedFlowchart.remove_success', {
          activities: studyActivitySelection.value.length,
        }),
      })
      studyActivitySelection.value = []
      loadSoaContent(true)
    })
}

function toggleActivitySelection(row, value) {
  const activityCell = row.cells[0]
  if (value) {
    studyActivitySelection.value.push(activityCell)
  } else {
    for (let i = 0; i < studyActivitySelection.value.length; i++) {
      if (
        studyActivitySelection.value[i].refs[0].uid === activityCell.refs[0].uid
      ) {
        studyActivitySelection.value.splice(i, 1)
        break
      }
    }
  }
}

function toggleSubgroupActivitiesSelection(subgroupRow, value) {
  const activityCells = getStudyActivitiesForSubgroup(
    subgroupRow.cells[0].refs?.[0]?.uid
  )
  if (value) {
    studyActivitySelection.value =
      studyActivitySelection.value.concat(activityCells)
  } else {
    for (const activityCell of activityCells) {
      const index = studyActivitySelection.value.findIndex(
        (cell) => cell.refs?.[0]?.uid === activityCell.refs?.[0]?.uid
      )
      if (index != -1) {
        studyActivitySelection.value.splice(index, 1)
      }
    }
  }
  // Remove duplicates in case if any activities in subgroup were already selected
  studyActivitySelection.value = studyActivitySelection.value.filter(
    (act1, i, arr) => arr.findIndex((act2) => act2.text === act1.text) === i
  )
}

async function loadSoaContent(keepDisplayState) {
  loadingSoaContent.value = true
  soaContentLoadingStore.changeLoadingState()
  studyActivitySelection.value = []
  try {
    getComplexityScore()
    const resp = await study.getStudyProtocolFlowchart(
      studiesGeneralStore.selectedStudy.uid,
      { layout: 'detailed' }
    )
    soaContent.value = resp.data
  } catch {
    loadingSoaContent.value = false
  }
  let currentSoaGroup
  let currentGroup
  let currentSubGroup

  let fallbackExpandState
  if (!keepDisplayState) {
    fallbackExpandState = Object.keys(rowsDisplayState.value).length
      ? snapshotExpandState()
      : soaExpandStateStore.get(studiesGeneralStore.selectedStudy.uid)
    rowsDisplayState.value = {}
    expandAllRows.value = false
  }
  for (const row of soaRows.value) {
    const rowUid = row.cells[0].refs[0]?.uid
    const key = `row-${rowUid}`
    if (row.cells && row.cells.length) {
      if (row.cells[0].style === 'soaGroup') {
        if (!keepDisplayState) {
          rowsDisplayState.value[key] = { value: false }
        }
        currentGroup = null
        currentSubGroup = null
        currentSoaGroup = rowUid
      } else if (row.cells[0].style === 'group') {
        if (!keepDisplayState) {
          rowsDisplayState.value[key] = {
            value: false,
            parent: currentSoaGroup,
          }
        }
        currentSubGroup = null
        currentGroup = rowUid
      } else if (row.cells[0].style === 'subGroup') {
        if (!keepDisplayState) {
          rowsDisplayState.value[key] = {
            value: false,
            parent: currentGroup,
          }
        }
        currentSubGroup = rowUid
      } else if (scheduleMethods.isActivityRow(row)) {
        const scheduleCells = row.cells.slice(1)
        if (!keepDisplayState) {
          rowsDisplayState.value[key] = {
            value: false,
            parent: currentSubGroup,
          }
        }
        if (row.cells[0].refs && row.cells[0].refs.length) {
          currentSelectionMatrix.value[row.cells[0].refs?.[0].uid] = {}
          for (const [visitIndex, cell] of soaVisitRow.value.entries()) {
            let props
            if (
              scheduleCells[visitIndex].refs &&
              scheduleCells[visitIndex].refs.length
            ) {
              if (cell.refs && cell.refs.length === 1) {
                props = {
                  value: true,
                  uid: scheduleCells[visitIndex].refs[0].uid,
                }
              } else {
                props = {
                  value: true,
                  uid: scheduleCells[visitIndex].refs.map((ref) => ref.uid),
                }
              }
            } else {
              props = { value: false, uid: null }
            }
            if (cell.refs) {
              currentSelectionMatrix.value[row.cells[0].refs[0].uid][
                cell.refs[0].uid
              ] = props
            }
          }
        }
      }
    }
  }
  if (!keepDisplayState && fallbackExpandState) {
    for (const key in rowsDisplayState.value) {
      if (fallbackExpandState.rowsDisplayState[key] !== undefined) {
        rowsDisplayState.value[key].value =
          fallbackExpandState.rowsDisplayState[key]
      }
    }
    expandAllRows.value = fallbackExpandState.expandAllRows
  }
  loadingSoaContent.value = false
  soaContentLoadingStore.changeLoadingState()
  if (scrollItemId.value) {
    setTimeout(() => {
      const targetElement = document.getElementById(scrollItemId.value)
      targetElement?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }, 1000)
  }
}

function onResize() {
  tableHeight.value =
    window.innerHeight - tableContainer.value.getBoundingClientRect().y - 100
}

function groupSelectedVisits() {
  const visitUids = selectedVisitIndexes.value
    .sort(function (a, b) {
      return a - b
    })
    .map((cell) => soaVisitRow.value[cell].refs[0].uid)
  const data = {
    visits_to_assign: visitUids,
    validate_only: true,
  }
  studyEpochs
    .createCollapsibleVisitGroup(studiesGeneralStore.selectedStudy.uid, data)
    .then(() => {
      showCollapsibleGroupForm.value = true
    })
    .catch((err) => {
      if (err.response.status === 400) {
        if (err.response.data.type !== 'BusinessLogicException') {
          showCollapsibleGroupForm.value = true
        } else {
          notificationHub.add({
            msg: err.response.data.message,
            type: 'error',
          })
        }
      }
    })
}

function closeCollapsibleVisitGroupForm() {
  showCollapsibleGroupForm.value = false
}

function collapsibleVisitGroupCreated() {
  notificationHub.add({
    msg: t('CollapsibleVisitGroupForm.creation_success'),
  })
  loadSoaContent(true)
  getStudyVisits()
  selectedVisitIndexes.value = []
}

async function deleteVisitGroup(cell) {
  const group = studyVisits.value.find(
    (visit) => visit.uid === cell.refs[0].uid
  )
  const message = t('DetailedFlowchart.confirm_group_deletion', {
    group: group.consecutive_visit_group,
  })
  const options = { type: 'warning' }
  if (!(await confirm.value.open(message, options))) {
    return
  }
  await studyEpochs.deleteCollapsibleVisitGroup(
    studiesGeneralStore.selectedStudy.uid,
    group.consecutive_visit_group_uid
  )
  loadSoaContent(true)
  getStudyVisits()
}

async function getHistoryData(options) {
  const params = {
    total_count: true,
  }
  if (options) {
    params.page_number = options.page ? options.page : 1
    params.page_size = options.itemsPerPage ? options.itemsPerPage : 10
  }
  const resp = await study.getStudySoAHistory(
    studiesGeneralStore.selectedStudy.uid,
    params
  )
  historyItems.value = resp.data.items
  historyItemsTotal.value = resp.data.total
}

async function openHistory() {
  await getHistoryData()
  showHistory.value = true
}

function closeHistory() {
  showHistory.value = false
}

async function downloadCSV() {
  soaContentLoadingStore.changeLoadingState()
  try {
    await soaDownloads.csvDownload('detailed')
  } finally {
    soaContentLoadingStore.changeLoadingState()
  }
}

async function downloadEXCEL() {
  soaContentLoadingStore.changeLoadingState()
  try {
    await soaDownloads.excelDownload('detailed')
  } finally {
    soaContentLoadingStore.changeLoadingState()
  }
}

async function downloadDOCX() {
  soaContentLoadingStore.changeLoadingState()
  try {
    await soaDownloads.docxDownload('detailed')
  } finally {
    soaContentLoadingStore.changeLoadingState()
  }
}

const areConsecutiveVisitsSelected = computed(() => {
  if (selectedVisitIndexes.value.length > 1) {
    const minIndex = selectedVisitIndexes.value.reduce((a, b) => Math.min(a, b))
    const maxIndex = selectedVisitIndexes.value.reduce((a, b) => Math.max(a, b))
    return selectedVisitIndexes.value.length - 1 === maxIndex - minIndex
  }
  return true
})
function multipleVisitsSelected() {
  // Check if more than one visit is selected
  return selectedVisitIndexes.value.length > 1
}

function getSearchHighlightedSegments(text) {
  const rowText = typeof text === 'string' ? text : ''
  const searchTerm = search.value?.trim()

  if (!(searchTerm?.length >= 3) || !rowText) {
    return [{ text: rowText, match: false }]
  }

  if (!rowText.toLowerCase().includes(searchTerm.toLowerCase())) {
    return [{ text: rowText, match: false }]
  }

  const escapedSearchTerm = searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const splitRegex = new RegExp(`(${escapedSearchTerm})`, 'gi')

  return rowText
    .split(splitRegex)
    .filter((segment) => segment.length > 0)
    .map((segment) => ({
      text: segment,
      match: segment.toLowerCase() === searchTerm.toLowerCase(),
    }))
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
  background-color: rgb(var(--v-theme-nnLightBlue100));
}
th,
td {
  position: relative;
  font-size: 11px;
  z-index: 0;
}

td {
  background-color: inherit;
}

.sticky-header {
  overflow-y: auto;
  overflow-anchor: none;

  thead th {
    position: sticky;
    top: 0;
    z-index: 3;
  }
}
.sticky-column {
  position: sticky;
  left: 0px;
  z-index: 4 !important;
}
.header {
  background-color: rgb(var(--v-theme-nnTrueBlue));
  color: rgb(var(--v-theme-nnWhite));
  z-index: 10;
  left: 0px;
}
.zindex25 {
  z-index: 25 !important;
}
.bottomCard {
  align-content: center;
  position: fixed;
  bottom: 0;
  z-index: 1100;
  height: 100px;
  width: -webkit-fill-available;
}
.flowchart {
  background-color: rgb(var(--v-theme-nnSeaBlue300));
  text-transform: uppercase;
  font-weight: bold;
}
.group {
  background-color: rgb(var(--v-theme-nnSeaBlue200));
  text-transform: uppercase;
  font-weight: bold;
}
.subgroup {
  background-color: rgb(var(--v-theme-nnSeaBlue100));
  text-transform: uppercase;
  font-weight: bold;
}
.text-strong {
  font-weight: 600;
}
.scale50 {
  scale: 50%;
}
.scale75 {
  scale: 75%;
}
.visitFootnote {
  margin-bottom: 8px;
}
.layoutSelector {
  border-color: rgb(var(--v-theme-nnBaseBlue));
}
.v-card-text {
  display: inline-flex;
}
td .actionButtons {
  display: none;
}
td:hover .actionButtons {
  display: flex;
}
input[type='checkbox'] {
  cursor: pointer;
}

:deep(.v-badge__badge) {
  font-weight: 700;
}

.badgeSchedules {
  position: absolute;
  top: -8px;
  left: 32px;
  transform: translateY(0);
  background: transparent;
  font-weight: 700;
  color: rgb(var(--v-theme-nnBaseBlue));
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  pointer-events: none;
}
.badgeActivities {
  flex-shrink: 0;
  font-size: 1.1em;
  font-weight: 700;
  color: rgb(var(--v-theme-nnBaseBlue));
  margin-left: 0.15em;
  line-height: 1;
  text-transform: lowercase;
}
.footnote-cell {
  display: inline-flex;
  height: 35px;
  align-items: center;
}

.row-fixed-width {
  width: 28px;
  min-width: 28px;
  display: flex;
  justify-content: center;
}

.row-label-wrapper {
  display: flex;
  align-items: flex-start;
  min-width: 0;
  max-width: 100%;
}

.row-label-activator {
  display: inline-block;
  max-width: 100%;
  min-width: 0;
}

.row-label-text {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  max-width: 100%;
  word-break: break-word;
}

.search-match-cell {
  background-color: rgb(var(--v-theme-nnGoldenSun200));
  border-radius: 10px;
  padding: 0px 3px;
  display: inline;
  box-decoration-break: clone;
}
</style>
