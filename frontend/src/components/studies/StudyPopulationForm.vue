<template>
  <SimpleFormDialog
    ref="form"
    :title="$t('StudyPopulationForm.title')"
    :help-items="helpItems"
    :open="open"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row class="pr-4">
          <v-col cols="11">
            <MultipleSelect
              v-model="form.therapeutic_area_codes"
              :data-cy="$t('StudyPopulationForm.therapeuticarea')"
              :label="$t('StudyPopulationForm.therapeuticarea')"
              :items="studiesGeneralStore.snomedTerms"
              item-title="name"
              item-value="term_uid"
              return-object
            />
          </v-col>
        </v-row>
        <NotApplicableField
          :clean-function="setNullValueStudyDisease"
          :checked="
            form.disease_condition_or_indication_null_value_code ? true : false
          "
        >
          <template #mainField="{ notApplicable }">
            <MultipleSelect
              v-model="form.disease_condition_or_indication_codes"
              :data-cy="$t('StudyPopulationForm.disease_condition')"
              :label="$t('StudyPopulationForm.disease_condition')"
              :disabled="notApplicable"
              :items="studiesGeneralStore.snomedTerms"
              item-value="term_uid"
              item-title="name"
              return-object
            />
          </template>
        </NotApplicableField>
        <NotApplicableField
          :label="$t('StudyPopulationForm.stable_disease_min_duration')"
          :clean-function="setNullValueDiseaseDuration"
          :checked="
            form.stable_disease_minimum_duration_null_value_code ? true : false
          "
        >
          <template #mainField="{ notApplicable }">
            <DurationField
              v-model="form.stable_disease_minimum_duration"
              data-cy="stable-disease-min-duration"
              class="unit-select"
              :disabled="notApplicable"
              :max="undefined"
            />
          </template>
        </NotApplicableField>
        <v-row class="pr-4">
          <v-col cols="11">
            <MultipleSelect
              v-model="form.diagnosis_group_codes"
              :data-cy="$t('StudyPopulationForm.diagnosis_group')"
              :label="$t('StudyPopulationForm.diagnosis_group')"
              :items="studiesGeneralStore.snomedTerms"
              item-value="term_uid"
              item-title="name"
              return-object
            />
          </v-col>
        </v-row>
        <NotApplicableField
          :clean-function="setNullValueRelapseCriteria"
          :checked="form.relapse_criteria_null_value_code ? true : false"
        >
          <template #mainField="{ notApplicable }">
            <v-text-field
              v-model="form.relapse_criteria"
              :data-cy="$t('StudyPopulationForm.relapse_criteria')"
              :label="$t('StudyPopulationForm.relapse_criteria')"
              class="pt-0 my-0"
              :disabled="notApplicable"
            />
          </template>
        </NotApplicableField>
        <v-row>
          <v-col cols="4">
            <v-text-field
              v-model="form.number_of_expected_subjects"
              :data-cy="$t('StudyPopulationForm.number_of_expected_subjects')"
              :label="$t('StudyPopulationForm.number_of_expected_subjects')"
              :hint="$t('StudyPopulationForm.number_of_expected_subjects_hint')"
              class="pt-0 my-0"
              type="number"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="4">
            <YesNoField
              v-model="form.healthy_subject_indicator"
              :data-cy="$t('StudyPopulationForm.healthy_subjects')"
              :label="$t('StudyPopulationForm.healthy_subjects')"
            />
          </v-col>
          <v-col cols="5">
            <YesNoField
              v-model="form.rare_disease_indicator"
              :data-cy="$t('StudyPopulationForm.rare_disease_indicator')"
              :label="$t('StudyPopulationForm.rare_disease_indicator')"
            />
          </v-col>
        </v-row>
        <v-row class="pr-4">
          <v-col cols="11">
            <v-select
              v-model="form.sex_of_participants_code"
              :data-cy="$t('StudyPopulationForm.sex_of_study_participants')"
              :label="$t('StudyPopulationForm.sex_of_study_participants')"
              :items="studiesGeneralStore.sexOfParticipants"
              item-value="term_uid"
              item-title="sponsor_preferred_name"
              return-object
              clearable
              hide-details="auto"
            />
          </v-col>
        </v-row>
        <div class="mt-10">
          <label class="v-label">
            {{ $t('StudyPopulationForm.planned_min_max_age') }}
          </label>
        </div>
        <NotApplicableField
          :na-label="$t('StudyPopulationForm.pinf')"
          :clean-function="setPositiveInfinity"
          :checked="
            form.planned_maximum_age_of_subjects_null_value_code ? true : false
          "
        >
          <template #mainField="{ notApplicable }">
            <v-row>
              <v-col cols="6">
                <DurationField
                  v-model="form.planned_minimum_age_of_subjects"
                  data-cy="planned-minimum-age"
                  numeric-field-name="duration_value"
                  unit-field-name="duration_unit_code"
                  :hint="$t('StudyPopulationForm.planned_min_age')"
                />
              </v-col>
              <v-col cols="6">
                <DurationField
                  v-model="form.planned_maximum_age_of_subjects"
                  data-cy="planned-maximum-age"
                  numeric-field-name="duration_value"
                  unit-field-name="duration_unit_code"
                  :disabled="notApplicable"
                  :hint="$t('StudyPopulationForm.planned_max_age')"
                />
              </v-col>
            </v-row>
          </template>
        </NotApplicableField>
        <v-row>
          <v-col cols="4">
            <YesNoField
              v-model="form.pediatric_study_indicator"
              :data-cy="$t('StudyPopulationForm.pediatric_study_indicator')"
              :label="$t('StudyPopulationForm.pediatric_study_indicator')"
            />
          </v-col>
          <v-col cols="7">
            <YesNoField
              v-model="form.pediatric_investigation_plan_indicator"
              :data-cy="
                $t('StudyPopulationForm.pediatric_investigation_plan_indicator')
              "
              :label="
                $t('StudyPopulationForm.pediatric_investigation_plan_indicator')
              "
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="9">
            <YesNoField
              v-model="form.pediatric_postmarket_study_indicator"
              :data-cy="
                $t('StudyPopulationForm.pediatric_postmarket_study_indicator')
              "
              :label="
                $t('StudyPopulationForm.pediatric_postmarket_study_indicator')
              "
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script>
import _isEqual from 'lodash/isEqual'
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

export default {
  components: {
    DurationField,
    MultipleSelect,
    NotApplicableField,
    SimpleFormDialog,
    YesNoField,
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
    const studiesGeneralStore = useStudiesGeneralStore()
    const studiesManageStore = useStudiesManageStore()
    return {
      studiesGeneralStore,
      studiesManageStore,
    }
  },
  data() {
    return {
      form: {
        planned_minimum_age_of_subjects: {},
        planned_maximum_age_of_subjects: {},
        stable_disease_minimum_duration: {},
      },
      helpItems: [
        'StudyPopulationForm.therapeuticarea',
        'StudyPopulationForm.disease_condition',
        'StudyPopulationForm.diagnosis_group',
        'StudyPopulationForm.rare_disease_indicator',
        'StudyPopulationForm.healthy_subjects',
        'StudyPopulationForm.planned_min_max_age',
        'StudyPopulationForm.pediatric_study_indicator',
        'StudyPopulationForm.pediatric_postmarket_study_indicator',
        'StudyPopulationForm.stable_disease_min_duration',
        'StudyPopulationForm.relapse_criteria',
        'StudyPopulationForm.number_of_expected_subjects',
        'StudyPopulationForm.sex_of_study_participants',
      ],
      minimumDurationCheckbox: false,
      data: {},
    }
  },
  watch: {
    minimumDurationCheckbox: function () {
      this.form.stable_disease_minimum_duration = {}
    },
  },
  mounted() {
    this.studiesGeneralStore.fetchNullValues()
    if (_isEmpty(this.initialData)) {
      study
        .getStudyPopulationMetadata(this.studiesGeneralStore.selectedStudy.uid)
        .then((resp) => {
          this.initForm(resp.data.current_metadata.study_population)
        })
    } else {
      this.initForm(this.initialData)
    }
  },
  methods: {
    initForm(data) {
      this.form = { ...data }
      if (!this.form.planned_minimum_age_of_subjects) {
        this.form.planned_minimum_age_of_subjects = {}
      }
      if (!this.form.planned_maximum_age_of_subjects) {
        this.form.planned_maximum_age_of_subjects = {}
      }
      if (!this.form.stable_disease_minimum_duration) {
        this.form.stable_disease_minimum_duration = {}
      }
    },
    setNullValueStudyDisease() {
      this.form.disease_condition_or_indication_codes = []
      if (this.form.disease_condition_or_indication_null_value_code) {
        this.form.disease_condition_or_indication_null_value_code = null
      } else {
        const termUid = this.studiesGeneralStore.nullValues.find(
          (el) =>
            el.submission_value === studyConstants.TERM_NOT_APPLICABLE_SUBMVAL
        ).term_uid
        this.form.disease_condition_or_indication_null_value_code = {
          term_uid: termUid,
          name: this.$t('_global.not_applicable_full_name'),
        }
      }
    },
    setNullValueDiseaseDuration() {
      this.form.stable_disease_minimum_duration = {}
      if (this.form.stable_disease_minimum_duration_null_value_code) {
        this.form.stable_disease_minimum_duration_null_value_code = null
      } else {
        const termUid = this.studiesGeneralStore.nullValues.find(
          (el) =>
            el.submission_value === studyConstants.TERM_NOT_APPLICABLE_SUBMVAL
        ).term_uid
        this.form.stable_disease_minimum_duration_null_value_code = {
          term_uid: termUid,
          name: this.$t('_global.not_applicable_full_name'),
        }
      }
    },
    setNullValueRelapseCriteria() {
      this.form.relapse_criteria = ''
      if (this.form.relapse_criteria_null_value_code) {
        this.form.relapse_criteria_null_value_code = null
      } else {
        const termUid = this.studiesGeneralStore.nullValues.find(
          (el) =>
            el.submission_value === studyConstants.TERM_NOT_APPLICABLE_SUBMVAL
        ).term_uid
        this.form.relapse_criteria_null_value_code = {
          term_uid: termUid,
          name: this.$t('_global.not_applicable_full_name'),
        }
      }
    },
    setNullValueNumberOfExpectedSubjects() {
      this.form.number_of_expected_subjects = ''
      if (this.form.number_of_expected_subjects_null_value_code) {
        this.form.number_of_expected_subjects_null_value_code = null
      } else {
        const termUid = this.studiesGeneralStore.nullValues.find(
          (el) =>
            el.submission_value === studyConstants.TERM_NOT_APPLICABLE_SUBMVAL
        ).term_uid
        this.form.number_of_expected_subjects_null_value_code = {
          term_uid: termUid,
          name: this.$t('_global.not_applicable_full_name'),
        }
      }
    },
    setPositiveInfinity() {
      this.form.planned_maximum_age_of_subjects = {}
      if (this.form.planned_maximum_age_of_subjects_null_value_code) {
        this.form.planned_maximum_age_of_subjects_null_value_code = null
      } else {
        const termUid = this.studiesGeneralStore.nullValues.find(
          (el) =>
            el.submission_value === studyConstants.TERM_POSITIVE_INF_SUBMVAL
        ).term_uid
        this.form.planned_maximum_age_of_subjects_null_value_code = {
          term_uid: termUid,
          name: this.$t('_global.positive_infinity_full_name'),
        }
      }
    },
    close() {
      this.$emit('close')
      this.notificationHub.clearErrors()
      this.$refs.observer.resetValidation()
    },
    async cancel() {
      if (_isEqual(this.metadata, this.prepareRequestPayload())) {
        this.close()
        return
      }
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
        this.data = {}
        this.data = this.metadata
        this.close()
      }
    },
    prepareRequestPayload() {
      const data = JSON.parse(JSON.stringify(this.form))
      if (
        Object.keys(data.planned_minimum_age_of_subjects).length === 0 ||
        !data.planned_minimum_age_of_subjects.duration_value
      ) {
        data.planned_minimum_age_of_subjects = null
      }
      if (
        Object.keys(data.planned_maximum_age_of_subjects).length === 0 ||
        !data.planned_maximum_age_of_subjects.duration_value
      ) {
        data.planned_maximum_age_of_subjects = null
      }
      if (
        Object.keys(data.stable_disease_minimum_duration).length === 0 ||
        !data.stable_disease_minimum_duration.duration_value
      ) {
        data.stable_disease_minimum_duration = null
      }
      if (!data.number_of_expected_subjects) {
        data.number_of_expected_subjects = null
      }
      data.sex_of_participants_code = studyMetadataForms.getTermPayload(
        data,
        'sex_of_participants_code'
      )
      data.therapeutic_area_codes = studyMetadataForms.getTermsPayload(
        data,
        'therapeutic_area_codes'
      )
      data.disease_condition_or_indication_codes =
        studyMetadataForms.getTermsPayload(
          data,
          'disease_condition_or_indication_codes'
        )
      data.diagnosis_group_codes = studyMetadataForms.getTermsPayload(
        data,
        'diagnosis_group_codes'
      )
      return data
    },
    async submit() {
      this.notificationHub.clearErrors()

      const data = this.prepareRequestPayload()
      try {
        await this.studiesManageStore.editStudyPopulation(
          this.studiesGeneralStore.selectedStudy.uid,
          data,
          this.studiesGeneralStore.selectedStudy.study_parent_part
            ? this.studiesGeneralStore.selectedStudy.study_parent_part.uid
            : null
        )
        this.$emit('updated', data)
        this.notificationHub.add({
          msg: this.$t('StudyPopulationForm.update_success'),
        })
        this.close()
      } finally {
        this.$refs.form.working = false
      }
    },
  },
}
</script>
