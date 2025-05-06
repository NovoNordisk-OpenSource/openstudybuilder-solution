<template>
  <HorizontalStepperForm
    ref="stepper"
    :title="title"
    :steps="steps"
    :form-observer-getter="getObserver"
    :extra-step-validation="extraStepValidation"
    :help-items="helpItems"
    :edit-data="form"
    :loading-continue="loadingContinue"
    @close="close"
    @save="submit"
  >
    <template #[`step.creationMode`]="{ step }">
      <v-radio-group v-model="creationMode" color="primary">
        <v-radio
          data-cy="footnote-from-template"
          :label="$t('StudyFootnoteForm.template_mode')"
          value="template"
        />
        <v-radio
          data-cy="footnote-from-select"
          :label="$t('StudyFootnoteForm.select_mode')"
          value="select"
        />
        <v-radio
          data-cy="footnote-from-scratch"
          :label="$t('StudyFootnoteForm.scratch_mode')"
          value="scratch"
        />
      </v-radio-group>
      <v-form :ref="`observer_${step}`">
        <v-row v-if="creationMode === 'select'">
          <v-col cols="3">
            <v-autocomplete
              v-model="selectedStudies"
              :data-cy="$t('StudySelectionTable.study_ids')"
              :label="$t('StudySelectionTable.studies')"
              :items="studies"
              :rules="[formRules.required]"
              item-title="current_metadata.identification_metadata.study_id"
              clearable
              multiple
              return-object
            />
          </v-col>
          <div class="mt-8">
            {{ $t('_global.and_or') }}
          </div>
          <v-col cols="3">
            <v-autocomplete
              v-model="selectedStudies"
              :label="$t('StudySelectionTable.study_acronyms')"
              :items="
                studies.filter(
                  (study) =>
                    study.current_metadata.identification_metadata.study_acronym
                )
              "
              :rules="[formRules.required]"
              item-title="current_metadata.identification_metadata.study_acronym"
              clearable
              multiple
              return-object
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #[`step.selectFootnote`]>
      <p class="text-grey text-subtitle-1 font-weight-bold">
        {{ $t('StudyFootnoteForm.selected_footnotes') }}
      </p>
      <v-data-table
        data-cy="selected-footnotes-table"
        :headers="selectedFootnoteHeaders"
        :items="selectedStudyFootnotes"
      >
        <template #[`item.footnote.name`]="{ item }">
          <NNParameterHighlighter :name="item.footnote.name" />
        </template>
        <template #[`item.actions`]="{ item }">
          <v-btn
            icon="mdi-delete-outline"
            color="red"
            variant="text"
            @click="unselectStudyFootnote(item)"
          />
        </template>
      </v-data-table>
    </template>
    <template #[`step.selectFootnote.after`]>
      <p class="text-grey text-subtitle-1 font-weight-bold mb-0 ml-3">
        {{ $t('StudyFootnoteForm.copy_instructions') }}
      </p>
      <v-col cols="12" flat class="pt-0 mt-0">
        <StudySelectionTable
          :headers="footnoteHeaders"
          data-fetcher-name="getAllStudyFootnotes"
          :extra-data-fetcher-filters="extraStudyFootnoteFilters"
          :studies="selectedStudies"
          column-data-resource="study-soa-footnotes"
          @item-selected="selectStudyFootnote"
        >
          <template #[`item.footnote.name`]="{ item }">
            <NNParameterHighlighter :name="item.footnote.name" />
          </template>
          <template #[`item.actions`]="{ item }">
            <v-btn
              :data-cy="$t('StudySelectionTable.copy_item')"
              icon="mdi-content-copy"
              :color="getCopyButtonColor(item)"
              :disabled="isStudyFootnoteSelected(item)"
              :title="$t('StudySelectionTable.copy_item')"
              variant="text"
              @click="selectStudyFootnote(item)"
            />
          </template>
        </StudySelectionTable>
      </v-col>
    </template>
    <template #[`step.selectTemplates`]>
      <v-data-table :headers="selectionHeaders" :items="selectedTemplates">
        <template #[`item.name`]="{ item }">
          <NNParameterHighlighter :name="item.name" default-color="orange" />
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
    <template #[`step.selectTemplates.after`]>
      <div class="d-flex align-center">
        <p class="text-grey text-subtitle-1 font-weight-bold mb-0 ml-3">
          {{ $t('StudyFootnoteForm.copy_instructions') }}
        </p>
        <v-switch
          v-model="preInstanceMode"
          color="primary"
          :label="$t('StudyFootnoteForm.show_pre_instances')"
          hide-details
          class="ml-4"
        />
      </div>
      <v-col cols="12" class="pt-0">
        <NNTable
          key="templatesTable"
          :headers="tplHeaders"
          :items="templates"
          hide-default-switches
          hide-actions-menu
          :default-filters="defaultTplFilters"
          :items-per-page="15"
          elevation="0"
          :items-length="total"
          :column-data-resource="
            preInstanceMode ? 'footnote-pre-instances' : 'footnote-templates'
          "
          @filter="getFootnoteTemplates"
        >
          <template #[`item.categories.name.sponsor_preferred_name`]="{ item }">
            <template v-if="item.categories">
              {{ $filters.terms(item.categories) }}
            </template>
            <template v-else>
              {{ $t('_global.not_applicable_long') }}
            </template>
          </template>
          <template #[`item.is_confirmatory_testing`]="{ item }">
            <template v-if="item.is_confirmatory_testing !== null">
              {{ $filters.yesno(item.is_confirmatory_testing) }}
            </template>
            <template v-else>
              {{ $t('_global.not_applicable_long') }}
            </template>
          </template>
          <template #[`item.indications`]="{ item }">
            <template v-if="item.indications && item.indications.length">
              {{ $filters.names(item.indications) }}
            </template>
            <template v-else>
              {{ $t('_global.not_applicable_long') }}
            </template>
          </template>
          <template #[`item.activity_groups`]="{ item }">
            <template
              v-if="item.activity_groups && item.activity_groups.length"
            >
              {{ $filters.names(item.activity_groups) }}
            </template>
            <template v-else>
              {{ $t('_global.not_applicable_long') }}
            </template>
          </template>
          <template #[`item.activity_subgroups`]="{ item }">
            <template
              v-if="item.activity_subgroups && item.activity_subgroups.length"
            >
              {{ $filters.names(item.activity_subgroups) }}
            </template>
            <template v-else>
              {{ $t('_global.not_applicable_long') }}
            </template>
          </template>
          <template #[`item.activities`]="{ item }">
            <template v-if="item.activities && item.activities.length">
              {{ $filters.names(item.activities) }}
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
              :data-cy="$t('StudyFootnoteForm.copy_template')"
              icon="mdi-content-copy"
              color="primary"
              :title="$t('StudyFootnoteForm.copy_template')"
              variant="text"
              @click="selectFootnoteTemplate(item)"
            />
          </template>
        </NNTable>
      </v-col>
    </template>
    <template #[`step.createTemplate`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <NNTemplateInputField
          v-model="templateForm.name"
          :data-cy="$t('FootnoteTemplateForm.name')"
          :label="$t('FootnoteTemplateForm.name')"
          :items="parameterTypes"
          :rules="[formRules.required]"
          :show-drop-down-early="true"
        />
      </v-form>
    </template>
    <template #[`step.createFootnote`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-progress-circular
          v-if="loadingParameters"
          indeterminate
          color="secondary"
        />

        <template v-if="form.footnote_template !== undefined">
          <ParameterValueSelector
            ref="paramSelector"
            :model-value="parameters"
            :template="form.footnote_template.name"
            color="white"
            preview-text=" "
          />
        </template>
      </v-form>
    </template>
  </HorizontalStepperForm>
</template>

<script>
import { computed } from 'vue'
import instances from '@/utils/instances'
import statuses from '@/constants/statuses'
import footnoteConstants from '@/constants/footnotes'
import footnoteTemplates from '@/api/footnoteTemplates'
import templatePreInstances from '@/api/templatePreInstances'
import templateParameterTypes from '@/api/templateParameterTypes'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter.vue'
import NNTable from '@/components/tools/NNTable.vue'
import NNTemplateInputField from '@/components/tools/NNTemplateInputField.vue'
import ParameterValueSelector from '@/components/tools/ParameterValueSelector.vue'
import study from '@/api/study'
import StudySelectionTable from './StudySelectionTable.vue'
import terms from '@/api/controlledTerminology/terms'
import filteringParameters from '@/utils/filteringParameters'
import constants from '@/constants/libraries'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useFootnotesStore } from '@/stores/studies-footnotes'

export default {
  components: {
    HorizontalStepperForm,
    NNParameterHighlighter,
    NNTable,
    NNTemplateInputField,
    ParameterValueSelector,
    StudySelectionTable,
  },
  inject: ['eventBusEmit', 'formRules'],
  props: {
    currentStudyFootnotes: {
      type: Array,
      default: () => [],
    },
    selectedElements: {
      type: Object,
      default: null,
    },
  },
  emits: ['close', 'added'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    const footnotesStore = useFootnotesStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
      footnotesStore,
    }
  },
  data() {
    return {
      apiEndpoint: null,
      helpItems: [],
      creationMode: 'template',
      extraStudyFootnoteFilters: {
        footnote_template: { v: [] },
        'footnote.status': { v: [statuses.FINAL] },
      },
      footnoteType: null,
      form: {},
      templateForm: {},
      loadingParameters: false,
      parameters: [],
      parameterTypes: [],
      alternateSteps: [
        {
          name: 'creationMode',
          title: this.$t('StudyFootnoteForm.creation_mode_label'),
        },
        {
          name: 'selectFootnote',
          title: this.$t('StudyFootnoteForm.select_footnote'),
        },
      ],
      scratchModeSteps: [
        {
          name: 'creationMode',
          title: this.$t('StudyFootnoteForm.creation_mode_label'),
        },
        {
          name: 'createTemplate',
          title: this.$t('StudyFootnoteForm.create_footnote_title'),
        },
        {
          name: 'createFootnote',
          title: this.$t('StudyFootnoteForm.step2_title'),
        },
      ],
      preInstanceMode: true,
      selectionHeaders: [
        { title: '', key: 'actions', width: '1%' },
        {
          title: this.$t('_global.template'),
          key: 'name',
          class: 'text-center',
        },
      ],
      selectedStudies: [],
      selectedStudyFootnotes: [],
      selectedTemplates: [],
      steps: this.getInitialSteps(),
      studies: [],
      templates: [],
      tplHeaders: [
        { title: '', key: 'actions', width: '1%' },
        {
          title: this.$t('_global.order_short'),
          key: 'sequence_id',
          width: '5%',
        },
        {
          title: this.$t('_global.template'),
          key: 'name',
          filteringName: 'name_plain',
        },
        {
          title: this.$t('FootnoteTemplateTable.indications'),
          key: 'indications',
        },
        {
          title: this.$t('ActivityTemplateTable.activity_group'),
          key: 'activity_groups',
        },
        {
          title: this.$t('ActivityTemplateTable.activity_subgroup'),
          key: 'activity_subgroups',
        },
        {
          title: this.$t('ActivityTemplateTable.activity_name'),
          key: 'activities',
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
          title: this.$t('StudyActivity.activity_group'),
          key: 'activity.activity_group.name',
        },
        {
          title: this.$t('StudyActivity.activity_sub_group'),
          key: 'activity.activity_subgroup.name',
        },
        { title: this.$t('StudyActivity.activity'), key: 'activity.name' },
      ],
      footnoteHeaders: [
        { title: '', key: 'actions', width: '1%' },
        { title: this.$t('Study.study_id'), key: 'study_id', noFilter: true },
        {
          title: this.$t('StudyFootnoteForm.study_footnote'),
          key: 'footnote.name',
          filteringName: 'footnote.name_plain',
        },
      ],
      selectedFootnoteHeaders: [
        { title: '', key: 'actions', width: '1%' },
        { title: this.$t('Study.study_id'), key: 'study_id' },
        {
          title: this.$t('StudyFootnoteForm.study_footnote'),
          key: 'footnote.name',
        },
      ],
      loadingContinue: false,
      total: 0,
    }
  },
  computed: {
    title() {
      return this.$t('StudyFootnoteForm.add_title')
    },
    selectedTemplateName() {
      return this.form.footnote_template ? this.form.footnote_template.name : ''
    },
  },
  watch: {
    creationMode(value) {
      if (value === 'template') {
        this.steps = this.getInitialSteps()
        this.getFootnoteTemplates()
      } else if (value === 'select') {
        this.steps = this.alternateSteps
      } else {
        this.steps = this.scratchModeSteps
      }
    },
    preInstanceMode(value) {
      this.apiEndpoint = value ? this.preInstanceApi : footnoteTemplates
      this.getFootnoteTemplates()
      this.selectedTemplates = []
    },
    footnoteType() {
      this.getFootnoteTemplates()
    },
  },
  created() {
    this.preInstanceApi = templatePreInstances('footnote')
    this.apiEndpoint = this.preInstanceApi
  },
  mounted() {
    templateParameterTypes.getTypes().then((resp) => {
      this.parameterTypes = resp.data
    })
    study.get({ has_study_footnote: true, page_size: 0 }).then((resp) => {
      this.studies = resp.data.items.filter(
        (study) => study.uid !== this.selectedStudy.uid
      )
    })
    terms.getByCodelist('footnoteTypes').then((resp) => {
      for (const type of resp.data.items) {
        if (
          type.name.sponsor_preferred_name ===
          footnoteConstants.FOOTNOTE_TYPE_SOA
        ) {
          this.footnoteType = type
          break
        }
      }
    })
  },
  methods: {
    close() {
      this.creationMode = 'template'
      this.form = {}
      this.templateForm = {}
      this.parameters = []
      this.selectedStudyFootnotes = []
      this.selectedStudies = []
      this.apiEndpoint = this.preInstanceApi
      this.$emit('close')
      this.$refs.stepper.reset()
    },
    getObserver(step) {
      return this.$refs[`observer_${step}`]
    },
    getInitialSteps() {
      return [
        {
          name: 'creationMode',
          title: this.$t('StudyFootnoteForm.creation_mode_label'),
        },
        {
          name: 'selectTemplates',
          title: this.$t('StudyFootnoteForm.select_tpl_title'),
        },
      ]
    },
    getFootnoteTemplates(filters, options, filtersUpdated) {
      if (this.footnoteType) {
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
        Object.assign(params.filters, {
          'library.name': { v: [constants.LIBRARY_SPONSOR] },
        })
        if (this.preInstanceMode) {
          params.filters.template_type_uid = {
            v: [this.footnoteType.term_uid],
          }
        } else {
          params.filters['type.name.sponsor_preferred_name'] = {
            v: [this.footnoteType.name.sponsor_preferred_name],
          }
        }
        this.apiEndpoint.get(params).then((resp) => {
          this.templates = resp.data.items
          this.total = resp.data.total
        })
      }
    },
    async loadParameters(template) {
      if (template) {
        if (this.cloneMode) {
          const parameters =
            this.$refs.paramSelector.getTemplateParametersFromTemplate(
              template.name_plain
            )
          if (parameters.length === this.parameters.length) {
            let differ = false
            for (let index = 0; index < parameters.length; index++) {
              if (parameters[index] !== this.parameters[index].name) {
                differ = true
                break
              }
            }
            if (!differ) {
              return
            }
          }
        }
        this.loadingParameters = true
        const templateUid =
          this.creationMode !== 'scratch' && this.preInstanceMode
            ? template.template_uid
            : template.uid
        const resp = await this.apiEndpoint.getParameters(templateUid, {
          study_uid: this.selectedStudy.uid,
        })
        this.parameters = resp.data
        this.loadingParameters = false
      } else {
        this.parameters = []
      }
    },
    selectFootnoteTemplate(template) {
      if (!this.selectedTemplates.some((el) => el.uid === template.uid)) {
        this.selectedTemplates.push(template)
      }
    },
    unselectTemplate(template) {
      this.selectedTemplates = this.selectedTemplates.filter(
        (item) => item.name !== template.name
      )
    },
    selectStudyFootnote(studyFootnote) {
      this.selectedStudyFootnotes.push(studyFootnote)
    },
    unselectStudyFootnote(studyFootnote) {
      this.selectedStudyFootnotes = this.selectedStudyFootnotes.filter(
        (item) => item.footnote.name !== studyFootnote.footnote.name
      )
    },
    isStudyFootnoteSelected(studyFootnote) {
      let selected = this.selectedStudyFootnotes.find(
        (item) => item.footnote.uid === studyFootnote.footnote.uid
      )
      if (!selected && this.currentStudyFootnotes.length) {
        selected = this.currentStudyFootnotes.find((item) =>
          item.footnote
            ? item.footnote.uid === studyFootnote.uid
            : item.template.uid === studyFootnote.uid
        )
      }
      return selected !== undefined
    },
    getCopyButtonColor(item) {
      return !this.isStudyFootnoteSelected(item) ? 'primary' : ''
    },
    async extraStepValidation(step) {
      if (this.creationMode === 'template' && step === 1) {
        this.getFootnoteTemplates()
      }
      if (this.creationMode === 'template' && step === 2) {
        if (
          this.form.footnote_template === undefined ||
          this.form.footnote_template === null
        ) {
          this.eventBusEmit('notification', {
            msg: this.$t('StudyFootnoteForm.template_not_selected'),
            type: 'error',
          })
          return false
        }
        return true
      }
      if (this.creationMode !== 'scratch' || step !== 2) {
        return true
      }
      if (
        this.form.footnote_template &&
        this.form.footnote_template.name === this.templateForm.name
      ) {
        return true
      }
      const data = {
        ...this.templateForm,
        studyUid: this.selectedStudy.uid,
        library_name: constants.LIBRARY_USER_DEFINED,
        type_uid: this.footnoteType.term_uid,
      }
      try {
        this.loadingContinue = true
        const resp = await footnoteTemplates.create(data)
        if (resp.data.status === statuses.DRAFT)
          await footnoteTemplates.approve(resp.data.uid)
        this.form.footnote_template = resp.data
        this.loadingContinue = false
      } catch (error) {
        this.loadingContinue = false
        return false
      }
      this.loadParameters(this.form.footnote_template)
      return true
    },
    async getStudyFootnoteNamePreview() {
      const footnoteData = {
        footnote_template_uid: this.form.footnote.footnote_template.uid,
        parameter_terms: await instances.formatParameterValues(this.parameters),
        library_name: this.form.footnote_template
          ? this.form.footnote_template.library.name
          : this.form.footnote.library.name,
      }
      const resp = await study.getStudyFootnotePreview(this.selectedStudy.uid, {
        footnote_data: footnoteData,
      })
      return resp.data.footnote.name
    },
    async submit() {
      let args = null
      if (this.creationMode === 'template') {
        if (!this.selectedTemplates.length) {
          this.eventBusEmit('notification', {
            msg: this.$t('EligibilityCriteriaForm.no_template_error'),
            type: 'error',
          })
          this.$refs.stepper.loading = false
          return
        }
        const data = []
        for (const template of this.selectedTemplates) {
          data.push({
            footnote_data: {
              footnote_template_uid: this.preInstanceMode
                ? template.template_uid
                : template.uid,
              parameter_terms: this.preInstanceMode
                ? template.parameter_terms
                : [],
              library_name: template.library.name,
            },
            referenced_items: this.selectedElements.referenced_items,
          })
        }
        await study.batchCreateStudyFootnotes(this.selectedStudy.uid, data)
      } else if (this.creationMode === 'scratch') {
        const data = JSON.parse(JSON.stringify(this.form))
        if (this.preInstanceMode && this.creationMode !== 'scratch') {
          data.footnote_template.uid = data.footnote_template.template_uid
        }
        args = {
          studyUid: this.selectedStudy.uid,
          form: data,
          parameters: this.parameters,
          referencedItems: this.selectedElements.referenced_items,
        }
        await this.footnotesStore.addStudyFootnoteFromTemplate(args)
      } else {
        for (const item of this.selectedStudyFootnotes) {
          args = {
            studyUid: this.selectedStudy.uid,
            footnoteUid: item.footnote.uid,
            referencedItems: this.selectedElements.referenced_items,
          }
          await this.footnotesStore.selectFromStudyFootnote(args)
        }
      }
      this.$emit('added')
      this.eventBusEmit('notification', {
        msg: this.$t('StudyFootnoteForm.footnote_added'),
      })
      this.close()
    },
  },
}
</script>
<style scoped>
.header-title {
  color: rgb(var(--v-theme-secondary)) !important;
  font-size: large;
}
</style>
