<template>
  <div
    class="visit-form pa-6"
    :class="{ 'visit-form--with-unsaved-bar': hasChanges }"
    data-cy="study-visit-timeline-form"
  >
    <div class="d-flex align-center mb-4">
      <span class="section-title">{{ $t('StudyVisitForm.timing') }}</span>
      <v-spacer />
      <v-btn
        prepend-icon="mdi-close"
        color="nnBaseBlue"
        variant="tonal"
        rounded="xl"
        data-cy="close-visit-form"
        @click="requestClose"
      >
        {{ $t('_global.close') }}
      </v-btn>
    </div>
    <v-form ref="observer">
      <div
        v-if="!manualMode && !isTechnicalVisit"
        class="d-flex align-center flex-wrap ga-8 mb-2"
      >
        <div class="d-flex align-center">
          <v-switch
            v-model="manuallyDefinedVisit"
            color="nnBaseBlue"
            hide-details
            inset
            class="flex-grow-0 mr-2"
            data-cy="manually-defined-visit-switch"
            @update:model-value="getVisitPreview"
          />
          <span class="mr-1">
            {{ $t('StudyVisitForm.manually_defined_visit') }}
          </span>
          <v-tooltip location="top">
            <template #activator="{ props: tooltipProps }">
              <v-icon v-bind="tooltipProps" size="small">
                mdi-information-outline
              </v-icon>
            </template>
            {{ $t('StudyVisitForm.manually_defined_visit_hint') }}
          </v-tooltip>
        </div>
        <div class="d-flex align-center">
          <v-tooltip
            location="top"
            :disabled="!globalAnchorVisitSwitchDisabled"
          >
            <template #activator="{ props: tooltipProps }">
              <span v-bind="tooltipProps">
                <v-switch
                  v-model="form.is_global_anchor_visit"
                  color="nnBaseBlue"
                  hide-details
                  inset
                  class="flex-grow-0 mr-2"
                  data-cy="global-anchor-visit-switch"
                  :disabled="globalAnchorVisitSwitchDisabled"
                  @update:model-value="getVisitPreview"
                />
              </span>
            </template>
            {{ $t('StudyVisitForm.global_anchor_visit_disabled_hint') }}
          </v-tooltip>
          <span>{{ $t('StudyVisitForm.global_anchor_visit') }}</span>
        </div>
        <div
          v-if="!manuallyDefinedVisit && !isEarlyDiscontinuationVisitType"
          class="d-flex align-center"
        >
          <v-switch
            v-model="isAnchorVisit"
            color="nnBaseBlue"
            hide-details
            inset
            class="flex-grow-0 mr-2"
            data-cy="anchor-visit-in-group-switch"
            @update:model-value="getVisitPreview"
          />
          <span>{{ $t('StudyVisitForm.anchor_visit_in_group') }}</span>
        </div>
        <div
          v-if="!manuallyDefinedVisit && !isFixedWindowVisitType"
          class="d-flex align-center"
        >
          <v-switch
            v-model="isRepeatingVisit"
            color="nnBaseBlue"
            hide-details
            inset
            class="flex-grow-0 mr-2"
            data-cy="repeating-visit-switch"
            @update:model-value="getVisitPreview"
          />
          <span>{{ $t('StudyVisitForm.repeating_visit') }}</span>
        </div>
      </div>

      <!-- What the visit is: both drive every derived value below. -->
      <span class="subsection-title d-block mt-6 mb-2">
        {{ $t('StudyVisitForm.section_definition') }}
      </span>
      <v-row>
        <v-col cols="12" md="3">
          <v-autocomplete
            v-model="form.visit_type_uid"
            :label="$t('StudyVisitForm.visit_type')"
            :items="visitTypes"
            item-title="sponsor_preferred_name"
            item-value="term_uid"
            autocomplete="off"
            clearable
            data-cy="visit-type"
            :rules="[formRules.required]"
            @update:model-value="getVisitPreview"
          />
        </v-col>
        <v-col cols="12" md="3">
          <v-autocomplete
            v-model="form.visit_contact_mode_uid"
            :label="$t('StudyVisitForm.contact_mode')"
            :items="contactModes"
            item-title="sponsor_preferred_name"
            item-value="term_uid"
            autocomplete="off"
            clearable
            data-cy="contact-mode"
            :rules="[formRules.required]"
            @update:model-value="getVisitPreview"
          />
        </v-col>
      </v-row>

      <div v-if="showTechnicalVisitSwitch" class="d-flex align-center mb-2">
        <v-switch
          v-model="technicalVisit"
          color="nnBaseBlue"
          hide-details
          inset
          class="flex-grow-0 mr-2"
          data-cy="technical-visit-switch"
          @update:model-value="getVisitPreview"
        />
        <span>
          {{
            $t('StudyVisitForm.technical_visit', {
              visit_type: technicalVisitTypeLabel,
            })
          }}
        </span>
      </div>

      <!-- Grouping — hidden as a whole for a manually defined visit (always a
         plain single visit), for the technical visit types, neither of
         which ever belongs to a group, and for Early discontinuation, which
         uses this same visit_sublabel_reference field via the Timing
         section's time reference control instead (see isEarlyDiscontinuationVisitType). -->
      <template
        v-if="
          !manuallyDefinedVisit &&
          !manualMode &&
          !isTechnicalVisit &&
          !isEarlyDiscontinuationVisitType
        "
      >
        <span class="subsection-title d-block mt-6 mb-2">
          {{ $t('StudyVisitForm.section_grouping') }}
        </span>
        <v-row>
          <v-col cols="12" md="3">
            <v-autocomplete
              v-model="form.visit_sublabel_reference"
              :label="$t('StudyVisitForm.visit_group') + $t('_global.optional')"
              :placeholder="$t('StudyVisitForm.visit_group_placeholder')"
              :items="visitGroupOptions"
              item-title="visit_name"
              item-value="uid"
              :disabled="isAnchorVisit"
              autocomplete="off"
              clearable
              data-cy="visit-group"
              @update:model-value="getVisitPreview"
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="form.visit_suffix"
              :label="
                $t('StudyVisitForm.visit_suffix') + $t('_global.optional')
              "
              :placeholder="$t('StudyVisitForm.visit_suffix_placeholder')"
              :hint="$t('StudyVisitForm.visit_suffix_hint')"
              :loading="previewLoading"
              autocomplete="off"
              persistent-hint
              data-cy="visit-suffix"
            />
          </v-col>
        </v-row>
      </template>

      <!-- Timing — hidden entirely for technical visits (Unscheduled or
         Non-visit with the Technical visit switch on); for the regular
         Non-visit/Unscheduled/Early discontinuation types, Timing collapses
         to a disabled 0 and ordering in the SoA instead comes from the (now
         required) expected timing. -->
      <template
        v-if="(!hideTimingFields || showExpectedTiming) && !isTechnicalVisit"
      >
        <span class="subsection-title d-block mt-6 mb-2">
          {{ $t('StudyVisitForm.section_timing') }}
        </span>
        <v-row>
          <v-col
            v-if="!manualMode && !isEarlyDiscontinuationVisitType"
            cols="12"
            md="3"
          >
            <v-autocomplete
              v-model="form.time_reference_uid"
              :label="$t('StudyVisitForm.time_reference')"
              :items="timeReferences"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              autocomplete="off"
              :disabled="timeReferenceDisabled"
              clearable
              data-cy="time-reference"
              :rules="[formRules.required]"
              @update:model-value="getVisitPreview"
            />
          </v-col>
          <!-- Early discontinuation visits inherit their timing from another
             Study Visit rather than from a CT term, so this control writes to
             visit_sublabel_reference instead of time_reference_uid — the
             backend resolves the anchor from that same field
             (api/common/utils.py's timeline-building loop). -->
          <v-col
            v-else-if="!manualMode && isEarlyDiscontinuationVisitType"
            cols="12"
            md="3"
          >
            <v-autocomplete
              v-model="form.visit_sublabel_reference"
              :label="$t('StudyVisitForm.time_reference')"
              :items="earlyDiscontinuationReferenceOptions"
              item-title="visit_name"
              item-value="uid"
              autocomplete="off"
              clearable
              data-cy="time-reference"
              :rules="[formRules.required]"
              @update:model-value="getVisitPreview"
            />
          </v-col>
          <v-col
            v-if="!hideTimingFields || isFixedWindowVisitType"
            cols="12"
            md="3"
          >
            <v-text-field
              v-model="form.time_value"
              :label="$t('StudyVisitForm.time_value')"
              type="number"
              autocomplete="off"
              :disabled="isFixedWindowVisitType || form.is_global_anchor_visit"
              :rules="timeValueRules"
              data-cy="visit-timing"
              @blur="getVisitPreview"
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-autocomplete
              v-model="form.time_unit_uid"
              :label="$t('StudyVisitForm.time_unit')"
              :items="timeUnits"
              item-title="name"
              item-value="uid"
              autocomplete="off"
              clearable
              data-cy="time-unit"
              :rules="[formRules.required]"
              @update:model-value="getVisitPreview"
            />
          </v-col>
          <v-col v-if="showExpectedTiming" cols="12" md="3">
            <v-text-field
              v-model="form.expected_time_value"
              :label="$t('StudyVisitForm.expected_timing')"
              type="number"
              autocomplete="off"
              :rules="expectedTimeValueRules"
              data-cy="expected-timing"
            />
          </v-col>
          <!-- Early discontinuation visits have no expected timing of their own
             (their absolute duration comes from the referenced visit above), so
             this slot carries the visit suffix instead — the one other field the
             now-hidden Grouping section used to expose for them. Manual mode
             has no derived naming for it to feed, so it is not asked for there. -->
          <v-col
            v-else-if="isEarlyDiscontinuationVisitType && !manualMode"
            cols="12"
            md="3"
          >
            <v-text-field
              v-model="form.visit_suffix"
              :label="$t('StudyVisitForm.visit_suffix')"
              :placeholder="$t('StudyVisitForm.visit_suffix_placeholder')"
              :hint="$t('StudyVisitForm.visit_suffix_hint')"
              :loading="previewLoading"
              :rules="[formRules.required]"
              autocomplete="off"
              persistent-hint
              data-cy="visit-suffix"
              @blur="getVisitPreview"
            />
          </v-col>
        </v-row>
        <!-- Read-only: derived from the timing above -->
        <v-row v-if="!hideTimingFields">
          <v-col cols="12" md="3">
            <v-text-field
              v-model="form.study_day_label"
              :label="$t('StudyVisitForm.study_day_label')"
              :loading="previewLoading"
              autocomplete="off"
              disabled
              data-cy="study-day-label"
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="form.study_week_label"
              :label="$t('StudyVisitForm.study_week_label')"
              :loading="previewLoading"
              autocomplete="off"
              disabled
              data-cy="study-week-label"
            />
          </v-col>
        </v-row>
      </template>

      <!-- Naming: typed in for manual visits, otherwise filled in by the preview -->
      <span class="subsection-title d-block mt-6 mb-2">
        {{ $t('StudyVisitForm.section_naming') }}
      </span>
      <v-row>
        <v-col cols="12" md="3">
          <v-text-field
            v-model="form.visit_name"
            :label="$t('StudyVisitForm.visit_name')"
            :loading="previewLoading"
            :disabled="!namesAreUserDefined"
            persistent-hint
            autocomplete="off"
            :rules="namesAreUserDefined ? [formRules.required] : []"
            data-cy="visit-name"
            @blur="getVisitPreview"
          />
        </v-col>
        <v-col cols="12" md="3">
          <v-text-field
            v-model="form.visit_short_name"
            :label="$t('StudyVisitForm.visit_short_name')"
            :loading="previewLoading"
            :disabled="!namesAreUserDefined"
            autocomplete="off"
            :rules="namesAreUserDefined ? [formRules.required] : []"
            data-cy="visit-short-name"
            @blur="getVisitPreview"
          />
        </v-col>
        <v-col cols="12" md="3">
          <v-text-field
            v-model="form.unique_visit_number"
            :label="$t('StudyVisitForm.unique_visit_number')"
            :loading="previewLoading"
            :disabled="!namesAreUserDefined"
            type="number"
            autocomplete="off"
            :rules="
              manuallyDefinedVisit || manualMode ? [formRules.required] : []
            "
            data-cy="visit-unique-number"
            @blur="getVisitPreview"
          />
        </v-col>
      </v-row>

      <span class="subsection-title d-block mt-6 mb-2">
        {{ $t('StudyVisitForm.visit_window') }}
      </span>
      <v-row>
        <v-col cols="6" md="2">
          <v-text-field
            v-model="form.min_visit_window_value"
            :label="$t('StudyVisitForm.visit_win_min')"
            type="number"
            autocomplete="off"
            :disabled="isFixedWindowVisitType"
            :rules="[
              formRules.required,
              (value) => formRules.max_value(value, 0),
            ]"
            data-cy="visit-window-min"
          />
        </v-col>
        <v-col cols="6" md="2">
          <v-text-field
            v-model="form.max_visit_window_value"
            :label="$t('StudyVisitForm.visit_win_max')"
            type="number"
            autocomplete="off"
            :disabled="isFixedWindowVisitType"
            :rules="[formRules.required]"
            data-cy="visit-window-max"
          />
        </v-col>
        <v-col cols="12" md="3">
          <v-autocomplete
            v-model="form.visit_window_unit_uid"
            :label="$t('StudyVisitForm.visit_win_unit')"
            :items="timeUnits"
            item-title="name"
            item-value="uid"
            autocomplete="off"
            clearable
            :rules="[formRules.required]"
            data-cy="visit-window-unit"
          />
        </v-col>
      </v-row>

      <div class="d-flex align-center mt-6">
        <span class="subsection-title">
          {{ $t('StudyVisitForm.visit_details') }}{{ $t('_global.optional') }}
        </span>
        <v-btn
          class="ml-4"
          variant="outlined"
          color="nnBaseBlue"
          rounded
          size="small"
          data-cy="toggle-visit-details"
          @click="showDetails = !showDetails"
        >
          {{ showDetails ? $t('_global.hide') : $t('_global.show') }}
        </v-btn>
      </div>
      <v-expand-transition>
        <v-row v-if="showDetails" class="mt-2">
          <v-col cols="12" md="3">
            <v-text-field
              v-model="form.start_rule"
              :label="$t('StudyVisitForm.visit_start_rule')"
              autocomplete="off"
              data-cy="visit-start-rule"
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="form.end_rule"
              :label="$t('StudyVisitForm.visit_stop_rule')"
              autocomplete="off"
              data-cy="visit-stop-rule"
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-autocomplete
              v-model="form.epoch_allocation_uid"
              :label="$t('StudyVisitForm.epoch_allocation')"
              :items="epochAllocations"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              autocomplete="off"
              clearable
              data-cy="epoch-allocation"
            />
          </v-col>
          <v-col v-if="isRepeatingVisit" cols="12" md="3">
            <v-autocomplete
              v-model="form.repeating_frequency_uid"
              :label="$t('StudyVisitForm.repeating_frequency')"
              :items="repeatingFrequencies"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              autocomplete="off"
              clearable
              data-cy="repeating-frequency"
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-autocomplete
              v-model="form.study_epoch_uid"
              :label="$t('StudyVisitForm.study_epoch')"
              :items="epochsStore.studyEpochs"
              item-title="epoch_name"
              item-value="uid"
              autocomplete="off"
              clearable
              data-cy="study-period"
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-textarea
              v-model="form.description"
              :label="$t('StudyVisitForm.visit_description')"
              autocomplete="off"
              rows="2"
              auto-grow
              data-cy="visit-description"
            />
          </v-col>
          <v-col cols="12" md="3" class="d-flex align-start">
            <div class="d-flex align-center">
              <v-switch
                v-model="form.show_visit"
                color="nnBaseBlue"
                hide-details
                inset
                class="flex-grow-0 mr-2"
                data-cy="show-visit-switch"
              />
              <span>{{ $t('StudyVisitForm.show_visit_in_protocol') }}</span>
            </div>
          </v-col>
          <v-col
            v-if="!isTechnicalVisit"
            cols="12"
            md="3"
            class="d-flex align-start"
          >
            <div class="d-flex align-center">
              <v-switch
                v-model="form.is_soa_milestone"
                color="nnBaseBlue"
                hide-details
                inset
                class="flex-grow-0 mr-2"
                data-cy="soa-milestone-switch"
              />
              <span>{{ $t('StudyVisitForm.soa_milestone') }}</span>
            </div>
          </v-col>
        </v-row>
      </v-expand-transition>
    </v-form>

    <StudyVisitUnsavedBar
      :show="hasChanges"
      :saving="saving"
      @discard="discard"
      @save="save"
    />
    <ConfirmDialog ref="confirmRef" />
  </div>
</template>

<script setup>
import { computed, inject, nextTick, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import studyEpochsApi from '@/api/studyEpochs'
import terms from '@/api/controlledTerminology/terms'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import visitConstants from '@/constants/visits'
import { useVisitTimeReferenceTerms } from '@/composables/visitTimeReferenceTerms'
import { useVisitTypeTerms } from '@/composables/visitTypeTerms'
import { useEpochsStore } from '@/stores/studies-epochs'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import StudyVisitUnsavedBar from './StudyVisitUnsavedBar.vue'

const { t } = useI18n()
const notificationHub = inject('notificationHub', null)
const formRules = inject('formRules')
const epochsStore = useEpochsStore()
const studiesGeneralStore = useStudiesGeneralStore()
const {
  contactModes,
  timeReferences,
  globalAnchorTermUid,
  anchorVisitInGroupTermUid,
  virtualVisitContactModeUid,
  fetchVisitTimeReferenceTerms,
} = useVisitTimeReferenceTerms()

const props = defineProps({
  studyVisit: {
    type: Object,
    default: undefined,
  },
})

const emit = defineEmits(['close', 'refresh'])

const observer = ref(null)
const confirmRef = ref(null)
const showDetails = ref(false)
const saving = ref(false)
const previewLoading = ref(false)
const visitTypes = ref([])
const epochAllocations = ref([])
const repeatingFrequencies = ref([])
const allStudyVisits = ref([])
const globalAnchorVisit = ref(null)
// A new visit defaults its units to those of the study's first visit
const firstVisitUnits = ref({
  time_unit_uid: null,
  visit_window_unit_uid: null,
})
// Only offered for regular visits (not technical, manually defined or fixed-window)
const isRepeatingVisit = ref(false)
const form = ref({})
const initialForm = ref('')

const hasChanges = computed(
  () => JSON.stringify(form.value) !== initialForm.value
)

const manuallyDefinedVisit = ref(false)
const isAnchorVisit = ref(false)
// Only offered for the Unscheduled and Non-visit types
const technicalVisit = ref(false)

// Manual mode: visits are named and numbered by hand, so the derived-field rules are off
const manualMode = computed(() => epochsStore.manualVisitMode)

// Whether the user types the visit names or the backend derives them.
const namesAreUserDefined = computed(
  () => manualMode.value || manuallyDefinedVisit.value
)

const {
  unscheduledVisitTypeUid,
  nonVisitTypeUid,
  earlyDiscontinuationVisitTypeUid,
  fixedWindowVisitTypeUids,
} = useVisitTypeTerms(visitTypes)

const isUnscheduledVisitType = computed(
  () =>
    Boolean(unscheduledVisitTypeUid.value) &&
    form.value.visit_type_uid === unscheduledVisitTypeUid.value
)

const isNonVisitType = computed(
  () =>
    Boolean(nonVisitTypeUid.value) &&
    form.value.visit_type_uid === nonVisitTypeUid.value
)

const isEarlyDiscontinuationVisitType = computed(
  () =>
    Boolean(earlyDiscontinuationVisitTypeUid.value) &&
    form.value.visit_type_uid === earlyDiscontinuationVisitTypeUid.value
)

const visitGroupOptions = computed(() =>
  allStudyVisits.value.filter(
    (visit) =>
      visit.visit_subclass ===
      visitConstants.SUBCLASS_ANCHOR_VISIT_IN_GROUP_OF_SUBV
  )
)

// Possible Early discontinuation parents; mirrors the backend's _can_be_early_discontinuation_parent
const earlyDiscontinuationReferenceOptions = computed(() =>
  allStudyVisits.value.filter(
    (visit) =>
      visit.visit_class === visitConstants.CLASS_SINGLE_VISIT &&
      (visit.visit_subclass === visitConstants.SUBCLASS_SINGLE_VISIT ||
        visit.visit_subclass ===
          visitConstants.SUBCLASS_ANCHOR_VISIT_IN_GROUP_OF_SUBV) &&
      !fixedWindowVisitTypeUids.value.includes(visit.visit_type?.term_uid) &&
      visit.uid !== props.studyVisit?.uid
  )
)

// Only the Unscheduled and Non-visit types offer the Technical visit switch
const showTechnicalVisitSwitch = computed(
  () => isUnscheduledVisitType.value || isNonVisitType.value
)

const technicalVisitNumber = computed(() => {
  if (isUnscheduledVisitType.value) {
    return 29500
  }
  if (isNonVisitType.value) {
    return 29999
  }
  return null
})

// Legacy visit number, shown next to the switch
const technicalVisitTypeLabel = computed(() =>
  technicalVisitNumber.value ? `V${technicalVisitNumber.value}` : ''
)

// Follows from the manually defined toggle and the Technical visit switch
const visitClass = computed(() => {
  // Manual mode: every visit is a plain single visit
  if (manualMode.value) {
    return visitConstants.CLASS_SINGLE_VISIT
  }
  if (manuallyDefinedVisit.value) {
    return visitConstants.CLASS_MANUALLY_DEFINED_VISIT
  }
  if (isNonVisitType.value && technicalVisit.value) {
    return visitConstants.CLASS_NON_VISIT
  }
  if (isUnscheduledVisitType.value && technicalVisit.value) {
    return visitConstants.CLASS_UNSCHEDULED_VISIT
  }
  return visitConstants.CLASS_SINGLE_VISIT
})

// Technical Unscheduled/Non-visit: no grouping, anchoring or real timing
const isTechnicalVisit = computed(
  () => showTechnicalVisitSwitch.value && technicalVisit.value
)

// Timing and the visit window are locked to placeholder values for these types
const isFixedWindowVisitType = computed(
  () =>
    isUnscheduledVisitType.value ||
    isEarlyDiscontinuationVisitType.value ||
    (!manualMode.value && isNonVisitType.value)
)

const timeUnits = computed(() =>
  epochsStore.studyTimeUnits.filter((unit) =>
    ['days', 'weeks', 'years'].includes(unit.name?.toLowerCase())
  )
)

const SINGULAR_TO_PLURAL_UNIT = { day: 'days', week: 'weeks', year: 'years' }

// Older visits can carry day/week/year, which timeUnits does not offer; swap in days/weeks/years
function offeredUnitUid(unitUid, unitName) {
  if (!unitUid || timeUnits.value.some((unit) => unit.uid === unitUid)) {
    return unitUid
  }
  const name = (
    unitName ??
    epochsStore.studyTimeUnits.find((unit) => unit.uid === unitUid)?.name
  )?.toLowerCase()
  const pluralName = SINGULAR_TO_PLURAL_UNIT[name]
  return (
    timeUnits.value.find((unit) => unit.name?.toLowerCase() === pluralName)
      ?.uid ?? unitUid
  )
}

// Locked to the group's anchor visit, or to the global anchor for Non-visit/Unscheduled
const timeReferenceDisabled = computed(
  () =>
    form.value.is_global_anchor_visit ||
    Boolean(form.value.visit_sublabel_reference) ||
    hideTimingFields.value
)

// Derived from the anchor switch and the visit group; never picked directly
const visitSubclass = computed(() => {
  if (manuallyDefinedVisit.value) {
    return visitConstants.SUBCLASS_SINGLE_VISIT
  }
  if (isAnchorVisit.value) {
    return visitConstants.SUBCLASS_ANCHOR_VISIT_IN_GROUP_OF_SUBV
  }
  // Early discontinuation keeps a plain subclass: its sublabel reference is not a group
  if (
    form.value.visit_sublabel_reference &&
    !isEarlyDiscontinuationVisitType.value
  ) {
    return visitConstants.SUBCLASS_ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV
  }
  return isRepeatingVisit.value
    ? visitConstants.SUBCLASS_REPEATING_VISIT
    : visitConstants.SUBCLASS_SINGLE_VISIT
})

// Only one global anchor visit per study; the switch is locked once one exists
const globalAnchorVisitSwitchDisabled = computed(
  () =>
    globalAnchorVisit.value !== null &&
    globalAnchorVisit.value.uid !== props.studyVisit?.uid
)

const hideTimingFields = computed(
  () =>
    !manualMode.value && (isNonVisitType.value || isUnscheduledVisitType.value)
)

// Expected timing is only for SoA ordering; Early discontinuation derives its timing instead
const showExpectedTiming = computed(
  () =>
    !manualMode.value &&
    (isNonVisitType.value ||
      isUnscheduledVisitType.value ||
      isRepeatingVisit.value)
)

function hasValue(value) {
  return (
    value !== undefined && value !== null && String(value).trim().length > 0
  )
}

// Repeating visit: exactly one of timing / expected timing
const timeValueRules = computed(() => {
  if (!isRepeatingVisit.value) {
    return [formRules.required]
  }
  return [
    (value) =>
      hasValue(value) && hasValue(form.value.expected_time_value)
        ? t('_errors.timing_or_expected_timing')
        : hasValue(value) ||
          hasValue(form.value.expected_time_value) ||
          t('_errors.required'),
  ]
})
const expectedTimeValueRules = computed(() => {
  if (!isRepeatingVisit.value) {
    return [formRules.required]
  }
  return [
    (value) =>
      hasValue(value) && hasValue(form.value.time_value)
        ? t('_errors.timing_or_expected_timing')
        : hasValue(value) ||
          hasValue(form.value.time_value) ||
          t('_errors.required'),
  ]
})

// Guards the side-effect watchers below from firing on buildForm's own assignments
let buildingForm = false
let previewRequestId = 0

// The visit the form was last built from; after a save, newer than props.studyVisit
let loadedVisit = null

function buildForm(visit) {
  buildingForm = true
  loadedVisit = visit
  // A preview still in flight belongs to the form being replaced.
  previewRequestId++
  previewLoading.value = false
  manuallyDefinedVisit.value =
    visit?.visit_class === visitConstants.CLASS_MANUALLY_DEFINED_VISIT
  isAnchorVisit.value =
    visit?.visit_subclass ===
    visitConstants.SUBCLASS_ANCHOR_VISIT_IN_GROUP_OF_SUBV
  isRepeatingVisit.value =
    visit?.visit_subclass === visitConstants.SUBCLASS_REPEATING_VISIT
  technicalVisit.value =
    visit?.visit_class === visitConstants.CLASS_UNSCHEDULED_VISIT ||
    visit?.visit_class === visitConstants.CLASS_NON_VISIT
  form.value = {
    visit_name: visit?.visit_name ?? '',
    visit_short_name: visit?.visit_short_name ?? '',
    visit_type_uid: visit?.visit_type?.term_uid ?? null,
    visit_contact_mode_uid: visit?.visit_contact_mode?.term_uid ?? null,
    time_value: visit?.time_value ?? null,
    time_unit_uid: offeredUnitUid(
      visit?.time_unit_uid ?? firstVisitUnits.value.time_unit_uid,
      visit?.time_unit_name
    ),
    study_epoch_uid: visit?.study_epoch_uid ?? null,
    min_visit_window_value: visit ? (visit.min_visit_window_value ?? null) : 0,
    max_visit_window_value: visit ? (visit.max_visit_window_value ?? null) : 0,
    visit_window_unit_uid: offeredUnitUid(
      visit?.visit_window_unit_uid ??
        firstVisitUnits.value.visit_window_unit_uid,
      visit?.visit_window_unit_name
    ),
    description: visit?.description ?? '',
    start_rule: visit?.start_rule ?? '',
    end_rule: visit?.end_rule ?? '',
    unique_visit_number: visit?.unique_visit_number ?? null,
    expected_time_value: visit?.expected_time_value ?? null,
    epoch_allocation_uid: visit?.epoch_allocation?.term_uid ?? null,
    repeating_frequency_uid: visit?.repeating_frequency?.term_uid ?? null,
    show_visit: visit?.show_visit ?? true,
    is_soa_milestone: visit?.is_soa_milestone ?? false,
    is_global_anchor_visit: visit?.is_global_anchor_visit ?? false,
    uid: visit?.uid ?? null,
    visit_class: null,
    visit_sublabel_reference: visit?.visit_sublabel_reference ?? null,
    visit_suffix: visit?.visit_suffix ?? '',
    visit_subclass: null,
    study_day_label: visit?.study_day_label ?? '',
    study_week_label: visit?.study_week_label ?? '',
    time_reference_uid:
      visit?.time_reference?.term_uid ?? globalAnchorTermUid.value,
  }
  form.value.visit_class = visitClass.value
  form.value.visit_subclass = visitSubclass.value
  initialForm.value = JSON.stringify(form.value)
  nextTick(() => {
    buildingForm = false
  })
}

// Rebuild once visitTypes/timeReferences arrive, but only while the form is pristine
function refreshDerivedDefaults() {
  if (!hasChanges.value) {
    buildForm(loadedVisit)
  }
}

watch(
  () => props.studyVisit,
  (visit) => buildForm(visit),
  { immediate: true }
)

// The units list may arrive after the form was built
watch(timeUnits, refreshDerivedDefaults)

watch(visitClass, (value) => {
  form.value.visit_class = value
})

// Non-visit/Unscheduled lock the time reference, so snap it back to the global anchor
watch(hideTimingFields, (value) => {
  if (buildingForm) {
    return
  }
  if (value) {
    form.value.time_reference_uid = globalAnchorTermUid.value
  }
})

// A visit filed under a group always times off that group's anchor visit.
watch(
  () => form.value.visit_sublabel_reference,
  (value) => {
    if (buildingForm || !value) {
      return
    }
    form.value.time_reference_uid = anchorVisitInGroupTermUid.value
  }
)

watch(visitSubclass, (value) => {
  form.value.visit_subclass = value
})

// An anchor visit defines its own group, it cannot be filed under another one.
watch(isAnchorVisit, (value) => {
  if (buildingForm) {
    return
  }
  if (value) {
    form.value.visit_sublabel_reference = null
  }
})

// The Anchor switch is hidden for Early discontinuation, so it cannot be left on.
watch(isEarlyDiscontinuationVisitType, (value) => {
  if (buildingForm) {
    return
  }
  if (value) {
    isAnchorVisit.value = false
  }
})

watch(
  () => form.value.is_global_anchor_visit,
  (value) => {
    if (buildingForm) {
      return
    }
    if (value) {
      form.value.time_reference_uid = globalAnchorTermUid.value
      form.value.time_value = 0
    }
  }
)

// Manual mode derives nothing, so a technical visit starts from its fixed names and window
const technicalVisitDefaults = computed(() => {
  if (!manualMode.value || !isTechnicalVisit.value) {
    return null
  }
  return {
    visit_name: isUnscheduledVisitType.value
      ? visitConstants.VISIT_TYPE_UNSCHEDULED
      : visitConstants.VISIT_TYPE_NON_VISIT,
    visit_short_name: technicalVisitTypeLabel.value,
    unique_visit_number: technicalVisitNumber.value,
    min_visit_window_value: -9999,
    max_visit_window_value: 9999,
  }
})

watch(isFixedWindowVisitType, (value) => {
  if (buildingForm) {
    return
  }
  if (value) {
    // The Repeating switch is hidden for these types, so it must not stay on
    isRepeatingVisit.value = false
    form.value.time_value = 0
    form.value.min_visit_window_value = -9999
    form.value.max_visit_window_value = 9999
  } else {
    // Clear the placeholder timing, except for the global anchor visit (locked at 0)
    form.value.time_value = form.value.is_global_anchor_visit ? 0 : null
    // A technical visit sets its own window
    if (!technicalVisitDefaults.value) {
      form.value.min_visit_window_value = 0
      form.value.max_visit_window_value = 0
    }
  }
})

watch(technicalVisitDefaults, (defaults) => {
  if (buildingForm) {
    return
  }
  Object.assign(
    form.value,
    defaults ?? {
      visit_name: '',
      visit_short_name: '',
      unique_visit_number: null,
      // Unscheduled keeps its locked window when the technical switch goes off
      ...(isFixedWindowVisitType.value
        ? {}
        : { min_visit_window_value: 0, max_visit_window_value: 0 }),
    }
  )
})

// Technical visits default to the Virtual Visit contact mode
watch(isTechnicalVisit, (value) => {
  if (buildingForm) {
    return
  }
  if (value) {
    form.value.visit_contact_mode_uid = virtualVisitContactModeUid.value
  }
})

// Turning off repeating visit drops the now-hidden frequency field.
watch(isRepeatingVisit, (value) => {
  if (buildingForm) {
    return
  }
  if (!value) {
    form.value.repeating_frequency_uid = null
  }
})

// Non-visit turns the Technical visit switch on by default; the user can turn it off
watch(isNonVisitType, (value) => {
  if (buildingForm) {
    return
  }
  if (value) {
    technicalVisit.value = true
  }
})

// Changing away from Unscheduled/Non-visit hides the switch, so drop the flag
watch(showTechnicalVisitSwitch, (value) => {
  if (buildingForm) {
    return
  }
  if (!value) {
    technicalVisit.value = false
  }
})

if (epochsStore.studyEpochs.length === 0) {
  epochsStore.fetchStudyEpochs({
    studyUid: studiesGeneralStore.selectedStudy.uid,
  })
}
if (epochsStore.studyTimeUnits.length === 0) {
  epochsStore.fetchStudyTimeUnits()
}
terms.getTermsByCodelist('visitTypes', { page_size: 0 }).then((resp) => {
  visitTypes.value = resp.data.items
  refreshDerivedDefaults()
})
fetchVisitTimeReferenceTerms().then(refreshDerivedDefaults)
terms.getTermsByCodelist('epochAllocations').then((resp) => {
  epochAllocations.value = resp.data.items
})
terms.getTermsByCodelist('repeatingVisitFrequency').then((resp) => {
  repeatingFrequencies.value = resp.data.items
})
function fetchStudyVisits() {
  return studyEpochsApi
    .getStudyVisits(studiesGeneralStore.selectedStudy.uid, { page_size: 0 })
    .then((resp) => {
      allStudyVisits.value = resp.data.items
      const firstVisit = resp.data.items[0]
      if (firstVisit) {
        firstVisitUnits.value = {
          time_unit_uid: firstVisit.time_unit_uid,
          visit_window_unit_uid: firstVisit.visit_window_unit_uid,
        }
        refreshDerivedDefaults()
      }
    })
}
fetchStudyVisits()
function fetchGlobalAnchorVisit() {
  // Reset first: a 404 (no global anchor visit) rejects instead of resolving
  globalAnchorVisit.value = null
  studyEpochsApi
    .getGlobalAnchorVisit(studiesGeneralStore.selectedStudy.uid)
    .then((resp) => {
      globalAnchorVisit.value = resp.data
    })
    .catch((error) => {
      // No global anchor visit yet is normal; ignoreErrors means no toast either
      if (error.response?.status !== 404) {
        console.error('Failed to load the global anchor visit', error)
      }
    })
}
fetchGlobalAnchorVisit()

function discard() {
  buildForm(loadedVisit)
}

const isEditing = computed(() => Boolean(props.studyVisit?.uid))

// Falls back to the group-anchor term before the time_reference_uid watcher has flushed
function getTimeReferenceInput() {
  const termUid =
    form.value.time_reference_uid ||
    (form.value.visit_sublabel_reference
      ? anchorVisitInGroupTermUid.value
      : null)
  return termUid ? { term_uid: termUid } : null
}

function buildPayload() {
  // Edits go over loadedVisit, not the stale props.studyVisit, to keep fields the form hides
  const data = {
    ...JSON.parse(JSON.stringify(loadedVisit ?? props.studyVisit ?? {})),
    ...JSON.parse(JSON.stringify(form.value)),
  }
  // A cleared number field is '' rather than null, which the backend rejects
  data.time_value = hasValue(data.time_value) ? Number(data.time_value) : null
  data.expected_time_value = hasValue(data.expected_time_value)
    ? Number(data.expected_time_value)
    : null
  data.unique_visit_number = hasValue(data.unique_visit_number)
    ? Number(data.unique_visit_number)
    : null
  data.visit_type = { term_uid: data.visit_type_uid }
  data.visit_contact_mode = { term_uid: data.visit_contact_mode_uid }
  data.epoch_allocation = data.epoch_allocation_uid
    ? { term_uid: data.epoch_allocation_uid }
    : null
  data.repeating_frequency = data.repeating_frequency_uid
    ? { term_uid: data.repeating_frequency_uid }
    : null
  data.time_reference = getTimeReferenceInput()
  delete data.time_unit
  // Technical visits carry no grouping or expected timing
  if (isTechnicalVisit.value) {
    delete data.visit_sublabel_reference
    delete data.visit_suffix
    data.expected_time_value = null
    data.is_soa_milestone = false
  } else if (!showExpectedTiming.value) {
    data.expected_time_value = null
  }
  // No timing for technical visit classes, except in manual mode (payload is as typed)
  if (
    !manualMode.value &&
    data.visit_class !== visitConstants.CLASS_SINGLE_VISIT &&
    data.visit_class !== visitConstants.CLASS_MANUALLY_DEFINED_VISIT
  ) {
    delete data.time_value
    delete data.time_unit_uid
  }
  return data
}

async function save() {
  const { valid } = await observer.value.validate()
  if (!valid) {
    return false
  }
  try {
    saving.value = true
    const data = buildPayload()
    if (isEditing.value) {
      const studyUid = studiesGeneralStore.selectedStudy.uid
      await epochsStore.updateStudyVisit({
        studyUid,
        studyVisitUid: props.studyVisit.uid,
        input: data,
      })
      // The form stays open after saving, so reload the visit to pick up derived values
      const resp = await studyEpochsApi.getStudyVisit(
        studyUid,
        props.studyVisit.uid
      )
      buildForm(resp.data)
      fetchGlobalAnchorVisit()
      fetchStudyVisits()
      notificationHub.add({ msg: t('StudyVisitForm.update_success') })
      emit('refresh')
    } else {
      delete data.uid
      await epochsStore.addStudyVisit({
        studyUid: studiesGeneralStore.selectedStudy.uid,
        input: data,
      })
      fetchGlobalAnchorVisit()
      fetchStudyVisits()
      notificationHub.add({ msg: t('StudyVisitForm.add_success') })
      emit('refresh')
      // Close rather than leave the form armed to create a second visit
      close()
    }
    return true
  } catch (error) {
    console.error('Error saving study visit:', error)
    return false
  } finally {
    saving.value = false
  }
}

function close() {
  emit('close')
}

// Resolves true when the form may be left (nothing pending, or the user agreed to discard)
async function confirmDiscardChanges() {
  if (!hasChanges.value) {
    return true
  }
  return confirmRef.value.open(t('_global.cancel_changes'), {
    type: 'warning',
    cancelLabel: t('_global.cancel'),
    agreeLabel: t('_global.continue'),
  })
}

// Like confirmDiscardChanges, but offers to save: agree saves, cancel discards
async function confirmUnsavedChanges() {
  if (!hasChanges.value) {
    return true
  }
  if (saving.value) {
    return false
  }
  const shouldSave = await confirmRef.value.open(
    t('StudyVisitForm.unsaved_changes'),
    {
      type: 'warning',
      cancelLabel: t('_global.discard_changes'),
      agreeLabel: t('_global.save_changes'),
    }
  )
  return shouldSave ? save() : true
}

async function requestClose() {
  if (await confirmDiscardChanges()) {
    close()
  }
}

defineExpose({ confirmDiscardChanges, confirmUnsavedChanges })

// Runs post-flush, once per tick, so derived fields written by the watchers are included
const previewRequests = ref(0)
function getVisitPreview() {
  previewRequests.value++
}
watch(previewRequests, () => fetchVisitPreview(), { flush: 'post' })

function fetchVisitPreview() {
  // The preview derives nothing in manual mode; the backend computes day/week on save
  if (props.studyVisit || manualMode.value) {
    return
  }
  const mandatoryFields = [
    'visit_type_uid',
    'visit_contact_mode_uid',
    // Early discontinuation keeps its reference in visit_sublabel_reference
    isEarlyDiscontinuationVisitType.value
      ? 'visit_sublabel_reference'
      : 'time_reference_uid',
    'time_value',
    'time_unit_uid',
  ]
  // Early discontinuation needs its typed suffix first, since it changes the previewed name
  if (isEarlyDiscontinuationVisitType.value) {
    mandatoryFields.push('visit_suffix')
  }
  // A manually defined visit keeps its own naming; the preview only fills the day/week labels
  if (manuallyDefinedVisit.value) {
    mandatoryFields.push(
      'visit_name',
      'visit_short_name',
      'unique_visit_number'
    )
  }
  for (const field of mandatoryFields) {
    const fieldValue = form.value[field]
    if (fieldValue === undefined || fieldValue === null || fieldValue === '') {
      // Inputs are incomplete again; drop any preview still in flight
      previewRequestId++
      previewLoading.value = false
      return
    }
  }
  const payload = { ...form.value }
  // Read class and subclass from the computeds; their form copies may not have flushed
  payload.visit_class = visitClass.value
  payload.visit_subclass = visitSubclass.value
  payload.visit_type = { term_uid: payload.visit_type_uid }
  payload.visit_contact_mode = { term_uid: payload.visit_contact_mode_uid }
  payload.time_reference = getTimeReferenceInput()
  if (payload.is_global_anchor_visit) {
    payload.time_value = 0
  }
  const requestId = ++previewRequestId
  previewLoading.value = true

  epochsStore
    .getStudyVisitPreview({
      studyUid: studiesGeneralStore.selectedStudy.uid,
      input: payload,
    })
    .then((resp) => {
      // Only the latest request may write; a late older response would overwrite newer values
      if (requestId !== previewRequestId) {
        return
      }
      let fields = []
      if (!manuallyDefinedVisit.value) {
        fields = fields.concat([
          'visit_name',
          'visit_short_name',
          'unique_visit_number',
          'start_rule',
        ])
        // The suffix is user-typed for Early discontinuation; the preview must not replace it
        if (!isEarlyDiscontinuationVisitType.value) {
          fields.push('visit_suffix')
        }
      }
      fields = fields.concat(['study_day_label', 'study_week_label'])
      for (const field of fields) {
        // A key the response omits must not blank the field
        if (resp.data[field] !== undefined) {
          form.value[field] = resp.data[field]
        }
      }
    })
    .catch((error) => {
      // The repository interceptor has already shown the error toast.
      console.error('Error in getVisitPreview:', error)
    })
    .finally(() => {
      if (requestId === previewRequestId) {
        previewLoading.value = false
      }
    })
}
</script>

<style scoped>
.section-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: rgb(var(--v-theme-nnBaseBlue));
}
.subsection-title {
  font-size: 1rem;
  font-weight: 700;
  color: rgb(var(--v-theme-nnBaseBlue));
}
/* Reserves room below the form's own content so it doesn't end flush against
   the fixed unsaved-bar once scrolled all the way down. */
.visit-form--with-unsaved-bar {
  padding-bottom: 96px;
}
</style>
