<template>
  <HorizontalStepperForm
    ref="stepper"
    :title="title"
    :steps="steps"
    :help-items="helpItems"
    :form-observer-getter="getObserver"
    help-text=""
    :reset-loading="resetLoading"
    custom-actions
    @close="close"
  >
    <template #[`step.creationMode`]>
      <div class="label mb-4">{{ $t('CohortsStepper.select_class') }}</div>
      <v-radio-group v-model="creationMode">
        <v-radio
          :label="$t('CohortsStepper.full_stepper')"
          :value="cohortConstants.FULL"
          data-cy="full-design-study"
        />
        <v-radio
          :label="$t('CohortsStepper.arms_only_stepper')"
          :value="cohortConstants.MANUAL"
          data-cy="manual-study"
        />
        <div class="label my-4">{{ $t('_global.or') }}</div>
        <v-radio
          :label="$t('CohortsStepper.select_from_studies')"
          :value="cohortConstants.SELECT"
          data-cy="select-from-studies"
        />
      </v-radio-group>
      <v-form ref="selectStudyForm">
        <v-row v-if="creationMode === cohortConstants.SELECT">
          <v-col cols="6">
            <StudySelectorField
              v-model="selectedSourceStudy"
              :data="studies"
              :loading="studiesLoading"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #[`step.arms`]>
      <v-form ref="armsForm">
        <div class="label mb-4">
          {{ $t('CohortsStepper.set_arms_for_study') }}
        </div>
        <v-sheet
          v-for="(arm, index) in arms"
          :key="index"
          color="nnLightBlue100"
          rounded="xl"
          style="max-width: 80%"
          class="mb-4 px-4 py-4"
          border="sm"
        >
          <v-row>
            <v-col cols="4">
              <v-autocomplete
                v-model="arm.arm_type_uid"
                data-cy="arm-type"
                :label="$t('CohortsStepper.study_arm_type')"
                :rules="[formRules.required]"
                :items="armTypes"
                bg-color="white"
                open-on-clear
                color="nnBaseBlue"
                base-color="nnBaseBlue"
                item-title="sponsor_preferred_name"
                item-value="term_uid"
                clearable
              />
            </v-col>
            <v-col cols="4">
              <v-text-field
                v-model="arm.name"
                data-cy="arm-name"
                :label="$t('CohortsStepper.arm_name')"
                :rules="[formRules.required, formRules.max(arm.name, 200)]"
                bg-color="white"
                color="nnBaseBlue"
                base-color="nnBaseBlue"
                clearable
                class="smallfont"
              />
            </v-col>
            <v-col cols="3">
              <v-text-field
                v-model="arm.short_name"
                data-cy="arm-short-name"
                :label="$t('CohortsStepper.arm_short_name')"
                :rules="[formRules.required, formRules.max(arm.short_name, 20)]"
                bg-color="white"
                color="nnBaseBlue"
                base-color="nnBaseBlue"
                clearable
              />
            </v-col>
            <v-col cols="1">
              <v-btn
                color="error"
                data-cy="remove-arm"
                class="text-none"
                variant="flat"
                @click="removeArm(arm, index)"
              >
                {{ $t('_global.remove') }}
              </v-btn>
            </v-col>
          </v-row>
          <v-row v-if="isArmsOnly" class="justify-center">
            <v-col cols="4">
              <v-text-field
                v-model="arm.label"
                data-cy="arm-label"
                :label="$t('CohortsStepper.arm_label')"
                :rules="[formRules.max(arm.label, 40)]"
                bg-color="white"
                color="nnBaseBlue"
                base-color="nnBaseBlue"
                clearable
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="4">
              <div style="display: flex">
                <v-text-field
                  v-if="isArmsOnly"
                  v-model="arm.number_of_subjects"
                  data-cy="number-of-subjects"
                  :label="$t('CohortsStepper.no_participants')"
                  type="number"
                  :rules="[formRules.min_value(arm.number_of_subjects, 0)]"
                  class="mr-1"
                  bg-color="white"
                  color="nnBaseBlue"
                  base-color="nnBaseBlue"
                  clearable
                />
                <v-text-field
                  v-model="arm.randomization_group"
                  data-cy="randomization-group"
                  :label="$t('CohortsStepper.rand_group_optional')"
                  class="mr-1"
                  bg-color="white"
                  color="nnBaseBlue"
                  base-color="nnBaseBlue"
                  clearable
                />
                <v-text-field
                  v-if="!isArmsOnly"
                  v-model="arm.code"
                  data-cy="arm-code"
                  :label="$t('CohortsStepper.arm_code_optional')"
                  :rules="[formRules.max(arm.code, 20)]"
                  class="ml-1"
                  bg-color="white"
                  color="nnBaseBlue"
                  base-color="nnBaseBlue"
                  clearable
                />
              </div>
            </v-col>
            <v-col cols="4">
              <v-text-field
                v-model="arm.description"
                data-cy="arm-description"
                :label="$t('CohortsStepper.desc')"
                bg-color="white"
                color="nnBaseBlue"
                base-color="nnBaseBlue"
                clearable
              />
            </v-col>
            <!-- Hidden for now, will be used later
            <v-col v-if="creationMode !== cohortConstants.MANUAL" cols="3">
              <v-switch
                v-model="arm.merge_branch_for_this_arm_for_sdtm_adam"
                inset
                hide-details
                class="mt-n2"
              >
                <template #label>
                  <div style="font-size: 14px; color: #454b5c">
                    {{ $t('CohortsStepper.merge_branch') }}
                  </div>
                </template>
              </v-switch>
            </v-col> -->
            <v-col v-if="isArmsOnly" cols="3">
              <v-text-field
                v-model="arm.code"
                data-cy="arm-code"
                :label="$t('CohortsStepper.arm_code_optional')"
                :rules="[formRules.max(arm.code, 20)]"
                class="ml-1"
                bg-color="white"
                color="nnBaseBlue"
                base-color="nnBaseBlue"
                clearable
              />
            </v-col>
            <v-col v-else cols="3">
              <v-text-field
                v-model="arm.label"
                data-cy="arm-label"
                :label="$t('CohortsStepper.arm_label')"
                :rules="[formRules.max(arm.label, 40)]"
                bg-color="white"
                color="nnBaseBlue"
                base-color="nnBaseBlue"
                clearable
              />
            </v-col>
          </v-row>
        </v-sheet>
        <v-btn
          class="secondary-btn text-none"
          data-cy="arm-push"
          variant="outlined"
          prepend-icon="mdi-plus"
          width="120px"
          rounded="xl"
          @click="arms.push({})"
        >
          {{ $t('CohortsStepper.add_arm') }}
        </v-btn>
      </v-form>
    </template>
    <template #[`step.selectArms`]>
      <div class="label mb-4">
        {{ $t('CohortsStepper.selected_arms') }}
      </div>
      <v-data-table
        data-cy="selected-arms-table"
        :headers="selectedArmHeaders"
        :items="selectedArms"
      >
        <template #[`item.actions`]="{ item }">
          <v-btn
            icon="mdi-delete-outline"
            color="red"
            variant="text"
            data-cy="remove-selected-arm"
            @click="unselectArm(item)"
          />
        </template>
      </v-data-table>
    </template>
    <template #[`step.selectArms.after`]>
      <p class="text-grey text-body-large font-weight-bold mb-0 ml-3">
        {{ $t('CohortsStepper.copy_instructions') }}
      </p>
      <v-col cols="12" class="pt-0 mt-0">
        <v-data-table
          data-cy="source-arms-table"
          :headers="sourceArmHeaders"
          :items="sourceStudyArms"
          :loading="sourceArmsLoading"
        >
          <template #[`header.actions`]>
            <v-checkbox
              v-model="selectAllSourceArms"
              :title="$t('_global.select_all')"
              :disabled="!sourceStudyArms.length"
              density="compact"
              hide-details
              data-cy="select-all-source-arms"
              @update:model-value="toggleSelectAllSourceArms"
            />
          </template>
          <template #[`item.actions`]="{ item }">
            <v-btn
              :data-cy="$t('StudySelectionTable.copy_item')"
              icon="mdi-content-copy"
              size="small"
              variant="text"
              :color="isArmDisabled(item) ? '' : 'primary'"
              :disabled="isArmDisabled(item)"
              :title="$t('StudySelectionTable.copy_item')"
              @click="selectArm(item)"
            />
          </template>
        </v-data-table>
      </v-col>
    </template>
    <template #[`step.cohorts`]>
      <v-form ref="cohortsForm">
        <div class="label mb-4">
          {{ $t('CohortsStepper.set_cohorts_for_study') }}
        </div>
        <v-row>
          <v-col cols="3">
            <v-autocomplete
              v-model="sourceVariable.source_variable"
              data-cy="source-variable"
              :label="$t('CohortsStepper.source_var_optional')"
              :items="sourceVariables"
              bg-color="white"
              open-on-clear
              color="nnBaseBlue"
              base-color="nnBaseBlue"
              clearable
            />
          </v-col>
          <v-col cols="3">
            <v-text-field
              v-model="sourceVariable.source_variable_description"
              data-cy="source-variable-description"
              :label="$t('CohortsStepper.source_var_desc')"
              bg-color="white"
              color="nnBaseBlue"
              base-color="nnBaseBlue"
              clearable
            />
          </v-col>
        </v-row>
        <v-sheet
          v-for="(cohort, index) in cohorts"
          :key="index"
          color="nnLightBlue100"
          rounded="xl"
          style="max-width: 80%"
          class="mb-4 px-4 py-4"
          border="xs"
        >
          <v-row>
            <v-col cols="2">
              <v-text-field
                v-model="cohort.code"
                data-cy="cohort-code"
                :label="$t('CohortsStepper.cohort_code')"
                :rules="[formRules.required]"
                bg-color="white"
                color="nnBaseBlue"
                base-color="nnBaseBlue"
                clearable
              />
            </v-col>
            <v-col cols="4">
              <v-text-field
                v-model="cohort.name"
                data-cy="cohort-name"
                :label="$t('CohortsStepper.cohort_name')"
                :rules="[formRules.required, formRules.max(cohort.name, 200)]"
                bg-color="white"
                color="nnBaseBlue"
                base-color="nnBaseBlue"
                clearable
              />
            </v-col>
            <v-col cols="4">
              <v-text-field
                v-model="cohort.short_name"
                data-cy="cohort-short-name"
                :label="$t('CohortsStepper.cohort_short_name')"
                :rules="[
                  formRules.required,
                  formRules.max(cohort.short_name, 20),
                ]"
                bg-color="white"
                color="nnBaseBlue"
                base-color="nnBaseBlue"
                clearable
              />
            </v-col>
            <v-col cols="2">
              <v-btn
                color="error"
                class="text-none"
                variant="flat"
                data-cy="remove-cohort"
                @click="removeCohort(cohort, index)"
              >
                {{ $t('_global.remove') }}
              </v-btn>
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="10">
              <v-text-field
                v-model="cohort.description"
                data-cy="cohort-description"
                :label="$t('CohortsStepper.desc')"
                bg-color="white"
                color="nnBaseBlue"
                base-color="nnBaseBlue"
                clearable
              />
            </v-col>
          </v-row>
        </v-sheet>
        <v-btn
          class="secondary-btn text-none"
          variant="outlined"
          prepend-icon="mdi-plus"
          data-cy="cohort-push"
          rounded="xl"
          @click="cohorts.push({})"
        >
          {{ $t('CohortsStepper.add_cohort') }}
        </v-btn>
      </v-form>
    </template>
    <template #[`step.linking`]>
      <v-form ref="linkingForm">
        <div class="label mb-4">
          {{ $t('CohortsStepper.link_arms_cohorts') }}
        </div>
        <v-alert
          color="nnLightBlue200"
          style="width: 75vw"
          class="mb-2 text-nnTrueBlue"
          type="info"
          rounded="lg"
          :text="$t('CohortsStepper.link_info')"
        />
        <div style="display: flex">
          <div style="display: grid">
            <v-sheet
              rounded="lg"
              width="300px"
              height="110px"
              class="mr-2 pt-2"
              style="justify-items: center; align-content: center"
            >
              <div style="color: grey">
                {{ $t('CohortsStepper.total_amount') }}
              </div>
              <v-text-field
                v-model="totalParticipants"
                data-cy="total-participants"
                prepend-inner-icon="mdi-account"
                width="110px"
                bg-color="white"
                color="nnBaseBlue"
                rounded
                clearable
                disabled
              />
            </v-sheet>
            <v-sheet
              v-for="cohort in cohorts"
              :key="cohort.name"
              data-cy="cohort-name"
              rounded="lg"
              border
              width="300px"
              height="100px"
              color="nnLightBlue100"
              class="mr-2 ps-4"
            >
              <v-row class="mt-1">
                <v-col class="text-nnTrueBlue">
                  <div class="text-body-medium">
                    {{ $t('CohortsStepper.cohort_name') }}
                  </div>
                  <div
                    class="text-body-large font-weight-bold"
                    style="line-height: 1.25"
                  >
                    {{ cohort.name }}
                  </div>
                </v-col>
                <v-col style="display: flex">
                  <div
                    class="mt-4 ml-n4"
                    style="color: grey; font-size: 0.9rem"
                  >
                    {{ $t('CohortsStepper.total') }}
                  </div>
                  <v-text-field
                    v-model="cohort.number_of_subjects"
                    prepend-inner-icon="mdi-account"
                    data-cy="number-of-subjects"
                    label="0"
                    single-line
                    width="85px"
                    bg-color="white"
                    color="nnBaseBlue"
                    rounded
                    clearable
                    disabled
                    class="mt-1"
                    style="scale: 80%; height: 60px"
                  />
                </v-col>
              </v-row>
            </v-sheet>
          </div>
          <div
            v-for="(arm, armIndex) in branches"
            :key="arm.name"
            style="display: grid"
          >
            <v-sheet
              rounded="lg"
              width="300px"
              height="100px"
              border
              color="nnLightBlue100"
              class="mb-2 mr-2 ps-4"
            >
              <v-row class="mt-1">
                <v-col class="text-nnTrueBlue">
                  <div class="text-body-medium">
                    {{ $t('CohortsStepper.arm_name') }}
                  </div>
                  <div
                    class="text-body-large font-weight-bold"
                    style="line-height: 1.25"
                  >
                    {{ arm.name }}
                  </div>
                </v-col>
                <v-col style="display: flex">
                  <div
                    class="mt-4 ml-n5"
                    style="color: grey; font-size: 0.9rem"
                  >
                    {{ $t('CohortsStepper.total') }}
                  </div>
                  <v-text-field
                    v-model="arm.number_of_subjects"
                    data-cy="number-of-subjects"
                    prepend-inner-icon="mdi-account"
                    width="85px"
                    bg-color="white"
                    color="nnBaseBlue"
                    rounded
                    clearable
                    disabled
                    class="mt-1"
                    style="scale: 80%; height: 60px"
                  />
                </v-col>
              </v-row>
            </v-sheet>
            <div
              v-for="(cohort, index) in arm.study_cohorts"
              :key="cohort.name"
              style="display: flex"
            >
              <v-sheet
                rounded="lg"
                width="300px"
                height="100px"
                border
                :class="
                  cohort.study_branch_arms[0].number_of_subjects > 0
                    ? 'mb-2 mr-2 tile'
                    : 'mb-2 mr-2 tile bg-greyBackground'
                "
                style="justify-content: center"
              >
                <div class="text-nnTrueBlue">
                  <p class="text-body-medium ml-3 mt-n4">
                    {{ cohort.study_branch_arms[0].name }}
                  </p>
                  <div style="display: flex; justify-content: center">
                    <v-number-input
                      :key="cohort.study_branch_arms[0].name"
                      v-model="cohort.study_branch_arms[0].number_of_subjects"
                      data-cy="number-of-subjects-single-arm"
                      :reverse="false"
                      control-variant="split"
                      :min="0"
                      inset
                      style="max-width: 160px"
                      @update:model-value="
                        (value) => updateParticipants(value, index, armIndex)
                      "
                    ></v-number-input>
                    <v-btn
                      class="mt-1 ml-2"
                      size="x-small"
                      variant="outlined"
                      color="nnBaseBlue"
                      icon="mdi-pencil"
                      data-cy="edit-branch"
                      @click="openBranchEditForm(cohort.study_branch_arms[0])"
                    />
                  </div>
                </div>
              </v-sheet>
              <v-btn
                v-if="index === 0 && armIndex === arms.length - 1"
                class="secondary-btn ml-2 mt-4"
                variant="outlined"
                rounded="xl"
                data-cy="copy-branches"
                :loading="loading"
                @click="copyBranches"
              >
                {{ $t('CohortsStepper.copy_row') }}
              </v-btn>
            </div>
          </div>
        </div>
      </v-form>
    </template>
    <template #customActions>
      <v-btn
        class="secondary-btn my-2 ml-2"
        variant="outlined"
        width="120px"
        rounded="xl"
        data-cy="cancel-stepper"
        :loading="loading"
        @click="cancel"
      >
        {{ $t('_global.cancel') }}
      </v-btn>
      <v-btn
        v-if="stepper.currentStep !== 1"
        class="secondary-btn"
        variant="outlined"
        width="120px"
        rounded="xl"
        data-cy="save-close-stepper"
        :loading="loading"
        @click="saveAndClose"
      >
        {{ $t('_global.save_exit') }}
      </v-btn>
      <v-spacer />
      <v-btn
        v-if="stepper.currentStep > 1"
        class="secondary-btn"
        variant="outlined"
        width="120px"
        rounded="xl"
        :loading="loading"
        data-cy="previous-stepper"
        @click="previousStep()"
      >
        {{ $t('_global.previous') }}
      </v-btn>
      <v-btn
        class="mr-2"
        color="secondary"
        variant="flat"
        rounded="xl"
        data-cy="continue-stepper"
        :loading="loading"
        :disabled="checkContinueDisabled"
        @click="saveAndContinue()"
      >
        {{ continueLabel }}
      </v-btn>
    </template>
  </HorizontalStepperForm>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  <BranchEditForm
    :branch="editBranch"
    :open="showBranchEditForm"
    @save="applyBranchChanges"
    @close="closeBranchEditForm"
  />
</template>

<script setup>
import { inject, onMounted, ref, watch, computed } from 'vue'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import codelists from '@/api/controlledTerminology/terms'
import cohortsApi from '@/api/cohorts'
import armsApi from '@/api/arms'
import study from '@/api/study'
import StudySelectorField from '@/components/studies/StudySelectorField.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import BranchEditForm from './BranchEditForm.vue'
import _isEmpty from 'lodash/isEmpty'
import { useI18n } from 'vue-i18n'
import cohortConstants from '@/constants/cohorts'

const { t } = useI18n()
const formRules = inject('formRules')
const notificationHub = inject('notificationHub')
const studiesGeneralStore = useStudiesGeneralStore()
const emit = defineEmits(['close'])

// The batch endpoints (study-arms/batch, study-cohorts/batch,
// study-branch-arms/batch) return a multi-status array where each entry carries
// its own `response_code` and `content`; a per-item failure no longer rejects
// the HTTP call. Surface those failures as error notifications and report
// whether the batch fully succeeded so callers can avoid advancing on error.
function reportBatchErrors(responseData) {
  let hasError = false
  for (const subResponse of responseData || []) {
    if (subResponse.response_code >= 400) {
      hasError = true
      notificationHub.add({
        msg: subResponse.content?.message,
        type: 'error',
        timeout: 0,
      })
    }
  }
  return hasError
}

const stepper = ref()
const confirm = ref()

const props = defineProps({
  designClass: {
    type: String,
    default: null,
  },
  initialStep: {
    type: Number,
    default: 0,
  },
})

const fullStepperSteps = [
  { name: 'creationMode', title: t('CohortsStepper.select_class') },
  { name: 'arms', title: t('CohortsStepper.set_arms') },
  { name: 'cohorts', title: t('CohortsStepper.set_cohorts') },
  { name: 'linking', title: t('CohortsStepper.linking') },
]

const manuallyDefinedSteps = [
  { name: 'creationMode', title: t('CohortsStepper.select_class') },
  { name: 'arms', title: t('CohortsStepper.set_arms') },
]

const selectFromStudiesSteps = [
  { name: 'creationMode', title: t('CohortsStepper.select_class') },
  { name: 'selectArms', title: t('CohortsStepper.set_arms') },
]

const selectedArmHeaders = [
  { title: '', key: 'actions', width: '1%' },
  { title: t('Study.study_id'), key: 'study_id' },
  { title: t('CohortsStepper.arm_name'), key: 'name' },
  {
    title: t('CohortsStepper.study_arm_type'),
    key: 'arm_type_name',
  },
  { title: t('CohortsStepper.arm_short_name'), key: 'short_name' },
]
const sourceArmHeaders = selectedArmHeaders
const steps = ref([])
const creationMode = ref(cohortConstants.FULL)
const resetLoading = ref(0)
const selectStudyForm = ref()
const selectedSourceStudy = ref(null)
const studies = ref([])
const studiesLoading = ref(false)
const sourceStudyArms = ref([])
const sourceArmsLoading = ref(false)
const selectedArms = ref([])
const selectAllSourceArms = ref(false)
const armsForm = ref()
const cohortsForm = ref()
const linkingForm = ref()
const arms = ref([{}])
const armTypes = ref([])
const cohorts = ref([{}])
const branches = ref([])
const totalParticipants = ref(0)
const loading = ref(false)
const editableDesignClass = ref(true)
const showBranchEditForm = ref(false)
const editBranch = ref(null)
const sourceVariable = ref({})
const sourceVariables = [
  t('CohortsStepper.cohort'),
  t('CohortsStepper.subgroup'),
  t('CohortsStepper.stratum'),
]
const currentDesignClass = ref('')
const helpItems = ref([
  'CohortsStepper.select_class',
  'CohortsStepper.set_arms_for_study',
  'CohortsStepper.study_arm_type',
  'CohortsStepper.arm_name',
  'CohortsStepper.arm_short_name',
  'CohortsStepper.arm_label',
  'CohortsStepper.rand_group',
  'CohortsStepper.arm_code',
  'CohortsStepper.set_cohorts_for_study',
  'CohortsStepper.source_var',
  'CohortsStepper.cohort_code',
  'CohortsStepper.cohort_name',
  'CohortsStepper.cohort_short_name',
  'CohortsStepper.link_arms_cohorts',
])

onMounted(async () => {
  currentDesignClass.value = JSON.parse(JSON.stringify(props.designClass))
  cohortsApi
    .checkDesignClassEditable(studiesGeneralStore.selectedStudy.uid)
    .then((resp) => {
      editableDesignClass.value = resp.data
    })
  codelists.getTermsByCodelist('armTypes').then((resp) => {
    armTypes.value = resp.data.items
  })
  studiesLoading.value = true
  study
    .getAllList()
    .then((resp) => {
      studies.value = resp.data.filter(
        (item) => item.uid !== studiesGeneralStore.selectedStudy.uid
      )
    })
    .finally(() => {
      studiesLoading.value = false
    })
  stepper.value.currentStep = props.initialStep
  if (stepper.value.currentStep === 2) {
    getArms()
  } else if (stepper.value.currentStep === 3) {
    await getArms()
    await getCohorts()
    cohortsApi
      .getSourceVariable(studiesGeneralStore.selectedStudy.uid)
      .then((resp) => {
        if (resp.data) {
          sourceVariable.value = resp.data
        }
      })
  } else if (stepper.value.currentStep === 4) {
    await getArms()
    await getCohorts()
    cohortsApi
      .getSourceVariable(studiesGeneralStore.selectedStudy.uid)
      .then((resp) => {
        if (resp.data) {
          sourceVariable.value = resp.data
        }
      })
    cohorts.value.forEach((cohort) => {
      if (!cohort.branch_arm_roots) {
        cohort.branch_arm_roots = []
        arms.value.forEach(() => {
          cohort.branch_arm_roots.push({ number_of_subjects: 0 })
        })
      }
    })
    getBranches()
  }
})

watch(creationMode, (value) => {
  if (value === cohortConstants.SELECT) {
    steps.value = selectFromStudiesSteps
  } else if (value === cohortConstants.MANUAL) {
    steps.value = manuallyDefinedSteps
  } else {
    steps.value = fullStepperSteps
  }
})

watch(
  () => props.designClass,
  (value) => {
    if (value === cohortConstants.MANUAL) {
      creationMode.value = cohortConstants.MANUAL
    } else {
      creationMode.value = cohortConstants.FULL
    }
  },
  { immediate: true }
)

const title = computed(() => {
  return arms.value.length > 0 || cohorts.value.length > 0
    ? t('CohortsStepper.update_structure')
    : t('CohortsStepper.create_stucture')
})

// "Select from studies" produces an arms-only study, so it shares the MANUAL
// layout and is persisted with the MANUAL design class.
const isArmsOnly = computed(
  () =>
    creationMode.value === cohortConstants.MANUAL ||
    creationMode.value === cohortConstants.SELECT
)
const effectiveDesignClass = computed(() =>
  creationMode.value === cohortConstants.SELECT
    ? cohortConstants.MANUAL
    : creationMode.value
)

const continueLabel = computed(() => {
  if (stepper.value.currentStep === 1) {
    return t('_global.continue')
  } else if (
    creationMode.value === cohortConstants.FULL &&
    stepper.value.currentStep === 4
  ) {
    return t('CohortsStepper.create_stucture')
  } else if (isArmsOnly.value && stepper.value.currentStep === 2) {
    return t('CohortsStepper.create_arms')
  }
  return t('_global.save_continue')
})

const checkContinueDisabled = computed(() => {
  if (
    stepper.value.currentStep === 3 &&
    (arms.value.length === 0 || cohorts.value.length === 0)
  ) {
    return true
  }
  if (
    creationMode.value === cohortConstants.SELECT &&
    stepper.value.currentStep === 2 &&
    selectedArms.value.length === 0
  ) {
    return true
  }
  return false
})

steps.value = fullStepperSteps

function updateParticipants(value, cohortIndex, armIndex) {
  try {
    let armCounter = 0
    branches.value[armIndex].study_cohorts.forEach((cohort) => {
      armCounter += cohort.study_branch_arms[0].number_of_subjects
    })
    branches.value[armIndex].number_of_subjects = armCounter

    let cohortCounter = 0
    if (!cohorts.value[cohortIndex].branch_arm_roots[armIndex]) {
      const iterations =
        armIndex + 1 - cohorts.value[cohortIndex].branch_arm_roots.length
      for (let i = iterations; i > 0; i--) {
        cohorts.value[cohortIndex].branch_arm_roots.push({
          number_of_subjects: 0,
        })
      }
    }
    cohorts.value[cohortIndex].branch_arm_roots[armIndex].number_of_subjects =
      value
    cohorts.value[cohortIndex].branch_arm_roots.forEach((branch) => {
      cohortCounter += branch.number_of_subjects
    })
    cohorts.value[cohortIndex].number_of_subjects = cohortCounter
    totalParticipants.value = 0
    cohorts.value.forEach((cohort) => {
      totalParticipants.value += cohort.number_of_subjects
    })
  } catch (error) {
    console.error(error)
  }
}

async function saveAndContinue() {
  if (!(await stepper.value.validateStepObserver(stepper.value.currentStep))) {
    return
  }
  loading.value = true
  if (stepper.value.currentStep === 0) {
    stepper.value.currentStep = 1
  }
  if (stepper.value.currentStep === 1) {
    saveDesignClass()
    // Always refresh the current study's arms so isArmInCurrentStudy() can
    // correctly dedup against them, even when the arm list started out as
    // the empty placeholder (e.g. reopening this step with arms already
    // present). Awaited so both lists are settled before the caller's
    // promise resolves, rather than racing the step-2 render.
    if (creationMode.value === cohortConstants.SELECT) {
      await Promise.all([getArms(), loadSourceStudyArms()])
    } else {
      await getArms()
    }
  } else if (
    stepper.value.currentStep === 2 &&
    creationMode.value === cohortConstants.SELECT
  ) {
    createSelectedArms()
  } else if (stepper.value.currentStep === 2) {
    saveArms(steps.value.length === 2)
    getCohorts()
    cohortsApi
      .getSourceVariable(studiesGeneralStore.selectedStudy.uid)
      .then((resp) => {
        if (resp.data) {
          sourceVariable.value = resp.data
        }
      })
  } else if (stepper.value.currentStep === 3) {
    saveSourceVariable()
    saveCohorts()
  } else if (stepper.value.currentStep === 4) {
    saveBranches()
  }
}

async function saveDesignClass() {
  // "Select from studies" is not a design class; persist it as MANUAL.
  const designClassValue = effectiveDesignClass.value
  if (props.designClass) {
    if (currentDesignClass.value === designClassValue) {
      loading.value = false
      stepper.value.currentStep += 1
      return
    }
    const options = {
      type: 'warning',
      width: 800,
      cancelLabel: t('CohortsStepper.keep_class'),
      agreeLabel: t('CohortsStepper.change_class'),
    }
    if (
      currentDesignClass.value === cohortConstants.MANUAL &&
      designClassValue !== cohortConstants.MANUAL
    ) {
      if (
        editableDesignClass.value ||
        (await confirm.value.open(
          t('CohortsStepper.change_class_warning_1'),
          options
        ))
      ) {
        cohortsApi
          .changeStudyDesignClass(studiesGeneralStore.selectedStudy.uid, {
            value: designClassValue,
          })
          .then(() => {
            currentDesignClass.value = designClassValue
            loading.value = false
            stepper.value.currentStep += 1
            return
          })
          .catch((error) => {
            console.error(t('CohortsStepper.error_update_class'), error)
            loading.value = false
          })
      }
      loading.value = false
      return
    } else if (
      currentDesignClass.value === cohortConstants.FULL &&
      designClassValue !== cohortConstants.FULL
    ) {
      if (
        editableDesignClass.value ||
        (await confirm.value.open(
          t('CohortsStepper.change_class_warning_2'),
          options
        ))
      ) {
        cohortsApi
          .changeStudyDesignClass(studiesGeneralStore.selectedStudy.uid, {
            value: designClassValue,
          })
          .then(() => {
            currentDesignClass.value = designClassValue
            loading.value = false
            stepper.value.currentStep += 1
            return
          })
          .catch((error) => {
            console.error(t('CohortsStepper.error_update_class'), error)
            loading.value = false
          })
      }
    }
    loading.value = false
    return
  } else {
    cohortsApi
      .setStudyDesignClass(studiesGeneralStore.selectedStudy.uid, {
        value: designClassValue,
      })
      .then(() => {
        currentDesignClass.value = designClassValue
        loading.value = false
        stepper.value.currentStep += 1
        return
      })
      .catch((error) => {
        console.error(t('CohortsStepper.error_update_class'), error)
        loading.value = false
      })
  }
}

function saveArms(close = false) {
  const payload = []
  arms.value.forEach((arm) => {
    payload.push({ method: arm.arm_uid ? 'PATCH' : 'POST', content: arm })
  })
  cohortsApi
    .armsBatchActions(studiesGeneralStore.selectedStudy.uid, payload)
    .then((resp) => {
      loading.value = false
      if (reportBatchErrors(resp.data)) {
        return
      }
      notificationHub.add({ msg: t('CohortsStepper.arms_saved') })
      if (close) {
        stepper.value.close()
        return
      }
      arms.value = resp.data.map((arm) => arm.content)
      arms.value.forEach((arm) => (arm.arm_type_uid = arm.arm_type.term_uid))
      stepper.value.currentStep += 1
      return
    })
    .catch((error) => {
      console.error(t('CohortsStepper.error_update_arms'), error)
      loading.value = false
    })
}
function saveSourceVariable() {
  if (sourceVariable.value.start_date) {
    cohortsApi.editSourceVariable(
      studiesGeneralStore.selectedStudy.uid,
      sourceVariable.value
    )
  } else if (!_isEmpty(sourceVariable.value)) {
    cohortsApi.setSourceVariable(
      studiesGeneralStore.selectedStudy.uid,
      sourceVariable.value
    )
  }
}
async function saveCohorts(close = false) {
  const payload = []
  cohorts.value.forEach((cohort) => {
    payload.push({
      method: cohort.cohort_uid ? 'PATCH' : 'POST',
      content: cohort,
    })
  })
  cohortsApi
    .cohortsBatchActions(studiesGeneralStore.selectedStudy.uid, payload)
    .then((resp) => {
      loading.value = false
      if (reportBatchErrors(resp.data)) {
        return
      }
      notificationHub.add({ msg: t('CohortsStepper.cohorts_saved') })
      if (close) {
        stepper.value.close()
        return
      }
      cohorts.value = resp.data.map((cohort) => cohort.content)
      cohorts.value.forEach((cohort) => {
        if (!cohort.branch_arm_roots) {
          cohort.branch_arm_roots = []
          arms.value.forEach(() => {
            cohort.branch_arm_roots.push({ number_of_subjects: 0 })
          })
        }
      })
      getBranches()
      stepper.value.currentStep += 1
    })
    .catch((error) => {
      console.error(t('CohortsStepper.error_update_cohorts'), error)
      loading.value = false
    })
}
function saveBranches() {
  loading.value = true
  const payload = []
  branches.value.forEach((arm) => {
    arm.study_cohorts.forEach((cohort) => {
      if (cohort.study_branch_arms[0].number_of_subjects > 0) {
        payload.push({
          method: cohort.study_branch_arms[0].branch_arm_uid ? 'PATCH' : 'POST',
          content: cohort.study_branch_arms[0],
        })
      } else if (
        cohort.study_branch_arms[0].branch_arm_uid &&
        !cohort.study_branch_arms[0].number_of_subjects
      ) {
        payload.push({
          method: 'DELETE',
          content: {
            branch_arm_uid: cohort.study_branch_arms[0].branch_arm_uid,
          },
        })
      }
    })
  })
  cohortsApi
    .branchesBatchActions(studiesGeneralStore.selectedStudy.uid, payload)
    .then((resp) => {
      loading.value = false
      if (reportBatchErrors(resp.data)) {
        return
      }
      notificationHub.add({ msg: t('CohortsStepper.branches_saved') })
      stepper.value.close()
      return
    })
    .catch((error) => {
      console.error(t('CohortsStepper.error_update_branches'), error)
      loading.value = false
    })
}
function copyBranches() {
  try {
    let numbersArray = []
    branches.value.forEach((arm) => {
      numbersArray.push(
        arm.study_cohorts[0].study_branch_arms[0].number_of_subjects
      )
    })
    branches.value.forEach((arm, index) => {
      arm.study_cohorts.forEach((cohort) => {
        arm.number_of_subjects = numbersArray[index] * cohorts.value.length
        cohort.study_branch_arms[0].number_of_subjects = numbersArray[index]
      })
    })
    const numbersCount = numbersArray.reduce((acc, curr) => acc + curr, 0)
    cohorts.value.forEach((cohort) => {
      cohort.number_of_subjects = numbersCount
    })
    totalParticipants.value = numbersCount * cohorts.value.length
  } catch (error) {
    console.error(error)
  }
}
function cancel() {
  stepper.value.cancel()
}
function close() {
  emit('close')
}
async function saveAndClose() {
  if (!(await stepper.value.validateStepObserver(stepper.value.currentStep))) {
    return
  }
  loading.value = true
  if (stepper.value.currentStep === 2) {
    saveArms(true)
  } else if (stepper.value.currentStep === 3) {
    saveSourceVariable()
    saveCohorts(true)
  } else if (stepper.value.currentStep === 4) {
    saveBranches()
  }
}
function previousStep() {
  if (stepper.value.currentStep === 2) {
    cohortsApi
      .checkDesignClassEditable(studiesGeneralStore.selectedStudy.uid)
      .then((resp) => {
        editableDesignClass.value = resp.data
      })
  }
  stepper.value.currentStep -= 1
}
function createBranchesMatrix(matrix) {
  matrix.forEach((arm) => {
    totalParticipants.value += arm.number_of_subjects
    const armUid = arm.uid
    arm.study_cohorts.forEach((cohort) => {
      const cohortUid = cohort.uid
      if (cohort.study_branch_arms[0]) {
        cohort.study_branch_arms[0].arm_uid = armUid
        cohort.study_branch_arms[0].study_cohort_uid = cohortUid
        cohort.study_branch_arms[0].branch_arm_uid =
          cohort.study_branch_arms[0].uid
        delete cohort.study_branch_arms[0].uid
      } else {
        cohort.study_branch_arms[0] = {
          name: `${arm.name} ${cohort.name}`,
          number_of_subjects: 0,
          short_name: `${arm.short_name} ${cohort.short_name}`,
          code: null,
          randomization_group: null,
          arm_uid: arm.uid,
          study_cohort_uid: cohort.uid,
        }
      }
    })
  })
  branches.value = matrix
}
function getObserver(step) {
  if (step === 1 && creationMode.value === cohortConstants.SELECT) {
    return selectStudyForm.value
  }
  if (step === 2) {
    return armsForm.value
  } else if (step === 3) {
    return cohortsForm.value
  } else if (step === 4) {
    return linkingForm.value
  }
}

async function getArms() {
  const params = {
    study_uid: studiesGeneralStore.selectedStudy.uid,
  }
  await armsApi
    .getAllForStudy(studiesGeneralStore.selectedStudy.uid, { params })
    .then((resp) => {
      if (resp.data.items.length === 0) {
        return
      }
      arms.value = resp.data.items
      arms.value.forEach((arm) => (arm.arm_type_uid = arm.arm_type.term_uid))
    })
}

async function loadSourceStudyArms() {
  selectedArms.value = []
  sourceStudyArms.value = []
  selectAllSourceArms.value = false
  if (!selectedSourceStudy.value) {
    return
  }
  const studyId =
    selectedSourceStudy.value.id ??
    selectedSourceStudy.value.current_metadata?.identification_metadata
      ?.study_id
  const params = { study_uid: selectedSourceStudy.value.uid }
  sourceArmsLoading.value = true
  await armsApi
    .getAllForStudy(selectedSourceStudy.value.uid, { params })
    .then((resp) => {
      sourceStudyArms.value = resp.data.items.map((arm) => ({
        ...arm,
        study_id: studyId,
        arm_type_name:
          arm.arm_type?.term_name ?? arm.arm_type?.sponsor_preferred_name ?? '',
      }))
    })
    .finally(() => {
      sourceArmsLoading.value = false
    })
}

function isArmSelected(arm) {
  return selectedArms.value.some((item) => item.arm_uid === arm.arm_uid)
}
// A source arm is treated as already present in the current study when an
// existing arm shares its type and either its name or its short_name; such
// arms must not be selectable to avoid creating duplicates.
function isArmInCurrentStudy(arm) {
  const armTypeUid = arm.arm_type?.term_uid
  if (!armTypeUid) {
    return false
  }
  return arms.value.some((existing) => {
    if (existing.arm_type?.term_uid !== armTypeUid) {
      return false
    }
    return existing.name === arm.name || existing.short_name === arm.short_name
  })
}
// Combined guard used by the table to disable a source arm's copy action.
function isArmDisabled(arm) {
  return isArmSelected(arm) || isArmInCurrentStudy(arm)
}
function selectArm(arm) {
  if (!isArmDisabled(arm)) {
    selectedArms.value.push(arm)
  }
}
function unselectArm(arm) {
  selectedArms.value = selectedArms.value.filter(
    (item) => item.arm_uid !== arm.arm_uid
  )
  // Removing an item means the selection is no longer "all".
  selectAllSourceArms.value = false
}
// "Select all" mirrors every selectable source arm into the selection, skipping
// arms already present in the current study. When the whole source study is
// selected (nothing skipped), createSelectedArms() copies it in one call.
function toggleSelectAllSourceArms(value) {
  selectedArms.value = value
    ? sourceStudyArms.value.filter((arm) => !isArmInCurrentStudy(arm))
    : []
}

function createSelectedArms() {
  if (!selectedArms.value.length) {
    loading.value = false
    return
  }
  // When every source arm is selected (none skipped as already present), let the
  // backend copy the whole source study in a single call instead of replaying
  // each arm individually.
  if (
    selectAllSourceArms.value &&
    selectedArms.value.length === sourceStudyArms.value.length
  ) {
    cohortsApi
      .copyArmsFromStudy(
        studiesGeneralStore.selectedStudy.uid,
        selectedSourceStudy.value.uid
      )
      .then(() => {
        loading.value = false
        notificationHub.add({ msg: t('CohortsStepper.arms_saved') })
        stepper.value.close()
      })
      .catch((error) => {
        console.error(t('CohortsStepper.error_update_arms'), error)
        loading.value = false
      })
    return
  }
  // Strip identifiers so the copied arms are created (POST) in the current
  // study rather than referencing the source study's arms.
  const payload = selectedArms.value.map((arm) => ({
    method: 'POST',
    content: {
      arm_type_uid: arm.arm_type ? arm.arm_type.term_uid : null,
      name: arm.name,
      short_name: arm.short_name,
      label: arm.label,
      code: arm.code,
      randomization_group: arm.randomization_group,
      number_of_subjects: arm.number_of_subjects,
      description: arm.description,
    },
  }))
  cohortsApi
    .armsBatchActions(studiesGeneralStore.selectedStudy.uid, payload)
    .then((resp) => {
      loading.value = false
      if (reportBatchErrors(resp.data)) {
        return
      }
      notificationHub.add({ msg: t('CohortsStepper.arms_saved') })
      stepper.value.close()
    })
    .catch((error) => {
      console.error(t('CohortsStepper.error_update_arms'), error)
      loading.value = false
    })
}

async function getCohorts() {
  const params = {
    study_uid: studiesGeneralStore.selectedStudy.uid,
  }
  await armsApi
    .getAllCohorts(studiesGeneralStore.selectedStudy.uid, params)
    .then((resp) => {
      if (resp.data.items.length === 0) {
        return
      }
      cohorts.value = resp.data.items
    })
}

function getBranches() {
  cohortsApi
    .getStudyStructure(studiesGeneralStore.selectedStudy.uid)
    .then((resp) => {
      createBranchesMatrix(resp.data)
    })
}

async function removeArm(arm, index) {
  if (arm.arm_uid) {
    const options = {
      type: 'error',
      cancelLabel: t('CohortsStepper.keep_arm'),
      agreeLabel: t('CohortsStepper.remove_arm'),
    }
    if (
      await confirm.value.open(t('CohortsStepper.remove_arm_warning'), options)
    ) {
      cohortsApi
        .removeArm(studiesGeneralStore.selectedStudy.uid, arm.arm_uid)
        .then(() => {
          arms.value.splice(index, 1)
        })
    }
  } else {
    arms.value.splice(index, 1)
  }
}
async function removeCohort(cohort, index) {
  if (cohort.cohort_uid) {
    const options = {
      type: 'error',
      cancelLabel: t('CohortsStepper.keep_cohort'),
      agreeLabel: t('CohortsStepper.remove_cohort'),
    }
    if (
      await confirm.value.open(
        t('CohortsStepper.remove_cohort_warning'),
        options
      )
    ) {
      cohortsApi
        .removeCohort(
          studiesGeneralStore.selectedStudy.uid,
          cohort.cohort_uid,
          true
        )
        .then(() => {
          cohorts.value.splice(index, 1)
        })
    }
  } else {
    cohorts.value.splice(index, 1)
  }
}
function openBranchEditForm(branch) {
  editBranch.value = branch
  showBranchEditForm.value = true
}
function closeBranchEditForm() {
  editBranch.value = null
  showBranchEditForm.value = false
}
function applyBranchChanges(updatedBranch) {
  branches.value.forEach((arm) => {
    arm.study_cohorts.forEach((cohort) => {
      if (
        cohort.study_branch_arms[0].arm_uid === updatedBranch.arm_uid &&
        cohort.study_branch_arms[0].study_cohort_uid ===
          updatedBranch.study_cohort_uid
      ) {
        cohort.study_branch_arms[0] = updatedBranch
      }
    })
  })
  closeBranchEditForm()
}
</script>
<style scoped>
.label {
  font-weight: 700;
  font-size: 18px;
  line-height: 24px;
  letter-spacing: -0.02em;
  color: var(--semantic-system-brand, #001965);
  min-height: 24px;
}
.tile {
  padding: 20px;
  display: inline-flex;
}
#v-field__field > label.v-label.v-field-label {
  font-size: 10px !important;
}
</style>
