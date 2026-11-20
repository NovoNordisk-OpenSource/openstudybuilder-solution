<template>
  <div>
    <div class="position-relative d-flex justify-center align-center mt-6">
      <v-btn-toggle
        :model-value="selectedViewType"
        :disabled="savingVisit"
        mandatory
        density="compact"
        color="nnBaseBlue"
        divided
        variant="outlined"
        class="layoutSelector text-body-medium"
        data-cy="visit-view-type-toggle"
        @update:model-value="onViewTypeChange"
      >
        <v-btn
          v-for="tab in viewTypes"
          :key="tab.value"
          :value="tab.value"
          :data-cy="`visit-view-type-${tab.value}`"
        >
          <v-icon v-if="tab.icon" :color="tab.color" class="mr-2">
            {{ tab.icon }}
          </v-icon>
          {{ tab.label }}
        </v-btn>
      </v-btn-toggle>

      <div class="position-absolute right-0 d-flex">
        <v-btn
          v-if="selectedViewType === 'timeline'"
          class="mr-4"
          variant="outlined"
          color="nnBaseBlue"
          icon
          size="small"
          data-cy="add-visit-timeline"
          :disabled="
            !accessGuard.checkPermission($roles.STUDY_WRITE) ||
            studiesGeneralStore.selectedStudyVersion !== null ||
            !epochsStore.visitModeKnown
          "
          @click.stop="timelineRef.openNewVisitForm()"
        >
          <v-icon>mdi-plus</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('StudyVisitTable.add_visit') }}
          </v-tooltip>
        </v-btn>
        <v-btn
          v-if="selectedViewType === 'timeline'"
          class="mr-4"
          variant="outlined"
          color="nnBaseBlue"
          icon
          size="small"
          data-cy="duplicate-visit-timeline"
          :disabled="
            !accessGuard.checkPermission($roles.STUDY_WRITE) ||
            studiesGeneralStore.selectedStudyVersion !== null ||
            !epochsStore.visitModeKnown ||
            !canDuplicateVisit(timelineRef?.selectedVisit)
          "
          @click.stop="openDuplicateForm(timelineRef.selectedVisit)"
        >
          <v-icon>mdi-plus-box-multiple-outline</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('StudyVisitTable.duplicate') }}
          </v-tooltip>
        </v-btn>
        <v-btn
          v-if="selectedViewType === 'timeline'"
          class="mr-4"
          variant="outlined"
          color="nnBaseBlue"
          icon
          size="small"
          data-cy="delete-visit-timeline"
          :disabled="
            !accessGuard.checkPermission($roles.STUDY_WRITE) ||
            studiesGeneralStore.selectedStudyVersion !== null ||
            !epochsStore.visitModeKnown ||
            !timelineRef?.selectedVisit
          "
          @click.stop="deleteTimelineVisit(timelineRef.selectedVisit)"
        >
          <v-icon>mdi-delete-outline</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('_global.delete') }}
          </v-tooltip>
        </v-btn>

        <v-btn
          class="mr-4"
          variant="outlined"
          color="nnBaseBlue"
          icon
          size="small"
          data-cy="study-visits-settings"
          :disabled="!epochsStore.visitModeKnown"
          @click.stop="openSettings"
        >
          <v-icon>mdi-cog-outline</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('StudyVisitTable.settings') }}
          </v-tooltip>
        </v-btn>
      </div>
    </div>
    <StudyVisitsTimeline
      v-if="selectedViewType === 'timeline'"
      ref="timelineRef"
      :visit-types="visitTypes"
      @duplicate-request="openDuplicateForm"
      @delete-request="deleteTimelineVisit"
    />
    <NNTable
      v-if="selectedViewType === 'table'"
      ref="tableRef"
      :table-id="
        editMode ? 'studies-visits-table-edit' : 'studies-visits-table'
      "
      :headers="headers"
      :default-headers="defaultColumns"
      :items="studyVisits"
      item-value="uid"
      class="mt-6"
      :table-height="tableHeight"
      :column-data-resource="`studies/${studiesGeneralStore.selectedStudy.uid}/study-visits`"
      :items-length="totalVisits"
      fixed-header
      :loading="tableLoading"
      :history-config="{
        dataFetcher: fetchVisitsHistory,
        title: $t('StudyVisitTable.global_history_title'),
      }"
      :export-config="{ objectLabel: 'StudyVisits', dataUrl: exportDataUrl }"
      @filter="fetchStudyVisits"
    >
      <template #headerCenter>
        <v-btn
          v-if="editMode"
          variant="outlined"
          color="nnBaseBlue"
          rounded
          :title="$t('_global.cancel')"
          data-cy="close-edit-mode"
          :disabled="savingVisit"
          @click.stop="closeEditMode"
        >
          {{ $t('StudyVisitTable.close_edit_mode') }}
        </v-btn>
      </template>
      <template #actions>
        <v-progress-circular v-show="loading" indeterminate color="primary" />
        <v-btn
          v-if="editMode"
          v-show="!loading"
          class="ml-2"
          icon
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          :disabled="
            !accessGuard.checkPermission($roles.STUDY_WRITE) ||
            studiesGeneralStore.selectedStudyVersion !== null ||
            timingEditVisit !== null
          "
          data-cy="add-visit"
          @click.stop="addNewVisitRow"
        >
          <v-icon>mdi-plus</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('StudyVisitTable.add_visit') }}
          </v-tooltip>
        </v-btn>
        <v-btn
          v-if="!editMode && !loading"
          class="ml-2"
          icon
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          data-cy="edit-study-visits"
          :disabled="
            !accessGuard.checkPermission($roles.STUDY_WRITE) ||
            studiesGeneralStore.selectedStudyVersion !== null ||
            !epochsStore.visitModeKnown
          "
          @click.stop="openEditMode"
        >
          <v-icon>mdi-pencil-outline</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('_global.edit_in_table') }}
          </v-tooltip>
        </v-btn>
        <v-progress-circular
          v-show="loading"
          indeterminate
          color="primary"
          class="ml-2"
        />
      </template>
      <template #[`item.is_soa_milestone`]="{ item }">
        <div
          v-if="
            editMode &&
            ![
              visitConstants.CLASS_NON_VISIT,
              visitConstants.CLASS_UNSCHEDULED_VISIT,
            ].includes(item.visit_class)
          "
        >
          <v-checkbox
            v-model="item.is_soa_milestone"
            :disabled="savingVisit"
            data-cy="is-soa-milestone-checkbox"
            @update:model-value="markEdited(item)"
          />
        </div>
        <div v-else>
          {{ $filters.yesno(item.is_soa_milestone) }}
        </div>
      </template>
      <template #[`item.visit_name`]="{ item }">
        <v-text-field
          v-if="editMode && isManuallyDefined(item)"
          v-model="item.visit_name"
          class="cellWidth"
          :loading="previewLoadingVisits.has(item)"
          :disabled="savingVisit"
          data-cy="visit-name"
          @input="markEdited(item)"
          @blur="refreshVisitPreview(item)"
        />
        <div v-else-if="editMode">
          {{ item.visit_name }}
        </div>
        <router-link
          v-else
          :to="{
            name: 'StudyVisitOverview',
            params: {
              study_id: studiesGeneralStore.selectedStudy.uid,
              id: item.uid,
            },
          }"
        >
          {{ item.visit_name }}
        </router-link>
      </template>
      <template #[`item.visit_short_name`]="{ item }">
        <v-text-field
          v-if="editMode && isManuallyDefined(item)"
          v-model="item.visit_short_name"
          class="cellWidth"
          :loading="previewLoadingVisits.has(item)"
          :disabled="savingVisit"
          data-cy="visit-short-name"
          @input="markEdited(item)"
          @blur="refreshVisitPreview(item)"
        />
        <div v-else>
          {{ item.visit_short_name }}
        </div>
      </template>
      <template #[`item.unique_visit_number`]="{ item }">
        <v-text-field
          v-if="editMode"
          v-model="item.unique_visit_number"
          type="number"
          class="cellWidth"
          :loading="previewLoadingVisits.has(item)"
          :disabled="savingVisit || !isManuallyDefined(item)"
          data-cy="visit-unique-number"
          @input="markEdited(item)"
          @blur="refreshVisitPreview(item)"
        />
        <div v-else>
          {{ item.unique_visit_number }}
        </div>
      </template>
      <template #[`item.study_epoch.sponsor_preferred_name`]="{ item }">
        <div v-if="editMode">
          <v-select
            v-model="item.study_epoch_uid"
            item-title="epoch_name"
            item-value="uid"
            :items="getFilteredPeriods(item)"
            class="epochCellWidth"
            :disabled="savingVisit"
            data-cy="study-period"
            @update:model-value="(markEdited(item), refreshVisitPreview(item))"
          />
        </div>
        <CTTermDisplay v-else :term="item.study_epoch || {}" />
      </template>
      <template #[`item.visit_type.sponsor_preferred_name`]="{ item }">
        <div v-if="editMode">
          <v-select
            :model-value="item.visit_type?.term_uid ?? null"
            class="cellWidth"
            :items="visitTypes"
            item-title="sponsor_preferred_name"
            item-value="term_uid"
            :disabled="savingVisit"
            data-cy="visit-type"
            @update:model-value="
              (value) => updateNestedTermUid(item, 'visit_type', value)
            "
          />
        </div>
        <CTTermDisplay v-else :term="item.visit_type" />
      </template>
      <template #[`item.visit_class`]="{ item }">
        <div v-if="editMode">
          <v-select
            v-model="item.visit_class"
            :items="visitClasses"
            item-title="label"
            item-value="value"
            class="cellWidth"
            :disabled="savingVisit || isTimingLocked(item)"
            data-cy="visit-class"
            @update:model-value="
              (markTimingEdited(item),
              (item.study_epoch_uid = null),
              refreshVisitPreview(item))
            "
          />
        </div>
        <div v-else>
          {{ getVisitClassLabel(item.visit_class) }}
        </div>
      </template>
      <template #[`item.visit_subclass`]="{ item }">
        <div v-if="editMode">
          <v-select
            v-model="item.visit_subclass"
            :items="visitSubClasses"
            item-title="label"
            item-value="value"
            class="cellWidth"
            :disabled="savingVisit || isTimingLocked(item)"
            data-cy="visit-subclass"
            @update:model-value="onVisitSubclassChange(item)"
          />
        </div>
        <div v-else>
          {{ getVisitSubClassLabel(item.visit_subclass) }}
        </div>
      </template>
      <template #[`item.repeating_frequency_name`]="{ item }">
        <div v-if="editMode">
          <v-select
            v-model="item.repeating_frequency_uid"
            :items="frequencies"
            item-title="sponsor_preferred_name"
            item-value="term_uid"
            :disabled="
              savingVisit ||
              item.visit_subclass !== visitConstants.SUBCLASS_REPEATING_VISIT
            "
            data-cy="repeating-frequency"
            @update:model-value="markEdited(item)"
          />
        </div>
        <div v-else>
          <CTTermDisplay :term="item.repeating_frequency" />
        </div>
      </template>
      <template #[`item.visit_window`]="{ item }">
        <div
          v-if="
            editMode &&
            [
              visitConstants.CLASS_MANUALLY_DEFINED_VISIT,
              visitConstants.CLASS_SINGLE_VISIT,
            ].indexOf(item.visit_class) !== -1
          "
        >
          <v-row class="wideCellWidth">
            <v-text-field
              v-model="item.min_visit_window_value"
              :disabled="savingVisit"
              data-cy="visit-window-min"
              @input="markEdited(item)"
            />
            <v-text-field
              v-model="item.max_visit_window_value"
              :disabled="savingVisit"
              data-cy="visit-window-max"
              @input="markEdited(item)"
            />
            <v-select
              v-model="item.visit_window_unit_uid"
              :items="epochsStore.studyTimeUnits"
              item-title="name"
              item-value="uid"
              class="cellWidth"
              :disabled="savingVisit"
              data-cy="visit-window-unit"
              @update:model-value="markEdited(item)"
            />
          </v-row>
        </div>
        <template
          v-else-if="
            item.min_visit_window_value !== null &&
            item.max_visit_window_value !== null
          "
        >
          {{ item.min_visit_window_value }} / {{ item.max_visit_window_value }}
          {{ getUnitName(item.visit_window_unit_uid) }}
        </template>
      </template>
      <template #[`item.min_visit_window_value`]="{ item }">
        <v-text-field
          v-if="
            editMode &&
            [
              visitConstants.CLASS_MANUALLY_DEFINED_VISIT,
              visitConstants.CLASS_SINGLE_VISIT,
            ].indexOf(item.visit_class) !== -1
          "
          v-model="item.min_visit_window_value"
          class="cellWidth"
          :disabled="savingVisit"
          data-cy="visit-window-min"
          @input="markEdited(item)"
        />
        <div v-else>
          {{ item.min_visit_window_value }}
        </div>
      </template>
      <template #[`item.max_visit_window_value`]="{ item }">
        <v-text-field
          v-if="
            editMode &&
            [
              visitConstants.CLASS_MANUALLY_DEFINED_VISIT,
              visitConstants.CLASS_SINGLE_VISIT,
            ].indexOf(item.visit_class) !== -1
          "
          v-model="item.max_visit_window_value"
          class="cellWidth"
          :disabled="savingVisit"
          data-cy="visit-window-max"
          @input="markEdited(item)"
        />
        <div v-else>
          {{ item.max_visit_window_value }}
        </div>
      </template>
      <template #[`item.visit_window_unit_uid`]="{ item }">
        <v-select
          v-if="
            editMode &&
            [
              visitConstants.CLASS_MANUALLY_DEFINED_VISIT,
              visitConstants.CLASS_SINGLE_VISIT,
            ].indexOf(item.visit_class) !== -1
          "
          v-model="item.visit_window_unit_uid"
          :items="epochsStore.studyTimeUnits"
          item-title="name"
          item-value="uid"
          class="cellWidth"
          :disabled="savingVisit"
          data-cy="visit-window-unit"
          @update:model-value="markEdited(item)"
        />
        <div v-else>
          {{ getUnitName(item.visit_window_unit_uid) }}
        </div>
      </template>
      <template #[`item.show_visit`]="{ item }">
        <div v-if="editMode">
          <v-checkbox
            v-model="item.show_visit"
            :disabled="savingVisit"
            data-cy="show-visit-switch"
            @update:model-value="markEdited(item)"
          />
        </div>
        <div v-else>
          {{ $filters.yesno(item.show_visit) }}
        </div>
      </template>
      <template #[`item.epoch_allocation.sponsor_preferred_name`]="{ item }">
        <div v-if="editMode">
          <v-select
            :model-value="item.epoch_allocation?.term_uid ?? null"
            data-cy="epoch-allocation-rule"
            :items="epochAllocations"
            item-title="sponsor_preferred_name"
            item-value="term_uid"
            class="cellWidth"
            :disabled="savingVisit"
            @update:model-value="
              (value) => updateNestedTermUid(item, 'epoch_allocation', value)
            "
          />
        </div>
        <div v-else>
          {{ item.epoch_allocation?.sponsor_preferred_name }}
        </div>
      </template>
      <template #[`item.is_global_anchor_visit`]="{ item }">
        {{ $filters.yesno(item.is_global_anchor_visit) }}
      </template>
      <template #[`item.anchor_visit_in_group`]="{ item }">
        {{
          item.visit_subclass ===
          visitConstants.SUBCLASS_ANCHOR_VISIT_IN_GROUP_OF_SUBV
            ? 'Yes'
            : 'No'
        }}
      </template>
      <template #[`item.visit_subname`]="{ item }">
        {{
          item.visit_subclass ===
          visitConstants.SUBCLASS_ANCHOR_VISIT_IN_GROUP_OF_SUBV
            ? item.visit_name
            : ''
        }}
      </template>
      <template #[`item.time_value`]="{ item }">
        <div
          v-if="
            editMode &&
            [
              visitConstants.CLASS_MANUALLY_DEFINED_VISIT,
              visitConstants.CLASS_SINGLE_VISIT,
            ].indexOf(item.visit_class) !== -1
          "
        >
          <v-text-field
            v-model="item.time_value"
            class="cellWidth"
            :disabled="savingVisit || isTimingLocked(item)"
            data-cy="timing"
            @input="markTimingEdited(item)"
            @blur="refreshVisitPreview(item)"
          />
        </div>
        <div v-else>
          {{ item.time_value }} {{ getUnitName(item.time_unit_uid) }}
        </div>
      </template>
      <template #[`item.time_unit_uid`]="{ item }">
        <div
          v-if="
            editMode &&
            [
              visitConstants.CLASS_MANUALLY_DEFINED_VISIT,
              visitConstants.CLASS_SINGLE_VISIT,
            ].indexOf(item.visit_class) !== -1
          "
        >
          <v-select
            v-model="item.time_unit_uid"
            :items="epochsStore.studyTimeUnits"
            item-title="name"
            item-value="uid"
            class="cellWidth"
            :disabled="savingVisit || isTimingLocked(item)"
            data-cy="time-unit"
            @update:model-value="
              (markTimingEdited(item), refreshVisitPreview(item))
            "
          />
        </div>
        <div v-else>
          {{ getUnitName(item.time_unit_uid) }}
        </div>
      </template>
      <template #[`item.visit_contact_mode.sponsor_preferred_name`]="{ item }">
        <div v-if="editMode">
          <v-select
            :model-value="item.visit_contact_mode?.term_uid ?? null"
            class="cellWidth"
            :items="contactModes"
            item-title="sponsor_preferred_name"
            item-value="term_uid"
            :disabled="savingVisit"
            data-cy="contact-mode"
            @update:model-value="
              (value) => updateNestedTermUid(item, 'visit_contact_mode', value)
            "
          />
        </div>
        <CTTermDisplay v-else :term="item.visit_contact_mode || {}" />
      </template>
      <template #[`item.time_reference_name`]="{ item }">
        <div
          v-if="
            editMode &&
            [
              visitConstants.CLASS_MANUALLY_DEFINED_VISIT,
              visitConstants.CLASS_SINGLE_VISIT,
            ].indexOf(item.visit_class) !== -1
          "
        >
          <v-select
            v-if="
              item.visit_subclass !==
              visitConstants.SUBCLASS_ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV
            "
            :model-value="item.time_reference?.term_uid ?? null"
            class="cellWidth"
            :items="timeReferences"
            item-title="sponsor_preferred_name"
            item-value="term_uid"
            :disabled="
              savingVisit || isTimingLocked(item) || item.is_global_anchor_visit
            "
            data-cy="time-reference"
            @update:model-value="
              (value) => updateNestedTermUid(item, 'time_reference', value)
            "
          />
          <v-select
            v-else
            v-model="item.visit_sublabel_reference"
            class="cellWidth"
            :items="anchorVisits"
            item-title="visit_name"
            item-value="uid"
            :disabled="savingVisit || isTimingLocked(item)"
            data-cy="visit-group"
            @update:model-value="setVisitGroup(item)"
          />
        </div>
        <div
          v-else-if="
            item.visit_subclass ===
            visitConstants.SUBCLASS_ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV
          "
        >
          {{ item.visit_subname }}
        </div>
        <div v-else>
          {{ item.time_reference?.sponsor_preferred_name }}
        </div>
      </template>
      <template #[`item.description`]="{ item }">
        <div v-if="editMode">
          <v-row>
            <v-text-field
              v-model="item.description"
              class="cellWidth"
              :disabled="savingVisit"
              data-cy="visit-description"
              @input="markEdited(item)"
            />
          </v-row>
        </div>
        <div v-else>
          {{ item.description }}
        </div>
      </template>
      <template #[`item.start_rule`]="{ item }">
        <div v-if="editMode">
          <v-row>
            <v-text-field
              v-model="item.start_rule"
              class="cellWidth"
              :disabled="savingVisit"
              data-cy="visit-start-rule"
              @input="markEdited(item)"
            />
          </v-row>
        </div>
        <div v-else>
          {{ item.start_rule }}
        </div>
      </template>
      <template #[`item.end_rule`]="{ item }">
        <div v-if="editMode">
          <v-row>
            <v-text-field
              v-model="item.end_rule"
              class="cellWidth"
              :disabled="savingVisit"
              data-cy="visit-end-rule"
              @input="markEdited(item)"
            />
          </v-row>
        </div>
        <div v-else>
          {{ item.end_rule }}
        </div>
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
      <template #[`item.actions`]="{ item }">
        <ActionsMenu
          v-if="
            editedVisits.size === 0 &&
            studiesGeneralStore.selectedStudyVersion === null
          "
          :actions="actions"
          :item="item"
        />
      </template>
    </NNTable>
    <StudyVisitsDuplicateForm
      :open="duplicateForm"
      :study-visit="selectedStudyVisit"
      @close="closeDuplicateForm"
    />
    <v-dialog
      v-model="showVisitHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeVisitHistory"
    >
      <HistoryTable
        :title="studyVisitHistoryTitle"
        :headers="headers"
        :items="visitHistoryItems"
        :items-total="visitHistoryItems.length"
        @close="closeVisitHistory"
      />
    </v-dialog>
    <StudyVisitsSettingsDialog
      :open="showSettings"
      :manual-visit-mode="epochsStore.manualVisitMode"
      @close="closeSettings"
    />
    <ConfirmDialog ref="confirmRef" :text-cols="6" :action-cols="5" />
    <StudyVisitUnsavedBar
      v-if="selectedViewType === 'table'"
      :show="hasUnsavedEdits"
      :saving="savingVisit"
      :hint="
        timingEditVisit ? $t('StudyVisitTable.timing_single_visit_hint') : ''
      "
      @discard="cancelVisitEditing"
      @save="saveVisits"
    />
  </div>
</template>

<script setup>
import terms from '@/api/controlledTerminology/terms'
import codelists from '@/api/controlledTerminology/terms'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StudyVisitsTimeline from './StudyVisitsTimeline.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import CTTermDisplay from '@/components/tools/CTTermDisplay.vue'
import visitConstants from '@/constants/visits'
import filteringParameters from '@/utils/filteringParameters'
import StudyVisitsDuplicateForm from './StudyVisitsDuplicateForm.vue'
import studyEpochsApi from '@/api/studyEpochs'
import dataFormating from '@/utils/dataFormating'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import StudyVisitsSettingsDialog from './StudyVisitsSettingsDialog.vue'
import StudyVisitUnsavedBar from './StudyVisitUnsavedBar.vue'
import { useAccessGuard } from '@/composables/accessGuard'
import { useVisitTimeReferenceTerms } from '@/composables/visitTimeReferenceTerms'
import { useVisitTypeTerms } from '@/composables/visitTypeTerms'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useEpochsStore } from '@/stores/studies-epochs'
import {
  inject,
  ref,
  reactive,
  shallowRef,
  computed,
  onMounted,
  toRaw,
  watch,
} from 'vue'
import { useI18n } from 'vue-i18n'

const notificationHub = inject('notificationHub')
const roles = inject('roles')
const { t } = useI18n()
const epochsStore = useEpochsStore()
const accessGuard = useAccessGuard()
const studiesGeneralStore = useStudiesGeneralStore()
const {
  contactModes,
  timeReferences,
  anchorVisitInGroupTermUid,
  fetchVisitTimeReferenceTerms,
} = useVisitTimeReferenceTerms()
const tableRef = ref()
const confirmRef = ref()
const selectedViewType = ref('timeline')
const viewTypes = [
  {
    label: t('StudyVisitTable.timeline_view'),
    value: 'timeline',
    icon: 'mdi-chart-timeline-variant',
  },
  {
    label: t('StudyVisitTable.table_view'),
    value: 'table',
    icon: 'mdi-table',
  },
]

// Switching view unmounts the current one, so pending edits are confirmed first
async function onViewTypeChange(value) {
  if (value === selectedViewType.value) {
    return
  }
  if (selectedViewType.value === 'timeline') {
    if (
      timelineRef.value &&
      !(await timelineRef.value.confirmDiscardChanges())
    ) {
      return
    }
  } else if (editMode.value) {
    if (
      hasUnsavedEdits.value &&
      !(await confirmRef.value.open(t('_global.cancel_changes'), {
        type: 'warning',
        cancelLabel: t('_global.cancel'),
        agreeLabel: t('_global.continue'),
      }))
    ) {
      return
    }
    closeEditMode()
  }
  selectedViewType.value = value
}

const actions = ref([
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'delete') &&
      !editMode.value,
    click: deleteVisit,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('StudyVisitTable.duplicate'),
    icon: 'mdi-plus-box-multiple-outline',
    iconColor: 'primary',
    condition: (item) => epochsStore.visitModeKnown && canDuplicateVisit(item),
    click: openDuplicateForm,
    accessRole: roles.STUDY_WRITE,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    condition: () => !editMode.value,
    click: openVisitHistory,
  },
])
const headers = ref([
  { title: '', key: 'actions', width: '1%' },
  {
    title: t('StudyVisitForm.visit_short_name'),
    key: 'visit_short_name',
    fixed: true,
  },
  { title: t('StudyVisitForm.visit_name'), key: 'visit_name' },
  {
    title: t('StudyVisitForm.study_epoch'),
    key: 'study_epoch.sponsor_preferred_name',
  },
  {
    title: t('StudyVisitForm.visit_type'),
    key: 'visit_type.sponsor_preferred_name',
  },
  { title: t('StudyVisitForm.soa_milestone'), key: 'is_soa_milestone' },
  { title: t('StudyVisitForm.visit_class'), key: 'visit_class' },
  { title: t('StudyVisitForm.visit_sub_class'), key: 'visit_subclass' },
  {
    title: t('StudyVisitForm.time_reference'),
    key: 'time_reference.sponsor_preferred_name',
  },
  {
    title: t('StudyVisitForm.repeating_frequency'),
    key: 'repeating_frequency_name',
  },
  {
    title: t('StudyVisitForm.anchor_visit_in_group'),
    key: 'anchor_visit_in_group',
  },
  { title: t('StudyVisitForm.visit_group'), key: 'visit_subname' },
  {
    title: t('StudyVisitForm.global_anchor_visit'),
    key: 'is_global_anchor_visit',
  },
  {
    title: t('StudyVisitForm.contact_mode'),
    key: 'visit_contact_mode.sponsor_preferred_name',
  },
  { title: t('StudyVisitForm.time_value'), key: 'time_value' },
  {
    title: t('StudyVisitForm.unique_visit_number'),
    key: 'unique_visit_number',
  },
  {
    title: t('StudyVisitForm.study_duration_days'),
    key: 'study_duration_days_label',
  },
  {
    title: t('StudyVisitForm.study_duration_weeks'),
    key: 'study_duration_weeks_label',
  },
  { title: t('StudyVisitForm.visit_window'), key: 'visit_window' },
  {
    title: t('StudyVisitForm.collapsible_visit'),
    key: 'consecutive_visit_group',
  },
  { title: t('StudyVisitForm.show_visit'), key: 'show_visit' },
  { title: t('StudyVisitForm.visit_description'), key: 'description' },
  {
    title: t('StudyVisitForm.epoch_allocation'),
    key: 'epoch_allocation.sponsor_preferred_name',
  },
  { title: t('StudyVisitForm.visit_start_rule'), key: 'start_rule' },
  { title: t('StudyVisitForm.visit_stop_rule'), key: 'end_rule' },
  { title: t('StudyVisitForm.study_day_label'), key: 'study_day_label' },
  { title: t('StudyVisitForm.study_week_label'), key: 'study_week_label' },
  { title: t('StudyVisitForm.week_in_study'), key: 'week_in_study_label' },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('StudyVisitForm.modified_user'), key: 'author_username' },
])
const defaultColumns = ref([
  { title: '', key: 'actions', width: '1%' },
  {
    title: t('StudyVisitForm.visit_short_name'),
    key: 'visit_short_name',
    fixed: true,
  },
  { title: t('StudyVisitForm.visit_name'), key: 'visit_name' },
  {
    title: t('StudyVisitForm.study_epoch'),
    key: 'study_epoch.sponsor_preferred_name',
  },
  {
    title: t('StudyVisitForm.visit_type'),
    key: 'visit_type.sponsor_preferred_name',
  },
  { title: t('StudyVisitForm.soa_milestone'), key: 'is_soa_milestone' },
  { title: t('StudyVisitForm.visit_class'), key: 'visit_class' },
  { title: t('StudyVisitForm.visit_sub_class'), key: 'visit_subclass' },
  {
    title: t('StudyVisitForm.time_reference'),
    key: 'time_reference.sponsor_preferred_name',
  },
  {
    title: t('StudyVisitForm.repeating_frequency'),
    key: 'repeating_frequency_name',
  },
  {
    title: t('StudyVisitForm.anchor_visit_in_group'),
    key: 'anchor_visit_in_group',
  },
  { title: t('StudyVisitForm.visit_group'), key: 'visit_subname' },
  {
    title: t('StudyVisitForm.global_anchor_visit'),
    key: 'is_global_anchor_visit',
  },
  {
    title: t('StudyVisitForm.contact_mode'),
    key: 'visit_contact_mode.sponsor_preferred_name',
  },
  { title: t('StudyVisitForm.time_value'), key: 'time_value' },
  {
    title: t('StudyVisitForm.unique_visit_number'),
    key: 'unique_visit_number',
  },
  {
    title: t('StudyVisitForm.study_duration_days'),
    key: 'study_duration_days_label',
  },
  {
    title: t('StudyVisitForm.study_duration_weeks'),
    key: 'study_duration_weeks_label',
  },
  { title: t('StudyVisitForm.visit_window'), key: 'visit_window' },
  {
    title: t('StudyVisitForm.collapsible_visit'),
    key: 'consecutive_visit_group',
  },
  { title: t('StudyVisitForm.show_visit'), key: 'show_visit' },
  { title: t('StudyVisitForm.visit_description'), key: 'description' },
  {
    title: t('StudyVisitForm.epoch_allocation'),
    key: 'epoch_allocation.sponsor_preferred_name',
  },
  { title: t('StudyVisitForm.visit_start_rule'), key: 'start_rule' },
  { title: t('StudyVisitForm.visit_stop_rule'), key: 'end_rule' },
  { title: t('StudyVisitForm.study_day_label'), key: 'study_day_label' },
  { title: t('StudyVisitForm.study_week_label'), key: 'study_week_label' },
  { title: t('StudyVisitForm.week_in_study'), key: 'week_in_study_label' },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('StudyVisitForm.modified_user'), key: 'author_username' },
])
const editHeaders = ref([
  { title: '', key: 'actions', width: '1%' },
  {
    title: t('StudyVisitForm.visit_short_name'),
    key: 'visit_short_name',
    fixed: true,
  },
  { title: t('StudyVisitForm.visit_name'), key: 'visit_name' },
  {
    title: t('StudyVisitForm.visit_type'),
    key: 'visit_type.sponsor_preferred_name',
  },
  { title: t('StudyVisitForm.soa_milestone'), key: 'is_soa_milestone' },
  { title: t('StudyVisitForm.visit_class'), key: 'visit_class' },
  {
    title: t('StudyVisitForm.contact_mode'),
    key: 'visit_contact_mode.sponsor_preferred_name',
  },
  {
    title: t('StudyVisitForm.time_reference'),
    key: 'time_reference_name',
  },
  { title: t('StudyVisitForm.time_value'), key: 'time_value' },
  { title: t('StudyVisitForm.time_unit'), key: 'time_unit_uid' },
  { title: t('StudyVisitForm.study_day_label'), key: 'study_day_label' },
  { title: t('StudyVisitForm.study_week_label'), key: 'study_week_label' },
  { title: t('StudyVisitForm.visit_win_min'), key: 'min_visit_window_value' },
  { title: t('StudyVisitForm.visit_win_max'), key: 'max_visit_window_value' },
  { title: t('StudyVisitForm.visit_win_unit'), key: 'visit_window_unit_uid' },
  {
    title: t('StudyVisitForm.unique_visit_number'),
    key: 'unique_visit_number',
  },
  { title: t('StudyVisitForm.visit_start_rule'), key: 'start_rule' },
  { title: t('StudyVisitForm.visit_stop_rule'), key: 'end_rule' },
  {
    title: t('StudyVisitForm.epoch_allocation'),
    key: 'epoch_allocation.sponsor_preferred_name',
  },
  {
    title: t('StudyVisitForm.study_epoch'),
    key: 'study_epoch.sponsor_preferred_name',
  },
  { title: t('StudyVisitForm.visit_description'), key: 'description' },
  { title: t('StudyVisitForm.show_visit'), key: 'show_visit' },
])
const headersHolder = ref([])
const selectedStudyVisit = ref(null)
const timelineRef = ref()
const showVisitHistory = ref(false)
const loading = ref(true)
const duplicateForm = ref(false)
const editMode = ref(false)
// Rows with unsaved edits; any number of them can be edited before saving
const editedVisits = reactive(new Set())
// The one row whose timing (and so possibly the visit order) is being edited
const timingEditVisit = shallowRef(null)
const previewLoadingVisits = reactive(new Set())
const visitTypes = ref([])
const { canDuplicateVisit } = useVisitTypeTerms(visitTypes)
const visitHistoryItems = ref([])
const fetchedStudyEpochs = ref([])
const frequencies = ref([])
const epochAllocations = ref([])
const tableLoading = ref(false)
const savingVisit = ref(false)
const showSettings = ref(false)
const visitClasses = [
  {
    label: t('StudyVisitForm.scheduled_visit'),
    value: visitConstants.CLASS_SINGLE_VISIT,
  },
  {
    label: t('StudyVisitForm.unscheduled_visit'),
    value: visitConstants.CLASS_UNSCHEDULED_VISIT,
  },
  {
    label: t('StudyVisitForm.non_visit'),
    value: visitConstants.CLASS_NON_VISIT,
  },
  {
    label: t('StudyVisitForm.manually_defined_visit'),
    value: visitConstants.CLASS_MANUALLY_DEFINED_VISIT,
  },
]
const visitSubClasses = [
  {
    label: t('StudyVisitForm.single_visit'),
    value: visitConstants.SUBCLASS_SINGLE_VISIT,
  },
  {
    label: t('StudyVisitForm.anchor_visit_in_group'),
    value: visitConstants.SUBCLASS_ANCHOR_VISIT_IN_GROUP_OF_SUBV,
  },
  {
    label: t('StudyVisitForm.repeating_visit'),
    value: visitConstants.SUBCLASS_REPEATING_VISIT,
  },
  {
    label: t('StudyVisitForm.additional_sub_visit'),
    value: visitConstants.SUBCLASS_ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV,
  },
]

const anchorVisits = computed(() => {
  return epochsStore.studyVisits.filter(
    (el) =>
      el.visit_subclass ===
      visitConstants.SUBCLASS_ANCHOR_VISIT_IN_GROUP_OF_SUBV
  )
})
// Pending edits: what the unsaved bar is shown for.
const hasUnsavedEdits = computed(() => editMode.value && editedVisits.size > 0)
const studyEpochs = computed(() => {
  return epochsStore.studyEpochs
})
const studyVisits = computed(() => {
  return epochsStore.studyVisits
})
const totalVisits = computed(() => {
  return epochsStore.totalVisits
})
// Fit the table to its rows; cap at ~10 rows (plus header) so more rows scroll.
const tableHeight = computed(() =>
  studyVisits.value.length > 10 ? `${48 * 11}px` : 'auto'
)
const exportDataUrl = computed(() => {
  return `studies/${studiesGeneralStore.selectedStudy.uid}/study-visits`
})
const studyVisitHistoryTitle = computed(() => {
  if (selectedStudyVisit.value) {
    return t('StudyVisitTable.study_visit_history_title', {
      visitUid: selectedStudyVisit.value.uid,
    })
  }
  return ''
})

function getFilteredPeriods(visit) {
  try {
    if (
      visit.visit_class === visitConstants.CLASS_SINGLE_VISIT ||
      visit.visit_class === visitConstants.CLASS_MANUALLY_DEFINED_VISIT
    ) {
      return studyEpochs.value.filter(
        (item) => item.epoch_name !== visitConstants.EPOCH_BASIC
      )
    }
    if (studyEpochs.value) {
      return studyEpochs.value.filter(
        (item) => item.epoch_name === visitConstants.EPOCH_BASIC
      )
    }
    return []
  } catch (error) {
    console.error(error)
  }
}

onMounted(() => {
  Promise.all([
    epochsStore.fetchStudyEpochs({
      studyUid: studiesGeneralStore.selectedStudy.uid,
    }),
    epochsStore.fetchStudyTimeUnits(),
    epochsStore.fetchStudyVisitMode(studiesGeneralStore.selectedStudy.uid),
  ]).finally(() => {
    loading.value = false
  })
  fetchVisitTimeReferenceTerms()
  terms.getTermsByCodelist('visitTypes', { page_size: 0 }).then((resp) => {
    visitTypes.value = resp.data.items
  })
  codelists.getTermsByCodelist('repeatingVisitFrequency').then((resp) => {
    frequencies.value = resp.data.items
  })
  codelists.getTermsByCodelist('epochAllocations').then((resp) => {
    epochAllocations.value = resp.data.items
  })
})

function getVisitClassLabel(visitClass) {
  return visitClasses.find((c) => c.value === visitClass)?.label ?? ''
}

function getVisitSubClassLabel(visitSubClass) {
  return visitSubClasses.find((c) => c.value === visitSubClass)?.label ?? ''
}

async function fetchVisitsHistory() {
  const resp = await studyEpochsApi.getStudyVisitsVersions(
    studiesGeneralStore.selectedStudy.uid
  )
  return transformItems(resp.data)
}

function transformItems(items) {
  const result = []
  for (const item of items) {
    const newItem = { ...item }
    newItem.study_epoch_uid = getStudyEpochName(newItem.study_epoch_uid)
    newItem.is_global_anchor_visit = dataFormating.yesno(
      newItem.is_global_anchor_visit
    )
    newItem.show_visit = dataFormating.yesno(newItem.show_visit)
    newItem.visit_window = `${item.min_visit_window_value} / ${item.max_visit_window_value} ${getUnitName(item.visit_window_unit_uid)}`
    result.push(newItem)
  }
  return result
}

function openEditMode() {
  headersHolder.value = tableRef.value.selectedColumns
  headers.value = editHeaders.value
  tableRef.value.setExternalColumns(editHeaders.value)
  editMode.value = true
}

function closeEditMode() {
  tableRef.value.filterTable()
  editMode.value = false
  resetEditState()
  headers.value = defaultColumns.value
  tableRef.value.setExternalColumns(headersHolder.value)
}

function resetEditState() {
  editedVisits.clear()
  timingEditVisit.value = null
}

// A reload replaces the rows the pending edits belong to
watch(() => epochsStore.studyVisits, resetEditState)

function markEdited(item) {
  if (item.min_visit_window_value > 0) {
    item.min_visit_window_value = item.min_visit_window_value * -1
  }
  editedVisits.add(item)
}

// Timing can move a visit within the order, so only one visit may have it edited at a time
function markTimingEdited(item) {
  if (!timingEditVisit.value) {
    timingEditVisit.value = toRaw(item)
  }
  markEdited(item)
}

function isTimingLocked(item) {
  return timingEditVisit.value !== null && timingEditVisit.value !== toRaw(item)
}

function updateNestedTermUid(item, fieldName, value) {
  if (!item[fieldName]) {
    item[fieldName] = {}
  }
  item[fieldName].term_uid = value
  if (fieldName === 'time_reference') {
    markTimingEdited(item)
  } else {
    markEdited(item)
  }
  refreshVisitPreview(item)
}

// Time reference a row had before joining a group, restored when it leaves; keyed by row
const timeReferenceBeforeGroup = new WeakMap()

function setVisitGroup(item) {
  if (item.visit_sublabel_reference) {
    if (!timeReferenceBeforeGroup.has(item)) {
      timeReferenceBeforeGroup.set(item, item.time_reference)
    }
    // A missing 'Anchor visit in visit group' term leaves the reference alone
    if (anchorVisitInGroupTermUid.value) {
      item.time_reference = { term_uid: anchorVisitInGroupTermUid.value }
    }
  } else if (timeReferenceBeforeGroup.has(item)) {
    item.time_reference = timeReferenceBeforeGroup.get(item)
    timeReferenceBeforeGroup.delete(item)
  }
  markTimingEdited(item)
  refreshVisitPreview(item)
}

// Only an additional subvisit has a group; changing the subclass takes the row out of it
function onVisitSubclassChange(item) {
  if (
    item.visit_subclass !==
      visitConstants.SUBCLASS_ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV &&
    item.visit_sublabel_reference
  ) {
    item.visit_sublabel_reference = null
    setVisitGroup(item)
    return
  }
  markTimingEdited(item)
}

function isManuallyDefined(item) {
  return (
    epochsStore.manualVisitMode ||
    item.visit_class === visitConstants.CLASS_MANUALLY_DEFINED_VISIT
  )
}

function refreshVisitPreview(item) {
  const mandatory = [
    item.visit_type?.term_uid,
    item.visit_contact_mode?.term_uid,
    item.time_reference?.term_uid,
    item.time_value,
    item.time_unit_uid,
  ]
  if (isManuallyDefined(item)) {
    mandatory.push(
      item.visit_name,
      item.visit_short_name,
      item.unique_visit_number
    )
  }
  if (
    mandatory.some(
      (value) => value === null || value === undefined || value === ''
    )
  ) {
    return
  }
  const payload = JSON.parse(JSON.stringify(item))
  payload.visit_type = { term_uid: item.visit_type.term_uid }
  payload.visit_contact_mode = { term_uid: item.visit_contact_mode.term_uid }
  payload.time_reference = { term_uid: item.time_reference.term_uid }
  previewLoadingVisits.add(item)
  epochsStore
    .getStudyVisitPreview({
      studyUid: studiesGeneralStore.selectedStudy.uid,
      input: payload,
    })
    .then((resp) => {
      let fields = ['study_day_label', 'study_week_label']
      if (!isManuallyDefined(item)) {
        fields = fields.concat([
          'visit_name',
          'visit_short_name',
          'unique_visit_number',
          'start_rule',
        ])
      }
      fields.forEach((field) => {
        item[field] = resp.data[field]
      })
    })
    .finally(() => {
      previewLoadingVisits.delete(item)
    })
}

// The store strips derived naming from a copy, so a failed save leaves the row as typed
function saveVisit(item) {
  const studyUid = studiesGeneralStore.selectedStudy.uid
  return item.uid
    ? epochsStore.updateStudyVisit({
        studyUid,
        studyVisitUid: item.uid,
        input: item,
        refreshEpochs: false,
      })
    : epochsStore.addStudyVisit({ studyUid, input: item, refreshEpochs: false })
}

// Saves one visit at a time and stops at the first failure, leaving the rest pending.
// A new visit goes last: once added it cannot be told apart from an unsaved row.
// Epochs are refreshed once at the end, also when a later row failed.
async function saveVisits() {
  const pending = [...editedVisits]
  const rows = [
    ...pending.filter(
      (visit) => visit.uid && toRaw(visit) !== timingEditVisit.value
    ),
    ...pending.filter(
      (visit) => visit.uid && toRaw(visit) === timingEditVisit.value
    ),
    ...pending.filter((visit) => !visit.uid),
  ]
  let saved = 0
  let added = 0
  savingVisit.value = true
  try {
    for (const visit of rows) {
      const isNewVisit = !visit.uid
      await saveVisit(visit)
      added += isNewVisit ? 1 : 0
      editedVisits.delete(visit)
      if (timingEditVisit.value === toRaw(visit)) {
        timingEditVisit.value = null
      }
      saved += 1
    }
  } catch {
    // The error toast is already shown; the failed row stays in edit so the save can be retried
  } finally {
    if (saved > 0) {
      await epochsStore
        .fetchStudyEpochs({ studyUid: studiesGeneralStore.selectedStudy.uid })
        .catch(() => {
          // The visits are saved; the error toast is already shown
        })
    }
    savingVisit.value = false
  }
  if (saved === 0) {
    return
  }
  if (editedVisits.size === 0) {
    tableRef.value.filterTable()
  }
  const msg =
    saved > 1
      ? t('StudyVisitTable.visits_saved', { count: saved })
      : t(
          added > 0
            ? 'StudyVisitForm.add_success'
            : 'StudyVisitForm.update_success'
        )
  notificationHub.add({ msg })
}

function cancelVisitEditing() {
  tableRef.value.filterTable()
  resetEditState()
}

function openDuplicateForm(item) {
  selectedStudyVisit.value = item
  duplicateForm.value = true
}

function closeDuplicateForm() {
  selectedStudyVisit.value = null
  duplicateForm.value = false
  tableRef.value?.filterTable()
  timelineRef.value?.refreshVisits()
}

function fetchStudyVisits(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  params.studyUid = studiesGeneralStore.selectedStudy.uid
  epochsStore.fetchFilteredStudyVisits(params)
}

async function addNewVisitRow() {
  if (studyEpochs.value.length === 0) {
    const options = {
      type: 'warning',
      cancelLabel: t('_global.cancel'),
      agreeLabel: t('StudyVisitForm.add_epoch'),
      redirect: {
        name: 'StudyStructure',
        params: { tab: 'epochs' },
      },
    }
    if (
      !(await confirmRef.value.open(t('StudyVisitForm.create_epoch'), options))
    ) {
      return
    }
    return
  }
  const newVisit = {
    study_epoch_uid: null,
    visit_type: null,
    visit_class: null,
    visit_contact_mode: null,
    show_visit: true,
    is_global_anchor_visit: false,
    time_reference: null,
    time_value: null,
    time_unit_uid: null,
    min_visit_window_value: null,
    max_visit_window_value: null,
    visit_window_unit_uid: null,
    description: null,
  }
  epochsStore.studyVisits.unshift(newVisit)
  epochsStore.totalVisits += 1
  markTimingEdited(newVisit)
}

async function deleteTimelineVisit(visit) {
  if (!visit) {
    return
  }
  const options = {
    type: 'warning',
    cancelLabel: t('_global.cancel'),
    agreeLabel: t('_global.delete'),
  }
  if (
    await confirmRef.value.open(
      t('StudyVisitTable.confirm_delete', {
        visit: visit.visit_short_name || visit.visit_name,
      }),
      options
    )
  ) {
    try {
      await timelineRef.value.deleteVisit(visit)
      notificationHub.add({ msg: t('StudyVisitTable.delete_success') })
    } catch {
      // The error toast is already shown; the timeline still shows the visit
    }
  }
}

async function deleteVisit(item) {
  tableLoading.value = true
  // Catch possible errors when deleting a study visit
  // to get out of tableLoading state
  try {
    await epochsStore.deleteStudyVisit({
      studyUid: studiesGeneralStore.selectedStudy.uid,
      studyVisitUid: item.uid,
    })
    notificationHub.add({ msg: t('StudyVisitTable.delete_success') })
  } finally {
    tableLoading.value = false
    tableRef.value.filterTable()
  }
}

async function openVisitHistory(visit) {
  selectedStudyVisit.value = visit
  const resp = await studyEpochsApi.getStudyVisitVersions(
    studiesGeneralStore.selectedStudy.uid,
    visit.uid
  )
  visitHistoryItems.value = transformItems(resp.data)
  showVisitHistory.value = true
}

function closeVisitHistory() {
  selectedStudyVisit.value = null
  showVisitHistory.value = false
}

function getStudyEpochName(studyEpochUid) {
  if (studyEpochs.value && studyEpochs.value.length > 0) {
    fetchedStudyEpochs.value = studyEpochs.value
  }
  if (fetchedStudyEpochs.value) {
    const epoch = fetchedStudyEpochs.value.find(
      (item) => item.uid === studyEpochUid
    )
    return epoch.epoch_name
  }
  return ''
}

function getUnitName(unitUid) {
  const unit = epochsStore.studyTimeUnits.find((item) => item.uid === unitUid)
  if (unit) {
    return unit.name
  }
  return ''
}

function openSettings() {
  showSettings.value = true
}
function closeSettings() {
  showSettings.value = false
}
</script>

<style scoped>
.cellWidth {
  min-width: 150px;
  width: max-content;
}
.v-table .v-select,
.v-table .v-text-field,
.v-table .v-checkbox {
  margin-top: 8px;
  margin-bottom: 8px;
}
.v-table .v-select :deep(.v-input__details),
.v-table .v-text-field :deep(.v-input__details),
.v-table .v-checkbox :deep(.v-input__details) {
  display: none;
}
.wideCellWidth {
  width: 310px;
}
.epochCellWidth {
  width: 200px;
}
</style>
