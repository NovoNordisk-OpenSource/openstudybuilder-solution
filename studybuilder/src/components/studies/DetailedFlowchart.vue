<template>
  <div
    v-if="!loadingSoaContent"
    v-resize="onResize"
    class="pa-4 bg-white"
    style="overflow-x: auto"
  >
    <v-row style="justify-content: center">
      <v-btn-toggle
        v-model="layout"
        mandatory
        density="compact"
        color="nnBaseBlue"
        divided
        variant="outlined"
        class="layoutSelector"
        :disabled="sortMode"
      >
        <v-btn value="detailed">
          {{ $t('DetailedFlowchart.detailed') }}
        </v-btn>
        <v-btn value="protocol">
          {{ $t('DetailedFlowchart.protocol') }}
        </v-btn>
        <v-btn value="operational">
          {{ $t('DetailedFlowchart.operational') }}
        </v-btn>
      </v-btn-toggle>
    </v-row>
    <ProtocolFlowchart
      v-if="['operational', 'protocol'].indexOf(layout) > -1"
      :layout="layout"
      :style="`max-height: ${tableHeight + 70}px;`"
    />
    <div v-else>
      <div class="d-flex align-center mb-4">
        <v-switch
          v-model="expandAllRows"
          :label="$t('DetailedFlowchart.expand_all')"
          hide-details
          class="ml-2 flex-grow-0"
          color="primary"
          :disabled="sortMode"
          @update:model-value="toggleAllRowState"
        />
        <v-spacer />
        <template v-if="!props.readOnly">
          <v-btn
            v-show="multipleConsecutiveVisitsSelected()"
            class="ml-2"
            size="small"
            variant="outlined"
            color="nnBaseBlue"
            :title="$t('GroupStudyVisits.title')"
            :disabled="
              footnoteMode ||
              !accessGuard.checkPermission($roles.STUDY_WRITE) ||
              studiesGeneralStore.selectedStudyVersion !== null
            "
            :loading="soaContentLoadingStore.loading"
            icon="mdi-arrow-expand-horizontal"
            @click="groupSelectedVisits()"
          />
          <v-btn
            class="ml-2"
            size="small"
            variant="outlined"
            color="nnBaseBlue"
            :title="$t('DetailedFlowchart.hide_activity_selection')"
            :disabled="
              footnoteMode ||
              !accessGuard.checkPermission($roles.STUDY_WRITE) ||
              studiesGeneralStore.selectedStudyVersion !== null ||
              sortMode
            "
            icon="mdi-eye-off-outline"
            :loading="soaContentLoadingStore.loading"
            @click="toggleActivitySelectionDisplay(false)"
          />
          <v-btn
            class="ml-2"
            size="small"
            variant="outlined"
            color="nnBaseBlue"
            :title="$t('DetailedFlowchart.show_activity_selection')"
            :disabled="
              footnoteMode ||
              !accessGuard.checkPermission($roles.STUDY_WRITE) ||
              studiesGeneralStore.selectedStudyVersion !== null ||
              sortMode
            "
            icon="mdi-eye-outline"
            :loading="soaContentLoadingStore.loading"
            @click="toggleActivitySelectionDisplay(true)"
          />
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
                size="small"
                variant="outlined"
                color="nnBaseBlue"
                v-bind="props"
                title="Bulk actions"
                icon="mdi-folder-multiple-outline"
                :loading="soaContentLoadingStore.loading"
              >
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
                size="small"
                variant="outlined"
                color="nnBaseBlue"
                v-bind="props"
                :title="$t('DataTableExportButton.export')"
                icon="mdi-download-outline"
                :disabled="sortMode"
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
          <v-btn
            class="ml-2"
            size="small"
            variant="outlined"
            color="nnBaseBlue"
            :title="$t('NNTableTooltips.history')"
            icon="mdi-history"
            :disabled="sortMode"
            @click="openHistory"
          />
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
                            ? getElementFootnotesLetters(cell.refs[0].uid)
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
                          ? getElementFootnotesLetters(cell.refs[0].uid)
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
                        addElementForFootnote(
                          cell.refs[0].uid,
                          'StudyVisit',
                          cell.text
                        )
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
                      density="compact"
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
                      @click="deleteVisitGroup(cell.text)"
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
          <tbody v-if="sortMode" ref="parent">
            <template
              v-for="(row, index) in soaRowsDrag"
              :key="`${row.cells[0].style}_${row.cells[0].text}`"
            >
              <tr
                :class="getSoaRowClasses(row)"
                :style="row.noIcon ? 'pointer-events: none !important' : ''"
              >
                <td
                  :class="getSoaFirstCellClasses(row.cells[0])"
                  class="sticky-column"
                  style="min-width: 300px"
                >
                  <div class="d-flex align-center justify-start">
                    <v-icon v-if="!row.noIcon" size="small" class="ml-4">
                      mdi-sort
                    </v-icon>
                    <v-btn variant="text" style="height: 32px" size="x-small" />
                    <v-checkbox
                      v-if="
                        !props.readOnly && getSoaRowType(row) === 'activity'
                      "
                      color="primary"
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
                      density="compact"
                      :style="footnoteMode ? 'visibility: hidden;' : ''"
                      class="flex-grow-0 ml-6 scale75"
                      @update:model-value="
                        (value) => toggleActivitySelection(row, value)
                      "
                    />
                    <v-checkbox
                      v-if="
                        !props.readOnly && getSoaRowType(row) === 'subGroup'
                      "
                      color="primary"
                      true-icon="mdi-checkbox-multiple-marked-outline"
                      false-icon="mdi-checkbox-multiple-blank-outline"
                      hide-details
                      :disabled="
                        !accessGuard.checkPermission($roles.STUDY_WRITE) ||
                        studiesGeneralStore.selectedStudyVersion !== null
                      "
                      density="compact"
                      :style="footnoteMode ? 'visibility: hidden;' : ''"
                      class="flex-grow-0 mr-2 scale75"
                      @update:model-value="
                        (value) => toggleSubgroupActivitiesSelection(row, value)
                      "
                    />
                    <v-badge
                      color="transparent"
                      text-color="secondary"
                      floating
                      :content="
                        row.cells[0].refs.length
                          ? getElementFootnotesLetters(
                              row.cells[0]?.refs[0]?.uid
                            )
                          : ''
                      "
                    >
                      <v-tooltip bottom>
                        <template #activator="{ props }">
                          <div v-bind="props">
                            <span
                              :class="
                                row.cells[0].style !== 'activity'
                                  ? 'text-uppercase'
                                  : ''
                              "
                            >
                              {{ row.cells[0].text.substring(0, 40) }}
                            </span>
                          </div>
                        </template>
                        <span
                          :class="
                            row.cells[0].style !== 'activity'
                              ? 'text-uppercase'
                              : ''
                          "
                        >
                          {{ row.cells[0].text }}
                        </span>
                      </v-tooltip>
                    </v-badge>
                    <v-btn
                      v-if="
                        footnoteMode &&
                        row.cells[0].refs[0] &&
                        !checkIfElementHasFootnote(row.cells[0].refs[0].uid)
                      "
                      icon="mdi-plus-circle-outline"
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
                      @click="
                        removeElementForFootnote(row.cells[0].refs[0].uid)
                      "
                    />
                    <v-spacer />
                    <v-btn
                      v-if="!props.readOnly"
                      icon
                      :title="$t('DetailedFlowchart.toggle_soa_group_display')"
                      :disabled="
                        footnoteMode ||
                        !accessGuard.checkPermission($roles.STUDY_WRITE) ||
                        studiesGeneralStore.selectedStudyVersion !== null
                      "
                      variant="text"
                      style="height: auto"
                      @click="toggleLevelDisplay(row)"
                    >
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
                    </v-btn>
                  </div>
                </td>
                <td
                  v-if="getSoaRowType(row) !== 'activity'"
                  :colspan="row.cells.length - 1"
                />
                <td
                  v-for="(visitCell, visitIndex) in soaVisitRow"
                  v-else
                  :key="`row-${index}-cell-${visitIndex}`"
                >
                  <v-row class="mt-0">
                    <v-badge
                      color="transparent"
                      floating
                      text-color="secondary"
                      offset-x="2"
                      :content="
                        row.cells[visitIndex + 1].refs &&
                        row.cells[visitIndex + 1].refs.length
                          ? getElementFootnotesLetters(
                              row.cells[visitIndex + 1].refs[0].uid
                            )
                          : ''
                      "
                      overlap
                    >
                      <input
                        v-model="
                          currentSelectionMatrix[row.cells[0].refs[0].uid][
                            visitCell.refs[0].uid
                          ].value
                        "
                        color="success"
                        :disabled="
                          isCheckboxDisabled(
                            row.cells[0].refs[0].uid,
                            visitCell.refs[0].uid
                          ) ||
                          footnoteMode ||
                          !accessGuard.checkPermission($roles.STUDY_WRITE) ||
                          studiesGeneralStore.selectedStudyVersion !== null
                        "
                        hide-details
                        density="compact"
                        true-icon="mdi-checkbox-marked-circle-outline"
                        false-icon="mdi-checkbox-blank-circle-outline"
                        class="mx-0 ml-6 mb-3 px-0"
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
                      <div class="actionButtons">
                        <v-btn
                          v-if="
                            !footnoteMode &&
                            !props.readOnly &&
                            currentSelectionMatrix[row.cells[0].refs[0].uid][
                              visitCell.refs[0].uid
                            ].value
                          "
                          key="1"
                          size="x-small"
                          class="ml-n2 mb-3 mt-n2 mr-n4 scale50"
                          variant="outlined"
                          color="nnBaseBlue"
                          icon="mdi-plus"
                          @click="
                            enableFootnoteModeWithElement(
                              row.cells[visitIndex + 1].refs[0].uid,
                              row.cells[visitIndex + 1].refs[0].type,
                              row.cells[visitIndex + 1].refs[0].text
                            )
                          "
                        />
                        <v-btn
                          v-if="
                            !footnoteMode &&
                            !props.readOnly &&
                            row.cells[visitIndex + 1].refs &&
                            row.cells[visitIndex + 1].refs.length &&
                            Boolean(
                              getElementFootnotesLetters(
                                row.cells[visitIndex + 1].refs[0].uid
                              )
                            )
                          "
                          key="2"
                          class="mb-3 mt-n2 mr-n2 scale50"
                          size="x-small"
                          variant="outlined"
                          color="nnBaseBlue"
                          icon="mdi-minus"
                          @click="
                            openRemoveFootnoteForm(row.cells[visitIndex + 1])
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
                            row.cells[visitIndex + 1].refs[0].uid
                          )
                        "
                        size="x-small"
                        icon="mdi-plus-circle-outline"
                        class="mx-0 px-0 ml-n3 mb-4 mt-n2 mr-n4"
                        variant="text"
                        @click="
                          addElementForFootnote(
                            row.cells[visitIndex + 1].refs[0].uid,
                            row.cells[visitIndex + 1].refs[0].type,
                            row.cells[visitIndex + 1].refs[0].text
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
                            row.cells[visitIndex + 1].refs[0].uid
                          )
                        "
                        size="x-small"
                        icon="mdi-minus-circle"
                        class="mx-0 px-0 ml-n3 mb-4 mt-n2 mr-n4"
                        color="nnBaseBlue"
                        variant="text"
                        @click="
                          removeElementForFootnote(
                            row.cells[visitIndex + 1].refs[0].uid
                          )
                        "
                      />
                    </v-badge>
                  </v-row>
                </td>
              </tr>
            </template>
          </tbody>
          <tbody v-if="!sortMode">
            <template v-for="(row, index) in soaRows">
              <tr
                v-if="showSoaRow(index, row)"
                :key="`row-${index}`"
                :class="getSoaRowClasses(row)"
              >
                <td
                  :class="getSoaFirstCellClasses(row.cells[0])"
                  class="sticky-column"
                  style="min-width: 300px"
                >
                  <div class="d-flex align-center justify-start">
                    <v-btn
                      v-if="
                        !props.readOnly && getSoaRowType(row) !== 'activity'
                      "
                      :icon="getDisplayButtonIcon(`row-${index}`)"
                      variant="text"
                      size="x-small"
                      @click="toggleRowState(`row-${index}`)"
                    />
                    <ActionsMenu
                      v-if="row.order"
                      size="small"
                      :actions="actions"
                      :item="{ row: row, index: index }"
                      :disabled="studiesGeneralStore.selectedStudyVersion"
                    />
                    <v-checkbox
                      v-if="
                        !props.readOnly && getSoaRowType(row) === 'activity'
                      "
                      color="primary"
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
                      density="compact"
                      :style="footnoteMode ? 'visibility: hidden;' : ''"
                      class="flex-grow-0 ml-12 scale75"
                      @update:model-value="
                        (value) => toggleActivitySelection(row, value)
                      "
                    />
                    <v-checkbox
                      v-if="
                        !props.readOnly && getSoaRowType(row) === 'subGroup'
                      "
                      color="primary"
                      true-icon="mdi-checkbox-multiple-marked-outline"
                      false-icon="mdi-checkbox-multiple-blank-outline"
                      hide-details
                      :disabled="
                        !accessGuard.checkPermission($roles.STUDY_WRITE) ||
                        studiesGeneralStore.selectedStudyVersion !== null
                      "
                      density="compact"
                      :style="footnoteMode ? 'visibility: hidden;' : ''"
                      class="flex-grow-0 scale75 ml-4"
                      @update:model-value="
                        (value) => toggleSubgroupActivitiesSelection(row, value)
                      "
                    />
                    <v-badge
                      color="transparent"
                      text-color="secondary"
                      floating
                      :content="
                        row.cells[0].refs.length
                          ? getElementFootnotesLetters(row.cells[0].refs[0].uid)
                          : ''
                      "
                    >
                      <v-tooltip bottom>
                        <template #activator="{ props }">
                          <div v-bind="props">
                            <span
                              :class="
                                row.cells[0].style !== 'activity'
                                  ? 'text-uppercase'
                                  : ''
                              "
                              class="ml-4"
                            >
                              {{ row.cells[0].text.substring(0, 40) }}
                            </span>
                          </div>
                        </template>
                        <span
                          :class="
                            row.cells[0].style !== 'activity'
                              ? 'text-uppercase'
                              : ''
                          "
                        >
                          {{ row.cells[0].text }}
                        </span>
                      </v-tooltip>
                    </v-badge>
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
                      :title="$t('DetailedFlowchart.toggle_soa_group_display')"
                      :disabled="
                        footnoteMode ||
                        !accessGuard.checkPermission($roles.STUDY_WRITE) ||
                        studiesGeneralStore.selectedStudyVersion !== null
                      "
                      variant="text"
                      style="height: auto"
                      @click="toggleLevelDisplay(row)"
                    >
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
                    </v-btn>
                  </div>
                </td>
                <td
                  v-if="getSoaRowType(row) !== 'activity'"
                  :colspan="row.cells.length - 1"
                />
                <td
                  v-for="(visitCell, visitIndex) in soaVisitRow"
                  v-else
                  :key="`row-${index}-cell-${visitIndex}`"
                >
                  <v-row class="mt-0">
                    <v-badge
                      color="transparent"
                      floating
                      text-color="secondary"
                      offset-x="2"
                      :content="
                        row.cells[visitIndex + 1].refs &&
                        row.cells[visitIndex + 1].refs.length
                          ? getElementFootnotesLetters(
                              row.cells[visitIndex + 1].refs[0].uid
                            )
                          : ''
                      "
                      overlap
                    >
                      <input
                        v-model="
                          currentSelectionMatrix[row.cells[0].refs[0].uid][
                            visitCell.refs[0].uid
                          ].value
                        "
                        color="success"
                        :disabled="
                          isCheckboxDisabled(
                            row.cells[0].refs[0].uid,
                            visitCell.refs[0].uid
                          ) ||
                          footnoteMode ||
                          !accessGuard.checkPermission($roles.STUDY_WRITE) ||
                          studiesGeneralStore.selectedStudyVersion !== null
                        "
                        hide-details
                        density="compact"
                        true-icon="mdi-checkbox-marked-circle-outline"
                        false-icon="mdi-checkbox-blank-circle-outline"
                        class="mx-0 ml-6 mb-3 px-0"
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
                      <div class="actionButtons">
                        <v-btn
                          v-if="
                            !footnoteMode &&
                            !props.readOnly &&
                            currentSelectionMatrix[row.cells[0].refs[0].uid][
                              visitCell.refs[0].uid
                            ].value
                          "
                          key="1"
                          size="x-small"
                          class="ml-n2 mb-3 mt-n2 mr-n4 scale50"
                          variant="outlined"
                          color="nnBaseBlue"
                          icon="mdi-plus"
                          :title="$t('DetailedFlowchart.add_footnote')"
                          @click="
                            enableFootnoteModeWithElement(
                              row.cells[visitIndex + 1].refs[0].uid,
                              row.cells[visitIndex + 1].refs[0].type,
                              row.cells[visitIndex + 1].refs[0].text
                            )
                          "
                        />
                        <v-btn
                          v-if="
                            !footnoteMode &&
                            !props.readOnly &&
                            row.cells[visitIndex + 1].refs &&
                            row.cells[visitIndex + 1].refs.length &&
                            Boolean(
                              getElementFootnotesLetters(
                                row.cells[visitIndex + 1].refs[0].uid
                              )
                            )
                          "
                          key="2"
                          class="mb-3 mt-n2 mr-n2 scale50"
                          size="x-small"
                          variant="outlined"
                          color="nnBaseBlue"
                          icon="mdi-minus"
                          :title="$t('DetailedFlowchart.remove_footnote')"
                          @click="
                            openRemoveFootnoteForm(row.cells[visitIndex + 1])
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
                            row.cells[visitIndex + 1].refs[0].uid
                          )
                        "
                        size="x-small"
                        icon="mdi-plus-circle-outline"
                        :title="$t('DetailedFlowchart.add_footnote')"
                        class="mx-0 px-0 ml-n3 mb-4 mt-n2 mr-n4"
                        variant="text"
                        @click="
                          addElementForFootnote(
                            row.cells[visitIndex + 1].refs[0].uid,
                            row.cells[visitIndex + 1].refs[0].type,
                            row.cells[visitIndex + 1].refs[0].text
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
                            row.cells[visitIndex + 1].refs[0].uid
                          )
                        "
                        size="x-small"
                        icon="mdi-minus-circle"
                        class="mx-0 px-0 ml-n3 mb-4 mt-n2 mr-n4"
                        color="nnBaseBlue"
                        variant="text"
                        :title="$t('DetailedFlowchart.remove_footnote')"
                        @click="
                          removeElementForFootnote(
                            row.cells[visitIndex + 1].refs[0].uid
                          )
                        "
                      />
                    </v-badge>
                  </v-row>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
      <div class="mt-8 ml-n4 mr-n4">
        <StudyFootnoteTable
          @update="loadSoaContent()"
          @enable-footnote-mode="enableFootnoteMode"
          @remove-element-from-footnote="removeElementForFootnote"
        />
      </div>
    </div>
    <v-card v-if="sortMode" id="bottomCard" elevation="24" class="bottomCard">
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
      elevation="24"
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
                  $t('StudyFootnoteEditForm.select_footnote_items', {
                    footnote: activeFootnote.template
                      ? activeFootnote.template.name_plain
                      : activeFootnote.footnote.name_plain,
                  })
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
      :open="showBatchEditForm"
      :selection="formattedStudyActivitySelection"
      :current-selection-matrix="currentSelectionMatrix"
      @updated="() => loadSoaContent(true)"
      @close="showBatchEditForm = false"
      @remove="unselectItem"
    />
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
    <v-dialog v-model="showCollapsibleGroupForm" persistent max-width="1000px">
      <CollapsibleVisitGroupForm
        :open="showCollapsibleGroupForm"
        :visits="selectedVisits"
        @close="closeCollapsibleVisitGroupForm"
        @created="collapsibleVisitGroupCreated"
      />
    </v-dialog>
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
        @added="table.filterTable()"
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
    v-else
    class="mt-6 mx-auto"
    max-width="800px"
    type="table-heading, table-thead, table-tbody"
  />
</template>

<script setup>
import { computed, inject, ref, watch, onUpdated, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import CollapsibleVisitGroupForm from './CollapsibleVisitGroupForm.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import study from '@/api/study'
import StudyActivityScheduleBatchEditForm from './StudyActivityScheduleBatchEditForm.vue'
import StudyFootnoteTable from './StudyFootnoteTable.vue'
import studyEpochs from '@/api/studyEpochs'
import StudyFootnoteForm from '@/components/studies/StudyFootnoteForm.vue'
import dataFormating from '@/utils/dataFormating'
import _isEmpty from 'lodash/isEmpty'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useFootnotesStore } from '@/stores/studies-footnotes'
import { useSoaContentLoadingStore } from '@/stores/soa-content-loading'
import soaDownloads from '@/utils/soaDownloads'
import ProtocolFlowchart from './ProtocolFlowchart.vue'
import RemoveFootnoteForm from './RemoveFootnoteForm.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import StudyActivityEditForm from './StudyActivityEditForm.vue'
import StudyDraftedActivityEditForm from './StudyDraftedActivityEditForm.vue'
import StudyActivityForm from './StudyActivityForm.vue'
import libraries from '@/constants/libraries.js'
import { useDragAndDrop } from '@formkit/drag-and-drop/vue'

const [parent, soaRowsDrag] = useDragAndDrop([], {
  onDragend: (event) => {
    if (event.state.targetIndex !== event.state.initialIndex) {
      reorder(
        event.draggedNode.data.value.cells[0].refs[0].uid,
        event.state.targetIndex + 1 + sortAlignValue.value,
        event.draggedNode.data.value.cells[0].style
      )
    }
  },
})

const soaRows = computed(() => {
  return soaContent.value?.rows.slice(soaContent.value.num_header_rows) || []
})

const { t } = useI18n()
const eventBusEmit = inject('eventBusEmit')
const roles = inject('roles')
const studiesGeneralStore = useStudiesGeneralStore()
const footnotesStore = useFootnotesStore()
const soaContentLoadingStore = useSoaContentLoadingStore()
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
  redirectFootnote: {
    type: Object,
    default: undefined,
  },
})

const firstHeader = ref()
const secondHeader = ref()
const thirdHeader = ref()
const milestoneHeader = ref()
const firstCol = ref()
const secondCol = ref()
const table = ref()
const confirm = ref()
const tableContainer = ref()

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
const showRemoveFootnoteForm = ref(false)
const removeItemUid = ref('')
const actions = [
  {
    label: t('DetailedFlowchart.edit_activity'),
    icon: 'mdi-pencil-outline',
    condition: (item) =>
      item.row.cells[0].style === 'activity' &&
      !studiesGeneralStore.selectedStudyVersion,
    click: editStudyActivity,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('DetailedFlowchart.add_activity'),
    icon: 'mdi-plus-circle-outline',
    condition: (item) =>
      item.row.cells[0].style === 'activity' &&
      !studiesGeneralStore.selectedStudyVersion,
    click: addStudyActivity,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('DetailedFlowchart.exchange_activity'),
    icon: 'mdi-autorenew',
    condition: (item) =>
      item.row.cells[0].style === 'activity' &&
      !studiesGeneralStore.selectedStudyVersion,
    click: exchangeStudyActivity,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('DetailedFlowchart.reorder'),
    icon: 'mdi-sort',
    condition: (item) =>
      !studiesGeneralStore.selectedStudyVersion && item.row.order,
    click: initiateReorder,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('DetailedFlowchart.remove_activity'),
    icon: 'mdi-minus-circle-outline',
    condition: (item) =>
      item.row.cells[0].style === 'activity' &&
      !studiesGeneralStore.selectedStudyVersion,
    click: removeActivity,
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
const sortAlignValue = ref(0)

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

watch(
  () => props.redirectFootnote,
  (value) => {
    enableFootnoteMode(value)
  }
)
watch(
  () => props.update,
  () => {
    loadSoaContent()
  }
)
watch(
  () => '$route.params.footnote',
  (value) => {
    if (value && !_isEmpty(value)) {
      enableFootnoteMode(value)
    }
  }
)

onMounted(() => {
  loadSoaContent()
  onResize()
  fetchFootnotes()
  if (route.params.footnote && !_isEmpty(route.params.footnote)) {
    enableFootnoteMode(route.params.footnote)
  }
})

onUpdated(() => {
  observeWidth()
  if (!firstHeader.value) {
    return
  }
  firstHeaderHeight.value = firstHeader.value.clientHeight
  secondHeaderHeight.value = secondHeader.value.clientHeight
  thirdHeaderHeight.value = thirdHeader.value.clientHeight
  if (milestoneHeader.value) {
    milestoneHeaderHeight.value = milestoneHeader.value.clientHeight
  }
  firstColWidth.value = firstCol.value.clientWidth
  secondColWidth.value = secondCol.value.clientWidth
})

function initiateReorder(item) {
  let content = item.row.cells[0]
  content.order = item.row.order
  let index = item.index
  if (content.style === 'activity') {
    sortAlignValue.value = -3
  } else if (content.style === 'subGroup') {
    sortAlignValue.value = -2
  } else if (content.style === 'group') {
    sortAlignValue.value = -1
  }
  try {
    soaRowsDrag.value = []
    if (content.style === 'soaGroup') {
      soaRows.value.forEach((row) => {
        if (row.cells[0].style === content.style) {
          soaRowsDrag.value.push(row)
        }
      })
    } else {
      gatherReorderData(content, index)
    }
    sortMode.value = true
  } catch (error) {
    console.error(error)
  }
}

function getStopType(type) {
  switch (type) {
    case 'group':
      return 'soaGroup'
    case 'subGroup':
      return 'group'
    case 'activity':
      return 'subGroup'
  }
}

function getApiCallType(type) {
  switch (type) {
    case 'soaGroup':
      return 'study-soa-groups'
    case 'group':
      return 'study-activity-groups'
    case 'subGroup':
      return 'study-activity-subgroups'
    case 'activity':
      return 'study-activities'
  }
}

function gatherReorderData(content, index) {
  if (content.order !== 1) {
    for (let i = index; i > 0; i--) {
      if (
        soaRows.value[i].cells[0].style === content.style &&
        soaRows.value[i].order === 1
      ) {
        content = soaRows.value[i].cells[0]
        break
      }
    }
    try {
      index = soaRows.value.indexOf(
        soaRows.value.find(
          (item) => item?.cells[0]?.refs[0]?.uid === content.refs[0].uid
        )
      )
    } catch (error) {
      console.error(error)
    }
  }
  for (let i = index; i <= soaRows.value.length; i++) {
    if (soaRows.value[i]?.cells[0]?.style === content.style) {
      soaRowsDrag.value.push(soaRows.value[i])
    } else if (soaRows.value[i]?.cells[0]?.style === getStopType(content.style)) {
      break
    }
  }
  if (content.style !== 'soaGroup') {
    getParents(index, content.style)
  }
}

function getParents(index, type) {
  const parentsMatrix = ['soaGroup', 'group', 'subGroup']
  let currentParentIndex = 0
  if (type === 'activity') {
    currentParentIndex = 2
  } else if (type === 'subGroup') {
    currentParentIndex = 1
  }
  for (let i = index; i >= 0; i--) {
    if (soaRows.value[i].cells[0].style === parentsMatrix[currentParentIndex]) {
      const el = soaRows.value[i]
      el.noIcon = true
      soaRowsDrag.value.unshift(el)
      if (currentParentIndex === 0) {
        break
      }
      currentParentIndex = currentParentIndex - 1
    }
  }
}

function reorder(uid, newOrder, type) {
  study.reorderSoa(
    studiesGeneralStore.selectedStudy.uid,
    uid,
    newOrder,
    getApiCallType(type)
  )
}

function finishReordering() {
  // TODO Formkit drag-and-drop breaks with conditional rendering in table tbody.
  // To fix that we can move whole tbody of SoA table to external component.
  // That will be implemented under next SoA Feature rigth after this one.
  location.reload()
}

function observeWidth() {
  const resizeObserver = new ResizeObserver(function (el) {
    if (
      el[0].target.offsetWidth &&
      document.getElementById('bottomCard') &&
      document.getElementById('bottomCard').style
    ) {
      document.getElementById('bottomCard').style.left =
        el[0].target.offsetWidth + 'px'
    }
  })
  resizeObserver.observe(document.getElementById('sideBar'))
}

async function removeActivity(activity) {
  activity = activity.row.cells[0].refs[0]
  const options = { type: 'warning' }
  if (
    !(await confirm.value.open(
      t('DetailedFlowchart.remove_activity_msg'),
      options
    ))
  ) {
    return
  }
  loadingSoaContent.value = true
  study
    .deleteStudyActivity(studiesGeneralStore.selectedStudy.uid, activity.uid)
    .then(() => {
      eventBusEmit('notification', {
        type: 'success',
        msg: t('DetailedFlowchart.remove_activity_success'),
      })
      loadSoaContent(true)
    })
}

function addStudyActivity(item) {
  item = item.row.cells[0].refs[0]
  study
    .getStudyActivity(studiesGeneralStore.selectedStudy.uid, item.uid)
    .then((resp) => {
      flowchartActivityOrder.value = resp.data.order
      showActivityForm.value = true
    })
}

function exchangeStudyActivity(item) {
  item = item.row.cells[0].refs[0]
  selectedStudyActivity.value = item.uid
  activityExchangeMode.value = true
  showActivityForm.value = true
}

function closeActivityForm() {
  selectedStudyActivity.value = null
  activityExchangeMode.value = false
  flowchartActivityOrder.value = null
  showActivityForm.value = false
  loadSoaContent()
}

function onActivityExchanged() {
  showActivityForm.value = false
  activityExchangeMode.value = false
  loadSoaContent()
}

function editStudyActivity(item) {
  item = item.row.cells[0].refs[0]
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
  showActivityEditForm.value = false
  showDraftedActivityEditForm.value = false
  selectedStudyActivity.value = null
}

function openRemoveFootnoteForm(ele) {
  removeItemUid.value = ele.refs[0].uid
  showRemoveFootnoteForm.value = true
}

function closeRemoveFootnoteForm() {
  removeItemUid.value = null
  showRemoveFootnoteForm.value = false
  loadSoaContent(true)
}

function showSoaRow(index, row) {
  let key = `row-${index}`
  let result = true

  // prettier-ignore
  while (true) { // eslint-disable-line no-constant-condition
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
}

function getSoaRowType(row) {
  return row.cells[0].style
}

function getSoaRowClasses(row) {
  if (row.cells && row.cells.length) {
    if (row.cells[0].style === 'soaGroup') {
      return 'flowchart'
    }
    if (row.cells[0].style === 'group') {
      return 'group'
    }
    if (row.cells[0].style === 'subGroup') {
      return 'subgroup'
    }
  }
  return 'bg-white'
}

function getSoaFirstCellClasses(cell) {
  let result = 'sticky-column'
  if (cell.style === 'soaGroup' || cell.style === 'group') {
    result += ' text-strong'
  } else if (cell.style === 'subGroup') {
    result += ' subgroup'
  }
  return result
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
      if (row.cells[0].style === 'activity') {
        result.push(row.cells[0])
      } else {
        break
      }
    }
  }
  return result
}

function getElementFootnotesLetters(uid) {
  let footnotesLetters = ''
  footnotesStore.studyFootnotes.forEach((footnote) => {
    footnote.referenced_items.forEach((item) => {
      if (item.item_uid === uid) {
        footnotesLetters += dataFormating.footnoteSymbol(footnote.order)
      } else if (
        uid &&
        typeof uid !== 'string' &&
        uid.includes(item.item_uid)
      ) {
        footnotesLetters += dataFormating.footnoteSymbol(footnote.order)
      }
    })
  })
  return Array.from(new Set(footnotesLetters.split(''))).toString()
}

function enableFootnoteMode(footnote) {
  if (footnote) {
    activeFootnote.value = footnote
    elementsForFootnote.value.referenced_items = footnote.referenced_items
  }
  footnoteMode.value = true
}

function enableFootnoteModeWithElement(uid, type, name) {
  elementsForFootnote.value.referenced_items.push({
    item_uid: uid,
    item_type: type,
    item_name: name,
  })
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
  fetchFootnotes()
}

function addElementForFootnote(uid, type, name) {
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
}

function removeFootnote(uid) {
  const indexToRemove = elementsForFootnote.value.referenced_items.findIndex(
    (item) => item.item_uid === uid
  )
  if (indexToRemove !== -1) {
    elementsForFootnote.value.referenced_items.splice(indexToRemove, 1)
  }
}

function removeElementForFootnote(uid) {
  if (typeof uid !== 'string') {
    uid.forEach((u) => {
      removeFootnote(u)
    })
  } else {
    removeFootnote(uid)
  }
}

function saveElementsForFootnote() {
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
        eventBusEmit('notification', {
          msg: t('StudyFootnoteEditForm.update_success'),
        })
      })
  } else {
    showFootnoteForm.value = true
  }
}

function closeFootnoteForm() {
  showFootnoteForm.value = false
  disableFootnoteMode()
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

function fetchFootnotes() {
  const params = {
    page_number: 1,
    page_size: 0,
    total_count: true,
    studyUid: studiesGeneralStore.selectedStudy.uid,
  }
  footnotesStore.fetchStudyFootnotes(params)
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
  const currentValue = rowsDisplayState.value[rowKey].value
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

function toggleRowState(rowKey) {
  const currentValue = getCurrentDisplayValue(rowKey)
  rowsDisplayState.value[rowKey].value = !currentValue
}

function toggleAllRowState(value) {
  for (const key in rowsDisplayState.value) {
    rowsDisplayState.value[key].value = value
  }
}

async function toggleLevelDisplay(row) {
  const firstCell = row.cells[0]
  let action
  let field

  if (firstCell.style === 'activity') {
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
  payload[field] = row.hide
  await study[action](
    studiesGeneralStore.selectedStudy.uid,
    firstCell.refs[0].uid,
    payload
  )
  row.hide = !row.hide
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
        const scheduleUids = resp.data.map(
          (item) => item.content.study_activity_schedule_uid
        )
        currentSelectionMatrix.value[studyActivityUid][
          studyVisitCell.refs[0].uid
        ].uid = scheduleUids
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
      .then(() => {
        currentSelectionMatrix.value[studyActivityUid][
          studyVisitCell.refs[0].uid
        ].uid = null
      })
  }
}

function updateSchedule(value, studyActivityUid, studyVisitCell) {
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
      })
  }
}

async function openBatchEditForm() {
  if (!studyActivitySelection.value.length) {
    eventBusEmit('notification', {
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
  if (!studyActivitySelection.value.length) {
    eventBusEmit('notification', {
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
      eventBusEmit('notification', {
        msg: t('DetailedFlowchart.remove_success', {
          activities: studyActivitySelection.value.length,
        }),
      })
      studyActivitySelection.value = []
      loadSoaContent(true)
    })
}

function toggleActivitySelectionDisplay(value) {
  if (!studyActivitySelection.value.length) {
    eventBusEmit('notification', {
      type: 'warning',
      msg: t('DetailedFlowchart.batch_edit_no_selection'),
    })
    return
  }
  const data = []
  for (const cell of studyActivitySelection.value) {
    data.push({
      method: 'PATCH',
      content: {
        study_activity_uid: cell.refs[0].uid,
        content: {
          show_activity_in_protocol_flowchart: value,
        },
      },
    })
  }
  study
    .studyActivityBatchOperations(studiesGeneralStore.selectedStudy.uid, data)
    .then(() => {
      eventBusEmit('notification', {
        type: 'success',
        msg: t('DetailedFlowchart.update_success'),
      })
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
      studyActivitySelection.value.splice(index, 1)
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

  if (!keepDisplayState) {
    rowsDisplayState.value = {}
    expandAllRows.value = false
  }
  for (const [index, row] of soaRows.value.entries()) {
    const key = `row-${index}`
    if (row.cells && row.cells.length) {
      if (row.cells[0].style === 'soaGroup') {
        if (!keepDisplayState) {
          rowsDisplayState.value[key] = { value: false }
        }
        currentGroup = null
        currentSubGroup = null
        currentSoaGroup = index
      } else if (row.cells[0].style === 'group') {
        if (!keepDisplayState) {
          rowsDisplayState.value[key] = {
            value: false,
            parent: currentSoaGroup,
          }
        }
        currentSubGroup = null
        currentGroup = index
      } else if (row.cells[0].style === 'subGroup') {
        if (!keepDisplayState) {
          rowsDisplayState.value[key] = {
            value: false,
            parent: currentGroup,
          }
        }
        currentSubGroup = index
      } else if (row.cells[0].style === 'activity') {
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
  loadingSoaContent.value = false
  soaContentLoadingStore.changeLoadingState()
}

function onResize() {
  tableHeight.value =
    window.innerHeight - tableContainer.value.getBoundingClientRect().y - 100
}

function groupSelectedVisits() {
  const visitUids = selectedVisitIndexes.value.map(
    (cell) => soaVisitRow.value[cell].refs[0].uid
  )
  studyEpochs
    .createCollapsibleVisitGroup(
      studiesGeneralStore.selectedStudy.uid,
      visitUids
    )
    .then(() => {
      collapsibleVisitGroupCreated()
    })
    .catch((err) => {
      if (err.response.status === 400) {
        if (err.response.data.type !== 'BusinessLogicException') {
          showCollapsibleGroupForm.value = true
        } else {
          eventBusEmit('notification', {
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
  eventBusEmit('notification', {
    msg: t('CollapsibleVisitGroupForm.creation_success'),
  })
  loadSoaContent(true)
  selectedVisitIndexes.value = []
}

async function deleteVisitGroup(groupName) {
  const message = t('DetailedFlowchart.confirm_group_deletion', {
    group: groupName,
  })
  const options = { type: 'warning' }
  if (!(await confirm.value.open(message, options))) {
    return
  }
  await studyEpochs.deleteCollapsibleVisitGroup(
    studiesGeneralStore.selectedStudy.uid,
    groupName
  )
  loadSoaContent(true)
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

function multipleConsecutiveVisitsSelected() {
  // Check if more than one visit is selected,
  // and that they are in consecutive order without gaps.
  if (selectedVisitIndexes.value.length > 1) {
    const minIndex = selectedVisitIndexes.value.reduce((a, b) => Math.min(a, b))
    const maxIndex = selectedVisitIndexes.value.reduce((a, b) => Math.max(a, b))
    return selectedVisitIndexes.value.length - 1 === maxIndex - minIndex
  }
  return false
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
}
.group {
  background-color: rgb(var(--v-theme-nnSeaBlue200));
}
.subgroup {
  background-color: rgb(var(--v-theme-nnSeaBlue100));
  font-weight: 600;
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
</style>
