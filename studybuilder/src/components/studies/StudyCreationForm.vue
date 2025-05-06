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
      <v-radio-group v-model="createFromScratch" color="primary">
        <v-radio
          :value="true"
          :label="$t('StudyCreationForm.create_from_scratch')"
        />
        <v-radio
          :value="false"
          :label="$t('StudyCreationForm.create_from_study')"
        />
      </v-radio-group>

      <div class="w-50">
        <v-alert
          v-if="!createFromScratch"
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
                density="compact"
                variant="outlined"
                rounded="lg"
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
                variant="outlined"
                rounded="lg"
                hide-details
                density="compact"
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
                variant="outlined"
                rounded="lg"
                hide-details
                density="compact"
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
                  (value) =>
                    formRules.max(value, appStore.userData.studyNumberLength),
                ]"
                density="compact"
                variant="outlined"
                rounded="lg"
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
                density="compact"
                variant="outlined"
                rounded="lg"
                clearable
                data-cy="study-acronym"
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                :label="$t('StudyForm.study_id')"
                :model-value="studyId"
                disabled
                variant="outlined"
                rounded="lg"
                hide-details
                density="compact"
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
import { computed, inject, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudiesManageStore } from '@/stores/studies-manage'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import StudyStructureCopyForm from '@/components/studies/StudyStructureCopyForm.vue'
import studyApi from '@/api/study'

const eventBusEmit = inject('eventBusEmit')
const formRules = inject('formRules')
const router = useRouter()
const { t } = useI18n()
const appStore = useAppStore()
const studiesGeneralStore = useStudiesGeneralStore()
const studiesManageStore = useStudiesManageStore()

const emit = defineEmits(['close'])

const createFromScratch = ref(true)
const project = ref({})
const studyForm = ref({})
const step1FormRef = ref()
const cloneStudyForm = ref({})
const confirmRef = ref()
const stepper = ref()
const copyForm = ref()

const createFromScratchSteps = [
  { name: 'study', title: t('StudyCreationForm.step1_title') },
]
const createFromStudySteps = [
  { name: 'study', title: t('StudyCreationForm.step1_title') },
  { name: 'copy', title: t('StudyCreationForm.step2_title') },
]

const steps = ref(createFromScratchSteps)

const studyId = computed(() => {
  if (project.value.project_number && studyForm.value.study_number) {
    return `${project.value.project_number}-${studyForm.value.study_number}`
  }
  return ''
})

const helpItems = []

function close() {
  studyForm.value = {}
  cloneStudyForm.value = {}
  createFromScratch.value = true
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
  if (createFromScratch.value) {
    const data = JSON.parse(JSON.stringify(studyForm.value))
    data.project_number = project.value.project_number
    return studiesManageStore.addStudy(data).then((resp) => {
      eventBusEmit('notification', { msg: t('StudyForm.add_success') })
      studiesGeneralStore.selectStudy(resp.data)
      router.push({ name: 'SelectOrAddStudy' })
      router.go()
    })
  } else {
    if (!copyForm.value.selectionMade) {
      eventBusEmit('notification', {
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
      ...cloneStudyForm.value,
    }
    data.project_number = data.project_number.project_number
    const studyUid = data.study.uid
    delete data.study
    try {
      const resp = await studyApi.cloneStudy(studyUid, data)
      studiesGeneralStore.selectStudy(resp.data)
    } finally {
      stepper.value.loading = false
    }
    eventBusEmit('notification', { msg: t('StudyForm.add_success') })
    close()
  }
}

watch(createFromScratch, (value) => {
  if (value) {
    steps.value = createFromScratchSteps
  } else {
    steps.value = createFromStudySteps
  }
})
</script>
