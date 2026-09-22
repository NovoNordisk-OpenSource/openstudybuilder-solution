<template>
  <HorizontalStepperForm
    ref="stepper"
    :title="$t('StudyCreationForm.title')"
    :steps="steps"
    :form-observer-getter="getObserver"
    :help-items="helpItems"
    @close="close"
    @save="submit"
  >
    <template #[`step.study`]>
      <div class="dialog-sub-title mb-4">
        {{ $t('StudyCreationForm.creation_mode_title') }}
      </div>
      <v-radio-group v-model="createMode">
        <v-radio
          value="scratch"
          :label="$t('StudyCreationForm.create_from_scratch')"
        />
        <v-radio
          value="copy"
          :label="$t('StudyCreationForm.create_from_study')"
        />
        <v-radio
          v-if="studyTemplate && studyTemplate?.study_uid !== ''"
          value="default"
        >
          <template #label>
            {{ $t('StudyCreationForm.create_from_template') }}
            <v-tooltip location="top">
              <template #activator="{ props }">
                <v-icon v-bind="props" class="ml-1" size="small">
                  mdi-information-outline
                </v-icon>
              </template>
              {{ $t('StudyCreationForm.create_from_template_help') }}
            </v-tooltip>
          </template>
        </v-radio>
      </v-radio-group>

      <div class="w-50">
        <v-alert
          v-if="createMode === 'copy'"
          color="nnLightBlue200"
          icon="$info"
          :text="$t('StudyCreationForm.copy_notice')"
          class="text-nnTrueBlue mb-6"
        />
        <v-form ref="step1FormRef" class="w-75">
          <v-row>
            <v-col cols="6">
              <v-autocomplete
                v-model="studyForm.project_number"
                :label="$t('StudyForm.project_id')"
                :items="studiesManageStore.projects"
                item-title="project_number"
                return-object
                :rules="[formRules.required]"
                clearable
                data-cy="project-id"
                @update:model-value="updateProject"
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                :label="$t('StudyForm.project_name')"
                :model-value="project.name"
                disabled
                hide-details
                data-cy="project-name"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="6">
              <v-text-field
                :label="$t('StudyForm.brand_name')"
                :model-value="project.brand_name"
                disabled
                hide-details
                data-cy="brand-name"
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                id="studyNumber"
                v-model="studyForm.study_number"
                :label="$t('StudyForm.number')"
                :rules="[
                  formRules.numeric,
                  (value) =>
                    formRules.oneOfTwo(
                      value,
                      studyForm.study_acronym,
                      $t('StudyForm.one_of_two_error_message')
                    ),
                  (value) => formRules.max(value, appStore.studyNumberLength),
                ]"
                clearable
                data-cy="study-number"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="6">
              <v-text-field
                id="studyAcronym"
                v-model="studyForm.study_acronym"
                :label="$t('StudyForm.acronym')"
                :rules="[
                  (value) =>
                    formRules.oneOfTwo(
                      value,
                      studyForm.study_number,
                      $t('StudyForm.one_of_two_error_message')
                    ),
                ]"
                clearable
                data-cy="study-acronym"
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                :label="$t('StudyForm.study_id')"
                :model-value="studyId"
                disabled
                hide-details
                data-cy="study-id"
              />
            </v-col>
          </v-row>
        </v-form>
      </div>
    </template>
    <template #[`step.copy`]>
      <StudyStructureCopyForm ref="copyForm" v-model="cloneStudyForm" />
    </template>
  </HorizontalStepperForm>
  <ConfirmDialog ref="confirmRef" />
</template>

<script setup>
import { computed, inject, ref, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudiesManageStore } from '@/stores/studies-manage'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import StudyStructureCopyForm from '@/components/studies/StudyStructureCopyForm.vue'
import studyApi from '@/api/study'
import studyTemplateApi from '@/api/studyTemplate'
import jobsApi from '@/api/jobs'

const notificationHub = inject('notificationHub')
const formRules = inject('formRules')
const { t } = useI18n()
const appStore = useAppStore()
const studiesGeneralStore = useStudiesGeneralStore()
const studiesManageStore = useStudiesManageStore()

const emit = defineEmits(['close'])

const createMode = ref('scratch')
const project = ref({})
const studyForm = ref({})
const step1FormRef = ref()
const cloneStudyForm = ref({})
const confirmRef = ref()
const stepper = ref()
const copyForm = ref()

const createDefaultSteps = [
  { name: 'study', title: t('StudyCreationForm.step1_title') },
]
const createFromScratchSteps = [
  { name: 'study', title: t('StudyCreationForm.step1_title') },
]
const createFromStudySteps = [
  { name: 'study', title: t('StudyCreationForm.step1_title') },
  { name: 'copy', title: t('StudyCreationForm.step2_title') },
]

const steps = ref(createFromScratchSteps)
const studyTemplate = ref({})

onMounted(() => {
  studyTemplateApi.getStudyTemplate().then((resp) => {
    studyTemplate.value = resp.data
  })
})

const studyId = computed(() => {
  if (project.value.project_number && studyForm.value.study_number) {
    return `${project.value.project_number}-${studyForm.value.study_number}`
  }
  return ''
})

const helpItems = []

/** All clone toggles the API accepts; merge on submit so unset keys are not omitted from JSON. */
const CLONE_STUDY_FLAG_DEFAULTS = {
  copy_study_arm: false,
  copy_study_branch_arm: false,
  copy_study_cohort: false,
  copy_study_element: false,
  copy_study_visit: false,
  copy_study_visits_study_footnote: false,
  copy_study_epoch: false,
  copy_study_epochs_study_footnote: false,
  copy_study_design_matrix: false,
  copy_study_soa_group: false,
  copy_study_activity_group: false,
  copy_study_activity_subgroup: false,
  copy_study_activity: false,
  copy_study_activity_instance: false,
  copy_study_activity_schedule: false,
}

function close() {
  notificationHub.clearErrors()
  studyForm.value = {}
  cloneStudyForm.value = {}
  createMode.value = 'default'
  emit('close')
}

function updateProject(value) {
  project.value = value
}

function getObserver(step) {
  if (step === 1) {
    return step1FormRef.value
  }
  return copyForm.value.formRef
}

async function submit() {
  notificationHub.clearErrors()

  if (createMode.value === 'scratch') {
    const data = JSON.parse(JSON.stringify(studyForm.value))
    data.project_number = project.value.project_number
    try {
      const resp = await studiesManageStore.addStudy(data)
      notificationHub.add({ msg: t('StudyForm.add_success') })
      await studiesGeneralStore.selectStudy(resp.data, true)
    } finally {
      stepper.value.loading = false
    }
  } else if (createMode.value === 'copy') {
    if (!copyForm.value.selectionMade) {
      notificationHub.add({
        msg: t('StudyStructureCopyForm.no_selection'),
        type: 'error',
      })
      stepper.value.loading = false
      return
    }
    /* await confirmRef.value.open(t('StudyForm.study_activity_warning_msg'), {
     *   title: t('StudyForm.study_activity_warning_title'),
     *   agreeLabel: t('StudyForm.study_activity_warning_agree'),
     *   noCancel: true,
     *   type: 'info',
     * }) */
    const data = {
      ...studyForm.value,
      ...CLONE_STUDY_FLAG_DEFAULTS,
      ...cloneStudyForm.value,
    }
    data.project_number = data.project_number.project_number
    const studyUid = data.study.uid
    const src_study_id = data.study.id
    delete data.study
    data.validation_mode = 'warning'
    try {
      const dest_study_id =
        data.project_number +
        '-' +
        (data.study_number ? data.study_number : data.study_acronym)
      const jobResp = await studyApi.cloneStudy(studyUid, data)
      const study = await jobsApi.waitForJobCompletion(
        jobResp.data.uid,
        t('StudyForm.clone_job', { src: src_study_id, dest: dest_study_id })
      )
      // Persist so the toast survives the full-page reload triggered by
      // selectStudy(study, true).
      notificationHub.add({ msg: t('StudyForm.add_success'), persist: true })
      await studiesGeneralStore.selectStudy(study, true)
    } catch (error) {
      notificationHub.add({ msg: error.message, type: 'error' })
    } finally {
      stepper.value.loading = false
    }
  } else {
    const data = {
      ...studyForm.value,
      copy_study_epoch: true,
      copy_study_visit: true,
      copy_study_soa_group: true,
      copy_study_activity: true,
      copy_study_activity_instance: true,
      copy_study_activity_group: true,
      copy_study_activity_subgroup: true,
      copy_study_activity_schedule: true,
      validation_mode: 'warning',
    }
    data.project_number = data.project_number.project_number
    const studyUid = studyTemplate.value.study_uid
    try {
      const dest_study_id =
        data.project_number +
        '-' +
        (data.study_number ? data.study_number : data.study_acronym)
      const jobResp = await studyApi.cloneStudy(studyUid, data)
      const study = await jobsApi.waitForJobCompletion(
        jobResp.data.uid,
        t('StudyForm.clone_default_study_job', { dest: dest_study_id })
      )
      // Persist so the toast survives the full-page reload triggered by
      // selectStudy(study, true).
      notificationHub.add({ msg: t('StudyForm.add_success'), persist: true })
      await studiesGeneralStore.selectStudy(study, true)
    } catch (error) {
      notificationHub.add({ msg: error.message, type: 'error' })
    } finally {
      stepper.value.loading = false
    }
  }
}

watch(createMode, (value) => {
  if (value === 'scratch') {
    steps.value = createFromScratchSteps
  } else if (value === 'copy') {
    steps.value = createFromStudySteps
    cloneStudyForm.value = { ...CLONE_STUDY_FLAG_DEFAULTS }
  } else {
    steps.value = createDefaultSteps
  }
})
</script>
