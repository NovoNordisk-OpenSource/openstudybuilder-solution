<template>
  <SimpleFormDialog
    ref="formRef"
    :title="$t('StudyDefineForm.title')"
    :help-items="helpItems"
    :help-text="$t('_help.StudyDefineForm.general')"
    :open="open"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-progress-linear v-if="loading" indeterminate color="primary" />
      <v-form ref="observer">
        <v-row class="pr-4">
          <v-col cols="11">
            <v-autocomplete
              v-model="form.study_type_code"
              data-cy="study-type"
              :label="$t('StudyDefineForm.studytype')"
              :items="studiesGeneralStore.studyTypes"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              return-object
              bg-color="white"
              color="nnBaseBlue"
              base-color="nnBaseBlue"
              clearable
            />
          </v-col>
        </v-row>
        <v-row class="pr-4">
          <v-col cols="11">
            <MultipleSelect
              v-model="form.trial_type_codes"
              data-cy="trial-type"
              :label="$t('StudyDefineForm.trialtype')"
              :items="studiesGeneralStore.trialTypes"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              return-object
            />
          </v-col>
        </v-row>
        <v-row class="pr-4">
          <v-col cols="11">
            <v-select
              v-model="form.trial_phase_code"
              data-cy="study-phase-classification"
              :label="$t('StudyDefineForm.trialphase')"
              :items="studiesGeneralStore.trialPhases"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              return-object
              bg-color="white"
              color="nnBaseBlue"
              base-color="nnBaseBlue"
              clearable
            />
          </v-col>
        </v-row>
        <v-row class="pr-4">
          <v-col cols="11">
            <v-select
              v-model="form.development_stage_code"
              data-cy="development_stage"
              :label="$t('StudyDefineForm.development_stage')"
              :items="studiesGeneralStore.developmentStageCodes"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              return-object
              bg-color="white"
              color="nnBaseBlue"
              base-color="nnBaseBlue"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6">
            <YesNoField
              v-model="form.is_extension_trial"
              data-cy="extension-study"
              :rules="[(value) => formRules.oneselected(value, null)]"
              :label="$t('StudyDefineForm.extensiontrial')"
            />
          </v-col>
          <v-col cols="6">
            <YesNoField
              v-model="form.is_adaptive_design"
              data-cy="adaptive-design"
              :label="$t('StudyDefineForm.adaptivedesign')"
            />
          </v-col>
        </v-row>
        <v-row class="pr-4 mb-4">
          <v-col cols="10">
            <v-text-field
              v-model="form.study_stop_rules"
              data-cy="stop-rule"
              :label="$t('StudyDefineForm.studystoprule')"
              bg-color="white"
              color="nnBaseBlue"
              base-color="nnBaseBlue"
              :disabled="stopRulesNone"
            />
          </v-col>
          <v-col cols="2">
            <v-checkbox
              v-model="stopRulesNone"
              bg-color="white"
              color="nnBaseBlue"
              base-color="nnBaseBlue"
              rounded="lg"
              autocomplete="off"
              :label="$t('StudyDefineForm.none')"
              hide-details
              @change="updateStopRules"
            />
          </v-col>
        </v-row>
        <NotApplicableField
          :label="$t('StudyDefineForm.confirmed_resp_min_duration')"
          data-cy="confirmed-resp-min-dur-field"
          :clean-function="setNullValueConfirmedDuration"
          :checked="
            form.confirmed_response_minimum_duration_null_value_code
              ? true
              : false
          "
        >
          <template #mainField="{ notApplicable }">
            <DurationField
              v-model="form.confirmed_response_minimum_duration"
              data-cy="confirmed-resp-min-dur"
              numeric-field-name="duration_value"
              unit-field-name="duration_unit_code"
              :disabled="notApplicable"
            />
          </template>
        </NotApplicableField>
        <v-row class="mt-4">
          <v-col cols="9">
            <YesNoField
              v-model="form.post_auth_indicator"
              data-cy="post-auth-safety-indicator"
              :label="$t('StudyDefineForm.post_auth_safety_indicator')"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { inject, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import _isEmpty from 'lodash/isEmpty'
import DurationField from '@/components/tools/DurationField.vue'
import MultipleSelect from '@/components/tools/MultipleSelect.vue'
import NotApplicableField from '@/components/tools/NotApplicableField.vue'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import studyConstants from '@/constants/study'
import YesNoField from '@/components/tools/YesNoField.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudiesManageStore } from '@/stores/studies-manage'
import studyMetadataForms from '@/utils/studyMetadataForms'
import study from '@/api/study'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const formRules = inject('formRules')

const props = defineProps({
  initialData: {
    type: Object,
    default: null,
  },
  open: Boolean,
})

const emit = defineEmits(['close', 'updated'])

const studiesGeneralStore = useStudiesGeneralStore()
const studiesManageStore = useStudiesManageStore()

const form = ref({})
const helpItems = [
  {
    key: 'StudyDefineForm.studytype',
    context: () => {
      return { url: '/library/ct_catalogues/All/C99077/terms' }
    },
  },
  'StudyDefineForm.studyintent',
  {
    key: 'StudyDefineForm.trialtype',
    context: () => {
      return { url: '/library/ct_catalogues/All/C99077/terms' }
    },
  },
  'StudyDefineForm.trialphase',
  'StudyDefineForm.development_stage',
  'StudyDefineForm.extensiontrial',
  'StudyDefineForm.adaptivedesign',
  'StudyDefineForm.studystoprule',
  'StudyDefineForm.confirmed_resp_min_duration',
  'StudyDefineForm.post_auth_safety_indicator',
]
const stopRulesNone = ref(false)
const loading = ref(false)
const formRef = ref()
const observer = ref()

onMounted(() => {
  if (_isEmpty(props.initialData)) {
    loading.value = true
    study
      .getHighLevelStudyDesignMetadata(studiesGeneralStore.selectedStudy.uid)
      .then((resp) => {
        initForm(resp.data.current_metadata.high_level_study_design)
      })
      .finally(() => {
        loading.value = false
      })
  } else {
    initForm(props.initialData)
  }
})

function initForm(data) {
  form.value = { ...data }
  if (!form.value.confirmed_response_minimum_duration) {
    form.value.confirmed_response_minimum_duration = {}
  }
  if (
    form.value.study_stop_rules == null ||
    form.value.study_stop_rules === studyConstants.STOP_RULE_NONE
  ) {
    stopRulesNone.value = true
    form.value.study_stop_rules = null
  } else {
    stopRulesNone.value = false
  }
}
function setNullValueConfirmedDuration() {
  form.value.confirmed_response_minimum_duration = {}
  if (form.value.confirmed_response_minimum_duration_null_value_code) {
    form.value.confirmed_response_minimum_duration_null_value_code = null
  } else {
    const termUid = studiesGeneralStore.nullValues.find(
      (el) => el.submission_value === studyConstants.TERM_NOT_APPLICABLE_SUBMVAL
    ).term_uid
    form.value.confirmed_response_minimum_duration_null_value_code = {
      term_uid: termUid,
      name: t('_global.not_applicable_full_name'),
    }
  }
}
function close() {
  emit('close')
  notificationHub.clearErrors()
  observer.value.resetValidation()
}
function prepareRequestPayload() {
  const data = { ...form.value }
  if (!data.confirmed_response_minimum_duration.duration_value) {
    data.confirmed_response_minimum_duration = null
  }
  data.study_type_code = studyMetadataForms.getTermPayload(
    data,
    'study_type_code'
  )
  data.trial_intent_types_codes = studyMetadataForms.getTermsPayload(
    data,
    'trial_intent_types_codes'
  )
  data.trial_type_codes = studyMetadataForms.getTermsPayload(
    data,
    'trial_type_codes'
  )
  data.trial_phase_code = studyMetadataForms.getTermPayload(
    data,
    'trial_phase_code'
  )
  if (stopRulesNone.value) {
    // This whole block can be removed if we decide to store NONE values as null in the backend
    data.study_stop_rules = studyConstants.STOP_RULE_NONE
  }
  return data
}
async function cancel() {
  const options = {
    type: 'warning',
    cancelLabel: t('_global.cancel'),
    agreeLabel: t('_global.continue'),
  }
  if (await formRef.value.confirm(t('_global.cancel_changes'), options)) {
    close()
  }
}
async function submit() {
  notificationHub.clearErrors()

  const data = prepareRequestPayload()
  try {
    const parentUid = studiesGeneralStore.selectedStudy.study_parent_part
      ? studiesGeneralStore.selectedStudy.study_parent_part.uid
      : null
    await studiesManageStore.editStudyType(
      studiesGeneralStore.selectedStudy.uid,
      data,
      parentUid
    )
    emit('updated', data)
    notificationHub.add({
      msg: t('StudyDefineForm.update_success'),
    })
    close()
  } finally {
    formRef.value.working = false
  }
}
function updateStopRules(value) {
  if (value) {
    form.value.study_stop_rules = null
  } else {
    form.value.study_stop_rules = ''
  }
}
</script>
