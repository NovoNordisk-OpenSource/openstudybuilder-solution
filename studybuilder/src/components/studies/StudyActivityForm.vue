<template>
  <HorizontalStepperForm
    ref="stepper"
    :title="title"
    :steps="steps"
    :form-observer-getter="getObserver"
    :help-text="$t('_help.StudyActivityTable.general')"
    :reset-loading="resetLoading"
    @close="close"
    @save="submit"
  >
    <template #[`step.creationMode`]>
      <v-radio-group v-model="creationMode" color="primary">
        <v-radio
          :label="$t('StudyActivityForm.select_from_studies')"
          value="selectFromStudies"
          data-cy="select-from-studies"
        />
        <v-radio
          :label="$t('StudyActivityForm.select_from_library')"
          value="selectFromLibrary"
          data-cy="select-from-library"
        />
        <v-radio
          v-if="!order"
          :label="$t('StudyActivityForm.create_placeholder_for_activity')"
          value="createPlaceholder"
          data-cy="create-placeholder"
        />
      </v-radio-group>
      <v-form ref="selectStudiesForm">
        <v-row v-if="creationMode === 'selectFromStudies'">
          <v-col cols="3">
            <v-autocomplete
              v-model="selectedStudy"
              :label="$t('StudySelectionTable.study_ids')"
              :items="studies"
              item-title="current_metadata.identification_metadata.study_id"
              data-cy="select-study-for-activity-by-id"
              return-object
              :rules="[formRules.required]"
              clearable
              rounded="lg"
              variant="outlined"
              color="nnBaseBlue"
              density="compact"
            />
          </v-col>
          <div class="mt-5">
            {{ $t('_global.and_or') }}
          </div>
          <v-col cols="3">
            <v-autocomplete
              v-model="selectedStudy"
              :label="$t('StudySelectionTable.study_acronyms')"
              :items="
                studies.filter(
                  (study) =>
                    study.current_metadata.identification_metadata.study_acronym
                )
              "
              item-title="current_metadata.identification_metadata.study_acronym"
              data-cy="select-study-for-activity-by-acronym"
              return-object
              :rules="[formRules.required]"
              clearable
              rounded="lg"
              variant="outlined"
              color="nnBaseBlue"
              density="compact"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #[`step.selectFromStudies`]>
      <v-col cols="12">
        <NNTable
          v-if="selectedStudy"
          key="studyActivityTable"
          ref="selectionTable"
          v-model="selectedActivities"
          item-value="uid"
          show-select
          :headers="studyActivityHeaders"
          :items="activities"
          hide-default-switches
          hide-export-button
          show-filter-bar-by-default
          :items-per-page="15"
          elevation="0"
          table-height="50vh"
          data-cy="activities-table"
          :items-length="activitiesTotal"
          :column-data-resource="`studies/${selectedStudy.uid}/study-activities`"
          :filters-modify-function="modifyFilters"
          @filter="getActivities"
        >
          <template #beforeSwitches="">
            <v-switch
              v-model="selectedOnly"
              color="primary"
              :label="$t('StudyActivityForm.show_selected')"
              data-cy="show-selected"
              class="mt-4"
              @update:model-value="switchTableItems"
            />
          </template>
          <template #[`header.data-table-select`]>
            <v-btn
              :disabled="exchangeMode"
              data-cy="copy-all-activities"
              icon="mdi-content-copy"
              color="nnWhite"
              :title="$t('StudyActivityForm.copy_all_activities')"
              variant="text"
              @click="selectAllStudyActivities()"
            />
          </template>
          <template
            #[`item.data-table-select`]="{
              internalItem,
              isSelected,
              toggleSelect,
            }"
          >
            <v-checkbox-btn
              :model-value="isSelected(internalItem)"
              color="primary"
              data-cy="select-activity"
              :disabled="
                isStudyActivitySelected(internalItem.raw) ||
                isStudyActivityRequested(internalItem.raw) ||
                !isGroupingValid(internalItem.raw) ||
                multipleSelectedInExchangeMode(internalItem.raw)
              "
              @update:model-value="toggleSelect(internalItem)"
            ></v-checkbox-btn>
          </template>
          <template #[`item.activity.is_data_collected`]="{ item }">
            <div v-if="item.activity">
              {{ $filters.yesno(item.activity.is_data_collected) }}
            </div>
          </template>
        </NNTable>
      </v-col>
    </template>
    <template #[`step.selectFromLibrary`]>
      <v-col cols="12">
        <NNTable
          key="activityTable"
          ref="selectionLibraryTable"
          v-model="selectedActivities"
          item-value="item_key"
          show-select
          :headers="activityHeaders"
          :items="activities"
          hide-default-switches
          hide-export-button
          show-filter-bar-by-default
          :items-per-page="15"
          elevation="0"
          table-height="50vh"
          :items-length="activitiesTotal"
          :initial-filters="initialFilters"
          column-data-resource="concepts/activities/activities"
          :filters-modify-function="modifyFilters"
          @filter="getActivities"
        >
          <template #beforeSwitches="">
            <v-switch
              v-model="selectedOnly"
              color="primary"
              :label="$t('StudyActivityForm.show_selected')"
              data-cy="show-selected"
              class="mt-6"
              @update:model-value="switchTableItems"
            />
            <v-checkbox
              v-model="sameGroup"
              :label="$t('StudyActivityForm.use_the_same_group')"
              class="mt-6 ml-10"
              @update:model-value="clearSelectedGroups"
            />
            <v-autocomplete
              v-if="sameGroup"
              v-model="unifiedGroup"
              :label="$t('StudyActivityForm.flowchart_group_title')"
              :items="flowchartGroups"
              item-title="name.sponsor_preferred_name"
              style="min-width: 250px"
              class="mt-6 ml-2"
              rounded="lg"
              variant="outlined"
              color="nnBaseBlue"
              density="compact"
              :rules="[formRules.required]"
              return-object
              clearable
            />
          </template>
          <template #[`item.soa_group`]="{ item }">
            <v-autocomplete
              v-model="item.flowchart_group"
              :label="$t('StudyActivityForm.flowchart_group_title')"
              data-cy="flowchart-group"
              :items="flowchartGroups"
              item-title="name.sponsor_preferred_name"
              style="min-width: 250px"
              class="mt-2 mb-n4"
              rounded="lg"
              variant="outlined"
              color="nnBaseBlue"
              density="compact"
              return-object
              clearable
              :disabled="
                sameGroup ||
                isActivitySelected(item) ||
                isActivityNotFinal(item) ||
                isActivityRequested(item) ||
                multipleSelectedInExchangeMode(item)
              "
              @update:model-value="pushActivityToSelected(item)"
            />
          </template>
          <template #[`header.data-table-select`]>
            <v-btn
              :disabled="exchangeMode"
              icon="mdi-content-copy"
              color="nnWhite"
              data-cy="copy-all-activities"
              :title="$t('StudyActivityForm.copy_all_activities')"
              variant="text"
              @click="selectAllActivities()"
            />
          </template>
          <template
            #[`item.data-table-select`]="{
              internalItem,
              isSelected,
              toggleSelect,
            }"
          >
            <v-checkbox-btn
              :model-value="isSelected(internalItem)"
              color="primary"
              data-cy="select-activity"
              :disabled="
                isActivitySelected(internalItem.raw) ||
                isActivityNotFinal(internalItem.raw) ||
                isActivityRequested(internalItem.raw) ||
                multipleSelectedInExchangeMode(internalItem.raw)
              "
              @update:model-value="toggleSelect(internalItem)"
            ></v-checkbox-btn>
          </template>
          <template #[`item.is_data_collected`]="{ item }">
            {{ $filters.yesno(item.is_data_collected) }}
          </template>
        </NNTable>
      </v-col>
    </template>
    <template #[`step.createPlaceholder`]>
      <v-form ref="createPlaceholderForm">
        <ChoiceField
          v-model="form.is_request_final"
          :choices="requestTypes"
          inline
          width="400"
        />
        <div v-if="form.is_request_final !== undefined">
          <v-row>
            <v-col cols="3">
              <v-autocomplete
                v-model="form.activity_groupings[0].activity_group_uid"
                :label="$t('ActivityForms.activity_group')"
                data-cy="activity-group"
                :items="groups"
                item-title="name"
                item-value="uid"
                rounded="lg"
                variant="outlined"
                color="nnBaseBlue"
                density="compact"
                clearable
              />
            </v-col>
            <v-col cols="3">
              <v-autocomplete
                v-model="form.activity_groupings[0].activity_subgroup_uid"
                :label="$t('ActivityForms.activity_subgroup')"
                data-cy="activity-subgroup"
                :items="filteredSubGroups"
                item-title="name"
                item-value="uid"
                rounded="lg"
                variant="outlined"
                color="nnBaseBlue"
                density="compact"
                clearable
                :rules="
                  form.activity_groupings[0].activity_group_uid
                    ? [formRules.required]
                    : []
                "
                :disabled="
                  form.activity_groupings[0].activity_group_uid ? false : true
                "
              />
            </v-col>
            <v-col cols="3">
              <v-text-field
                v-model="form.name"
                :label="$t('ActivityFormsRequested.name')"
                data-cy="instance-name"
                rounded="lg"
                variant="outlined"
                color="nnBaseBlue"
                density="compact"
                clearable
                :rules="[formRules.required]"
                @input="placeholderSearch"
              />
            </v-col>
            <v-col cols="3">
              <v-autocomplete
                v-model="form.flowchart_group"
                :label="$t('StudyActivityForm.flowchart_group_title')"
                data-cy="flowchart-group"
                :items="flowchartGroups"
                :rules="[formRules.required]"
                item-title="name.sponsor_preferred_name"
                rounded="lg"
                variant="outlined"
                color="nnBaseBlue"
                density="compact"
                return-object
                clearable
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="3">
              <v-textarea
                v-model="form.request_rationale"
                :label="$t('ActivityFormsRequested.rationale_for_request')"
                data-cy="activity-rationale"
                rounded="lg"
                variant="outlined"
                color="nnBaseBlue"
                density="compact"
                clearable
                auto-grow
                rows="1"
                :rules="[formRules.required]"
              />
            </v-col>
            <v-col cols="3">
              <v-checkbox
                v-model="form.is_data_collected"
                class="mt-n2"
                color="nnBaseBlue"
                :label="$t('ActivityForms.is_data_collected')"
              />
            </v-col>
          </v-row>
          <div v-if="activities.length > 0">
            <span class="dialog-title">{{
              $t('ActivityForms.similar_activity_title')
            }}</span>
            <v-alert
              color="nnGoldenSun200"
              icon="mdi-information-outline"
              class="text-nnTrueBlue my-4"
            >
              {{ $t('ActivityForms.similar_activity_alert') }}
            </v-alert>
            <v-data-table
              v-model="selectedActivities"
              item-value="item_key"
              show-select
              :headers="activityHeaders"
              :items="activities"
              :items-length="activitiesTotal"
              :items-per-page="5"
              return-object
              @pagination="getActivities()"
            >
              <template #[`item.soa_group`]="{ item }">
                <v-autocomplete
                  v-model="item.flowchart_group"
                  :label="$t('StudyActivityForm.flowchart_group_title')"
                  data-cy="flowchart-group"
                  :items="flowchartGroups"
                  item-title="name.sponsor_preferred_name"
                  style="min-width: 250px"
                  class="mt-2 mb-n4"
                  rounded="lg"
                  variant="outlined"
                  color="nnBaseBlue"
                  density="compact"
                  return-object
                  clearable
                  :disabled="
                    isActivitySelected(item) ||
                    isActivityNotFinal(item) ||
                    isActivityRequested(item) ||
                    multipleSelectedInExchangeMode(item)
                  "
                />
              </template>
              <template #[`header.data-table-select`]>
                <v-btn
                  :disabled="exchangeMode"
                  icon="mdi-content-copy"
                  color="nnWhite"
                  :title="$t('StudyActivityForm.copy_all_activities')"
                  variant="text"
                  @click="selectAllActivities()"
                />
              </template>
              <template
                #[`item.data-table-select`]="{
                  internalItem,
                  isSelected,
                  toggleSelect,
                }"
              >
                <v-checkbox-btn
                  :model-value="isSelected(internalItem)"
                  color="primary"
                  :disabled="
                    isActivitySelected(internalItem.raw) ||
                    isActivityNotFinal(internalItem.raw) ||
                    isActivityRequested(internalItem.raw) ||
                    multipleSelectedInExchangeMode(internalItem.raw)
                  "
                  @update:model-value="toggleSelect(internalItem)"
                ></v-checkbox-btn>
              </template>
              <template #[`item.is_data_collected`]="{ item }">
                {{ $filters.yesno(item.is_data_collected) }}
              </template>
            </v-data-table>
          </div>
        </div>
      </v-form>
    </template>
  </HorizontalStepperForm>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import activitiesApi from '@/api/activities'
import statuses from '@/constants/statuses'
import study from '@/api/study'
import terms from '@/api/controlledTerminology/terms'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import NNTable from '@/components/tools/NNTable.vue'
import _isEmpty from 'lodash/isEmpty'
import _isEqual from 'lodash/isEqual'
import libConstants from '@/constants/libraries'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import ChoiceField from '@/components/ui/ChoiceField.vue'

const eventBusEmit = inject('eventBusEmit')
const formRules = inject('formRules')
const { t } = useI18n()
const emit = defineEmits(['close', 'added'])
const studiesGeneralStore = useStudiesGeneralStore()

const props = defineProps({
  exchangeMode: {
    type: Boolean,
    default: false,
  },
  exchangeActivityUid: {
    type: String,
    default: null,
  },
  order: {
    type: Number,
    default: null,
  },
})

const creationMode = ref('selectFromLibrary')
const activities = ref([])
const activitiesTotal = ref(0)
const currentFlowchartGroup = ref(null)
const flowchartGroups = ref([])
const selectedStudy = ref(null)
const steps = ref([])
const studies = ref([])
const selectedActivities = ref([])
const studyActivities = ref([])
const savedFilters = ref('')
const form = ref({
  name: '',
  activity_groupings: [{}],
  is_data_collected: true,
})
const groups = ref([])
const subgroups = ref([])
const resetLoading = ref(0)
const confirm = ref()
const stepper = ref()
const flowchartGroupForm = ref()
const selectStudiesForm = ref()
const createPlaceholderForm = ref()
const selectionTable = ref()
const selectionLibraryTable = ref()
const selectedOnly = ref(false)
const timeout = ref(null)
const sameGroup = ref(false)
const unifiedGroup = ref(null)

const requestTypes = [
  {
    value: true,
    title: t('StudyActivityForm.request_radio_title'),
    help: t('StudyActivityForm.request_radio_text'),
  },
  {
    value: false,
    title: t('StudyActivityForm.placeholder_radio_title'),
    help: t('StudyActivityForm.placeholder_radio_text'),
  },
]

const activityHeaders = [
  { title: t('_global.library'), key: 'library_name', noFilter: true },
  {
    title: t('StudyActivityForm.flowchart_group'),
    key: 'soa_group',
    noFilter: true,
  },
  {
    title: t('StudyActivity.activity_group'),
    key: 'activity_group.name',
    externalFilterSource: 'concepts/activities/activity-groups$name',
    exludeFromHeader: ['is_data_collected'],
  },
  {
    title: t('StudyActivity.activity_sub_group'),
    key: 'activity_subgroup.name',
    externalFilterSource: 'concepts/activities/activity-sub-groups$name',
    exludeFromHeader: ['is_data_collected'],
  },
  {
    title: t('StudyActivity.activity'),
    key: 'name',
    exludeFromHeader: ['is_data_collected'],
  },
  { title: t('StudyActivity.data_collection'), key: 'is_data_collected' },
  { title: t('_global.status'), key: 'status' },
]

const selectFromStudiesSteps = [
  { name: 'creationMode', title: t('StudyActivityForm.creation_mode_title') },
  {
    name: 'selectFromStudies',
    title: t('StudyActivityForm.select_from_studies_title'),
  },
]
const selectFromLibrarySteps = [
  { name: 'creationMode', title: t('StudyActivityForm.creation_mode_title') },
  {
    name: 'selectFromLibrary',
    title: t('StudyActivityForm.select_from_library_title'),
  },
]
const createPlaceholderSteps = [
  { name: 'creationMode', title: t('StudyActivityForm.creation_mode_title') },
  {
    name: 'createPlaceholder',
    title: t('StudyActivityForm.create_placeholder'),
  },
]
const studyActivityHeaders = [
  { title: t('StudyActivityForm.study_id'), key: 'study_id', noFilter: true },
  { title: t('_global.library'), key: 'activity.library_name', noFilter: true },
  {
    title: t('StudyActivityForm.flowchart_group'),
    key: 'study_soa_group.soa_group_term_name',
  },
  {
    title: t('StudyActivity.activity_group'),
    key: 'study_activity_group.activity_group_name',
    disableColumnFilters: true,
  },
  {
    title: t('StudyActivity.activity_sub_group'),
    key: 'study_activity_subgroup.activity_subgroup_name',
    disableColumnFilters: true,
  },
  { title: t('StudyActivity.activity'), key: 'activity.name' },
  {
    title: t('StudyActivity.data_collection'),
    key: 'activity.is_data_collected',
  },
]
const initialFilters = { status: [statuses.FINAL] }

const filteredSubGroups = computed(() => {
  if (!form.value.activity_groupings[0].activity_group_uid) {
    return []
  }
  return subgroups.value.filter(
    (el) =>
      el.activity_groups.find(
        (o) => o.uid === form.value.activity_groupings[0].activity_group_uid
      ) !== undefined
  )
})

const title = computed(() => {
  if (props.exchangeMode) {
    return t('DetailedFlowchart.exchange_study_activity')
  }
  return t('StudyActivityForm.add_title')
})

const successMessage = computed(() => {
  if (props.exchangeMode) {
    return t('DetailedFlowchart.exchange_success')
  }
  return t('StudyActivityForm.add_success')
})

watch(filteredSubGroups, (value) => {
  if (value.length === 1) {
    form.value.activity_groupings[0].activity_subgroup_uid = value[0].uid
  } else {
    form.value.activity_groupings[0].activity_subgroup_uid = null
  }
})

watch(creationMode, (value) => {
  if (value === 'selectFromStudies') {
    steps.value = selectFromStudiesSteps
  } else if (value === 'selectFromLibrary') {
    steps.value = selectFromLibrarySteps
  } else {
    steps.value = createPlaceholderSteps
  }
  selectedOnly.value = false
  selectedActivities.value = []
  activities.value = []
})

watch(selectedStudy, () => {
  if (selectionTable.value) {
    selectionTable.value.filterTable()
  }
})

steps.value = selectFromLibrarySteps

onMounted(() => {
  terms.getByCodelist('flowchartGroups').then((resp) => {
    flowchartGroups.value = resp.data.items
  })
  study.get({ has_study_activity: true, page_size: 0 }).then((resp) => {
    studies.value = resp.data.items.filter(
      (study) => study.uid !== studiesGeneralStore.selectedStudy.uid
    )
  })
  getGroups()
  study
    .getStudyActivities(studiesGeneralStore.selectedStudy.uid, { page_size: 0 })
    .then((resp) => {
      studyActivities.value = resp.data.items
    })
})

function switchTableItems() {
  if (selectedOnly.value) {
    activities.value = selectedActivities.value
  } else {
    creationMode.value === 'selectFromLibrary'
      ? selectionLibraryTable.value.filterTable()
      : selectionTable.value.filterTable()
  }
}

function close() {
  emit('close')
  selectedActivities.value = []
  currentFlowchartGroup.value = null
  creationMode.value = 'selectFromLibrary'
  steps.value = selectFromLibrarySteps
  selectedStudy.value = null
  form.value = {
    name: '',
    activity_groupings: [{}],
  }
  stepper.value.reset()
}

function getObserver(step) {
  if (step === 1 && creationMode.value === 'selectFromStudies') {
    return selectStudiesForm.value
  } else if (step === 2) {
    return flowchartGroupForm.value
  } else if (step === 3) {
    return createPlaceholderForm.value
  }
}

function placeholderSearch(filters) {
  if (filters.target._value.length >= 3) {
    if (timeout.value) clearTimeout(timeout.value)
    timeout.value = setTimeout(() => {
      getActivities(filters)
    }, 500)
  }
}

function clearSelectedGroups() {
  selectedActivities.value.forEach((activity) => {
    activity.flowchart_group = null
  })
}

function pushActivityToSelected(item) {
  if (!selectedActivities.value.find((activity) => activity.uid === item.uid)) {
    selectedActivities.value.push(item)
  }
}

function getActivities(filters, options) {
  if (creationMode.value === 'createPlaceholder') {
    const params = {
      page_number: options && options.page ? options.page : 1,
      page_size: options && options.itemsPerPage ? options.itemsPerPage : 50,
      total_count: true,
      library_name: libConstants.LIBRARY_SPONSOR,
      filters: `{"*":{"v":["${form.value.name}"]}}`,
    }
    activitiesApi.get(params, 'activities').then((resp) => {
      const items = []
      for (const item of resp.data.items) {
        if (item.activity_groupings.length > 0) {
          for (const grouping of item.activity_groupings) {
            items.push({
              activity_group: {
                name: grouping.activity_group_name,
                uid: grouping.activity_group_uid,
              },
              activity_subgroup: {
                name: grouping.activity_subgroup_name,
                uid: grouping.activity_subgroup_uid,
              },
              item_key:
                item.uid +
                grouping.activity_group_uid +
                grouping.activity_subgroup_uid,
              ...item,
            })
          }
        } else {
          items.push({
            activity_group: { name: '', uid: '' },
            activity_subgroup: { name: '', uid: '' },
            item_key: item.uid,
            ...item,
          })
        }
      }
      activities.value = items
      activitiesTotal.value = resp.data.total
    })
    return
  } else if (creationMode.value === 'selectFromStudies') {
    const params = {
      page_number: options ? options.page : 1,
      page_size: options ? options.itemsPerPage : 15,
      total_count: true,
    }
    if (filters) {
      params.filters = JSON.parse(filters)
    } else {
      params.filters = {}
    }
    params.filters.study_uid = { v: [selectedStudy.value.uid] }
    params.filters['activity.library_name'] = {
      v: [libConstants.LIBRARY_SPONSOR],
    }
    params.filters['activity.status'] = {
      v: [statuses.FINAL],
    }
    study.getAllStudyActivities(params).then((resp) => {
      const items = resp.data.items
      items.forEach((el) => {
        el.study_id =
          studies.value[
            studies.value.findIndex((study) => study.uid === el.study_uid)
          ].current_metadata.identification_metadata.study_id
      })
      const result = []
      for (const item of items) {
        let grouping = null
        if (item.activity.activity_groupings.length > 0) {
          if (item.study_activity_group && item.study_activity_subgroup) {
            grouping = item.activity.activity_groupings.find(
              (o) =>
                o.activity_group_uid ===
                  item.study_activity_group.activity_group_uid &&
                o.activity_subgroup_uid ===
                  item.study_activity_subgroup.activity_subgroup_uid
            )
          }
        }
        if (grouping) {
          result.push({
            ...item,
            activity: {
              activity_group: {
                name: grouping.activity_group_name,
                uid: grouping.activity_group_uid,
              },
              activity_subgroup: {
                name: grouping.activity_subgroup_name,
                uid: grouping.activity_subgroup_uid,
              },
              ...item.activity,
            },
            item_key:
              item.activity.uid +
              grouping.activity_group_uid +
              grouping.activity_subgroup_uid,
          })
        } else {
          result.push({
            ...item,
            activity: {
              ...item.activity,
              activity_group: { name: '', uid: '' },
              activity_subgroup: { name: '', uid: '' },
            },
            item_key: item.activity.uid,
          })
        }
      }
      activities.value = result
      if (selectedActivities.value.length > 0) {
        for (const sa of selectedActivities.value) {
          activities.value[
            activities.value.indexOf(
              activities.value.find((ac) => ac.item_key === sa.item_key)
            )
          ] = sa
        }
      }
      activitiesTotal.value = resp.data.total
    })
    return
  }
  if (filters !== undefined && !_isEqual(filters, savedFilters.value)) {
    // New filters, also reset current page
    savedFilters.value = filters
  }
  const params = {
    page_number: options ? options.page : 1,
    page_size: options ? options.itemsPerPage : 15,
    library_name: libConstants.LIBRARY_SPONSOR,
    total_count: true,
  }
  if (options && options.sortBy && options.sortBy.length) {
    const ascending = options.sortBy[0].order === 'asc'
    params.sort_by = `{"${options.sortBy[0].key}":${ascending}}`
  }
  if (options.sortBy[0] && options.sortBy[0].key === 'activity_group.name') {
    params.sort_by = JSON.stringify({
      'activity_groupings[0].activity_group_name':
        options.sortBy[0].order === 'desc' ? false : true,
    })
  } else if (
    options.sortBy[0] &&
    options.sortBy[0].key === 'activity_subgroup.name'
  ) {
    params.sort_by = JSON.stringify({
      'activity_groupings[0].activity_subgroup_name':
        options.sortBy[0].order === 'desc' ? false : true,
    })
  }
  if (savedFilters.value && savedFilters.value !== undefined) {
    const filtersObj = JSON.parse(savedFilters.value)
    filtersObj['is_used_by_legacy_instances'] = {
      v: [false],
      op: 'eq',
    }
    if (filtersObj['activity_group.name']) {
      params.activity_group_names = []
      filtersObj['activity_group.name'].v.forEach((value) => {
        params.activity_group_names.push(value)
      })
      delete filtersObj['activity_group.name']
    }
    if (filtersObj['activity_subgroup.name']) {
      params.activity_subgroup_names = []
      filtersObj['activity_subgroup.name'].v.forEach((value) => {
        params.activity_subgroup_names.push(value)
      })
      delete filtersObj['activity_subgroup.name']
    }
    if (filtersObj.name) {
      params.activity_names = []
      filtersObj.name.v.forEach((value) => {
        params.activity_names.push(value)
      })
      delete filtersObj.name
    }
    if (
      Object.keys(filtersObj).length !== 0 &&
      filtersObj.constructor === Object
    ) {
      params.filters = JSON.stringify(filtersObj)
    }
  }
  activitiesApi.get(params, 'activities').then((resp) => {
    const items = []
    for (const item of resp.data.items) {
      if (item.activity_groupings.length > 0) {
        for (const grouping of item.activity_groupings) {
          items.push({
            activity_group: {
              name: grouping.activity_group_name,
              uid: grouping.activity_group_uid,
            },
            activity_subgroup: {
              name: grouping.activity_subgroup_name,
              uid: grouping.activity_subgroup_uid,
            },
            item_key:
              item.uid +
              grouping.activity_group_uid +
              grouping.activity_subgroup_uid,
            ...item,
          })
        }
      } else {
        items.push({
          activity_group: { name: '', uid: '' },
          activity_subgroup: { name: '', uid: '' },
          item_key: item.uid,
          ...item,
        })
      }
    }
    activities.value = items
    if (selectedActivities.value.length > 0) {
      for (const sa of selectedActivities.value) {
        activities.value[
          activities.value.indexOf(
            activities.value.find((ac) => ac.item_key === sa.item_key)
          )
        ] = sa
      }
    }
    activitiesTotal.value = resp.data.total
  })
}

function modifyFilters(jsonFilter, params, externalFilterSource) {
  if (jsonFilter['activity_group.name']) {
    params.activity_group_names = []
    jsonFilter['activity_group.name'].v.forEach((value) => {
      params.activity_group_names.push(value)
    })
    delete jsonFilter['activity_group.name']
  }
  if (jsonFilter['activity_subgroup.name']) {
    params.activity_subgroup_names = []
    jsonFilter['activity_subgroup.name'].v.forEach((value) => {
      params.activity_subgroup_names.push(value)
    })
    delete jsonFilter['activity_subgroup.name']
  }
  if (jsonFilter.name) {
    params.activity_names = []
    jsonFilter.name.v.forEach((value) => {
      params.activity_names.push(value)
    })
    delete jsonFilter.name
  }
  if (creationMode.value === 'selectFromLibrary') {
    jsonFilter.library_name = { v: [libConstants.LIBRARY_SPONSOR] }
  } else {
    jsonFilter['activity.library_name'] = { v: [libConstants.LIBRARY_SPONSOR] }
  }
  if (!externalFilterSource) {
    if (creationMode.value === 'selectFromStudies') {
      jsonFilter['activity.is_used_by_legacy_instances'] = {
        v: [false],
        op: 'eq',
      }
    } else {
      jsonFilter['is_used_by_legacy_instances'] = { v: [false], op: 'eq' }
    }
  }
  const filters = {
    jsonFilter: jsonFilter,
    params: params,
  }
  return filters
}

function selectAllActivities() {
  for (const activity of activities.value) {
    if (
      !isActivitySelected(activity) &&
      !isActivityNotFinal(activity) &&
      !isActivityRequested(activity)
    ) {
      selectedActivities.value.push(activity)
    }
  }
}

function isGroupingValid(studyActivity) {
  if (!studyActivity.latest_activity) {
    return true
  }
  let found = false
  for (const grouping of studyActivity.latest_activity.activity_groupings) {
    if (
      studyActivity.study_activity_group.activity_group_uid ===
        grouping.activity_group_uid &&
      studyActivity.study_activity_subgroup.activity_subgroup_uid ===
        grouping.activity_subgroup_uid
    ) {
      found = true
      break
    }
  }
  return found
}

function multipleSelectedInExchangeMode(item) {
  if (selectedActivities.value.length > 0 && props.exchangeMode) {
    if (item && selectedActivities.value[0].uid === item.uid) {
      return false
    }
    return true
  }
  return false
}

async function selectAllStudyActivities() {
  for (const studyActivity of activities.value) {
    if (
      !isStudyActivitySelected(studyActivity) &&
      !isStudyActivityRequested(studyActivity) &&
      isGroupingValid(studyActivity)
    ) {
      const copy = { ...studyActivity }
      selectedActivities.value.push(copy)
    }
  }
}

function isActivitySelected(activity) {
  if (studyActivities.value) {
    let selected
    if (studyActivities.value.length) {
      selected = studyActivities.value.find(
        (item) =>
          item.activity.uid === activity.uid &&
          item.study_activity_group.activity_group_uid ===
            activity.activity_group.uid &&
          item.study_activity_subgroup.activity_subgroup_uid ===
            activity.activity_subgroup.uid
      )
    }
    return selected !== undefined
  }
  return false
}

function isActivityNotFinal(activity) {
  return activity.status !== statuses.FINAL
}

function isActivityRequested(activity) {
  return activity.library_name === libConstants.LIBRARY_REQUESTED
}

function isStudyActivityRequested(activity) {
  return activity.activity.library_name === libConstants.LIBRARY_REQUESTED
}

function isStudyActivitySelected(studyActivity) {
  let selected
  if (!selected && studyActivities.value.length) {
    selected = studyActivities.value.find(
      (item) => item.activity.uid === studyActivity.activity.uid
    )
  }
  return selected !== undefined
}

function getCreationPayload(selectedItem) {
  function getPayloadFromActivity() {
    const result = {
      soa_group_term_uid: sameGroup.value
        ? unifiedGroup.value.term_uid
        : selectedItem.flowchart_group.term_uid,
      activity_uid: selectedItem.uid,
      order: props.order,
    }
    if (form.value.activity_groupings) {
      result.activity_group_uid = selectedItem.activity_group.uid
      result.activity_subgroup_uid = selectedItem.activity_subgroup.uid
    }
    return result
  }

  function getPayloadFromStudyActivity() {
    return {
      soa_group_term_uid: selectedItem.study_soa_group.soa_group_term_uid,
      activity_uid: selectedItem.activity.uid,
      activity_group_uid: selectedItem.study_activity_group.activity_group_uid,
      activity_subgroup_uid:
        selectedItem.study_activity_subgroup.activity_subgroup_uid,
      order: props.order,
    }
  }

  const payloadFuncByCreationMode = {
    selectFromStudies: getPayloadFromStudyActivity,
    selectFromLibrary: getPayloadFromActivity,
    createPlaceholder: getPayloadFromActivity,
  }
  return payloadFuncByCreationMode[creationMode.value]()
}

async function batchCreateStudyActivities() {
  const operations = []
  for (const item of selectedActivities.value) {
    let payload = getCreationPayload(item)
    operations.push({
      method: 'POST',
      content: payload,
    })
  }
  await study.studyActivityBatchOperations(
    studiesGeneralStore.selectedStudy.uid,
    operations
  )
}

async function exchangeStudyActivity() {
  for (const item of selectedActivities.value) {
    let payload = getCreationPayload(item)
    payload.show_activity_in_protocol_flowchart = true
    await study.exchangeStudyActivity(
      studiesGeneralStore.selectedStudy.uid,
      props.exchangeActivityUid,
      payload
    )
  }
}

async function submit() {
  if (
    creationMode.value !== 'selectFromLibrary' &&
    creationMode.value !== 'selectFromStudies' &&
    selectedActivities.value.length === 0
  ) {
    form.value.library_name = libConstants.LIBRARY_REQUESTED
    form.value.name_sentence_case = form.value.name.toLowerCase()
    const { valid } = await createPlaceholderForm.value.validate()
    if (!valid) {
      resetLoading.value += 1
      return
    }
    if (_isEmpty(form.value.activity_groupings[0])) {
      delete form.value.activity_groupings
    }
    const createdActivity = await activitiesApi.create(form.value, 'activities')
    await activitiesApi
      .approve(createdActivity.data.uid, 'activities')
      .then((resp) => {
        const activity = {
          ...resp.data,
          item_key: resp.data.uid,
        }
        if (resp.data.activity_groupings.length > 0) {
          activity.activity_group = {
            uid: resp.data.activity_groupings[0].activity_group_uid,
          }
          activity.activity_subgroup = {
            uid: resp.data.activity_groupings[0].activity_subgroup_uid,
          }
          activity.item_key =
            resp.data.uid +
            resp.data.activity_groupings[0].activity_group_uid +
            resp.data.activity_groupings[0].activity_subgroup_uid
        }
        activity.flowchart_group = { ...form.value.flowchart_group }
        selectedActivities.value.push(activity)
      })
  }
  if (
    !selectedActivities.value.length &&
    creationMode.value !== 'createPlaceholder'
  ) {
    eventBusEmit('notification', {
      type: 'info',
      msg: t('StudyActivityForm.select_activities_info'),
    })
    resetLoading.value += 1
    return
  }

  // Check if every activity has SoA group selected
  if (
    ['createPlaceholder', 'selectFromLibrary'].indexOf(creationMode.value) !==
    -1
  ) {
    if (sameGroup.value && !unifiedGroup.value) {
      eventBusEmit('notification', {
        type: 'info',
        msg: t('StudyActivityForm.soa_group_required_info'),
      })
      resetLoading.value += 1
      return
    } else if (!sameGroup.value) {
      for (const activity of selectedActivities.value) {
        if (!activity.flowchart_group) {
          eventBusEmit('notification', {
            type: 'info',
            msg: t('StudyActivityForm.soa_group_required_info'),
          })
          resetLoading.value += 1
          return
        }
      }
    }
  }
  try {
    if (!props.exchangeMode) {
      await batchCreateStudyActivities()
    } else {
      await exchangeStudyActivity()
    }
  } catch (error) {
    stepper.value.loading = false
    return
  }
  eventBusEmit('notification', {
    type: 'success',
    msg: successMessage,
  })
  emit('added')
  close()
}

function getGroups() {
  const params = {
    page_size: 0,
    filters: { status: { v: [statuses.FINAL], op: 'co' } },
    sort_by: JSON.stringify({ name: true }),
  }
  activitiesApi.get(params, 'activity-groups').then((resp) => {
    groups.value = resp.data.items
  })
  activitiesApi.get(params, 'activity-sub-groups').then((resp) => {
    subgroups.value = resp.data.items
  })
}
</script>

<style scoped lang="scss">
.v-stepper {
  background-color: rgb(var(--v-theme-dfltBackground)) !important;
  box-shadow: none;
}

.step-title {
  color: rgb(var(--v-theme-secondary)) !important;
}
.choice {
  border: 1px solid #dbdddf;
  cursor: pointer;
  height: 120px;
  padding: 14px 16px;

  &--selected {
    background-color: rgb(var(--v-theme-nnSeaBlue100));
  }

  &--disabled {
    cursor: unset;
    opacity: 0.5;
  }

  .title {
    font-size: 14px;
  }
  .text {
    font-size: 14px;
  }
}
.label--disabled {
  opacity: 0.5;
}
</style>
