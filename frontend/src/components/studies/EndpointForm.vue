<template>
  <HorizontalStepperForm
    ref="stepper"
    :title="title"
    :steps="steps"
    :form-observer-getter="getObserver"
    :extra-step-validation="extraStepValidation"
    :help-items="helpItems"
    :edit-data="form"
    @close="close"
    @save="submit"
  >
    <template #[`step.creationMode`]="{ step }">
      <v-radio-group v-model="creationMode">
        <v-radio
          :label="$t('StudyEndpointForm.template_mode')"
          value="template"
        />
        <v-radio :label="$t('StudyEndpointForm.select_mode')" value="studies" />
        <v-radio
          :label="$t('StudyEndpointForm.scratch_mode')"
          value="scratch"
        />
      </v-radio-group>
      <v-form :ref="`observer_${step}`">
        <v-row v-if="creationMode === 'studies'">
          <v-col>
            <StudySelectorField
              v-model="formSelectedStudy"
              :data="studies"
              :loading="studiesLoading"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #[`step.selectEndpoint`]>
      <p class="text-grey text-body-large font-weight-bold">
        {{ $t('StudyEndpointForm.selected_endpoints') }}
      </p>
      <v-data-table
        data-cy="selected-endpoints-table"
        :headers="selectedEndpointHeaders"
        :items="selectedStudyEndpoints"
      >
        <template #[`item.endpoint.name`]="{ item }">
          <NNParameterHighlighter :name="item.endpoint.name" />
        </template>
        <template #[`item.actions`]="{ item }">
          <v-btn
            icon="mdi-delete-outline"
            size="small"
            color="red"
            variant="text"
            @click="unselectStudyEndpoint(item)"
          />
        </template>
      </v-data-table>
    </template>
    <template #[`step.selectEndpoint.after`]>
      <p class="text-grey text-body-large font-weight-bold mb-0 ml-3">
        {{ $t('StudyObjectiveForm.copy_instructions') }}
      </p>
      <v-col cols="12" class="pt-0 mt-0">
        <StudySelectionTable
          :headers="endpointHeaders"
          data-fetcher-name="getAllStudyEndpoints"
          :extra-data-fetcher-filters="extraStudyEndpointFilters"
          :selected-study="formSelectedStudy"
          column-data-resource="study-endpoints"
          @item-selected="selectStudyEndpoint"
        >
          <template #[`item.endpoint.name`]="{ item }">
            <NNParameterHighlighter :name="item.endpoint.name" />
          </template>
          <template #[`item.actions`]="{ item }">
            <v-btn
              :data-cy="$t('StudySelectionTable.copy_item')"
              icon="mdi-content-copy"
              size="small"
              :color="getCopyButtonColor(item)"
              :disabled="isStudyEndpointSelected(item)"
              :title="$t('StudySelectionTable.copy_item')"
              variant="text"
              @click="selectStudyEndpoint(item)"
            />
          </template>
        </StudySelectionTable>
      </v-col>
    </template>
    <template #[`step.objective`]>
      <v-card flat>
        <v-card-text>
          <v-row>
            <v-col cols="10" class="bg-parameterBackground">
              <NNParameterHighlighter
                :name="selectedStudyObjectiveName"
                default-color="orange"
              />
            </v-col>
            <v-col cols="2">
              <v-checkbox
                v-model="selectLater"
                :label="$t('StudyEndpointForm.select_later')"
                hide-details
                @change="onSelectLaterChange"
              />
            </v-col>
          </v-row>
          <v-row v-if="objectives.length === 0">
            <v-col cols="2"></v-col>
            <v-col cols="6">
              <v-card
                color="white"
                class="text-red"
                :text="$t('StudyEndpointForm.no_objective_available')"
              />
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
    </template>
    <template #[`step.objective.after`]>
      <p class="text-grey text-body-large font-weight-bold mb-0 ml-3 mt-2">
        {{ $t('StudyObjectiveForm.copy_instructions') }}
      </p>
      <v-col cols="12" class="pt-0">
        <NNTable
          key="objectivesTable"
          table-id="endpoint-form-objectives"
          :headers="objectiveHeaders"
          :items="objectives"
          :items-length="objectiveTotal"
          hide-default-switches
          hide-actions-menu
          :items-per-page="15"
          elevation="0"
          :loading="objectivesLoading"
        >
          <template #[`item.objective.name`]="{ item }">
            <NNParameterHighlighter :name="item.objective.name" />
          </template>
          <template #[`item.actions`]="{ item }">
            <v-btn
              :data-cy="$t('StudyEndpointForm.copy_objective')"
              icon="mdi-content-copy"
              size="small"
              color="primary"
              :title="$t('StudyEndpointForm.copy_objective')"
              variant="text"
              @click="selectStudyObjective(item)"
            />
          </template>
        </NNTable>
      </v-col>
    </template>

    <template #[`step.selectEndpointTemplate`]>
      <v-data-table
        :headers="templateSelectionHeaders"
        :items="selectedTemplates"
      >
        <template #[`item.name`]="{ item }">
          <NNParameterHighlighter :name="item.name" default-color="orange" />
        </template>
        <template #[`item.actions`]="{ item }">
          <v-btn
            icon="mdi-delete-outline"
            size="small"
            color="red"
            variant="text"
            @click="unselectEndpointTemplate(item)"
          />
        </template>
      </v-data-table>
    </template>

    <template #[`step.selectEndpointTemplate.after`]>
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
          key="templateTable"
          table-id="endpoint-form-templates"
          :headers="tplHeaders"
          :items="endpointTemplates"
          hide-default-switches
          hide-actions-menu
          :items-length="total"
          :column-data-resource="
            preInstanceMode ? 'endpoint-pre-instances' : 'endpoint-templates'
          "
          :default-filters="defaultTplFilters"
          @filter="getEndpointTemplates"
        >
          <template #[`item.categories`]="{ item }">
            <template v-if="item.categories">
              {{ $filters.terms(item.categories) }}
            </template>
            <template v-else>
              {{ $t('_global.not_applicable_long') }}
            </template>
          </template>
          <template #[`item.sub_categories`]="{ item }">
            <template v-if="item.sub_categories">
              {{ $filters.terms(item.sub_categories) }}
            </template>
            <template v-else>
              {{ $t('_global.not_applicable_long') }}
            </template>
          </template>
          <template #[`item.indications`]="{ item }">
            <template v-if="item.indications">
              {{ $filters.names(item.indications) }}
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
              icon="mdi-content-copy"
              size="small"
              color="primary"
              :title="$t('StudyObjectiveForm.copy_template')"
              variant="text"
              @click="selectEndpointTemplate(item)"
            />
          </template>
        </NNTable>
      </v-col>
    </template>

    <template #[`step.endpointDetails`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-progress-circular
          v-if="loadingEndpointParameters"
          indeterminate
          color="secondary"
        />
        <v-row>
          <v-col cols="5">
            <ParameterValueSelector
              v-if="form.endpoint_template !== undefined"
              ref="endpointParamSelector"
              :model-value="endpointTemplateParameters"
              :template="form.endpoint_template.name"
              color="white"
              :preview-text="$t('StudyEndpointForm.endpoint_title')"
              stacked
            />
          </v-col>
          <v-col cols="2" class="px-0">
            <p class="text-grey text-body-large font-weight-bold my-2">
              {{ $t('StudyEndpointForm.selected_endpoint_units') }}
            </p>
            <v-card flat class="bg-parameterBackground">
              <v-card-text>
                <NNParameterHighlighter
                  :name="unitsDisplay(form.endpoint_units.units)"
                />
              </v-card-text>
            </v-card>
            <v-row class="mt-5">
              <v-col cols="8">
                <MultipleSelect
                  v-model="form.endpoint_units.units"
                  :label="$t('StudyEndpointForm.units')"
                  :items="units"
                  :rules="[
                    (value) => formRules.requiredIfNotNA(value, skipUnits),
                  ]"
                  item-title="name"
                  return-object
                  :disabled="skipUnits"
                />
              </v-col>
              <v-col cols="2">
                <v-btn
                  :icon="!skipUnits ? 'mdi-eye-outline' : 'mdi-eye-off-outline'"
                  size="small"
                  class="ml-n4"
                  @click="clearUnits"
                />
              </v-col>
              <v-col
                v-if="
                  form.endpoint_units.units &&
                  form.endpoint_units.units.length > 1
                "
                cols="12"
              >
                <v-select
                  v-model="form.endpoint_units.separator"
                  :label="$t('StudyEndpointForm.separator')"
                  :items="separators"
                  clearable
                  :rules="[formRules.required]"
                />
              </v-col>
            </v-row>
          </v-col>
          <v-col cols="5">
            <ParameterValueSelector
              v-if="
                form.timeframe_template && timeframeTemplateParameters.length
              "
              ref="timeframeParamSelector"
              :model-value="timeframeTemplateParameters"
              :template="form.timeframe_template.name"
              color="white"
              :preview-text="$t('StudyEndpointForm.timeframe')"
              stacked
            />
            <v-progress-circular
              v-if="loadingTimeframeParameters"
              indeterminate
              color="secondary"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>

    <template #[`step.createEndpointTemplate`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <NNTemplateInputField
          v-model="endpointTemplateForm.name"
          :label="$t('EndpointTemplateForm.name')"
          :items="parameterTypes"
          show-drop-down-early
          @input="watchEndpointTemplate()"
        />
      </v-form>
    </template>

    <template #[`step.selectTimeframe`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-row class="align-center">
          <v-col cols="10">
            <v-autocomplete
              v-model="form.timeframe_template"
              :label="$t('StudyEndpointForm.timeframe_template')"
              :items="timeframeTemplates"
              item-title="name_plain"
              return-object
              clearable
              append-icon="mdi-magnify"
              :disabled="selectTimeFrameLater"
              @update:model-value="loadTimeframeTemplateParameters"
            />
          </v-col>
          <v-col cols="2">
            <v-checkbox
              v-model="selectTimeFrameLater"
              :label="$t('StudyEndpointForm.select_later')"
              hide-details
              @change="onSelectTimeFrameLaterChange"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>

    <template #[`step.level`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-select
          v-model="form.endpoint_level"
          :label="$t('StudyEndpointForm.endpoint_level')"
          :items="endpointLevels"
          item-title="sponsor_preferred_name"
          return-object
          clearable
          style="max-width: 400px"
        />
      </v-form>
      <v-select
        v-model="form.endpoint_sublevel"
        :label="$t('StudyEndpointForm.endpoint_sub_level')"
        :items="endpointSubLevels"
        item-title="sponsor_preferred_name"
        return-object
        clearable
        style="max-width: 400px"
      />
    </template>
  </HorizontalStepperForm>
</template>

<script>
import endpoints from '@/api/endpoints'
import endpointTemplates from '@/api/endpointTemplates'
import study from '@/api/study'
import templateParameterTypes from '@/api/templateParameterTypes'
import timeframes from '@/api/timeframes'
import timeframeTemplates from '@/api/timeframeTemplates'
import instances from '@/utils/instances'
import statuses from '@/constants/statuses'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import MultipleSelect from '@/components/tools/MultipleSelect.vue'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter.vue'
import NNTable from '@/components/tools/NNTable.vue'
import NNTemplateInputField from '@/components/tools/NNTemplateInputField.vue'
import ParameterValueSelector from '@/components/tools/ParameterValueSelector.vue'
import StudySelectionTable from './StudySelectionTable.vue'
import templatePreInstances from '@/api/templatePreInstances'
import filteringParameters from '@/utils/filteringParameters'
import constants from '@/constants/libraries'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudiesEndpointsStore } from '@/stores/studies-endpoints'
import { computed } from 'vue'
import StudySelectorField from '@/components/studies/StudySelectorField.vue'

export default {
  components: {
    HorizontalStepperForm,
    MultipleSelect,
    ParameterValueSelector,
    NNParameterHighlighter,
    NNTable,
    NNTemplateInputField,
    StudySelectionTable,
    StudySelectorField,
  },
  inject: ['notificationHub', 'formRules'],
  props: {
    currentStudyEndpoints: {
      type: Array,
      default: () => [],
    },
  },
  emits: ['close', 'added'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    const studiesEndpointsStore = useStudiesEndpointsStore()
    return {
      endpointLevels: computed(() => studiesGeneralStore.endpointLevels),
      endpointSubLevels: computed(() => studiesGeneralStore.endpointSubLevels),
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
      units: computed(() => studiesGeneralStore.allUnits),
      addStudyEndpoint: studiesEndpointsStore.addStudyEndpoint,
      selectFromStudyEndpoint: studiesEndpointsStore.selectFromStudyEndpoint,
    }
  },
  data() {
    return {
      helpItems: [
        'StudyEndpointForm.template_mode',
        'StudyEndpointForm.scratch_mode',
        'StudyEndpointForm.select_objective_title',
        'StudyEndpointForm.step2_title',
        'StudyEndpointForm.timeframe_template',
        'StudyEndpointForm.step3_title',
        'StudyEndpointForm.endpoint_level',
      ],
      creationMode: 'template',
      endpointHeaders: [
        { title: '', key: 'actions', width: '1%' },
        { title: this.$t('Study.study_id'), key: 'study_id', noFilter: true },
        {
          title: this.$t('StudyEndpointForm.study_endpoint'),
          key: 'endpoint.name',
          filteringName: 'endpoint.name_plain',
        },
        {
          title: this.$t('StudyEndpointForm.endpoint_level'),
          key: 'endpoint_level.sponsor_preferred_name',
        },
      ],
      endpointTemplates: [],
      endpointTemplateForm: {},
      endpointTemplateParameters: [],
      extraStudyEndpointFilters: {
        endpoint_template: { v: [] },
        'endpoint.status': { v: [statuses.FINAL] },
      },
      form: this.getInitialForm(),
      studiesLoading: false,
      loadingEndpointParameters: false,
      loadingTimeframeParameters: false,
      objectiveHeaders: [
        { title: this.$t('_global.actions'), key: 'actions' },
        { title: this.$t('_global.name'), key: 'objective.name' },
        {
          title: this.$t('StudyEndpointForm.objective_level'),
          key: 'objective_level.sponsor_preferred_name',
        },
      ],
      objectives: [],
      objectiveTotal: 0,
      objectivesLoading: true,
      parameterTypes: [],
      preInstanceMode: true,
      selectLater: false,
      selectTimeFrameLater: false,
      selectedTemplates: [],
      separators: ['and', 'or', ','],
      steps: [],
      studiesSteps: [
        {
          name: 'creationMode',
          title: this.$t('StudyEndpointForm.creation_mode_title'),
        },
        {
          name: 'selectEndpoint',
          title: this.$t('StudyEndpointForm.select_endpoint'),
        },
      ],
      templateSteps: [
        {
          name: 'creationMode',
          title: this.$t('StudyEndpointForm.creation_mode_title'),
        },
        {
          name: 'selectEndpointTemplate',
          title: this.$t('StudyEndpointForm.step2_title'),
        },
      ],
      scratchSteps: [
        {
          name: 'creationMode',
          title: this.$t('StudyEndpointForm.creation_mode_title'),
        },
        {
          name: 'objective',
          title: this.$t('StudyEndpointForm.select_objective_title'),
        },
        {
          name: 'createEndpointTemplate',
          title: this.$t('StudyEndpointForm.create_tpl_title'),
        },
        {
          name: 'selectTimeframe',
          title: this.$t('StudyEndpointForm.select_timeframe_title'),
        },
        {
          name: 'endpointDetails',
          title: this.$t('StudyEndpointForm.step3_title'),
        },
        {
          name: 'level',
          title: this.$t('StudyEndpointForm.endpoint_level_title'),
        },
      ],
      templateSelectionHeaders: [
        { title: '', key: 'actions', width: '1%' },
        {
          title: this.$t('_global.template'),
          key: 'name',
          class: 'text-center',
        },
      ],
      formSelectedStudy: null,
      selectedEndpointHeaders: [
        { title: '', key: 'actions', width: '1%' },
        { title: this.$t('Study.study_id'), key: 'study_id' },
        {
          title: this.$t('StudyEndpointForm.study_endpoint'),
          key: 'endpoint.name',
        },
        {
          title: this.$t('StudyEndpointForm.endpoint_level'),
          key: 'endpoint_level.sponsor_preferred_name',
        },
      ],
      selectedStudyEndpoints: [],
      skipUnits: false,
      studies: [],
      timeframeTemplates: [],
      timeframeTemplateParameters: [],
      tplHeaders: [
        { title: '', key: 'actions', width: '1%' },
        {
          title: this.$t('_global.sequence_number_short'),
          key: 'sequence_id',
          width: '5%',
        },
        {
          title: this.$t('_global.template'),
          key: 'name',
          filteringName: 'name_plain',
        },
      ],
      defaultTplFilters: [
        { title: this.$t('_global.sequence_number_short'), key: 'sequence_id' },
        {
          title: this.$t('_global.indications'),
          key: 'indications',
          filteringName: 'indications.name',
        },
        {
          title: this.$t('EndpointTemplateTable.endpoint_cat'),
          key: 'categories.name.sponsor_preferred_name',
        },
        {
          title: this.$t('EndpointTemplateTable.endpoint_sub_cat'),
          key: 'sub_categories.name.sponsor_preferred_name',
        },
      ],
      options: {},
      total: 0,
      endpointTitleWarning: false,
    }
  },
  computed: {
    title() {
      return this.$t('StudyEndpointForm.add_title')
    },
    studyObjectiveLevel() {
      if (
        this.form.study_objective &&
        this.form.study_objective.objective_level
      ) {
        return this.form.study_objective.objective_level.sponsor_preferred_name
      }
      return ''
    },
    selectedStudyObjectiveName() {
      return this.form.study_objective
        ? this.form.study_objective.objective.name
        : ''
    },
    selectedEndpointTemplateName() {
      return this.form.endpoint_template ? this.form.endpoint_template.name : ''
    },
    selectedStudyEndpointUnits() {
      if (this.form.selected_study_endpoint) {
        if (this.form.selected_study_endpoint.endpoint_units.units.length > 1) {
          return this.form.selected_study_endpoint.endpoint_units.units.join(
            this.form.selected_study_endpoint.endpoint_units.separator
          )
        }
        return this.form.selected_study_endpoint.endpoint_units.units[0]
      }
      return ''
    },
  },
  watch: {
    studyEndpoint(val) {
      if (val) {
        this.api = endpointTemplates
        this.initFromStudyEndpoint(val)
        this.getEndpointTemplates()
        this.getTimeframeTemplates()
      } else {
        this.form = this.getInitialForm()
      }
    },
    creationMode(value) {
      if (!this.studyEndpoint) {
        if (value === 'studies') {
          this.steps = this.studiesSteps
        } else if (value === 'template') {
          this.steps = this.templateSteps
        } else {
          this.steps = this.scratchSteps
        }
      }
    },
    endpointTemplates(value) {
      if (value && value.length && this.studyEndpoint) {
        this.loadEndpointTemplate()
      }
    },
    timeframeTemplates(value) {
      if (value && value.length && this.studyEndpoint) {
        this.loadTimeframeTemplate()
      }
    },
    endpointTemplateParameters(value) {
      value.forEach((el) => {
        if (
          el.name === 'TextValue' &&
          el.selected_values &&
          el.selected_values.length
        ) {
          value[value.indexOf(el)].selected_values = el.selected_values[0].name
        }
      })
    },
    timeframeTemplateParameters(value) {
      value.forEach((el) => {
        if (
          el.name === 'TextValue' &&
          el.selected_values &&
          el.selected_values.length
        ) {
          value[value.indexOf(el)].selected_values = el.selected_values[0].name
        }
      })
    },
    preInstanceMode(value) {
      this.api = value ? this.preInstanceApi : endpointTemplates
      this.getEndpointTemplates()
      this.selectedTemplates = []
    },
  },
  created() {
    this.steps = this.templateSteps
  },
  mounted() {
    this.preInstanceApi = templatePreInstances('endpoint')
    this.api = !this.studyEndpoint ? this.preInstanceApi : endpointTemplates
    study.getStudyObjectives(this.selectedStudy.uid).then((resp) => {
      this.objectives = resp.data.items
      this.objectiveTotal = resp.data.total
      this.objectivesLoading = false
    })
    if (this.studyEndpoint) {
      this.initFromStudyEndpoint(this.studyEndpoint)
    }
    this.getTimeframeTemplates()
    templateParameterTypes.getTypes().then((resp) => {
      this.parameterTypes = resp.data
    })
    this.studiesLoading = true
    study
      .getSelectableStudies({ has_study_endpoint: true })
      .then((resp) => {
        this.studies = resp.data.filter(
          (study) => study.uid !== this.selectedStudy.uid
        )
      })
      .finally(() => {
        this.studiesLoading = false
      })
  },
  methods: {
    watchEndpointTemplate() {
      if (
        this.endpointTemplateForm.name &&
        this.endpointTemplateForm.name.length > 254 &&
        !this.endpointTitleWarning
      ) {
        this.notificationHub.add({
          msg: this.$t('StudyEndpointForm.endpoint_title_warning'),
          type: 'warning',
        })
        this.endpointTitleWarning = true
      }
    },
    unitsDisplay(units) {
      let result = ''
      if (units) {
        units.forEach((unit) => {
          result += this.units.find((u) => u.uid === unit.uid).name + ', '
        })
      }
      return result.slice(0, -2)
    },
    getInitialForm() {
      return {
        endpoint_units: {},
      }
    },
    close() {
      this.$emit('close')
      this.notificationHub.clearErrors()
      this.form = this.getInitialForm()
      this.endpointTemplateForm = {}
      this.creationMode = 'template'
      this.steps = this.templateSteps
      this.$refs.stepper.reset()
      this.skipUnits = false
      this.endpointTitleWarning = false
      this.preInstanceMode = true
    },
    clearUnits() {
      this.form.endpoint_units.units = []
      this.skipUnits = !this.skipUnits
    },
    getObserver(step) {
      return this.$refs[`observer_${step}`]
    },
    async loadEndpointTemplateParameters(template) {
      if (template) {
        this.loadingEndpointParameters = true
        const templateUid =
          this.creationMode !== 'scratch' && this.preInstanceMode
            ? template.template_uid
            : template.uid
        const resp = await endpointTemplates.getParameters(templateUid)
        this.endpointTemplateParameters = resp.data
        this.loadingEndpointParameters = false
      } else {
        this.endpointTemplateParameters = []
      }
    },
    loadTimeframeTemplateParameters(template) {
      this.timeframeTemplateParameters = []
      if (template) {
        this.loadingTimeframeParameters = true
        timeframeTemplates
          .getParameters(template.uid, { study_uid: this.selectedStudy.uid })
          .then((resp) => {
            this.timeframeTemplateParameters = resp.data
            this.loadingTimeframeParameters = false
          })
      }
    },
    async getStudyEndpointNamePreview() {
      const endpointData = {
        endpoint_template_uid: this.form.endpoint_template.uid,
        parameter_terms: await instances.formatParameterValues(
          this.endpointTemplateParameters
        ),
        library_name: this.form.endpoint_template.library.name,
      }
      const resp = await study.getStudyEndpointPreview(this.selectedStudy.uid, {
        endpoint_data: endpointData,
      })
      return resp.data.endpoint.name
    },
    async submit() {
      this.notificationHub.clearErrors()

      let args = null

      if (this.creationMode === 'template') {
        if (!this.selectedTemplates.length) {
          this.notificationHub.add({
            msg: this.$t('EligibilityCriteriaForm.no_template_error'),
            type: 'error',
          })
          this.$refs.stepper.loading = false
          return
        }
        const data = []
        for (const template of this.selectedTemplates) {
          data.push({
            endpoint_template_uid: this.preInstanceMode
              ? template.template_uid
              : template.uid,
            parameter_terms: this.preInstanceMode
              ? template.parameter_terms
              : [],
            library_name: template.library.name,
          })
        }
        await study.batchCreateStudyEndpoints(this.selectedStudy.uid, data)
      } else if (this.creationMode === 'scratch') {
        const data = JSON.parse(JSON.stringify(this.form))
        if (data.timeframe_template) {
          data.timeframe_template.library.name = constants.LIBRARY_USER_DEFINED
        }
        args = {
          studyUid: this.selectedStudy.uid,
          data,
          endpointParameters: this.endpointTemplateParameters,
          timeframeParameters: this.timeframeTemplateParameters,
        }
        await this.addStudyEndpoint(args)
      } else {
        for (const item of this.selectedStudyEndpoints) {
          delete item.timeframe
          args = {
            studyUid: this.selectedStudy.uid,
            studyEndpoint: item,
          }
          await this.selectFromStudyEndpoint(args)
        }
      }
      this.$emit('added')
      this.notificationHub.add({
        msg: this.$t('StudyEndpointForm.endpoint_added'),
      })
      this.close()
    },
    loadEndpointTemplate() {
      if (!this.form.endpoint && !this.form.endpoint_template) {
        return
      }
      this.form.endpoint_template = this.endpointTemplates.find(
        (item) => item.uid === this.form.endpoint.endpoint_template.uid
      )

      endpoints.getObjectParameters(this.form.endpoint.uid).then((resp) => {
        this.endpointTemplateParameters = resp.data
        instances.loadParameterValues(
          this.form.endpoint.parameter_terms,
          this.endpointTemplateParameters
        )
      })
    },
    loadTimeframeTemplate() {
      if (!this.form.timeframe) {
        return
      }
      this.form.timeframe_template = this.timeframeTemplates.find(
        (item) => item.uid === this.form.timeframe.timeframe_template.uid
      )
      timeframes
        .getObjectParameters(this.form.timeframe.uid, {
          study_uid: this.selectedStudy.uid,
        })
        .then((resp) => {
          this.timeframeTemplateParameters = resp.data
          instances.loadParameterValues(
            this.form.timeframe.parameter_terms,
            this.timeframeTemplateParameters
          )
        })
    },
    selectStudyObjective(value) {
      this.selectLater = false
      this.form.study_objective = value
    },
    onSelectLaterChange(value) {
      if (value) {
        this.form.study_objective = null
      }
    },
    onSelectTimeFrameLaterChange(value) {
      if (value) {
        this.form.timeframe_template = null
        this.timeframeTemplateParameters = []
      }
    },
    async selectEndpointTemplate(template) {
      if (!this.selectedTemplates.some((el) => el.uid === template.uid)) {
        this.selectedTemplates.push(template)
      }
    },
    unselectEndpointTemplate(template) {
      this.selectedTemplates = this.selectedTemplates.filter(
        (item) => item.name !== template.name
      )
    },
    selectStudyEndpoint(studyEndpoint) {
      this.selectedStudyEndpoints.push(studyEndpoint)
      this.form.endpoint_level = studyEndpoint.endpoint_level
      this.form.endpoint_sublevel = studyEndpoint.endpoint_sublevel
    },
    unselectStudyEndpoint(studyEndpoint) {
      this.selectedStudyEndpoints = this.selectedStudyEndpoints.filter(
        (item) => item.endpoint.name !== studyEndpoint.endpoint.name
      )
    },
    isStudyEndpointSelected(studyEndpoint) {
      let selected = this.selectedStudyEndpoints.find(
        (item) => item.endpoint.uid === studyEndpoint.endpoint.uid
      )
      if (!selected && this.currentStudyEndpoints.length) {
        selected = this.currentStudyEndpoints.find(
          (item) =>
            item.endpoint && item.endpoint.uid === studyEndpoint.endpoint.uid
        )
      }
      return selected !== undefined
    },
    getCopyButtonColor(item) {
      return !this.isStudyEndpointSelected(item) ? 'primary' : ''
    },
    async extraStepValidation(step) {
      if (
        (this.creationMode === 'scratch' && step === 3) ||
        (this.creationMode === 'clone' && step === 1)
      ) {
        if (
          this.form.endpoint_template &&
          this.form.endpoint_template.name === this.endpointTemplateForm.name
        ) {
          return true
        }
        const data = {
          ...this.endpointTemplateForm,
          studyUid: this.selectedStudy.uid,
        }
        data.library_name = constants.LIBRARY_USER_DEFINED
        let resp
        try {
          resp = await endpointTemplates.create(data)
          if (resp.data.status === statuses.DRAFT)
            await endpointTemplates.approve(resp.data.uid)
          this.form.endpoint_template = resp.data
        } catch (_error) {
          return false
        }
        await this.loadEndpointTemplateParameters(resp.data)
        return true
      }
      if (this.creationMode === 'scratch' && step === 2) {
        if (this.selectLater || this.form.study_objective) {
          return true
        }
        this.notificationHub.add({
          type: 'error',
          msg: this.$t('StudyEndpointForm.select_objective'),
        })
        return false
      }
      return true
    },
    getEndpointTemplates(filters, options, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      if (params.filters) {
        params.filters = JSON.parse(params.filters)
      } else {
        params.filters = {}
      }
      if (!this.studyEndpoint) {
        params.status = statuses.FINAL
        Object.assign(params.filters, {
          'library.name': { v: [constants.LIBRARY_SPONSOR] },
        })
      }
      this.api.get(params).then((resp) => {
        this.endpointTemplates = resp.data.items
        this.total = resp.data.total
      })
    },
    getTimeframeTemplates() {
      const params = {
        filters: { 'library.name': { v: [constants.LIBRARY_SPONSOR] } },
        status: statuses.FINAL,
      }
      timeframeTemplates.get(params).then((resp) => {
        this.timeframeTemplates = resp.data.items
      })
    },
  },
}
</script>

<style scoped lang="scss">
.v-stepper {
  background-color: rgb(var(--v-theme-dfltBackground)) !important;
  box-shadow: none;
}
</style>
