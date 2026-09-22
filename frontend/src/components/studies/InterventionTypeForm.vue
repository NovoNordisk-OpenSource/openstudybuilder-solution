<template>
  <SimpleFormDialog
    ref="form"
    :title="$t('StudyInterventionTypeForm.title')"
    :help-items="helpItems"
    :help-text="$t('_help.StudyInterventionTypeForm.general')"
    :open="open"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-progress-linear v-if="loading" indeterminate color="primary" />
      <v-form ref="observer">
        <v-row>
          <v-col cols="11">
            <v-autocomplete
              v-model="form.intervention_type_code"
              :data-cy="$t('StudyInterventionTypeForm.intervention_type')"
              :label="$t('StudyInterventionTypeForm.intervention_type')"
              :items="studiesGeneralStore.interventionTypes"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              return-object
              clearable
            />
          </v-col>
        </v-row>
        <NotApplicableField
          :clean-function="setNullValueTrialIntentTypesCodes"
          :checked="form.trial_intent_types_null_value_code ? true : false"
        >
          <template #mainField="{ notApplicable }">
            <MultipleSelect
              v-model="form.trial_intent_types_codes"
              :data-cy="$t('StudyDefineForm.studyintent')"
              :label="$t('StudyDefineForm.studyintent')"
              :items="studiesGeneralStore.trialIntentTypes"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              return-object
              :disabled="notApplicable"
              density="compact"
              clearable
            />
          </template>
        </NotApplicableField>
        <v-row>
          <v-col cols="11">
            <v-autocomplete
              v-model="form.control_type_code"
              :data-cy="$t('StudyInterventionTypeForm.control_type')"
              :label="$t('StudyInterventionTypeForm.control_type')"
              :items="studiesGeneralStore.controlTypes"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              return-object
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="11">
            <v-autocomplete
              v-model="form.intervention_model_code"
              :data-cy="$t('StudyInterventionTypeForm.intervention_model')"
              :label="$t('StudyInterventionTypeForm.intervention_model')"
              :items="studiesGeneralStore.interventionModels"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              return-object
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="5">
            <YesNoField
              v-model="form.is_trial_randomised"
              :data-cy="$t('StudyInterventionTypeForm.randomised')"
              :label="$t('StudyInterventionTypeForm.randomised')"
            />
          </v-col>
          <v-col cols="5">
            <YesNoField
              v-model="form.add_on_to_existing_treatments"
              :data-cy="$t('StudyInterventionTypeForm.added_to_et')"
              :label="$t('StudyInterventionTypeForm.added_to_et')"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="11">
            <v-autocomplete
              v-model="form.trial_blinding_schema_code"
              :data-cy="$t('StudyInterventionTypeForm.blinding_schema')"
              :label="$t('StudyInterventionTypeForm.blinding_schema')"
              :items="studiesGeneralStore.trialBlindingSchemas"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              return-object
              clearable
            />
          </v-col>
        </v-row>
        <NotApplicableField
          :clean-function="setNullValueStratificationFactor"
          :checked="form.stratification_factor_null_value_code ? true : false"
        >
          <template #mainField="{ notApplicable }">
            <v-text-field
              v-model="form.stratification_factor"
              :data-cy="$t('StudyInterventionTypeForm.strfactor')"
              :label="$t('StudyInterventionTypeForm.strfactor')"
              :disabled="notApplicable"
              clearable
            />
          </template>
        </NotApplicableField>
        <v-row>
          <v-col cols="10">
            <label class="v-label">{{
              $t('StudyInterventionTypeForm.planned_st_length')
            }}</label>
            <DurationField
              v-model="form.planned_study_length"
              data-cy="planned-study-length"
              numeric-field-name="duration_value"
              unit-field-name="duration_unit_code"
              :max="1000"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script>
import DurationField from '@/components/tools/DurationField.vue'
import MultipleSelect from '@/components/tools/MultipleSelect.vue'
import NotApplicableField from '@/components/tools/NotApplicableField.vue'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import studyConstants from '@/constants/study'
import YesNoField from '@/components/tools/YesNoField.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudiesManageStore } from '@/stores/studies-manage'
import { useFormStore } from '@/stores/form'
import studyMetadataForms from '@/utils/studyMetadataForms'
import study from '@/api/study'
import _isEmpty from 'lodash/isEmpty'

export default {
  components: {
    DurationField,
    NotApplicableField,
    SimpleFormDialog,
    YesNoField,
    MultipleSelect,
  },
  inject: ['notificationHub'],
  props: {
    initialData: {
      type: Object,
      default: () => {},
    },
    open: Boolean,
  },
  emits: ['close', 'updated'],
  setup() {
    const formStore = useFormStore()
    const studiesGeneralStore = useStudiesGeneralStore()
    const studiesManageStore = useStudiesManageStore()
    return {
      formStore,
      studiesGeneralStore,
      studiesManageStore,
    }
  },
  data() {
    return {
      form: {},
      loading: false,
      helpItems: [
        'StudyInterventionTypeForm.intervention_type',
        'StudyInterventionTypeForm.study_intent_type',
        'StudyInterventionTypeForm.added_to_et',
        'StudyInterventionTypeForm.control_type',
        'StudyInterventionTypeForm.intervention_model',
        'StudyInterventionTypeForm.randomised',
        'StudyInterventionTypeForm.strfactor',
        'StudyInterventionTypeForm.blinding_schema',
        'StudyInterventionTypeForm.planned_st_length',
      ],
      data: this.metadata,
    }
  },
  mounted() {
    if (_isEmpty(this.initialData)) {
      this.loading = true
      study
        .getStudyInterventionMetadata(
          this.studiesGeneralStore.selectedStudy.uid
        )
        .then((resp) => {
          this.initForm(resp.data.current_metadata.study_intervention)
        })
        .finally(() => {
          this.loading = false
        })
    } else {
      this.initForm(this.initialData)
    }
  },
  methods: {
    initForm(data) {
      this.form = { ...data }
      if (!this.form.planned_study_length) {
        this.form.planned_study_length = {}
      }
      this.formStore.save(this.form)
    },
    setNullValueTrialIntentTypesCodes() {
      this.form.trial_intent_types_codes = []
      if (this.form.trial_intent_types_null_value_code) {
        this.form.trial_intent_types_null_value_code = null
      } else {
        const termUid = this.studiesGeneralStore.nullValues.find(
          (el) =>
            el.submission_value === studyConstants.TERM_NOT_APPLICABLE_SUBMVAL
        ).term_uid
        this.form.trial_intent_types_null_value_code = {
          term_uid: termUid,
          name: this.$t('_global.not_applicable_full_name'),
        }
      }
    },
    setNullValueStratificationFactor() {
      this.form.stratification_factor = ''
      if (this.form.stratification_factor_null_value_code) {
        this.form.stratification_factor_null_value_code = null
      } else {
        const termUid = this.studiesGeneralStore.nullValues.find(
          (el) =>
            el.submission_value === studyConstants.TERM_NOT_APPLICABLE_SUBMVAL
        ).term_uid
        this.form.stratification_factor_null_value_code = {
          term_uid: termUid,
          name: this.$t('_global.not_applicable_full_name'),
        }
      }
    },
    close() {
      this.$emit('close')
      this.notificationHub.clearErrors()
      this.formStore.reset()
      this.$refs.observer.resetValidation()
    },
    async cancel() {
      if (this.formStore.isEmpty || this.formStore.isEqual(this.form)) {
        this.close()
      } else {
        const options = {
          type: 'warning',
          cancelLabel: this.$t('_global.cancel'),
          agreeLabel: this.$t('_global.continue'),
        }
        if (
          await this.$refs.form.confirm(
            this.$t('_global.cancel_changes'),
            options
          )
        ) {
          this.close()
        }
      }
    },
    prepareRequestPayload() {
      const data = JSON.parse(JSON.stringify(this.form))
      const durationValue = data.planned_study_length.duration_value
      if (durationValue === undefined || durationValue === '') {
        data.planned_study_length = null
      }
      data.control_type_code = studyMetadataForms.getTermPayload(
        data,
        'control_type_code'
      )
      data.intervention_model_code = studyMetadataForms.getTermPayload(
        data,
        'intervention_model_code'
      )
      data.trial_blinding_schema_code = studyMetadataForms.getTermPayload(
        data,
        'trial_blinding_schema_code'
      )
      data.intervention_type_code = studyMetadataForms.getTermPayload(
        data,
        'intervention_type_code'
      )
      data.trial_intent_types_codes = studyMetadataForms.getTermsPayload(
        data,
        'trial_intent_types_codes'
      )
      return data
    },
    async submit() {
      this.notificationHub.clearErrors()

      const data = this.prepareRequestPayload()
      try {
        const parentUid = this.studiesGeneralStore.selectedStudy
          .study_parent_part
          ? this.studiesGeneralStore.selectedStudy.study_parent_part.uid
          : null

        await this.studiesManageStore.updateStudyIntervention(
          this.studiesGeneralStore.selectedStudy.uid,
          data,
          parentUid
        )
        this.$emit('updated', data)
        this.notificationHub.add({
          msg: this.$t('StudyInterventionTypeForm.update_success'),
        })
        this.close()
      } finally {
        this.$refs.form.working = false
      }
    },
  },
}
</script>
