<template>
  <HorizontalStepperForm
    ref="stepper"
    :title="title"
    :steps="steps"
    :form-observer-getter="getObserver"
    :help-items="helpItems"
    :extra-step-validation="createTemplate"
    @close="close"
    @save="submit"
  >
    <template #[`step.creation_mode`]="{ step }">
      <v-radio-group v-model="creationMode">
        <v-radio
          data-cy="criteria-from-template"
          :label="$t('EligibilityCriteriaForm.create_from_template')"
          value="template"
        />
        <v-radio
          data-cy="criteria-from-study"
          :label="$t('EligibilityCriteriaForm.select_from_studies')"
          value="select"
        />
        <v-radio
          data-cy="criteria-from-scratch"
          :label="$t('EligibilityCriteriaForm.create_from_scratch')"
          value="scratch"
        />
      </v-radio-group>
      <v-form :ref="`observer_${step}`">
        <v-row v-if="creationMode === 'select'">
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
    <template #[`step.select`]>
      <p class="text-grey text-body-large font-weight-bold">
        {{ $t('EligibilityCriteriaForm.selected_criteria') }}
      </p>
      <v-data-table :headers="selectionHeaders" :items="selectedCriteria">
        <template #[`item.name`]="{ item }">
          <template v-if="item.criteria_template">
            <NNParameterHighlighter
              :name="item.criteria_template.name"
              default-color="orange"
            />
          </template>
          <template v-else>
            <NNParameterHighlighter
              :name="item.criteria.name"
              :show-prefix-and-postfix="false"
            />
          </template>
        </template>
        <template #[`item.guidance_text`]="{ item }">
          <template v-if="item.criteria_template">
            <span
              v-html="sanitizeHTMLHandler(item.criteria_template.guidance_text)"
            />
          </template>
          <template v-else>
            <span
              v-html="
                sanitizeHTMLHandler(
                  item.criteria.criteria_template.guidance_text
                )
              "
            />
          </template>
        </template>
        <template #[`item.actions`]="{ item }">
          <v-btn
            icon="mdi-delete-outline"
            color="red"
            variant="text"
            @click="unselectStudyCriteria(item)"
          />
        </template>
      </v-data-table>
    </template>
    <template #[`step.select.after`]>
      <p class="text-grey text-body-large font-weight-bold mb-0 ml-3">
        {{ $t('StudyObjectiveForm.copy_instructions') }}
      </p>
      <v-col cols="12">
        <StudySelectionTable
          :headers="stdHeaders"
          data-fetcher-name="getAllStudyCriteria"
          :selected-study="formSelectedStudy"
          :extra-data-fetcher-filters="extraDataFetcherFilters"
          column-data-resource="study-criteria"
          @item-selected="selectTemplate"
        >
          <template #[`item.name`]="{ item }">
            <template v-if="item.criteria_template">
              <NNParameterHighlighter
                :name="item.criteria_template.name"
                default-color="orange"
              />
            </template>
            <template v-else>
              <NNParameterHighlighter
                :name="item.criteria.name"
                :show-prefix-and-postfix="false"
              />
            </template>
          </template>
          <template #[`item.guidance_text`]="{ item }">
            <template v-if="item.criteria_template">
              <span
                v-html="
                  sanitizeHTMLHandler(item.criteria_template.guidance_text)
                "
              />
            </template>
            <template v-else>
              <span v-html="sanitizeHTMLHandler(item.criteria.guidance_text)" />
            </template>
          </template>
        </StudySelectionTable>
      </v-col>
    </template>
    <template #[`step.createFromTemplate`]>
      <v-data-table :headers="selectionHeaders" :items="selectedCriteria">
        <template #[`item.name`]="{ item }">
          <NNParameterHighlighter :name="item.name" default-color="orange" />
        </template>
        <template #[`item.guidance_text`]="{ item }">
          <span v-html="sanitizeHTMLHandler(item.guidance_text)" />
        </template>
        <template #[`item.actions`]="{ item }">
          <v-btn
            icon="mdi-delete-outline"
            color="red"
            variant="text"
            @click="unselectTemplate(item)"
          />
        </template>
      </v-data-table>
    </template>
    <template #[`step.createFromTemplate.after`]>
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
      <v-col cols="12">
        <NNTable
          key="criteriaTemplateTable"
          table-id="eligibility-criteria-form-templates"
          :headers="tplHeaders"
          :items="criteriaTemplates"
          :items-per-page="15"
          hide-default-switches
          hide-export-button
          elevation="0"
          :items-length="total"
          :column-data-resource="
            preInstanceMode ? 'criteria-pre-instances' : 'criteria-templates'
          "
          :default-filters="defaultTplFilters"
          :filters-modify-function="addTypeFilterToHeader"
          @filter="getCriteriaTemplates"
        >
          <template #[`item.indications`]="{ item }">
            <template v-if="item.indications">
              {{ $filters.names(item.indications) }}
            </template>
            <template v-else>
              {{ $t('_global.not_applicable_long') }}
            </template>
          </template>
          <template #[`item.categories`]="{ item }">
            <template v-if="item.categories">
              {{ $filters.terms(item.categories) }}
            </template>
            <template v-else>
              {{ $t('_global.not_applicable_long') }}
            </template>
          </template>
          <template #[`item.subCategories`]="{ item }">
            <template v-if="item.subCategories">
              {{ $filters.terms(item.subCategories) }}
            </template>
            <template v-else>
              {{ $t('_global.not_applicable_long') }}
            </template>
          </template>
          <template #[`item.name`]="{ item }">
            <NNParameterHighlighter
              v-if="preInstanceMode"
              :name="item.name"
              default-color="green"
              :show-prefix-and-postfix="false"
            />
            <NNParameterHighlighter
              v-else
              :name="item.name"
              default-color="orange"
            />
          </template>
          <template #[`item.guidance_text`]="{ item }">
            <span v-html="sanitizeHTMLHandler(item.guidance_text)" />
          </template>
          <template #[`item.actions`]="{ item }">
            <v-btn
              :data-cy="$t('StudyObjectiveForm.copy_template')"
              icon="mdi-content-copy"
              color="primary"
              :title="$t('StudyObjectiveForm.copy_template')"
              variant="text"
              :disabled="loadingTemplates"
              @click="selectTemplate(item)"
            />
          </template>
        </NNTable>
      </v-col>
    </template>
    <template #[`step.createFromScratch`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-row>
          <v-col>
            <NNTemplateInputField
              v-model="form.name"
              :data-cy="$t('EligibilityCriteriaForm.criteria_template')"
              :label="$t('EligibilityCriteriaForm.criteria_template')"
              :items="parameterTypes"
              :rules="[formRules.required]"
              :show-drop-down-early="true"
            />
          </v-col>
        </v-row>
      </v-form>
      <v-row>
        <v-col>
          <div>
            <QuillEditor
              id="editor"
              ref="editor"
              v-model:content="form.guidance_text"
              content-type="html"
              :toolbar="customToolbar"
              :placeholder="$t('CriteriaTemplateForm.guidance_text')"
              class="pt-4"
            />
          </div>
        </v-col>
      </v-row>
    </template>
    <template #[`step.createCriteria`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <ParameterValueSelector
          v-if="form.criteria_template"
          max-template-length
          :model-value="parameters"
          :template="form.criteria_template.name"
          color="white"
        />
      </v-form>
    </template>
  </HorizontalStepperForm>
</template>

<script>
import { computed } from 'vue'
import templateParameterTypes from '@/api/templateParameterTypes'
import criteriaTemplates from '@/api/criteriaTemplates'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import instances from '@/utils/instances'
import libraries from '@/constants/libraries'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter.vue'
import NNTable from '@/components/tools/NNTable.vue'
import NNTemplateInputField from '@/components/tools/NNTemplateInputField.vue'
import ParameterValueSelector from '@/components/tools/ParameterValueSelector.vue'
import study from '@/api/study'
import StudySelectionTable from './StudySelectionTable.vue'
import templatePreInstances from '@/api/templatePreInstances'
import filteringParameters from '@/utils/filteringParameters'
import statuses from '@/constants/statuses'
import { QuillEditor } from '@vueup/vue-quill'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { sanitizeHTML } from '@/utils/sanitize'
import StudySelectorField from '@/components/studies/StudySelectorField.vue'

export default {
  components: {
    HorizontalStepperForm,
    NNParameterHighlighter,
    NNTable,
    NNTemplateInputField,
    ParameterValueSelector,
    StudySelectionTable,
    QuillEditor,
    StudySelectorField,
  },
  inject: ['notificationHub', 'formRules'],
  props: {
    criteriaType: {
      type: Object,
      default: undefined,
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
      customToolbar: [
        ['bold', 'italic', 'underline'],
        [{ script: 'sub' }, { script: 'super' }],
        [{ list: 'ordered' }, { list: 'bullet' }],
      ],
      helpItems: [
        'EligibilityCriteriaForm.add_criteria',
        'EligibilityCriteriaForm.select_from_studies',
        'EligibilityCriteriaForm.create_from_template',
        'EligibilityCriteriaForm.create_from_scratch',
        'EligibilityCriteriaForm.select_criteria_templates',
      ],
      creationMode: 'template',
      extraDataFetcherFilters: {
        'criteria.library.name': { v: [libraries.LIBRARY_SPONSOR] },
        'criteria_type.term_name': {
          v: [this.criteriaType.sponsor_preferred_name],
        },
        'criteria.status': { v: [statuses.FINAL] },
      },
      tplHeaders: [
        { title: '', key: 'actions', width: '1%' },
        {
          title: this.$t('_global.number'),
          key: 'sequence_id',
          width: '5%',
        },
        {
          title: this.$t('EligibilityCriteriaForm.criteria_template'),
          key: 'name',
        },
        {
          title: this.$t('EligibilityCriteriaForm.guidance_text'),
          key: 'guidance_text',
        },
      ],
      defaultTplFilters: [
        { title: this.$t('_global.number'), key: 'sequence_id' },
        {
          title: this.$t('_global.indications'),
          key: 'indications',
          filteringName: 'indications.name',
        },
        {
          title: this.$t('EligibilityCriteriaForm.criterion_cat'),
          key: 'categories',
          filteringName: 'categories.name.sponsor_preferred_name',
        },
        {
          title: this.$t('EligibilityCriteriaForm.criterion_sub_cat'),
          key: 'subCategories',
          filteringName: 'subCategories.name.sponsor_preferred_name',
        },
      ],
      criteriaTemplates: [],
      form: {},
      loadingParameters: false,
      loadingTemplates: false,
      studiesLoading: false,
      parameters: [],
      parameterTypes: [],
      preInstanceMode: true,
      selectedCriteria: [],
      formSelectedStudy: null,
      steps: this.getInitialSteps(),
      studies: [],
      createFromScratchSteps: [
        {
          name: 'creation_mode',
          title: this.$t('EligibilityCriteriaForm.creation_mode_label'),
        },
        {
          name: 'createFromScratch',
          title: this.$t('EligibilityCriteriaForm.create_from_scratch'),
          noStyle: true,
        },
        {
          name: 'createCriteria',
          title: this.$t('EligibilityCriteriaForm.create_criteria'),
        },
      ],
      selectFromStudiesSteps: [
        {
          name: 'creation_mode',
          title: this.$t('EligibilityCriteriaForm.creation_mode_label'),
        },
        {
          name: 'select',
          title: this.$t('EligibilityCriteriaForm.select_criteria'),
        },
      ],
      selectionHeaders: [
        { title: '', key: 'actions', width: '1%' },
        {
          title: this.$t('EligibilityCriteriaForm.criteria_text'),
          key: 'name',
          class: 'text-center',
        },
        {
          title: this.$t('EligibilityCriteriaForm.guidance_text'),
          key: 'guidance_text',
        },
      ],
      stdHeaders: [
        { title: '', key: 'actions', width: '1%' },
        { title: this.$t('Study.study_id'), key: 'studyUid' },
        {
          title: this.$t('EligibilityCriteriaForm.criteria_text'),
          key: 'name',
        },
        {
          title: this.$t('EligibilityCriteriaForm.guidance_text'),
          key: 'guidance_text',
        },
      ],
      options: {},
      total: 0,
    }
  },
  computed: {
    title() {
      return (
        this.$t('_global.add') +
        ' ' +
        this.criteriaType.sponsor_preferred_name_sentence_case
      )
    },
  },
  watch: {
    creationMode(value) {
      if (value === 'select') {
        this.steps = this.selectFromStudiesSteps
      } else if (value === 'template') {
        this.steps = this.getInitialSteps()
      } else {
        this.steps = this.createFromScratchSteps
      }
    },
    preInstanceMode(value) {
      this.apiEndpoint = value ? this.preInstanceApi : criteriaTemplates
      this.getCriteriaTemplates()
      this.selectedCriteria = []
    },
  },
  created() {
    this.preInstanceApi = templatePreInstances('criteria')
    if (!this.studyCriteria) {
      this.apiEndpoint = this.preInstanceApi
    }
  },
  mounted() {
    templateParameterTypes.getTypes().then((resp) => {
      this.parameterTypes = resp.data
    })

    this.studiesLoading = true
    study
      .getSelectableStudies({ has_study_criteria: true })
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
    sanitizeHTMLHandler(html) {
      return sanitizeHTML(html)
    },
    close() {
      this.$emit('close')
      this.notificationHub.clearErrors()
      this.$refs.stepper.reset()
      this.steps = this.getInitialSteps()
      this.creationMode = 'template'
      this.form = {}
      this.formSelectedStudy = null
      this.selectedCriteria = []
      this.preInstanceMode = true
      this.apiEndpoint = this.preInstanceApi
    },
    getInitialSteps() {
      return [
        {
          name: 'creation_mode',
          title: this.$t('EligibilityCriteriaForm.creation_mode_label'),
        },
        {
          name: 'createFromTemplate',
          title: this.$t('EligibilityCriteriaForm.select_criteria_templates'),
        },
      ]
    },
    getObserver(step) {
      return this.$refs[`observer_${step}`]
    },
    async getCriteriaTemplates(filters, options, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      params.status = statuses.FINAL
      if (params.filters) {
        params.filters = JSON.parse(params.filters)
      } else {
        params.filters = {}
      }
      if (!this.preInstanceMode) {
        Object.assign(params.filters, {
          'type.name.sponsor_preferred_name_sentence_case': {
            v: [this.criteriaType.sponsor_preferred_name_sentence_case],
          },
          'library.name': { v: [libraries.LIBRARY_SPONSOR] },
        })
      } else {
        Object.assign(params.filters, {
          template_type_uid: {
            v: [this.criteriaType.term_uid],
          },
        })
      }
      this.loadingTemplates = true
      try {
        const resp = await this.apiEndpoint.get(params)
        this.criteriaTemplates = resp.data.items
        this.total = resp.data.total
      } finally {
        this.loadingTemplates = false
      }
    },
    addTypeFilterToHeader(jsonFilter, params) {
      if (!this.preInstanceMode) {
        jsonFilter['type.name.sponsor_preferred_name_sentence_case'] = {
          v: [this.criteriaType.sponsor_preferred_name_sentence_case],
        }
      } else {
        jsonFilter.template_type_uid = {
          v: [this.criteriaType.term_uid],
        }
      }
      jsonFilter['library.name'] = { v: [libraries.LIBRARY_SPONSOR] }
      return {
        jsonFilter,
        params,
      }
    },
    selectTemplate(template) {
      if (
        template.criteria &&
        !this.selectedCriteria.some(
          (el) => el.criteria.uid === template.criteria.uid
        )
      ) {
        this.selectedCriteria.push(template)
      } else if (
        template.uid &&
        !this.selectedCriteria.some((el) => el.uid === template.uid)
      ) {
        this.selectedCriteria.push(template)
      }
    },
    unselectTemplate(template) {
      this.selectedCriteria = this.selectedCriteria.filter(
        (item) => item.name !== template.name
      )
    },
    unselectStudyCriteria(studyCriteria) {
      this.selectedCriteria = this.selectedCriteria.filter(
        (item) => item.study_criteria_uid !== studyCriteria.study_criteria_uid
      )
    },
    async loadParameters(template) {
      if (template) {
        this.loadingParameters = true
        const resp = await criteriaTemplates.getObjectTemplateParameters(
          template.uid
        )
        this.parameters = resp.data
        this.loadingParameters = false
      } else {
        this.parameters = []
      }
    },
    async createTemplate(step) {
      if (this.creationMode !== 'scratch' || step !== 2) {
        return true
      }
      const data = {
        ...this.form,
        library_name: 'User Defined',
        type_uid: this.criteriaType.term_uid,
        study_uid: this.selectedStudy.uid,
      }
      try {
        const resp = await criteriaTemplates.create(data)
        if (resp.data.status === statuses.DRAFT)
          await criteriaTemplates.approve(resp.data.uid)
        this.form.criteria_template = resp.data
      } catch (_error) {
        return false
      }
      this.loadParameters(this.form.criteria_template)
      return true
    },
    async submit() {
      this.notificationHub.clearErrors()

      if (this.creationMode !== 'scratch') {
        if (this.creationMode === 'template') {
          if (!this.selectedCriteria.length) {
            this.notificationHub.add({
              msg: this.$t('EligibilityCriteriaForm.no_template_error'),
              type: 'error',
            })
            this.$refs.stepper.loading = false
            return
          }
          const data = []
          for (const criteria of this.selectedCriteria) {
            data.push({
              criteria_template_uid: this.preInstanceMode
                ? criteria.template_uid
                : criteria.uid,
              parameter_terms: this.preInstanceMode
                ? criteria.parameter_terms
                : undefined,
              library_name: criteria.library.name,
            })
          }
          await study.batchCreateStudyCriteria(this.selectedStudy.uid, data)
        } else {
          if (!this.selectedCriteria.length) {
            this.notificationHub.add({
              msg: this.$t('EligibilityCriteriaForm.no_criteria_error'),
              type: 'error',
            })
            this.$refs.stepper.loading = false
            return
          }
          const data = []
          for (const studyCriteria of this.selectedCriteria) {
            if (studyCriteria.criteria_template) {
              data.push({
                criteria_template_uid: studyCriteria.criteria_template.uid,
                library_name: studyCriteria.criteria_template.library.name,
              })
            } else {
              const payload = {
                criteria_data: {
                  parameter_terms: studyCriteria.criteria.parameter_terms,
                  criteria_template_uid: studyCriteria.criteria.template.uid,
                  library_name: studyCriteria.criteria.library.name,
                },
              }
              await study.createStudyCriteria(this.selectedStudy.uid, payload)
            }
          }
          await study.batchCreateStudyCriteria(this.selectedStudy.uid, data)
        }
      } else {
        const data = {
          criteria_data: {
            criteria_template_uid: this.form.criteria_template.uid,
            parameter_terms: await instances.formatParameterValues(
              this.parameters
            ),
            library_name: libraries.LIBRARY_SPONSOR,
          },
        }
        await study.createStudyCriteria(this.selectedStudy.uid, data)
      }
      this.notificationHub.add({
        type: 'success',
        msg: this.$t('EligibilityCriteriaForm.add_success'),
      })
      this.$emit('added')
      this.close()
    },
  },
}
</script>
