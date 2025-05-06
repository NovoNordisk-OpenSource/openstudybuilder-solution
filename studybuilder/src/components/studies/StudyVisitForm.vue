<template>
  <HorizontalStepperForm
    ref="stepperRef"
    :title="title"
    :steps="steps"
    :form-observer-getter="getObserver"
    data-cy="form-body"
    :help-items="helpItems"
    :edit-data="form"
    :extra-step-validation="extraValidation"
    @close="close"
    @save="submit"
    @change="onTabChange"
  >
    <template #[`step.visitType`]>
      <v-form ref="observer_1">
        <v-row>
          <v-col>
            <v-radio-group
              v-if="!loading"
              v-model="form.visit_class"
              :rules="[formRules.required]"
              color="primary"
            >
              <v-radio
                v-for="visitClass in visitClasses"
                :key="visitClass.value"
                :label="visitClass.label"
                :value="visitClass.value"
                :data-cy="visitClass.value"
              />
            </v-radio-group>
            <v-skeleton-loader v-else type="card" />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #[`step.epoch`]>
      <v-form ref="observer_2">
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="studyEpoch"
              data-cy="study-period"
              :label="$t('StudyVisitForm.period')"
              :items="filteredPeriods"
              item-title="epoch_name"
              item-value="uid"
              :rules="[formRules.required]"
              clearable
              :loading="loading"
              class="required"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #[`step.details`]>
      <v-row>
        <v-col cols="8">
          <v-form ref="observer_3">
            <div class="sub-title">
              {{ $t('StudyVisitForm.timing') }}
            </div>
            <v-row class="mt-2">
              <v-col
                v-if="form.visit_class === visitConstants.CLASS_SINGLE_VISIT"
                cols="12"
              >
                <v-radio-group
                  v-model="form.visit_subclass"
                  inline
                  hide-details
                  color="primary"
                >
                  <v-radio
                    :label="$t('StudyVisitForm.single_visit')"
                    data-cy="single-visit"
                    :value="visitConstants.SUBCLASS_SINGLE_VISIT"
                  />
                  <v-radio
                    :label="$t('StudyVisitForm.anchor_visit_in_group')"
                    data-cy="anchor-visit-in-visit-group"
                    :value="
                      visitConstants.SUBCLASS_ANCHOR_VISIT_IN_GROUP_OF_SUBV
                    "
                  />
                  <v-radio
                    v-if="anchorVisitsInSubgroup.length"
                    :label="$t('StudyVisitForm.additional_sub_visit')"
                    :value="
                      visitConstants.SUBCLASS_ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV
                    "
                  />
                  <v-radio
                    :label="$t('StudyVisitForm.repeating_visit')"
                    data-cy="anchor-visit-in-visit-group"
                    :value="visitConstants.SUBCLASS_REPEATING_VISIT"
                  />
                </v-radio-group>
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="4">
                <v-autocomplete
                  v-model="form.visit_type_uid"
                  :label="$t('StudyVisitForm.visit_type')"
                  data-cy="visit-type"
                  :items="visitTypes"
                  item-title="sponsor_preferred_name"
                  item-value="term_uid"
                  :rules="[formRules.required]"
                  clearable
                  :disabled="visitTypeDisabled"
                  class="required"
                  @update:model-value="getVisitPreview"
                />
              </v-col>
              <v-col cols="4">
                <v-autocomplete
                  v-model="form.visit_contact_mode_uid"
                  :label="$t('StudyVisitForm.contact_mode')"
                  data-cy="contact-mode"
                  :items="contactModes"
                  item-title="name.sponsor_preferred_name"
                  item-value="term_uid"
                  :rules="[formRules.required]"
                  clearable
                  class="required"
                  @update:model-value="getVisitPreview"
                />
              </v-col>
              <v-col
                v-if="form.visit_class !== visitConstants.CLASS_SPECIAL_VISIT"
                cols="4"
              >
                <div class="d-flex">
                  <v-checkbox
                    v-if="displayAnchorVisitFlag"
                    v-model="form.is_global_anchor_visit"
                    :label="$t('StudyVisitForm.anchor_visit')"
                    data-cy="anchor-visit-checkbox"
                    :hint="$t('StudyVisitForm.anchor_visit_hint')"
                    persistent-hint
                  />
                  <v-text-field
                    v-model="currentAnchorVisit"
                    :label="$t('StudyVisitForm.current_anchor_visit')"
                    readonly
                    variant="filled"
                    class="ml-4"
                  />
                </div>
              </v-col>
            </v-row>
            <v-row v-if="milestoneAvailable">
              <v-checkbox
                v-model="form.is_soa_milestone"
                class="ml-4 pt-0 mt-0"
                :label="$t('StudyVisitForm.soa_milestone')"
                density="compact"
                color="primary"
              />
            </v-row>
            <v-row v-if="showTimingFields">
              <v-col cols="4">
                <v-autocomplete
                  v-if="
                    form.visit_subclass !==
                      visitConstants.SUBCLASS_ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV &&
                    form.visit_class !== visitConstants.CLASS_SPECIAL_VISIT
                  "
                  v-model="form.time_reference_uid"
                  :label="$t('StudyVisitForm.time_reference')"
                  data-cy="time-reference"
                  :items="timeReferences"
                  item-title="name.sponsor_preferred_name"
                  item-value="term_uid"
                  :rules="[formRules.required]"
                  clearable
                  :disabled="form.is_global_anchor_visit"
                  class="required"
                  @update:model-value="getVisitPreview"
                />
                <v-autocomplete
                  v-else
                  v-model="form.visit_sublabel_reference"
                  :label="$t('StudyVisitForm.time_reference')"
                  data-cy="time-reference"
                  :items="timerefVisits"
                  item-title="visit_name"
                  item-value="uid"
                  :rules="[formRules.required]"
                  clearable
                  @update:model-value="getVisitPreview"
                />
              </v-col>
              <v-col
                v-if="form.visit_class !== visitConstants.CLASS_SPECIAL_VISIT"
                cols="4"
              >
                <v-autocomplete
                  v-model="form.time_unit"
                  :label="$t('StudyVisitForm.time_unit_name')"
                  data-cy="time-unit"
                  :items="epochsStore.studyTimeUnits"
                  item-title="name"
                  item-value="uid"
                  return-object
                  :rules="[formRules.required]"
                  clearable
                  class="required"
                  @update:model-value="getVisitPreview"
                />
              </v-col>
              <v-col
                v-if="form.visit_class !== visitConstants.CLASS_SPECIAL_VISIT"
                cols="4"
              >
                <v-text-field
                  v-model="form.time_value"
                  type="number"
                  :label="$t('StudyVisitForm.time_dist')"
                  data-cy="visit-timing"
                  clearable
                  :rules="[formRules.required]"
                  :disabled="disableTimeValue"
                  class="required"
                  @blur="getVisitPreview"
                />
              </v-col>
            </v-row>
            <v-row
              v-if="
                form.visit_class === visitConstants.CLASS_SINGLE_VISIT &&
                form.visit_subclass === visitConstants.SUBCLASS_REPEATING_VISIT
              "
            >
              <v-autocomplete
                v-model="form.repeating_frequency_uid"
                :label="$t('StudyVisitForm.repeating_frequency')"
                :items="frequencies"
                item-title="name.sponsor_preferred_name"
                item-value="term_uid"
                clearable
                @update:model-value="getVisitPreview"
              />
            </v-row>
            <v-alert
              v-if="
                form.visit_class === visitConstants.CLASS_MANUALLY_DEFINED_VISIT
              "
              density="compact"
              type="warning"
              class="text-white"
              :text="$t('StudyVisitForm.visit_number_uniqueness_warning')"
            />
            <v-row>
              <v-col cols="6">
                <v-row>
                  <v-col cols="6">
                    <v-text-field
                      v-model="form.visit_name"
                      :label="$t('StudyVisitForm.visit_name')"
                      data-cy="visit-name"
                      :disabled="visitNameDisabled"
                      :loading="previewLoading"
                      :rules="requiredIfManuallyDefinedVisit"
                      @blur="getVisitPreview"
                    />
                  </v-col>
                  <v-col cols="6">
                    <v-text-field
                      v-model="form.visit_short_name"
                      :label="$t('StudyVisitForm.visit_short_name')"
                      data-cy="visit-short-name"
                      :disabled="visitShortNameDisabled"
                      :loading="previewLoading"
                      :rules="requiredIfManuallyDefinedVisit"
                      @blur="getVisitPreview"
                    />
                  </v-col>
                  <v-col cols="6">
                    <v-text-field
                      v-model="form.visit_number"
                      :label="$t('StudyVisitForm.visit_number')"
                      data-cy="visit-number"
                      type="number"
                      :disabled="visitNumberDisabled"
                      :loading="previewLoading"
                      :rules="requiredIfManuallyDefinedVisit"
                      @blur="getVisitPreview"
                    />
                  </v-col>
                  <v-col cols="6">
                    <v-text-field
                      v-model="form.unique_visit_number"
                      :label="$t('StudyVisitForm.unique_visit_number')"
                      type="number"
                      data-cy="visit-unique-number"
                      :disabled="visitUniqueNumberDisabled"
                      :loading="previewLoading"
                      :rules="requiredIfManuallyDefinedVisit"
                      @blur="getVisitPreview"
                    />
                  </v-col>
                </v-row>
              </v-col>

              <template
                v-if="
                  form.visit_class === visitConstants.CLASS_SINGLE_VISIT ||
                  form.visit_class ===
                    visitConstants.CLASS_MANUALLY_DEFINED_VISIT
                "
              >
                <v-col cols="6">
                  <v-text-field
                    v-model="form.study_day_label"
                    :label="$t('StudyVisitForm.study_day_label')"
                    data-cy="study-day-label"
                    readonly
                    disabled
                    variant="filled"
                    :loading="previewLoading"
                  />
                  <v-text-field
                    v-model="form.study_week_label"
                    :label="$t('StudyVisitForm.study_week_label')"
                    data-cy="study-week-label"
                    class="mt-6"
                    readonly
                    disabled
                    variant="filled"
                    :loading="previewLoading"
                  />
                </v-col>
              </template>
            </v-row>
            <template
              v-if="
                form.visit_class === visitConstants.CLASS_SINGLE_VISIT ||
                form.visit_class === visitConstants.CLASS_MANUALLY_DEFINED_VISIT
              "
            >
              <div class="sub-title">
                {{ $t('StudyVisitForm.visit_window') }}
              </div>
              <v-alert
                v-if="!disableWindowUnit"
                density="compact"
                type="warning"
                class="text-white"
                :text="$t('StudyVisitForm.visit_window_alert')"
              />
              <div class="d-flex align-center">
                <div class="mr-2 flex-grow-1">
                  <v-row>
                    <v-col>
                      <v-text-field
                        v-model="form.min_visit_window_value"
                        :label="$t('StudyVisitForm.visit_win_min')"
                        data-cy="visit-win-min"
                        clearable
                        :rules="[(value) => formRules.max_value(value, 0)]"
                        type="number"
                      />
                    </v-col>
                  </v-row>
                </div>
                <div class="mr-2 text-secondary text-h4">/</div>
                <div class="mr-2 flex-grow-1">
                  <v-row>
                    <v-col>
                      <v-text-field
                        v-model="form.max_visit_window_value"
                        :label="$t('StudyVisitForm.visit_win_max')"
                        data-cy="visit-win-max"
                        clearable
                        type="number"
                      />
                    </v-col>
                  </v-row>
                </div>
                <div>
                  <v-row>
                    <v-col>
                      <v-autocomplete
                        v-model="form.visit_window_unit_uid"
                        :label="$t('StudyVisitForm.visit_win_unit')"
                        data-cy="visit-win-unit"
                        :items="epochsStore.studyTimeUnits"
                        item-title="name"
                        item-value="uid"
                        style="width: 200px"
                        :rules="[formRules.required]"
                        clearable
                        class="required"
                        :disabled="disableWindowUnit"
                        @update:model-value="getVisitPreview"
                      />
                    </v-col>
                  </v-row>
                </div>
              </div>
            </template>
            <div class="sub-title mt-8">
              {{ $t('StudyVisitForm.visit_details') }}
            </div>
            <v-row>
              <v-col>
                <v-text-field
                  v-model="form.description"
                  :label="$t('StudyVisitForm.visit_description')"
                  data-cy="visit-description"
                  clearable
                />
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="6">
                <v-autocomplete
                  v-model="form.epoch_allocation_uid"
                  :label="$t('StudyVisitForm.epoch_allocation')"
                  data-cy="epoch-allocation-rule"
                  :items="epochAllocations"
                  item-title="name.sponsor_preferred_name"
                  item-value="term_uid"
                  clearable
                />
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="6">
                <v-textarea
                  v-model="form.start_rule"
                  :label="$t('StudyVisitForm.visit_start_rule')"
                  data-cy="visit-start-rule"
                  clearable
                  rows="1"
                  auto-grow
                />
              </v-col>
              <v-col cols="6">
                <v-textarea
                  v-model="form.end_rule"
                  :label="$t('StudyVisitForm.visit_stop_rule')"
                  data-cy="visit-end-rule"
                  clearable
                  rows="1"
                  auto-grow
                />
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="6" class="d-flex align-center">
                <v-checkbox
                  v-model="form.show_visit"
                  default="true"
                  :label="$t('StudyVisitForm.show_visit')"
                />
              </v-col>
            </v-row>
          </v-form>
        </v-col>
        <v-col cols="4" class="d-flex justify-center">
          <v-data-iterator
            :items="epochStudyVisits"
            :no-data-text="$t('StudyVisitForm.no_visit_available')"
            :items-per-page="-1"
          >
            <template #bottom />
            <template #header>
              <div class="sub-title">
                {{ $t('StudyVisitForm.existing_visits') }}<br />{{
                  $t('StudyVisitForm.names_and_timing')
                }}
              </div>
            </template>
            <template #default="{ items }">
              <v-card class="data-iterator">
                <v-list>
                  <v-list-item v-for="item in items" :key="item.uid" cols="12">
                    {{ item.raw.visit_name }} -
                    <template
                      v-if="['day', 'days'].includes(form.time_unit.name)"
                      >{{ item.raw.study_day_label }}</template
                    ><template v-else>{{ item.raw.study_week_label }}</template>
                  </v-list-item>
                </v-list>
              </v-card>
            </template>
          </v-data-iterator>
        </v-col>
      </v-row>
    </template>
  </HorizontalStepperForm>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
</template>

<script setup>
import epochs from '@/api/studyEpochs'
import terms from '@/api/controlledTerminology/terms'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import visitConstants from '@/constants/visits'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useEpochsStore } from '@/stores/studies-epochs'
import { inject, ref, watch, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

const eventBusEmit = inject('eventBusEmit')
const formRules = inject('formRules')
const { t } = useI18n()
const emit = defineEmits(['close', 'refresh'])
const epochsStore = useEpochsStore()
const studiesGeneralStore = useStudiesGeneralStore()
const stepperRef = ref()
const observer_1 = ref()
const observer_2 = ref()
const observer_3 = ref()

const props = defineProps({
  studyVisit: {
    type: Object,
    default: undefined,
  },
  firstVisit: Boolean,
  opened: Boolean,
})

const anchorVisitsInSubgroup = ref([])
const anchorVisitsForSpecialVisit = ref([])
const currentAnchorVisit = ref(null)
const disableTimeValue = ref(false)
const form = ref({})
const helpItems = ref([
  'StudyVisitForm.vtype_step_label',
  'StudyVisitForm.period',
  'StudyVisitForm.single_anchor_addtional',
  'StudyVisitForm.visit_type',
  'StudyVisitForm.contact_mode',
  'StudyVisitForm.anchor_visit',
  'StudyVisitForm.current_anchor_visit',
  'StudyVisitForm.time_reference',
  'StudyVisitForm.time_value',
  'StudyVisitForm.time_unit',
  'StudyVisitForm.visit_name',
  'StudyVisitForm.visit_short_name',
  'StudyVisitForm.study_day_label',
  'StudyVisitForm.study_week_label',
  'StudyVisitForm.visit_window_min',
  'StudyVisitForm.visit_window_max',
  'StudyVisitForm.visit_win_unit',
  'StudyVisitForm.visit_description',
  'StudyVisitForm.epoch_allocation',
  'StudyVisitForm.visit_start_rule',
  'StudyVisitForm.visit_stop_rule',
  'StudyVisitForm.duplicate_visit',
])
const globalAnchorVisit = ref(null)
const periods = ref([])
const steps = ref([
  { name: 'visitType', title: t('StudyVisitForm.vtype_step_label') },
  { name: 'epoch', title: t('StudyVisitForm.epoch_step_label') },
  {
    name: 'details',
    title: t('StudyVisitForm.details_step_label'),
  },
])
const timeReferences = ref([])
const visitTypes = ref([])
const loading = ref(true)
const previewLoading = ref(false)
const contactModes = ref([])
const epochAllocations = ref([])
const studyEpoch = ref('')
const studyVisits = ref([])
const epochsData = ref([])
const frequencies = ref([])

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
const milestoneAvailable = computed(() => {
  if (
    form.value.visit_type_uid &&
    [
      visitConstants.VISIT_TYPE_NON_VISIT,
      visitConstants.VISIT_TYPE_UNSCHEDULED,
    ].indexOf(
      visitTypes.value.find(
        (type) => type.term_uid === form.value.visit_type_uid
      ).sponsor_preferred_name
    ) === -1
  ) {
    return true
  }
  return false
})
const selectedStudy = computed(() => {
  return studiesGeneralStore.selectedStudy
})
const groups = computed(() => {
  return epochsStore.allowedConfigs
})
const displayAnchorVisitFlag = computed(() => {
  return (
    form.value.visit_class !== visitConstants.CLASS_MANUALLY_DEFINED_VISIT &&
    (globalAnchorVisit.value === null ||
      (props.studyVisit &&
        props.studyVisit.uid === globalAnchorVisit.value.uid))
  )
})
const title = computed(() => {
  return props.studyVisit
    ? t('StudyVisitForm.edit_title')
    : t('StudyVisitForm.add_title')
})
const filteredPeriods = computed(() => {
  if (
    form.value.visit_class === visitConstants.CLASS_SPECIAL_VISIT ||
    form.value.visit_class === visitConstants.CLASS_SINGLE_VISIT ||
    form.value.visit_class === visitConstants.CLASS_MANUALLY_DEFINED_VISIT
  ) {
    return periods.value.filter(
      (item) => item.epoch_name !== visitConstants.EPOCH_BASIC
    )
  }
  if (periods.value) {
    return periods.value.filter(
      (item) => item.epoch_name === visitConstants.EPOCH_BASIC
    )
  }
  return []
})
const timerefVisits = computed(() => {
  if (
    form.value.visit_subclass ===
    visitConstants.SUBCLASS_ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV
  ) {
    return anchorVisitsInSubgroup.value
  } else if (form.value.visit_class === visitConstants.CLASS_SPECIAL_VISIT) {
    return anchorVisitsForSpecialVisit.value
  }
  return studyVisits.value
})
const epochStudyVisits = computed(() => {
  return studyVisits.value.filter(
    (item) => item.study_epoch_uid === studyEpoch.value
  )
})
const visitNameDisabled = computed(() => {
  return form.value.visit_class !== visitConstants.CLASS_MANUALLY_DEFINED_VISIT
})
const visitShortNameDisabled = computed(() => {
  return form.value.visit_class !== visitConstants.CLASS_MANUALLY_DEFINED_VISIT
})
const visitTypeDisabled = computed(() => {
  const allowedClasses = [
    visitConstants.CLASS_SINGLE_VISIT,
    visitConstants.CLASS_SPECIAL_VISIT,
    visitConstants.CLASS_MANUALLY_DEFINED_VISIT,
  ]
  return allowedClasses.indexOf(form.value.visit_class) === -1
})
const visitNumberDisabled = computed(() => {
  return form.value.visit_class !== visitConstants.CLASS_MANUALLY_DEFINED_VISIT
})
const visitUniqueNumberDisabled = computed(() => {
  return (
    form.value.visit_class === visitConstants.CLASS_SINGLE_VISIT ||
    form.value.visit_class === visitConstants.CLASS_SPECIAL_VISIT ||
    form.value.visit_class === visitConstants.CLASS_NON_VISIT ||
    form.value.visit_class === visitConstants.CLASS_UNSCHEDULED_VISIT
  )
})
const showTimingFields = computed(() => {
  return (
    form.value.visit_class === visitConstants.CLASS_SINGLE_VISIT ||
    form.value.visit_class === visitConstants.CLASS_SPECIAL_VISIT ||
    form.value.visit_class === visitConstants.CLASS_MANUALLY_DEFINED_VISIT
  )
})
const requiredIfManuallyDefinedVisit = computed(() => {
  return form.value.visit_class === visitConstants.CLASS_MANUALLY_DEFINED_VISIT
    ? [formRules.required]
    : []
})
const disableWindowUnit = computed(() => {
  if (atLeastOneNormalVisit.value) {
    return props.studyVisit
      ? studyVisits.value.length > 1
      : studyVisits.value.length > 0
  }
  return false
})
const atLeastOneNormalVisit = computed(() => {
  for (let index = studyVisits.value.length - 1; index >= 0; index--) {
    if (
      [
        visitConstants.CLASS_NON_VISIT,
        visitConstants.CLASS_UNSCHEDULED_VISIT,
      ].indexOf(studyVisits.value[index].visit_class) === -1
    ) {
      return true
    }
  }
  return false
})

watch(
  () => props.studyVisit,
  (value) => {
    if (value) {
      epochs.getStudyVisit(selectedStudy.value.uid, value.uid).then((resp) => {
        form.value = resp.data
        form.value.time_unit = epochsStore.studyTimeUnits.find(
          (unit) => unit.uid === form.value.time_unit_uid
        )
      })
    }
  },
  { immediate: true }
)
watch(
  () => props.opened,
  (value) => {
    if (value) {
      callbacks()
    }
  }
)
watch(studyEpoch, (value) => {
  if (!value) {
    return
  }
  form.value.study_epoch_uid = value
  terms.getNamesByCodelist('visitTypes', { page_size: 0 }).then((resp) => {
    visitTypes.value = resp.data.items
    terms.getByCodelist('timepointReferences').then((resp) => {
      timeReferences.value = resp.data.items
      if (
        form.value.visit_class === visitConstants.CLASS_UNSCHEDULED_VISIT &&
        visitTypes.value.length
      ) {
        setVisitType(visitConstants.VISIT_TYPE_UNSCHEDULED)
      }
      if (
        form.value.visit_class === visitConstants.CLASS_NON_VISIT &&
        visitTypes.value.length
      ) {
        setVisitType(visitConstants.VISIT_TYPE_NON_VISIT)
      }
    })
  })
  if (
    form.value.visit_class === visitConstants.CLASS_NON_VISIT ||
    form.value.visit_class === visitConstants.CLASS_UNSCHEDULED_VISIT
  ) {
    setEpochAllocationRule(visitConstants.DATE_CURRENT_VISIT)
  } else {
    const studyEpochConst = periods.value.find((item) => item.uid === value)
    if (
      studyEpochConst.epoch_name === visitConstants.EPOCH_TREATMENT ||
      studyEpochConst.epoch_name === visitConstants.EPOCH_TREATMENT_1
    ) {
      epochs
        .getAmountOfVisitsInStudyEpoch(
          selectedStudy.value.uid,
          studyEpochConst.uid
        )
        .then((resp) => {
          const amountOfVisitsInTreatment = resp.data
          if (amountOfVisitsInTreatment === 0) {
            setEpochAllocationRule(visitConstants.PREVIOUS_VISIT)
          } else {
            setEpochAllocationRule(visitConstants.CURRENT_VISIT)
          }
        })
    } else {
      setEpochAllocationRule(visitConstants.CURRENT_VISIT)
    }
  }
  if (form.value.visit_class === visitConstants.CLASS_SPECIAL_VISIT) {
    epochs
      .getAnchorVisitsForSpecialVisit(selectedStudy.value.uid, studyEpoch.value)
      .then((resp) => {
        anchorVisitsForSpecialVisit.value = resp.data
      })
  }
})
watch(
  () => form.value.is_global_anchor_visit,
  (value) => {
    if (value) {
      form.value.time_value = 0
      disableTimeValue.value = true
      form.value.time_reference_uid = timeReferences.value.find(
        (val) =>
          val.name.sponsor_preferred_name ===
          visitConstants.TIMEREF_GLOBAL_ANCHOR_VISIT
      ).term_uid
    } else {
      disableTimeValue.value = false
    }
  }
)
watch(
  () => form.value.visit_class,
  (value) => {
    studyEpoch.value = ''
    if (
      value === visitConstants.CLASS_UNSCHEDULED_VISIT ||
      value === visitConstants.CLASS_NON_VISIT
    ) {
      setStudyEpochToBasic()
      const contactMode = contactModes.value.find(
        (item) =>
          item.name.sponsor_preferred_name ===
          visitConstants.CONTACT_MODE_VIRTUAL_VISIT
      )
      if (contactMode) {
        form.value.visit_contact_mode_uid = contactMode.term_uid
      }
    }
    if (
      value === visitConstants.CLASS_UNSCHEDULED_VISIT &&
      visitTypes.value.length
    ) {
      setVisitType(visitConstants.VISIT_TYPE_UNSCHEDULED)
    }
    if (value === visitConstants.CLASS_NON_VISIT && visitTypes.value.length) {
      setVisitType(visitConstants.VISIT_TYPE_NON_VISIT)
    }
  }
)

onMounted(() => {
  form.value = getInitialFormContent(props.studyVisit)
  callbacks()
})

function extraValidation(step) {
  if (step === 2 && (!studyEpoch.value || studyEpoch.value === '')) {
    return false
  }
  return true
}
function getObserver(step) {
  let result = undefined
  switch (step) {
    case 1:
      result = observer_1.value
      break
    case 2:
      result = observer_2.value
      break
    case 3:
      result = observer_3.value
  }
  return result
}
function close() {
  emit('close')
  form.value = getInitialFormContent()
  stepperRef.value.reset()
}
function getInitialFormContent(item) {
  if (item) {
    return item
  }
  studyEpoch.value = ''
  return {
    is_global_anchor_visit: false,
    visit_class: visitConstants.CLASS_SINGLE_VISIT,
    show_visit: true,
    min_visit_window_value: 0,
    max_visit_window_value: 0,
    visit_subclass: visitConstants.CLASS_SINGLE_VISIT,
  }
}
async function submit() {
  let { valid } = await observer_1.value.validate()
  if (!valid) {
    return
  }
  ;({ valid } = await observer_2.value.validate())
  if (!valid) {
    return
  }
  try {
    if (!props.studyVisit) {
      await addObject()
    } else {
      await updateObject()
    }
    close()
  } catch {
    return
  } finally {
    stepperRef.value.loading = false
  }
  stepperRef.value.reset()
}

async function addObject() {
  const data = JSON.parse(JSON.stringify(form.value))
  data.time_unit_uid = data.time_unit.uid
  delete data.time_unit
  if (
    data.visit_class === visitConstants.CLASS_SPECIAL_VISIT ||
    data.visit_subclass ===
      visitConstants.SUBCLASS_ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV
  ) {
    data.time_reference_uid = timeReferences.value.find(
      (item) =>
        item.name.sponsor_preferred_name ===
        visitConstants.TIMEREF_ANCHOR_VISIT_IN_VISIT_GROUP
    ).term_uid
  } else if (
    data.visit_class !== visitConstants.CLASS_SINGLE_VISIT &&
    data.visit_class !== visitConstants.CLASS_MANUALLY_DEFINED_VISIT
  ) {
    delete data.time_value
    delete data.time_reference_uid
    delete data.min_visit_window_value
    delete data.max_visit_window_value
    delete data.time_unit_uid
  }
  await epochsStore.addStudyVisit({
    studyUid: selectedStudy.value.uid,
    input: data,
  })
  emit('refresh')
  eventBusEmit('notification', { msg: t('StudyVisitForm.add_success') })
}
async function updateObject() {
  const data = JSON.parse(JSON.stringify(form.value))
  if (data.time_unit) {
    data.time_unit_uid = data.time_unit.uid
  }
  delete data.time_unit
  await epochsStore.updateStudyVisit({
    studyUid: selectedStudy.value.uid,
    studyVisitUid: props.studyVisit.uid,
    input: data,
  })
  emit('refresh')
  eventBusEmit('notification', { msg: t('StudyVisitForm.update_success') })
}
function getVisitPreview() {
  if (props.studyVisit) {
    return
  }
  const mandatoryFields = [
    'visit_type_uid',
    'visit_contact_mode_uid',
    'study_epoch_uid',
  ]
  if (
    form.value.visit_class === visitConstants.CLASS_SINGLE_VISIT ||
    form.value.visit_class === visitConstants.CLASS_MANUALLY_DEFINED_VISIT
  ) {
    mandatoryFields.push('time_reference_uid', 'time_value')
    if (
      form.value.visit_class === visitConstants.CLASS_MANUALLY_DEFINED_VISIT
    ) {
      mandatoryFields.push(
        'visit_name',
        'visit_short_name',
        'visit_number',
        'unique_visit_number'
      )
    }
  }
  if (
    form.value.visit_subclass ===
    visitConstants.SUBCLASS_ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV
  ) {
    mandatoryFields[mandatoryFields.indexOf('time_reference_uid')] =
      'visit_sublabel_reference'
  }
  for (const field of mandatoryFields) {
    if (form.value[field] === undefined || form.value[field] === null) {
      return
    }
  }
  const payload = { ...form.value }
  if (
    payload.visit_class !== visitConstants.CLASS_SINGLE_VISIT &&
    payload.visit_class !== visitConstants.CLASS_MANUALLY_DEFINED_VISIT
  ) {
    payload.time_reference_uid = timeReferences.value.find(
      (item) =>
        item.name.sponsor_preferred_name ===
        visitConstants.TIMEREF_GLOBAL_ANCHOR_VISIT
    ).term_uid
    payload.time_value = 0
  }
  if (
    payload.visit_subclass ===
    visitConstants.SUBCLASS_ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV
  ) {
    payload.time_reference_uid = timeReferences.value.find(
      (item) =>
        item.name.sponsor_preferred_name ===
        visitConstants.TIMEREF_GLOBAL_ANCHOR_VISIT
    ).term_uid
  }
  if (
    payload.visit_class === visitConstants.CLASS_SPECIAL_VISIT &&
    !payload.visit_sublabel_reference
  ) {
    return
  }
  payload.time_unit_uid = payload.time_unit.uid
  delete payload.time_unit
  payload.is_global_anchor_visit = false
  previewLoading.value = true

  epochsStore
    .getStudyVisitPreview({ studyUid: selectedStudy.value.uid, input: payload })
    .then((resp) => {
      let fields = []
      if (
        form.value.visit_class !== visitConstants.CLASS_MANUALLY_DEFINED_VISIT
      ) {
        fields = fields.concat([
          'visit_name',
          'visit_short_name',
          'visit_number',
          'unique_visit_number',
        ])
      }
      fields = fields.concat(['study_day_label', 'study_week_label'])
      for (const field of fields) {
        form.value[field] = resp.data[field]
      }
    })
    .finally(() => {
      previewLoading.value = false
    })
}

function callbacks() {
  epochsStore.fetchAllowedConfigs()
  epochs.getGlobalAnchorVisit(selectedStudy.value.uid).then((resp) => {
    globalAnchorVisit.value = resp.data
    if (globalAnchorVisit.value) {
      currentAnchorVisit.value = globalAnchorVisit.value.visit_type_name
    }
  })
  epochs
    .getAnchorVisitsInGroupOfSubvisits(selectedStudy.value.uid)
    .then((resp) => {
      anchorVisitsInSubgroup.value = resp.data
    })
  terms.getByCodelist('epochs').then((resp) => {
    epochsData.value = resp.data.items
    epochs.getStudyEpochs(selectedStudy.value.uid).then((resp) => {
      periods.value = resp.data.items
      periods.value.forEach((item) => {
        epochsData.value.forEach((epochDef) => {
          if (epochDef.term_uid === item.epoch) {
            item.epoch_name = epochDef.name.sponsor_preferred_name
          }
        })
      })
      if (props.studyVisit) {
        studyEpoch.value = props.studyVisit.study_epoch_uid
      }
      loading.value = false
    })
  })
  terms.getByCodelist('contactModes').then((resp) => {
    contactModes.value = resp.data.items
  })
  terms.getByCodelist('repeatingVisitFrequency').then((resp) => {
    frequencies.value = resp.data.items
  })

  terms.getByCodelist('epochAllocations').then((resp) => {
    epochAllocations.value = resp.data.items
  })
  const params = {
    page_size: 50,
    sort_by: JSON.stringify({ order: false }),
  }
  epochs.getStudyVisits(selectedStudy.value.uid, params).then((resp) => {
    studyVisits.value = resp.data.items

    if (!props.studyVisit) {
      const defaultUnit = epochsStore.studyTimeUnits.find(
        (unit) => unit.name === 'days'
      )
      if (studyVisits.value.length > 0 && atLeastOneNormalVisit.value) {
        let lockedUnit = {}
        for (let index = studyVisits.value.length - 1; index >= 0; index--) {
          if (
            [
              visitConstants.CLASS_NON_VISIT,
              visitConstants.CLASS_UNSCHEDULED_VISIT,
            ].indexOf(studyVisits.value[index].visit_class) === -1
          ) {
            lockedUnit = epochsStore.studyTimeUnits.find(
              (unit) =>
                unit.name === studyVisits.value[index].visit_window_unit_name
            )
            break
          }
        }
        form.value.time_unit = defaultUnit
        form.value.visit_window_unit_uid = lockedUnit.uid
      } else {
        form.value.time_unit = defaultUnit
        form.value.visit_window_unit_uid = defaultUnit.uid
      }
    }
  })
}
function onTabChange(number) {
  if (number === 3 && globalAnchorVisit.value === null) {
    eventBusEmit('notification', {
      msg: t('StudyVisitForm.no_anchor_visit'),
      type: 'warning',
    })
  }
}
function setVisitType(value) {
  if (visitTypes.value.length) {
    form.value.visit_type_uid = visitTypes.value.find(
      (item) => item.sponsor_preferred_name === value
    ).term_uid
    getVisitPreview()
  }
}
function setEpochAllocationRule(value) {
  if (epochAllocations.value.length) {
    form.value.epoch_allocation_uid = epochAllocations.value.find(
      (item) => item.name.sponsor_preferred_name === value
    ).term_uid
  }
}
function setStudyEpochToBasic() {
  if (loading.value) {
    return
  }
  if (periods.value.length) {
    studyEpoch.value = periods.value.find(
      (item) => item.epoch_name === visitConstants.EPOCH_BASIC
    )
    if (studyEpoch.value) {
      studyEpoch.value = studyEpoch.value.uid
    }
  }
  if (!studyEpoch.value) {
    const subType = groups.value.find(
      (item) => item.subtype_name === visitConstants.EPOCH_BASIC
    )
    const payload = {
      epoch_subtype: subType.subtype,
      study_uid: selectedStudy.value.uid,
    }
    epochs.getPreviewEpoch(selectedStudy.value.uid, payload).then((resp) => {
      const data = {
        study_uid: selectedStudy.value.uid,
        epoch: resp.epoch,
        epoch_type: subType.type,
        epoch_subtype: subType.subtype,
        color_hash: '#FFFFFF',
      }
      epochs.addStudyEpoch(selectedStudy.value.uid, data).then(() => {
        epochs.getStudyEpochs(selectedStudy.value.uid).then((resp) => {
          periods.value = resp.data.items
          studyEpoch.value = periods.value.find(
            (item) => item.epoch_name === visitConstants.EPOCH_BASIC
          ).uid
        })
      })
    })
  }
}
</script>

<style scoped lang="scss">
.sub-title {
  color: rgb(var(--v-theme-secondary));
  font-weight: 600;
  margin: 10px 0;
  font-size: 1.1em;
}
.data-iterator {
  height: 440px;
  overflow: auto;
}
.text-white {
  color: white !important;
}
</style>
