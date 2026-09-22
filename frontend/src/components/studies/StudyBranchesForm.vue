<template>
  <HorizontalStepperForm
    ref="stepper"
    :title="title"
    :steps="steps"
    :help-items="helpItems"
    :form-observer-getter="getObserver"
    :edit-data="editData"
    help-text=""
    custom-actions
    @close="close"
  >
    <template #[`step.method`]>
      <div class="label mb-4">
        {{ $t('StudyBranchArms.select_method') }}
      </div>
      <v-radio-group v-model="creationMethod">
        <v-radio
          :label="$t('StudyBranchArms.create_from_scratch')"
          :value="methods.SCRATCH"
          data-cy="create-from-scratch"
        />
        <v-radio
          :label="$t('StudyBranchArms.select_from_studies')"
          :value="methods.SELECT"
          data-cy="select-from-studies"
        />
      </v-radio-group>
      <v-form ref="selectStudyForm">
        <v-row v-if="creationMethod === methods.SELECT">
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
    <template #[`step.details`]>
      <v-form ref="observer">
        <v-row>
          <v-col cols="12">
            <v-autocomplete
              v-model="form.arm_uid"
              :label="$t('StudyBranchArms.study_arm')"
              data-cy="study-arm"
              :items="arms"
              item-title="name"
              item-value="arm_uid"
              :rules="[formRules.required]"
              clearable
              :disabled="isEdit"
              class="required"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.name"
              :label="$t('StudyBranchArms.branch_arm_name')"
              data-cy="study-branch-arm-name"
              :rules="[formRules.required, formRules.max(form.name, 200)]"
              clearable
              class="required"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.short_name"
              :label="$t('StudyBranchArms.branch_arm_short_name')"
              data-cy="study-branch-arm-short-name"
              :rules="[formRules.required, formRules.max(form.short_name, 20)]"
              clearable
              class="required"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.randomization_group"
              :label="$t('StudyBranchArms.randomisation_group')"
              data-cy="study-branch-arm-randomisation-group"
              clearable
              :rules="[formRules.max(form.randomization_group, 20)]"
              @blur="enableBranchCode"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.code"
              :label="$t('StudyBranchArms.code')"
              data-cy="study-branch-arm-code"
              :rules="codeRules"
              clearable
              :disabled="!branchCodeEnable && !isEdit"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.number_of_subjects"
              :disabled="!form.arm_uid"
              :label="$t('StudyBranchArms.nuber_of_subjects')"
              data-cy="study-branch-arm-planned-number-of-subjects"
              :rules="[
                formRules.min_value(form.number_of_subjects, 1),
                numberOfSubjectsMaxValueRule(
                  form.number_of_subjects,
                  findMaxNuberOfSubjects()
                ),
              ]"
              type="number"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.description"
              :label="$t('_global.description')"
              data-cy="study-branch-arm-description"
              clearable
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #[`step.selectBranches`]>
      <div class="label mb-4">
        {{ $t('StudyBranchArms.selected_branches') }}
      </div>
      <v-data-table
        data-cy="selected-branches-table"
        :headers="selectedBranchHeaders"
        :items="selectedBranches"
      >
        <template #[`item.actions`]="{ item }">
          <v-btn
            icon="mdi-delete-outline"
            color="red"
            variant="text"
            data-cy="remove-selected-branch"
            @click="unselectBranch(item)"
          />
        </template>
      </v-data-table>
    </template>
    <template #[`step.selectBranches.after`]>
      <p class="text-grey text-body-large font-weight-bold mb-0 ml-3">
        {{ $t('StudyBranchArms.copy_instructions') }}
      </p>
      <v-col cols="12" class="pt-0 mt-0">
        <v-data-table
          data-cy="source-branches-table"
          :headers="sourceBranchHeaders"
          :items="sourceStudyBranches"
          :loading="sourceBranchesLoading"
        >
          <template #[`header.actions`]>
            <v-checkbox
              v-model="selectAllSourceBranches"
              :title="$t('_global.select_all')"
              :disabled="!sourceStudyBranches.length"
              density="compact"
              hide-details
              data-cy="select-all-source-branches"
              @update:model-value="toggleSelectAllSourceBranches"
            />
          </template>
          <template #[`item.actions`]="{ item }">
            <v-btn
              :data-cy="$t('StudySelectionTable.copy_item')"
              icon="mdi-content-copy"
              size="small"
              variant="text"
              :color="isBranchSelected(item) ? '' : 'primary'"
              :disabled="isBranchSelected(item)"
              :title="$t('StudySelectionTable.copy_item')"
              @click="selectBranch(item)"
            />
          </template>
        </v-data-table>
      </v-col>
    </template>
    <template #customActions>
      <v-btn
        class="secondary-btn my-2 ml-2"
        variant="outlined"
        width="120px"
        rounded="xl"
        data-cy="cancel-button"
        :loading="loading"
        @click="cancel"
      >
        {{ $t('_global.cancel') }}
      </v-btn>
      <v-spacer />
      <v-btn
        v-if="stepper && stepper.currentStep > 1"
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
        @click="primaryAction()"
      >
        {{ continueLabel }}
      </v-btn>
    </template>
  </HorizontalStepperForm>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import armsApi from '@/api/arms'
import study from '@/api/study'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import StudySelectorField from '@/components/studies/StudySelectorField.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const methods = {
  SCRATCH: 'scratch',
  SELECT: 'select',
}

const { t } = useI18n()
const formRules = inject('formRules')
const notificationHub = inject('notificationHub')
const studiesGeneralStore = useStudiesGeneralStore()

const props = defineProps({
  editedBranchArm: {
    type: Object,
    default: () => ({}),
  },
  arms: {
    type: Array,
    default: () => [],
  },
})
const emit = defineEmits(['close'])

const selectedStudy = studiesGeneralStore.selectedStudy

const stepper = ref()
const confirm = ref()
const observer = ref()
const selectStudyForm = ref()

const form = ref({})
const editData = ref({})
const helpItems = ref([])
const branchCodeEnable = ref(false)
const codeRules = ref([])
const selectedArm = ref({})
const loading = ref(false)

const creationMethod = ref(methods.SCRATCH)
const studies = ref([])
const studiesLoading = ref(false)
const selectedSourceStudy = ref(null)
const sourceStudyBranches = ref([])
const sourceBranchesLoading = ref(false)
const selectedBranches = ref([])
const selectAllSourceBranches = ref(false)

const isEdit = computed(() => Object.keys(props.editedBranchArm).length !== 0)

const selectedBranchHeaders = [
  { title: '', key: 'actions', width: '1%' },
  { title: t('Study.study_id'), key: 'study_id' },
  { title: t('StudyBranchArms.arm_name'), key: 'arm_name' },
  { title: t('StudyBranchArms.name'), key: 'name' },
  { title: t('StudyBranchArms.short_name'), key: 'short_name' },
]
const sourceBranchHeaders = selectedBranchHeaders

const detailsStep = {
  name: 'details',
  title: t('StudyBranchArms.branch_details'),
}
const methodStep = { name: 'method', title: t('StudyBranchArms.select_method') }
const selectStep = {
  name: 'selectBranches',
  title: t('StudyBranchArms.select_branches'),
}

const steps = computed(() => {
  if (isEdit.value) {
    return [detailsStep]
  }
  if (creationMethod.value === methods.SELECT) {
    return [methodStep, selectStep]
  }
  return [methodStep, detailsStep]
})

const currentStepName = computed(() => {
  const step = stepper.value ? stepper.value.currentStep : 1
  return steps.value[step - 1] ? steps.value[step - 1].name : ''
})

const continueLabel = computed(() => {
  switch (currentStepName.value) {
    case 'method':
      return t('_global.continue')
    default:
      return t('_global.save')
  }
})

const checkContinueDisabled = computed(() => {
  if (
    currentStepName.value === 'method' &&
    creationMethod.value === methods.SELECT &&
    !selectedSourceStudy.value
  ) {
    return true
  }
  if (
    currentStepName.value === 'selectBranches' &&
    selectedBranches.value.length === 0
  ) {
    return true
  }
  return false
})

const title = computed(() =>
  isEdit.value
    ? t('StudyBranchArms.edit_branch')
    : t('StudyBranchArms.add_branch')
)

onMounted(async () => {
  if (isEdit.value) {
    const resp = await armsApi.getStudyBranchArm(
      selectedStudy.uid,
      props.editedBranchArm.branch_arm_uid
    )
    form.value = JSON.parse(JSON.stringify(resp.data))
    form.value.arm_uid = resp.data.arm_root.arm_uid
    editData.value = JSON.parse(JSON.stringify(form.value))
  } else {
    // Load the studies a branch arm may be copied from (all but the current).
    studiesLoading.value = true
    study
      .getAllList()
      .then((resp) => {
        studies.value = resp.data.filter(
          (item) => item.uid !== selectedStudy.uid
        )
      })
      .finally(() => {
        studiesLoading.value = false
      })
  }
})

// Keep the form store (used by the stepper's cancel guard) in sync with edits.
watch(
  form,
  (value) => {
    if (!isEdit.value) {
      editData.value = JSON.parse(JSON.stringify(value))
    }
  },
  { immediate: true, deep: true }
)

function getObserver(step) {
  const name = steps.value[step - 1] ? steps.value[step - 1].name : ''
  if (name === 'method') {
    return selectStudyForm.value
  }
  if (name === 'details') {
    return observer.value
  }
  return undefined
}

// This rule is same as max_value generic rule but with custom message
function numberOfSubjectsMaxValueRule(value, max) {
  let result = true
  if (value !== undefined && value !== null) {
    if (Array.isArray(value)) {
      result =
        value.length > 0 && value.every((val) => formRules.max_value(val, max))
    } else {
      result = Number(value) <= Number(max)
    }
  }
  return result || t('StudyBranchArms.number_of_subjects_exceeds')
}

function enableBranchCode() {
  if (!branchCodeEnable.value) {
    form.value.code = form.value.randomization_group
    branchCodeEnable.value = true
    codeRules.value = [
      (v) =>
        (v && v.length <= 20) ||
        t('_errors.max_length_reached', { length: '20' }),
    ]
  }
}

function findMaxNuberOfSubjects() {
  selectedArm.value = props.arms.find((e) => e.arm_uid === form.value.arm_uid)
  return selectedArm.value ? selectedArm.value.number_of_subjects : 0
}

async function primaryAction() {
  if (!(await stepper.value.validateStepObserver(stepper.value.currentStep))) {
    return
  }
  if (currentStepName.value === 'method') {
    if (creationMethod.value === methods.SELECT) {
      await loadSourceStudyBranches()
    }
    stepper.value.currentStep += 1
    return
  }
  if (currentStepName.value === 'selectBranches') {
    createSelectedBranches()
    return
  }
  // details step
  if (isEdit.value) {
    edit()
  } else {
    create()
  }
}

function previousStep() {
  stepper.value.currentStep -= 1
}

async function create() {
  notificationHub.clearErrors()
  loading.value = true

  let armNumberOfSubjects = 0
  ;(
    await armsApi.getAllBranchesForArm(selectedStudy.uid, form.value.arm_uid)
  ).data.forEach((el) => {
    armNumberOfSubjects += el.number_of_subjects
  })
  if (
    selectedArm.value.number_of_subjects <
    parseInt(armNumberOfSubjects, 10) +
      parseInt(form.value.number_of_subjects, 10)
  ) {
    const options = {
      type: 'warning',
      cancelLabel: t('_global.cancel'),
      agreeLabel: t('_global.save_anyway'),
    }
    if (
      !(await confirm.value.open(
        t('StudyBranchArms.subjects_exceeded'),
        options
      ))
    ) {
      loading.value = false
      return
    }
  }
  armsApi
    .createBranchArm(selectedStudy.uid, form.value)
    .then(() => {
      notificationHub.add({ msg: t('StudyBranchArms.branch_created') })
      close()
    })
    .finally(() => {
      loading.value = false
    })
}

async function edit() {
  notificationHub.clearErrors()
  loading.value = true

  let armNumberOfSubjects = 0
  ;(
    await armsApi.getAllBranchesForArm(selectedStudy.uid, form.value.arm_uid)
  ).data.forEach((el) => {
    armNumberOfSubjects +=
      el.branch_arm_uid === props.editedBranchArm.branch_arm_uid
        ? 0
        : el.number_of_subjects
  })
  if (
    selectedArm.value.number_of_subjects <
    parseInt(armNumberOfSubjects, 10) +
      parseInt(form.value.number_of_subjects, 10)
  ) {
    const options = {
      type: 'warning',
      cancelLabel: t('_global.cancel'),
      agreeLabel: t('_global.save_anyway'),
    }
    if (
      !(await confirm.value.open(
        t('StudyBranchArms.subjects_exceeded'),
        options
      ))
    ) {
      loading.value = false
      return
    }
  }
  armsApi
    .editBranchArm(
      selectedStudy.uid,
      props.editedBranchArm.branch_arm_uid,
      form.value
    )
    .then(() => {
      notificationHub.add({ msg: t('StudyBranchArms.branch_updated') })
      close()
    })
    .finally(() => {
      loading.value = false
    })
}

async function loadSourceStudyBranches() {
  selectedBranches.value = []
  sourceStudyBranches.value = []
  selectAllSourceBranches.value = false
  if (!selectedSourceStudy.value) {
    return
  }
  const studyId =
    selectedSourceStudy.value.id ??
    selectedSourceStudy.value.current_metadata?.identification_metadata
      ?.study_id
  sourceBranchesLoading.value = true
  await armsApi
    .getAllBranchArms(selectedSourceStudy.value.uid, {
      study_uid: selectedSourceStudy.value.uid,
    })
    .then((resp) => {
      sourceStudyBranches.value = resp.data.items.map((branch) => ({
        ...branch,
        study_id: studyId,
        arm_name: branch.arm_root?.name ?? '',
      }))
    })
    .finally(() => {
      sourceBranchesLoading.value = false
    })
}

function isBranchSelected(branch) {
  return selectedBranches.value.some(
    (item) => item.branch_arm_uid === branch.branch_arm_uid
  )
}
function selectBranch(branch) {
  if (!isBranchSelected(branch)) {
    selectedBranches.value.push(branch)
  }
}
function unselectBranch(branch) {
  selectedBranches.value = selectedBranches.value.filter(
    (item) => item.branch_arm_uid !== branch.branch_arm_uid
  )
  // Removing an item means the selection is no longer "all".
  selectAllSourceBranches.value = false
}
// "Select all" mirrors every available source branch arm into the selection.
// When active, createSelectedBranches() copies the whole source study at once.
function toggleSelectAllSourceBranches(value) {
  selectedBranches.value = value ? [...sourceStudyBranches.value] : []
}

// Resolve the arm a copied branch should attach to: reuse a same-named arm
// already in the current study, otherwise copy the source arm over.
async function resolveTargetArmUid(sourceArm, armUidMap) {
  if (!sourceArm) {
    return null
  }
  if (armUidMap.has(sourceArm.arm_uid)) {
    return armUidMap.get(sourceArm.arm_uid)
  }
  const existing = props.arms.find((arm) => arm.name === sourceArm.name)
  if (existing) {
    armUidMap.set(sourceArm.arm_uid, existing.arm_uid)
    return existing.arm_uid
  }
  const { data: fullArm } = await armsApi.getStudyArm(
    selectedSourceStudy.value.uid,
    sourceArm.arm_uid
  )
  const { data: createdArm } = await armsApi.create(selectedStudy.uid, {
    arm_type_uid: fullArm.arm_type ? fullArm.arm_type.term_uid : null,
    name: fullArm.name,
    short_name: fullArm.short_name,
    label: fullArm.label,
    code: fullArm.code,
    description: fullArm.description,
    arm_colour: fullArm.arm_colour,
    randomization_group: fullArm.randomization_group,
    number_of_subjects: fullArm.number_of_subjects,
  })
  armUidMap.set(sourceArm.arm_uid, createdArm.arm_uid)
  return createdArm.arm_uid
}

async function createSelectedBranches() {
  if (!selectedBranches.value.length) {
    return
  }
  notificationHub.clearErrors()
  loading.value = true
  try {
    // When every available branch arm is selected, let the backend copy the
    // whole source study (arms included) in a single call.
    if (selectAllSourceBranches.value) {
      await armsApi.copyBranchArmsFromStudy(
        selectedStudy.uid,
        selectedSourceStudy.value.uid
      )
      notificationHub.add({ msg: t('StudyBranchArms.branch_created') })
      close()
      return
    }
    // Copy the arm each branch arm belongs to (deduplicated within the batch),
    // then create the branch arms attached to their copied arm.
    const armUidMap = new Map()
    for (const branch of selectedBranches.value) {
      await resolveTargetArmUid(branch.arm_root, armUidMap)
    }
    // Create each branch independently and report the per-item outcome so a
    // single failure neither aborts the others nor masks the error.
    const results = await Promise.allSettled(
      selectedBranches.value.map((branch) =>
        armsApi.createBranchArm(selectedStudy.uid, {
          arm_uid: armUidMap.get(branch.arm_root?.arm_uid),
          name: branch.name,
          short_name: branch.short_name,
          randomization_group: branch.randomization_group,
          code: branch.code,
          number_of_subjects: branch.number_of_subjects,
          description: branch.description,
        })
      )
    )
    const failures = results.filter((r) => r.status === 'rejected')
    const created = results.length - failures.length
    if (created > 0) {
      notificationHub.add({
        msg: t('StudyBranchArms.branches_created', { count: created }),
      })
    }
    if (failures.length === 0) {
      close()
    }
  } finally {
    loading.value = false
  }
}

function cancel() {
  stepper.value.cancel()
}
function close() {
  notificationHub.clearErrors()
  emit('close')
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
</style>
