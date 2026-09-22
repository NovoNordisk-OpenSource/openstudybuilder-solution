<template>
  <div>
    <div id="visjs" class="pa-6">
      <span class="text-headline-small ml-2">{{
        $t('StudyVisitTable.title')
      }}</span>
      <v-expansion-panels accordion tile class="mt-2">
        <v-expansion-panel>
          <v-expansion-panel-title>{{
            $t('StudyVisitTable.timeline_preview')
          }}</v-expansion-panel-title>
          <v-expansion-panel-text>
            <div v-if="!loading && studyVisits.length > 0" :key="chartsKey">
              <v-row>
                <label class="v-label theme--light mr-4 mt-2 mb-2">
                  {{ $t('StudyVisitTable.time_unit') }}
                </label>
                <v-radio-group
                  v-model="preferredTimeUnit"
                  inline
                  hide-details
                  focused
                  class="mt-2 mb-2"
                  @update:model-value="updatePreferredTimeUnit"
                >
                  <v-radio :label="$t('_global.day')" value="day" />
                  <v-radio :label="$t('_global.week')" value="week" />
                </v-radio-group>
              </v-row>
              <div class="studyVisitBarChartContainer">
                <BarChart
                  :key="barChartKey"
                  :chart-data="barChartDatasets"
                  :options="barChartOptions"
                  :style="barChartStyles"
                  class="pr-3"
                />
              </div>
              <div class="studyVisitBubbleChartContainer">
                <BubbleChart
                  :chart-data="lineChartDatasets"
                  :options="lineChartOptions"
                  :style="lineChartStyles"
                  class="ml-1"
                />
              </div>
            </div>
            <div v-else-if="loading">
              <v-progress-linear class="mt-5" indeterminate />
            </div>
            <div v-else class="mt-3">
              {{ $t('StudyVisitForm.no_data') }}
            </div>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </div>
    <NNTable
      ref="tableRef"
      table-id="studies-visits-table"
      :headers="headers"
      :default-headers="defaultColumns"
      :items="studyVisits"
      item-value="uid"
      class="mt-6"
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
        <div
          v-if="editMode && itemsDisabled && editingVisit"
          class="d-flex flex-nowrap ga-1 ml-2"
        >
          <v-btn
            variant="outlined"
            color="nnBaseBlue"
            rounded
            prepend-icon="mdi-content-save-outline"
            :loading="savingVisit"
            @click.stop="saveVisit(editingVisit)"
          >
            {{ $t('StudyVisitTable.save_visit') }}
          </v-btn>
          <v-btn
            variant="outlined"
            color="nnBaseBlue"
            rounded
            prepend-icon="mdi-close"
            :disabled="savingVisit"
            @click.stop="cancelVisitEditing"
          >
            {{ $t('StudyVisitTable.cancel_editing') }}
          </v-btn>
        </div>
      </template>
      <template #actions>
        <v-progress-circular v-show="loading" indeterminate color="primary" />
        <v-btn
          v-show="!loading"
          class="ml-2"
          icon
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          :disabled="
            !accessGuard.checkPermission($roles.STUDY_WRITE) ||
            studiesGeneralStore.selectedStudyVersion !== null
          "
          data-cy="add-visit"
          @click.stop="openForm"
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
            studiesGeneralStore.selectedStudyVersion !== null
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
            :disabled="item.disabled && itemsDisabled"
            @update:model-value="disableOthers(item)"
          />
        </div>
        <div v-else>
          {{ $filters.yesno(item.is_soa_milestone) }}
        </div>
      </template>
      <template #[`item.visit_name`]="{ item }">
        <router-link
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
      <template #[`item.study_epoch.sponsor_preferred_name`]="{ item }">
        <div v-if="editMode">
          <v-select
            v-model="item.study_epoch_uid"
            item-title="epoch_name"
            item-value="uid"
            :items="getFilteredPeriods(item)"
            class="epochCellWidth"
            :disabled="item.disabled && itemsDisabled"
            @update:model-value="disableOthers(item)"
          />
        </div>
        <CTTermDisplay v-else :term="item.study_epoch || {}" />
      </template>
      <template #[`item.visit_type.sponsor_preferred_name`]="{ item }">
        <CTTermDisplay :term="item.visit_type" />
      </template>
      <template #[`item.visit_class`]="{ item }">
        <div v-if="editMode">
          <v-select
            v-model="item.visit_class"
            :items="visitClasses"
            item-title="label"
            item-value="value"
            class="cellWidth"
            :disabled="item.disabled && itemsDisabled"
            @update:model-value="
              (disableOthers(item), (item.study_epoch_uid = null))
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
            :disabled="item.disabled && itemsDisabled"
            @update:model-value="disableOthers(item)"
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
              (item.disabled && itemsDisabled) ||
              item.visit_subclass !== visitConstants.SUBCLASS_REPEATING_VISIT
            "
            @update:model-value="disableOthers(item)"
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
              :disabled="item.disabled && itemsDisabled"
              @input="disableOthers(item)"
            />
            <v-text-field
              v-model="item.max_visit_window_value"
              :disabled="item.disabled && itemsDisabled"
              @input="disableOthers(item)"
            />
            <v-select
              v-model="item.visit_window_unit_uid"
              :items="epochsStore.studyTimeUnits"
              item-title="name"
              item-value="uid"
              class="cellWidth"
              :disabled="item.disabled && itemsDisabled"
              @update:model-value="disableOthers(item)"
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
      <template #[`item.show_visit`]="{ item }">
        <div v-if="editMode">
          <v-checkbox
            v-model="item.show_visit"
            :disabled="item.disabled && itemsDisabled"
            @update:model-value="disableOthers(item)"
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
            :disabled="item.disabled && itemsDisabled"
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
            ? item.visit_subname
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
          <v-row class="cellWidth">
            <v-text-field
              v-model="item.time_value"
              width="60px"
              :disabled="item.disabled && itemsDisabled"
              @input="disableOthers(item)"
            />
            <v-select
              v-model="item.time_unit_uid"
              :items="epochsStore.studyTimeUnits"
              item-title="name"
              item-value="uid"
              class="cellWidth"
              :disabled="item.disabled && itemsDisabled"
              @update:model-value="disableOthers(item)"
            />
          </v-row>
        </div>
        <div v-else>
          {{ item.time_value }} {{ getUnitName(item.time_unit_uid) }}
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
            :disabled="item.disabled && itemsDisabled"
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
              visitConstants.CLASS_SPECIAL_VISIT,
              visitConstants.CLASS_MANUALLY_DEFINED_VISIT,
              visitConstants.CLASS_SINGLE_VISIT,
            ].indexOf(item.visit_class) !== -1
          "
        >
          <v-select
            v-if="
              item.visit_subclass !==
                visitConstants.SUBCLASS_ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV &&
              item.visit_class !== visitConstants.CLASS_SPECIAL_VISIT
            "
            :model-value="item.time_reference?.term_uid ?? null"
            class="cellWidth"
            :items="timeReferences"
            item-title="sponsor_preferred_name"
            item-value="term_uid"
            :disabled="item.disabled && itemsDisabled"
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
            :disabled="item.disabled && itemsDisabled"
            @update:model-value="disableOthers(item)"
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
              :disabled="item.disabled && itemsDisabled"
              @input="disableOthers(item)"
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
              :disabled="item.disabled && itemsDisabled"
              @input="disableOthers(item)"
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
              :disabled="item.disabled && itemsDisabled"
              @input="disableOthers(item)"
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
            (!itemsDisabled || item.disabled) &&
            studiesGeneralStore.selectedStudyVersion === null
          "
          :actions="actions"
          :item="item"
        />
        <div
          v-if="editMode && itemsDisabled && !item.disabled"
          class="d-flex flex-nowrap ga-1"
        >
          <v-btn
            size="x-small"
            variant="outlined"
            color="nnBaseBlue"
            icon="mdi-content-save-outline"
            :loading="savingVisit"
            @click="saveVisit(item)"
          />
          <v-btn
            size="x-small"
            variant="outlined"
            color="nnBaseBlue"
            icon="mdi-close"
            :disabled="savingVisit"
            @click="cancelVisitEditing"
          />
        </div>
      </template>
    </NNTable>
    <StudyVisitsDuplicateForm
      :open="duplicateForm"
      :study-visit="selectedStudyVisit"
      @close="closeDuplicateForm"
    />
    <v-dialog
      v-model="showForm"
      persistent
      fullscreen
      content-class="fullscreen-dialog"
    >
      <StudyVisitForm
        :opened="showForm"
        :first-visit="studyVisits ? studyVisits.length === 0 : true"
        :study-visit="selectedStudyVisit"
        @close="closeForm"
      />
    </v-dialog>
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
    <ConfirmDialog ref="confirmRef" :text-cols="6" :action-cols="5" />
  </div>
</template>

<script setup>
import units from '@/api/units'
import terms from '@/api/controlledTerminology/terms'
import codelists from '@/api/controlledTerminology/terms'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StudyVisitForm from './StudyVisitForm.vue'
import BarChart from '@/components/tools/BarChart.vue'
import BubbleChart from '@/components/tools/BubbleChart.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import CTTermDisplay from '@/components/tools/CTTermDisplay.vue'
import visitConstants from '@/constants/visits'
import filteringParameters from '@/utils/filteringParameters'
import studyConstants from '@/constants/study'
import StudyVisitsDuplicateForm from './StudyVisitsDuplicateForm.vue'
import unitConstants from '@/constants/units'
import studyEpochsApi from '@/api/studyEpochs'
import dataFormating from '@/utils/dataFormating'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useEpochsStore } from '@/stores/studies-epochs'
import { inject, ref, watch, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

const notificationHub = inject('notificationHub')
const roles = inject('roles')
const { t } = useI18n()
const epochsStore = useEpochsStore()
const accessGuard = useAccessGuard()
const studiesGeneralStore = useStudiesGeneralStore()
const tableRef = ref()
const confirmRef = ref()

const actions = ref([
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'edit') &&
      !editMode.value,
    click: editVisit,
    accessRole: roles.STUDY_WRITE,
  },
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
    condition: (item) =>
      ![
        visitConstants.CLASS_NON_VISIT,
        visitConstants.CLASS_UNSCHEDULED_VISIT,
        visitConstants.CLASS_MANUALLY_DEFINED_VISIT,
      ].includes(item.visit_class) &&
      item.visit_subclass !==
        visitConstants.SUBCLASS_ANCHOR_VISIT_IN_GROUP_OF_SUBV,
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
  { title: t('StudyVisitForm.visit_name'), key: 'visit_name' },
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
  { title: t('StudyVisitForm.visit_number'), key: 'visit_number' },
  {
    title: t('StudyVisitForm.unique_visit_number'),
    key: 'unique_visit_number',
  },
  { title: t('StudyVisitForm.visit_short_name'), key: 'visit_short_name' },
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
  { title: t('StudyVisitForm.visit_name'), key: 'visit_name' },
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
  { title: t('StudyVisitForm.visit_number'), key: 'visit_number' },
  {
    title: t('StudyVisitForm.unique_visit_number'),
    key: 'unique_visit_number',
  },
  { title: t('StudyVisitForm.visit_short_name'), key: 'visit_short_name' },
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
    title: t('StudyVisitForm.global_anchor_visit'),
    key: 'is_global_anchor_visit',
  },
  {
    title: t('StudyVisitForm.contact_mode'),
    key: 'visit_contact_mode.sponsor_preferred_name',
  },
  { title: t('StudyVisitForm.time_value'), key: 'time_value', width: '10%' },
  { title: t('StudyVisitForm.visit_name'), key: 'visit_name' },
  { title: t('StudyVisitForm.visit_window'), key: 'visit_window' },
  { title: t('StudyVisitForm.show_visit'), key: 'show_visit' },
  { title: t('StudyVisitForm.visit_description'), key: 'description' },
  {
    title: t('StudyVisitForm.epoch_allocation'),
    key: 'epoch_allocation.sponsor_preferred_name',
  },
  { title: t('StudyVisitForm.visit_start_rule'), key: 'start_rule' },
  { title: t('StudyVisitForm.visit_stop_rule'), key: 'end_rule' },
])
const headersHolder = ref([])
const preferredTimeUnit = ref(studyConstants.STUDY_TIME_UNIT_DAY)
const preferredTimeUnits = ref([])
const selectedStudyVisit = ref(null)
const showForm = ref(false)
const showVisitHistory = ref(false)
const loading = ref(true)
const barChartOptions = ref({
  responsive: true,
  maintainAspectRatio: false,
  tooltips: {
    enabled: false,
  },
  interaction: {
    intersect: false,
  },
  scales: {
    x: {
      ticks: {
        display: false,
        max: 0,
        min: 0,
      },
      grid: {
        display: false,
      },
      stacked: false,
    },
    y: {
      stacked: true,
    },
  },
  indexAxis: 'y',
})
const lineChartOptions = ref({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      callbacks: {
        label: function (context) {
          return (
            context.dataset.label,
            [
              `${context.dataset.contact_mode}, ${context.dataset.visit_type}`,
              `${context.dataset.study_day}, ${context.dataset.week}`,
            ]
          )
        },
        labelColor: function () {
          return {
            backgroundColor: 'rgba(226, 230, 240, 0.8)',
          }
        },
      },
    },
  },
  interaction: {
    mode: 'dataset',
  },
  scales: {
    y: {
      grid: {
        display: false,
      },
      ticks: {
        display: false,
      },
    },
    x: {
      ticks: {
        max: 0,
        min: 1,
        stepSize: 7,
        precision: 0,
      },
      scaleLabel: {
        display: true,
        labelString: t('StudyVisitTable.study_day'),
      },
    },
  },
  indexAxis: 'y',
})
const barChartDatasets = ref({
  datasets: [],
})
const lineChartDatasets = ref({
  datasets: [],
})
const chartsKey = ref(0)
const barChartKey = ref(0)
const duplicateForm = ref(false)
const editMode = ref(false)
const contactModes = ref([])
const itemsDisabled = ref(false)
const timeReferences = ref([])
const visitHistoryItems = ref([])
const fetchedStudyEpochs = ref([])
const timeLineVisits = ref([])
const frequencies = ref([])
const epochAllocations = ref([])
const tableLoading = ref(false)
const savingVisit = ref(false)
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
    label: t('StudyVisitForm.special_visit'),
    value: visitConstants.CLASS_SPECIAL_VISIT,
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
    (el) => el.visit_class !== visitConstants.CLASS_SPECIAL_VISIT
  )
})
const editingVisit = computed(() => {
  if (!itemsDisabled.value) {
    return null
  }
  return epochsStore.studyVisits.find((visit) => !visit.disabled) || null
})
const studyEpochs = computed(() => {
  return epochsStore.studyEpochs
})
const studyVisits = computed(() => {
  return epochsStore.studyVisits
})
const totalVisits = computed(() => {
  return epochsStore.totalVisits
})
const barChartStyles = computed(() => {
  return {
    position: 'relative',
    height: '100%',
  }
})
const lineChartStyles = computed(() => {
  return {
    position: 'relative',
    height: '100%',
  }
})
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
      visit.visit_class === visitConstants.CLASS_SPECIAL_VISIT ||
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

watch(studyVisits, () => {
  getTimeLineVisits()
})

onMounted(() => {
  getTimeLineVisits()
  epochsStore.fetchStudyEpochs({
    studyUid: studiesGeneralStore.selectedStudy.uid,
  })
  epochsStore.fetchStudyTimeUnits()
  units
    .getBySubset(unitConstants.TIME_UNIT_SUBSET_STUDY_PREFERRED_TIME_UNIT)
    .then((resp) => {
      preferredTimeUnits.value = resp.data.items
    })
  terms.getTermsByCodelist('contactModes').then((resp) => {
    contactModes.value = resp.data.items
  })
  terms.getTermsByCodelist('timepointReferences').then((resp) => {
    timeReferences.value = resp.data.items
  })
  codelists.getTermsByCodelist('repeatingVisitFrequency').then((resp) => {
    frequencies.value = resp.data.items
  })
  codelists.getTermsByCodelist('epochAllocations').then((resp) => {
    epochAllocations.value = resp.data.items
  })
  if (studiesGeneralStore.studyPreferredTimeUnit) {
    preferredTimeUnit.value =
      studiesGeneralStore.studyPreferredTimeUnit.time_unit_name
  }
})

function getVisitClassLabel(visitClass) {
  return visitClasses.find((c) => c.value === visitClass).label
}

function getVisitSubClassLabel(visitSubClass) {
  return visitSubClasses.find((c) => c.value === visitSubClass).label
}

function getTimeLineVisits() {
  const params = {
    page_size: 0,
    filters: JSON.stringify({
      visit_class: {
        v: [
          visitConstants.CLASS_SINGLE_VISIT,
          visitConstants.CLASS_MANUALLY_DEFINED_VISIT,
        ],
      },
    }),
  }
  studyEpochsApi
    .getStudyVisits(studiesGeneralStore.selectedStudy.uid, params)
    .then((resp) => {
      timeLineVisits.value = resp.data.items
      buildChart()
    })
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
  editMode.value = true
}

function closeEditMode() {
  tableRef.value.filterTable()
  editMode.value = false
  itemsDisabled.value = false
  headers.value = defaultColumns.value
  tableRef.value.setExternalColumns(headersHolder.value)
}

function disableOthers(item) {
  if (item.min_visit_window_value > 0) {
    item.min_visit_window_value = item.min_visit_window_value * -1
  }
  if (!itemsDisabled.value) {
    studyVisits.value.forEach((visit) => {
      visit.disabled = visit.uid !== item.uid
    })
    itemsDisabled.value = true
  }
}

function updateNestedTermUid(item, fieldName, value) {
  if (!item[fieldName]) {
    item[fieldName] = {}
  }
  item[fieldName].term_uid = value
  disableOthers(item)
}

function saveVisit(item) {
  if (item.visit_class !== visitConstants.CLASS_MANUALLY_DEFINED_VISIT) {
    delete item.visit_name
    delete item.visit_number
    delete item.visit_short_name
    delete item.unique_visit_number
  }
  savingVisit.value = true
  return epochsStore
    .updateStudyVisit({
      studyUid: studiesGeneralStore.selectedStudy.uid,
      studyVisitUid: item.uid,
      input: item,
    })
    .then(() => {
      tableRef.value.filterTable()
      notificationHub.add({ msg: t('StudyVisitForm.update_success') })
      itemsDisabled.value = false
    })
    .finally(() => {
      savingVisit.value = false
    })
}

function cancelVisitEditing() {
  tableRef.value.filterTable()
  itemsDisabled.value = false
}

async function openDuplicateForm(item) {
  if (item.visit_class === visitConstants.CLASS_SPECIAL_VISIT) {
    const newVisit = JSON.parse(JSON.stringify(item))
    delete newVisit.visit_number
    delete newVisit.unique_visit_number
    delete newVisit.visit_short_name
    delete newVisit.visit_name
    await epochsStore.addStudyVisit({
      studyUid: studiesGeneralStore.selectedStudy.uid,
      input: newVisit,
    })
    notificationHub.add({
      msg: t('StudyVisitForm.visit_duplicated'),
    })
    tableRef.value.filterTable()
  } else {
    selectedStudyVisit.value = item
    duplicateForm.value = true
  }
}

function closeDuplicateForm() {
  selectedStudyVisit.value = null
  duplicateForm.value = false
  tableRef.value.filterTable()
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

function editVisit(item) {
  selectedStudyVisit.value = item
  showForm.value = true
}

async function openForm() {
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
  }
  showForm.value = true
}

function closeForm() {
  selectedStudyVisit.value = null
  showForm.value = false
  tableRef.value.filterTable()
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

function buildChart() {
  loading.value = true
  barChartDatasets.value.datasets = []
  lineChartDatasets.value.datasets = []
  const negativeDaysEpochs = []
  let maxXvalue = 0
  for (const d of studyEpochs.value) {
    if (d.start_day >= 0) {
      break
    } else {
      negativeDaysEpochs.push(d)
    }
  }
  studyEpochs.value.splice(0, negativeDaysEpochs.length) // Reordering of the epochs with visit with the negative day number
  negativeDaysEpochs.forEach((el) => {
    //  needed for correct timeline display
    studyEpochs.value.unshift(el)
  })
  let startField
  let endField
  if (preferredTimeUnit.value === studyConstants.STUDY_TIME_UNIT_DAY) {
    startField = 'start_day'
    endField = 'end_day'
  } else {
    startField = 'start_week'
    endField = 'end_week'
  }
  studyEpochs.value.forEach((el) => {
    if (el.epoch_name !== visitConstants.EPOCH_BASIC) {
      if (el[endField] > maxXvalue) {
        maxXvalue = el[endField]
      }
      barChartDatasets.value.datasets.push({
        data: [[el[startField], el[endField]]],
        backgroundColor: el.color_hash, // and for the rest we need to just provide duration of epoch, but if the first epoch has positive first day number than we need to build
        label: el.epoch_name, // such array just for the first epoch
      })
    }
  })
  let sameWeek
  timeLineVisits.value.forEach((el) => {
    const value =
      preferredTimeUnit.value === studyConstants.STUDY_TIME_UNIT_DAY
        ? el.study_day_number
        : el.study_week_number
    lineChartDatasets.value.datasets.push({
      data: [
        {
          x: value,
          y: sameWeek === el.study_week_label ? 0 : 1,
          r: 7,
        },
      ],
      study_day: el.study_day_label,
      label: el.visit_name,
      backgroundColor: 'rgb(6, 57, 112)',
      contact_mode: el.visit_contact_mode.sponsor_preferred_name,
      visit_type: el.visit_type.sponsor_preferred_name,
      week: el.study_week_label,
    })
    sameWeek = el.study_week_label
  })
  if (timeLineVisits.value.length > 0) {
    const lastVisitDay =
      timeLineVisits.value[timeLineVisits.value.length - 1].study_day_number
    let minXvalue
    let label
    let stepSize
    if (preferredTimeUnit.value === studyConstants.STUDY_TIME_UNIT_DAY) {
      minXvalue = timeLineVisits.value[0].study_day_number
      label = t('StudyVisitTable.study_day')
      stepSize = 7 * Math.ceil(lastVisitDay / 100)
    } else {
      minXvalue = timeLineVisits.value[0].study_week_number
      label = t('StudyVisitTable.study_week')
      stepSize = 1
    }
    lineChartOptions.value.scales.x.title = label
    barChartOptions.value.scales.x.max = Math.round(maxXvalue) + 2
    lineChartOptions.value.scales.x.max = Math.round(maxXvalue) + 2
    barChartOptions.value.scales.x.min =
      minXvalue < 0 ? Math.round(minXvalue) - 1 : Math.round(minXvalue)
    lineChartOptions.value.scales.x.min =
      minXvalue < 0 ? Math.round(minXvalue) - 1 : Math.round(minXvalue)
    lineChartOptions.value.scales.x.stepSize = stepSize
  }
  barChartDatasets.value.labels = ['']
  loading.value = false
  chartsKey.value += 1
  barChartKey.value += 1
}

function updatePreferredTimeUnit(value) {
  for (const timeUnit of preferredTimeUnits.value) {
    if (timeUnit.name === value) {
      studiesGeneralStore.setStudyPreferredTimeUnit({
        timeUnitUid: timeUnit.uid,
        protocolSoa: false,
      })
      tableRef.value.filterTable()
      break
    }
  }
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
.studyVisitBarChartContainer {
  position: relative;
  height: 150px;
}
.studyVisitBubbleChartContainer {
  position: relative;
  height: 70px;
}
</style>
