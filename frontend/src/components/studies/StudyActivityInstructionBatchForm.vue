<template>
  <HorizontalStepperForm
    ref="stepper"
    :title="$t('StudyActivityInstructionBatchForm.add_title')"
    :steps="steps"
    :form-observer-getter="getObserver"
    :help-text="$t('_help.StudyActivityInstructionBatchForm.general')"
    :extra-step-validation="extraStepValidation"
    @close="close"
    @save="submit"
    @step-loaded="onStepLoaded"
  >
    <template #[`step.creationMode`]>
      <v-radio-group v-model="creationMode" data-cy="objective-method-radio">
        <v-radio
          :label="$t('StudyActivityInstructionBatchForm.select_mode')"
          value="select"
        />
        <v-radio
          :label="$t('StudyActivityInstructionBatchForm.template_mode')"
          value="template"
        />
        <v-radio
          :label="$t('StudyActivityInstructionBatchForm.scratch_mode')"
          value="scratch"
        />
      </v-radio-group>
    </template>
    <template #[`step.creationMode.after`]>
      <StudyActivitySelectionTable
        :selection="studyActivities"
        :title="$t('StudyActivityInstructionBatchForm.batch_table_title')"
      />
    </template>
    <template #[`step.selectStudies`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-select
          v-model="selectedStudies"
          :data-cy="$t('StudySelectionTable.select_studies')"
          :label="$t('StudySelectionTable.select_studies')"
          :items="studies"
          :rules="[formRules.required]"
          item-title="current_metadata.identification_metadata.study_id"
          clearable
          multiple
          class="pt-10"
          return-object
        />
      </v-form>
    </template>
    <template #[`step.selectFromStudies`]>
      <p class="text-grey text-body-large font-weight-bold">
        {{ $t('StudyActivityInstructionBatchForm.selected_items') }}
      </p>
      <v-data-table
        data-cy="selected-instructions-table"
        :headers="selectedInstructionsHeaders"
        :items="selectedInstructions"
      >
        <template #[`item.activity_instruction_name`]="{ item }">
          <NNParameterHighlighter
            :name="item.activity_instruction_name"
            :show-prefix-and-postfix="false"
          />
        </template>
        <template #[`item.actions`]="{ item }">
          <v-btn
            icon="mdi-delete-outline"
            color="red"
            variant="text"
            @click="unselectStudyActivityInstruction(item)"
          />
        </template>
      </v-data-table>
    </template>
    <template #[`step.selectFromStudies.after`]>
      <p class="text-grey text-body-large font-weight-bold mb-0 ml-3">
        {{ $t('StudyObjectiveForm.copy_instructions') }}
      </p>
      <v-col cols="12" class="pt-0 mt-0">
        <StudySelectionTable
          :headers="activityInstructionHeaders"
          data-fetcher-name="getAllStudyActivityInstructions"
          :extra-data-fetcher-filters="extraStudyActivityInstructionFilters"
          :studies="selectedStudies"
          :show-filter-bar-by-default="false"
          @item-selected="selectStudyActivityInstruction"
        >
          <template #[`item.activity_instruction_name`]="{ item }">
            <NNParameterHighlighter
              :name="item.activity_instruction_name"
              :show-prefix-and-postfix="false"
            />
          </template>
          <template #[`item.actions`]="{ item }">
            <v-btn
              :data-cy="$t('StudySelectionTable.copy_item')"
              icon="mdi-content-copy"
              :color="getCopyButtonColor(item)"
              :disabled="isStudyActivityInstructionSelected(item)"
              :title="$t('StudySelectionTable.copy_item')"
              variant="text"
              @click="selectStudyActivityInstruction(item)"
            />
          </template>
        </StudySelectionTable>
      </v-col>
    </template>

    <template #[`step.selectTemplate`]>
      <p class="text-grey text-body-large font-weight-bold">
        {{ $t('StudyActivityInstructionBatchForm.select_template_title') }}
      </p>
      <v-card flat class="parameterBackground">
        <v-card-text>
          <NNParameterHighlighter
            :name="selectedTemplateName"
            default-color="orange"
          />
        </v-card-text>
      </v-card>
    </template>
    <template #[`step.selectTemplate.after`]>
      <div class="d-flex align-center">
        <p class="text-grey text-body-large font-weight-bold mb-0 ml-3">
          {{ $t('StudyObjectiveForm.copy_instructions') }}
        </p>
        <v-switch
          v-model="preInstanceMode"
          :label="$t('StudyObjectiveForm.show_pre_instances')"
          hide-details
          class="ml-4"
        />
      </div>
      <v-col cols="12" class="pt-0">
        <NNTable
          ref="templateTable"
          key="templatesTable"
          table-id="study-activity-instruction-batch-templates"
          :headers="tplHeaders"
          :items="templates"
          hide-default-switches
          hide-actions-menu
          :items-per-page="15"
          elevation="0"
          :items-length="templatesTotal"
          show-filter-bar-by-default
          :column-data-resource="
            preInstanceMode
              ? 'activity-instruction-pre-instances'
              : 'activity-instruction-templates'
          "
          :initial-column-data="prefilteredTplHeaders"
          @filter="getTemplates"
        >
          <template #[`item.indications.name`]="{ item }">
            <template v-if="item.indications && item.indications.length">
              {{ $filters.names(item.indications) }}
            </template>
            <template v-else>
              {{ $t('_global.not_applicable_long') }}
            </template>
          </template>
          <template #[`item.activity_groups.name`]="{ item }">
            <template v-if="item.activity_groups.length">
              {{ item.activity_groups[0].name }}
            </template>
          </template>
          <template #[`item.activity_subgroups.name`]="{ item }">
            <template v-if="item.activity_subgroups.length">
              {{ item.activity_subgroups[0].name }}
            </template>
          </template>
          <template #[`item.activities.name`]="{ item }">
            <template v-if="item.activities && item.activities.length">
              {{ item.activities[0].name }}
            </template>
            <template v-else>
              {{ $t('_global.not_applicable_long') }}
            </template>
          </template>
          <template #[`item.name`]="{ item }">
            <NNParameterHighlighter :name="item.name" default-color="orange" />
          </template>
          <template #[`item.actions`]="{ item }">
            <v-btn
              :data-cy="$t('StudyActivityInstructionBatchForm.copy_template')"
              icon="mdi-content-copy"
              color="primary"
              :title="$t('StudyActivityInstructionBatchForm.copy_template')"
              variant="text"
              @click="selectTemplate(item)"
            />
          </template>
        </NNTable>
      </v-col>
    </template>
    <template #[`step.createTemplate`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <NNTemplateInputField
          v-model="templateForm.name"
          :data-cy="$t('StudyActivityInstructionBatchForm.name')"
          :label="$t('StudyActivityInstructionBatchForm.name')"
          :items="parameterTypes"
          :rules="[formRules.required]"
          show-drop-down-early
        />
        <div class="dialog-sub-title">
          {{ $t('_global.indexing') }}
        </div>
        <ActivityTemplateIndexingForm ref="indexingForm" :form="templateForm" />
      </v-form>
    </template>
    <template #[`step.createInstructionText`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-progress-circular
          v-if="loadingParameters"
          indeterminate
          color="secondary"
        />
        <template v-if="form.activity_instruction_template !== undefined">
          <ParameterValueSelector
            ref="paramSelector"
            :model-value="parameters"
            :template="form.activity_instruction_template.name"
            color="white"
          />
        </template>
      </v-form>
    </template>
  </HorizontalStepperForm>
</template>

<script>
import { computed } from 'vue'
import activityInstructionTemplates from '@/api/activityInstructionTemplates'
import ActivityTemplateIndexingForm from '@/components/library/ActivityTemplateIndexingForm.vue'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import instances from '@/utils/instances'
import libraryConstants from '@/constants/libraries'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter.vue'
import NNTable from '@/components/tools/NNTable.vue'
import NNTemplateInputField from '@/components/tools/NNTemplateInputField.vue'
import ParameterValueSelector from '@/components/tools/ParameterValueSelector.vue'
import filteringParameters from '@/utils/filteringParameters'
import statuses from '@/constants/statuses'
import study from '@/api/study'
import StudyActivitySelectionTable from './StudyActivitySelectionTable.vue'
import StudySelectionTable from './StudySelectionTable.vue'
import templateParameterTypes from '@/api/templateParameterTypes'
import templatePreInstances from '@/api/templatePreInstances'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    ActivityTemplateIndexingForm,
    HorizontalStepperForm,
    NNParameterHighlighter,
    NNTable,
    NNTemplateInputField,
    ParameterValueSelector,
    StudyActivitySelectionTable,
    StudySelectionTable,
  },
  inject: ['notificationHub', 'formRules'],
  props: {
    studyActivities: {
      type: Array,
      default: () => [],
    },
    currentStudyActivityInstructions: {
      type: Array,
      default: () => [],
    },
  },
  emits: ['added', 'close'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
    }
  },
  data() {
    return {
      activityInstructionHeaders: [
        { title: this.$t('Study.study_id'), key: 'study_uid' },
        {
          title: this.$t('StudyActivityInstructionBatchForm.instruction_text'),
          key: 'activity_instruction_name',
        },
        { title: this.$t('_global.actions'), key: 'actions', width: '5%' },
      ],
      creationMode: 'select',
      extraStudyActivityInstructionFilters: {},
      form: {},
      loadingParameters: false,
      noTemplateAvailableAtAll: false,
      parameters: [],
      parameterTypes: [],
      preInstanceMode: true,
      selectedInstructions: [],
      selectedInstructionsHeaders: [
        { title: this.$t('Study.study_id'), key: 'study_uid' },
        {
          title: this.$t('StudyActivityInstructionBatchForm.instruction_text'),
          key: 'activity_instruction_name',
        },
        { title: this.$t('_global.actions'), key: 'actions', width: '5%' },
      ],
      selectedStudies: [],
      selectFromStudiesSteps: [
        {
          name: 'creationMode',
          title: this.$t(
            'StudyActivityInstructionBatchForm.creation_mode_title'
          ),
        },
        {
          name: 'selectStudies',
          title: this.$t('StudyActivityInstructionBatchForm.select_studies'),
        },
        {
          name: 'selectFromStudies',
          title: this.$t(
            'StudyActivityInstructionBatchForm.select_from_studies_title'
          ),
        },
      ],
      createFromTemplateSteps: [
        {
          name: 'creationMode',
          title: this.$t(
            'StudyActivityInstructionBatchForm.creation_mode_title'
          ),
        },
        {
          name: 'selectTemplate',
          title: this.$t('StudyActivityInstructionBatchForm.select_tpl_title'),
        },
        {
          name: 'createInstructionText',
          title: this.$t('StudyActivityInstructionBatchForm.create_text_title'),
        },
      ],
      scratchModeSteps: [
        {
          name: 'creationMode',
          title: this.$t(
            'StudyActivityInstructionBatchForm.creation_mode_title'
          ),
        },
        {
          name: 'createTemplate',
          title: this.$t(
            'StudyActivityInstructionBatchForm.create_template_title'
          ),
        },
        {
          name: 'createInstructionText',
          title: this.$t('StudyActivityInstructionBatchForm.create_text_title'),
        },
      ],
      steps: [],
      studies: [],
      templateForm: {},
      templatesFetched: false,
      templates: [],
      templatesTotal: 0,
      templatesFilters: {},
      templatesOptions: {},
      tplHeaders: [
        { title: '', key: 'actions', width: '1%' },
        { title: this.$t('_global.sequence_number'), key: 'sequence_id' },
        { title: this.$t('_global.indications'), key: 'indications.name' },
        {
          title: this.$t('StudyActivity.activity_group'),
          key: 'activity_groups.name',
        },
        {
          title: this.$t('StudyActivity.activity_sub_group'),
          key: 'activity_subgroups.name',
        },
        { title: this.$t('StudyActivity.activity'), key: 'activities.name' },
        {
          title: this.$t('_global.template'),
          key: 'name',
          filteringName: 'name',
          width: '30%',
        },
      ],
    }
  },
  computed: {
    selectedTemplateName() {
      return this.form.activity_instruction_template
        ? this.form.activity_instruction_template.name
        : ''
    },
    selectedActivityGroups() {
      const result = []
      if (!this.noTemplateAvailableAtAll) {
        for (const studyActivity of this.studyActivities) {
          result.push({
            uid: studyActivity.activity.activity_groupings.activity_group_uid,
            name: studyActivity.activity.activity_groupings.activity_group_name,
          })
        }
      }
      return result
    },
    selectedActivitySubGroups() {
      const result = []
      if (!this.noTemplateAvailableAtAll) {
        for (const studyActivity of this.studyActivities) {
          result.push({
            uid: studyActivity.activity.activity_groupings
              .activity_subgroup_uid,
            name: studyActivity.activity.activity_groupings
              .activity_subgroup_name,
          })
        }
      }
      return result
    },
    prefilteredTplHeaders() {
      return {
        'activity_groups.name': this.selectedActivityGroups.map(
          (item) => item.name
        ),
        'activity_subgroups.name': this.selectedActivitySubGroups.map(
          (item) => item.name
        ),
      }
    },
  },
  watch: {
    creationMode(value) {
      if (value === 'template') {
        this.steps = this.createFromTemplateSteps
      } else if (value === 'select') {
        this.steps = this.selectFromStudiesSteps
      } else {
        this.steps = this.scratchModeSteps
      }
    },
    preInstanceMode(value) {
      this.apiEndpoint = value
        ? this.preInstanceApi
        : activityInstructionTemplates
      this.getTemplates()
    },
  },
  created() {
    this.steps = this.selectFromStudiesSteps
    this.preInstanceApi = templatePreInstances('activity-instruction')
    this.apiEndpoint = this.preInstanceApi
  },
  mounted() {
    this.getTemplates()
    study
      .get({ has_study_activity_instruction: true, page_size: 0 })
      .then((resp) => {
        this.studies = resp.data.items.filter(
          (study) => study.uid !== this.selectedStudy.uid
        )
      })
    templateParameterTypes.getTypes().then((resp) => {
      this.parameterTypes = resp.data
    })
  },
  methods: {
    close() {
      this.notificationHub.clearErrors()
      this.creationMode = 'select'
      this.$refs.stepper.reset()
      this.$emit('close')
      this.templateForm = {}
      this.form = {}
      this.apiEndpoint = this.preInstanceApi
      this.preInstanceApi = true
      this.parameters = []
    },
    getObserver(step) {
      return this.$refs[`observer_${step}`]
    },
    async loadParameters(template) {
      if (template) {
        this.loadingParameters = true
        const templateUid = this.preInstanceMode
          ? template.template_uid
          : template.uid
        const resp =
          await activityInstructionTemplates.getObjectTemplateParameters(
            templateUid
          )
        this.parameters = resp.data
        /* Filter received parameters based on current study activity selection */
        for (const parameterValues of this.parameters) {
          if (parameterValues.name === 'ActivityGroup') {
            const activityGroupUids = this.selectedActivityGroups.map(
              (item) => item.uid
            )
            parameterValues.values = parameterValues.values.filter(
              (item) => activityGroupUids.indexOf(item.uid) !== -1
            )
          } else if (parameterValues.name === 'ActivitySubGroup') {
            const activitySubGroupUids = this.selectedActivitySubGroups.map(
              (item) => item.uid
            )
            parameterValues.values = parameterValues.values.filter(
              (item) => activitySubGroupUids.indexOf(item.uid) !== -1
            )
          }
        }
        this.loadingParameters = false
      } else {
        this.parameters = []
      }
    },
    getTemplates(filters, options, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      params.status = statuses.FINAL
      const newFilters = filters ? JSON.parse(filters) : {}
      if (this.selectedActivityGroups.length) {
        newFilters['activity_groups.uid'] = {
          v: this.selectedActivityGroups.map((item) => item.uid),
        }
      }
      if (this.selectedActivitySubGroups.length) {
        newFilters['activity_subgroups.uid'] = {
          v: this.selectedActivitySubGroups.map((item) => item.uid),
        }
      }
      params.filters = newFilters
      if (params.filters !== '{}') {
        params.operator = 'or'
      }
      return this.apiEndpoint.get(params).then((resp) => {
        // Apply filtering on library here because we cannot mix operators in API queries...
        this.templates = resp.data.items.filter(
          (item) => item.library.name === libraryConstants.LIBRARY_SPONSOR
        )
        this.templatesTotal = resp.data.total
        if (!this.templatesFetched) {
          // It was the first time we fetched templates, ifO there is
          // no result we empty pre-defined filters to avoid confusion
          if (this.templates.length === 0) {
            this.noTemplateAvailableAtAll = true
          }
          this.templatesFetched = true
        }
      })
    },
    async selectTemplate(template) {
      await this.loadParameters(template)
      if (this.preInstanceMode) {
        instances.loadParameterValues(template.parameter_terms, this.parameters)
      }
      this.form.activity_instruction_template = {}
      this.form.activity_instruction_template = template
    },
    selectStudyActivityInstruction(studyActivityInstruction) {
      this.selectedInstructions.push(studyActivityInstruction)
    },
    unselectStudyActivityInstruction(studyActivityInstruction) {
      this.selectedInstructions = this.selectedInstructions.filter(
        (item) =>
          item.activy_instruction_name !==
          studyActivityInstruction.activy_instruction_name
      )
    },
    isStudyActivityInstructionSelected(studyActivityInstruction) {
      let selected = this.selectedInstructions.find(
        (item) =>
          item.activity_instruction_uid ===
          studyActivityInstruction.activity_instruction_uid
      )
      if (!selected && this.currentStudyActivityInstructions.length) {
        selected = this.currentStudyActivityInstructions.find(
          (item) =>
            item.activy_instruction_uid ===
            studyActivityInstruction.activy_instruction_uid
        )
      }
      return selected !== undefined
    },
    getCopyButtonColor(item) {
      return !this.isStudyActivityInstructionSelected(item) ? 'primary' : ''
    },
    async extraStepValidation(step) {
      if (this.creationMode !== 'scratch' || step !== 2) {
        return true
      }
      if (
        this.form.activity_instruction_template &&
        this.form.activity_instruction_template.name === this.templateForm.name
      ) {
        return true
      }
      const data = {
        ...this.templateForm,
        study_uid: this.selectedStudy.uid,
        ...this.$refs.indexingForm.preparePayload(),
      }
      data.library_name = libraryConstants.LIBRARY_USER_DEFINED
      if (data.indications) {
        data.indication_uids = data.indications.map(
          (indication) => indication.term_uid
        )
        delete data.indications
      }
      if (data.activity_group) {
        data.activity_group_uids = [data.activity_group]
        delete data.activity_group
      }
      if (data.activity_subgroups) {
        data.activity_subgroup_uids = data.activity_subgroups
        delete data.activity_subgroups
      }
      if (data.activities) {
        data.activity_uids = data.activities.map((activity) => activity.uid)
        delete data.activities
      }
      try {
        const resp = await activityInstructionTemplates.create(data)
        if (resp.data.status === statuses.DRAFT)
          await activityInstructionTemplates.approve(resp.data.uid)
        this.form.activity_instruction_template = resp.data
      } catch (_error) {
        return false
      }
      this.loadParameters(this.form.activity_instruction_template)
      return true
    },
    async submit() {
      this.notificationHub.clearErrors()

      const operations = []
      if (this.creationMode === 'template' || this.creationMode === 'scratch') {
        for (const studyActivity of this.studyActivities) {
          const templateUid =
            this.creationMode !== 'scratch' && this.preInstanceMode
              ? this.form.activity_instruction_template.template_uid
              : this.form.activity_instruction_template.uid
          operations.push({
            method: 'POST',
            content: {
              activity_instruction_data: {
                activity_instruction_template_uid: templateUid,
                parameter_terms: await instances.formatParameterValues(
                  this.parameters
                ),
                library_name:
                  this.form.activity_instruction_template.library.name,
              },
              study_activity_uid: studyActivity.study_activity_uid,
            },
          })
        }
      } else if (this.creationMode === 'select') {
        for (const studyActivity of this.studyActivities) {
          for (const studyActivityInstruction of this.selectedInstructions) {
            operations.push({
              method: 'POST',
              content: {
                activity_instruction_uid:
                  studyActivityInstruction.activity_instruction_uid,
                study_activity_uid: studyActivity.study_activity_uid,
              },
            })
          }
        }
      }
      if (operations.length === 0) {
        return
      }
      await study.studyActivityInstructionBatchOperations(
        this.selectedStudy.uid,
        operations
      )
      this.$emit('added')
      this.notificationHub.add({
        msg: this.$t('StudyActivityInstructionBatchForm.add_success'),
      })
      this.close()
    },
    onStepLoaded(step) {
      if (this.creationMode === 'template' && step === 2) {
        this.$refs.templateTable.loading = false
      }
    },
  },
}
</script>
