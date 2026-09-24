<template>
  <SimpleFormDialog
    ref="form"
    :title="title"
    :help-items="helpItems"
    :open="open"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <div class="d-flex align-center">
        <div class="text-secondary text-headline-small">
          {{ $t('_global.template') }}
        </div>
        <v-btn
          v-if="!editTemplate"
          color="primary"
          icon="mdi-pencil-outline"
          :title="$t('StudySelectionEditForm.edit_syntax')"
          class="ml-4"
          variant="text"
          @click="editTemplate = true"
        />
        <v-btn
          v-if="editTemplate"
          icon="mdi-content-save-outline"
          color="success"
          class="ml-4"
          :loading="savingTemplate"
          :title="$t('StudySelectionEditForm.save_syntax')"
          variant="text"
          @click="saveTemplate"
        />
        <v-btn
          v-if="editTemplate"
          icon="mdi-close"
          :loading="savingTemplate"
          :title="$t('StudySelectionEditForm.cancel_modifications')"
          variant="text"
          @click="editTemplate = false"
        />
      </div>
      <v-form v-if="editTemplate" ref="observer_1">
        <v-alert density="compact" type="info">
          {{ templateEditWarning }}
        </v-alert>
        <div class="text-secondary text-h8">
          {{ $t('_global.name') }}
        </div>
        <NNTemplateInputField
          v-model="templateForm.name"
          :label="$t('ObjectiveTemplateForm.name')"
          :items="parameterTypes"
          :show-drop-down-early="true"
        />
        <div v-if="templateForm.guidance_text">
          <div class="text-secondary text-h8 mt-2">
            {{ $t('CriteriaTemplateForm.guidance_text') }}
          </div>
          <div class="pa-4 bg-parameterBackground rounded">
            <NNParameterHighlighter
              :name="templateForm.guidance_text"
              default-color="orange"
              :tooltip="false"
            />
          </div>
        </div>
      </v-form>
      <v-card v-else flat class="bg-parameterBackground">
        <v-card-text>
          <div class="text-secondary text-h8">
            {{ $t('_global.name') }}
          </div>
          <NNParameterHighlighter
            :name="templateForm.name"
            default-color="orange"
            :tooltip="false"
          />
          <div v-if="templateForm.guidance_text">
            <div class="text-secondary text-h8">
              {{ $t('CriteriaTemplateForm.guidance_text') }}
            </div>
            <NNParameterHighlighter
              :name="templateForm.guidance_text"
              default-color="orange"
              :tooltip="false"
            />
          </div>
        </v-card-text>
      </v-card>
      <v-form ref="observer_2">
        <div class="mt-6">
          <v-progress-circular
            v-if="loadingParameters"
            indeterminate
            color="secondary"
          />

          <template v-else>
            <ParameterValueSelector
              ref="paramSelector"
              v-model="parameters"
              :template="templateName"
              color="white"
              stacked
              :max-template-length="maxTemplateLength"
              :disabled="editTemplate"
              :with-unformatted-version="withUnformattedVersion"
              :unformatted-label="$t('StudySelectionEditForm.unformatted_text')"
            />
          </template>
        </div>
      </v-form>
      <slot name="formFields" :edit-template="editTemplate" :form="form" />
    </template>
  </SimpleFormDialog>
</template>

<script>
import { computed } from 'vue'
import constants from '@/constants/libraries'
import statuses from '@/constants/statuses'
import libraryObjects from '@/api/libraryObjects'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter.vue'
import NNTemplateInputField from '@/components/tools/NNTemplateInputField.vue'
import ParameterValueSelector from '@/components/tools/ParameterValueSelector.vue'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import templateParameters from '@/utils/templateParameters'
import templateParameterTypes from '@/api/templateParameterTypes'
import templates from '@/api/templates'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import instances from '@/utils/instances'

export default {
  components: {
    NNParameterHighlighter,
    NNTemplateInputField,
    ParameterValueSelector,
    SimpleFormDialog,
  },
  inject: ['formRules'],
  props: {
    title: {
      type: String,
      default: '',
    },
    studySelection: {
      type: Object,
      default: undefined,
    },
    template: {
      type: Object,
      default: undefined,
    },
    libraryName: {
      type: String,
      default: '',
    },
    objectType: {
      type: String,
      default: '',
    },
    getObjectFromSelection: {
      type: Function,
      default: undefined,
    },
    open: Boolean,
    withUnformattedVersion: {
      type: Boolean,
      default: true,
    },
    prepareTemplatePayloadFunc: {
      type: Function,
      required: false,
      default: undefined,
    },
    maxTemplateLength: {
      type: Boolean,
      default: null,
    },
  },
  emits: ['close', 'initForm', 'submit'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
    }
  },
  data() {
    return {
      editTemplate: false,
      form: { template: {} },
      helpItems: [],
      loadingParameters: false,
      newTemplate: null,
      parameters: [],
      parameterTypes: [],
      savingTemplate: false,
      steps: [
        {
          name: 'editSyntax',
          title: this.$t('StudySelectionEditForm.edit_syntax'),
        },
        {
          name: 'editValues',
          title: this.$t('StudySelectionEditForm.edit_values'),
        },
      ],
      templateForm: {},
    }
  },
  computed: {
    templateName() {
      return this.newTemplate
        ? this.newTemplate.name
        : this.template
          ? this.template.name
          : ''
    },
    apiEndpoint() {
      if (this.objectType !== 'criteria') {
        return libraryObjects(`/${this.objectType}s`)
      }
      return libraryObjects(`/${this.objectType}`)
    },
    templateApi() {
      return templates(`/${this.objectType}-templates`)
    },
    templateEditWarning() {
      if (this.newTemplate) {
        return this.$t('StudySelectionEditForm.edit_user_tpl_warning')
      }
      if (
        this.studySelection &&
        this.libraryName === constants.LIBRARY_USER_DEFINED
      ) {
        return this.$t('StudySelectionEditForm.edit_user_tpl_warning')
      }
      return this.$t('StudySelectionEditForm.edit_parent_tpl_warning')
    },
  },
  watch: {
    template: {
      handler(newValue) {
        if (newValue) {
          this.templateForm = { ...newValue }
          this.$emit('initForm', this.form)
          this.loadParameters()
        } else {
          this.templateForm = {}
        }
      },
      immediate: true,
    },
    editTemplate(value) {
      if (value) {
        this.$refs.form.disableActions()
      } else {
        this.$refs.form.enableActions()
      }
    },
  },
  mounted() {
    templateParameterTypes.getTypes().then((resp) => {
      this.parameterTypes = resp.data
    })
  },
  methods: {
    close() {
      this.form = { template: {} }
      this.templateForm = {}
      this.parameters = []
      if (this.$refs.observer_1) {
        this.$refs.observer_1.reset()
      }
      this.$refs.observer_2.reset()
      this.editTemplate = false
      this.$refs.form.working = false
      this.$emit('close')
    },
    compareParameters(oldTemplate, newTemplate) {
      const oldParams =
        templateParameters.getTemplateParametersFromTemplate(oldTemplate)
      const newParams =
        templateParameters.getTemplateParametersFromTemplate(newTemplate)
      if (oldParams.length === newParams.length) {
        let differ = false
        for (let index = 0; index < oldParams.length; index++) {
          if (oldParams[index] !== newParams[index]) {
            differ = true
            break
          }
        }
        if (!differ) {
          return true
        }
      }
      return false
    },
    cleanName(value) {
      const result = value.replace(/^<p>/, '')
      return result.replace(/<\/p>$/, '')
    },
    async saveTemplate() {
      const { valid } = await this.$refs.observer_1.validate()
      if (!valid) {
        this.$refs.form.working = false
        return
      }
      this.savingTemplate = true
      const cleanedName = this.cleanName(this.templateForm.name)
      const cleanedOriginalName = this.cleanName(this.template.name)
      if (
        (!this.newTemplate && cleanedName !== cleanedOriginalName) ||
        (this.newTemplate && this.templateForm.name !== this.newTemplate.name)
      ) {
        const data = { ...this.templateForm, studyUid: this.selectedStudy.uid }
        data.library_name = constants.LIBRARY_USER_DEFINED
        if (this.prepareTemplatePayloadFunc) {
          this.prepareTemplatePayloadFunc(data)
        }
        try {
          const resp = await this.templateApi.create(data)
          if (resp.data.status === statuses.DRAFT)
            await this.templateApi.approve(resp.data.uid)
          this.newTemplate = resp.data
          if (
            !this.compareParameters(
              this.template.name_plain,
              this.newTemplate.name_plain
            )
          ) {
            this.loadParameters(true)
          }
        } catch (_error) {
          return
        } finally {
          this.savingTemplate = false
          this.editTemplate = false
        }
      }
    },
    showParametersFromObject(object) {
      this.apiEndpoint.getObjectParameters(object.uid).then((resp) => {
        this.parameterResponse = resp.data

        const parameters = []
        resp.data.forEach((value) => {
          if (value.format) {
            parameters.push(...value.parameters)
          } else {
            parameters.push(value)
          }
        })
        this.apiEndpoint.getObject(object.uid).then((resp) => {
          instances.loadParameterValues(resp.data.parameter_terms, parameters)
          this.parameters = parameters
        })
      })
    },
    loadParameters(forceLoading) {
      if (this.parameters.length && !forceLoading) {
        return
      }
      this.loadingParameters = true
      const templateUid = this.newTemplate
        ? this.newTemplate.uid
        : this.template.uid
      try {
        this.templateApi
          .getParameters(templateUid, { study_uid: this.selectedStudy.uid })
          .then((resp) => {
            if (this.parameters.length) {
              resp.data.forEach((param, index) => {
                if (this.parameters.length) {
                  const found = this.parameters?.find(
                    (el) => el.name === param.name
                  )
                  const foundParam = found
                    ? JSON.parse(JSON.stringify(found))
                    : null
                  if (foundParam) {
                    resp.data[index] = foundParam
                    const foundParamIndex = this.parameters.findIndex(
                      (param) => param.name === foundParam.name
                    )
                    this.parameters.splice(foundParamIndex, 1)
                  }
                }
              })
            }
            this.parameters = resp.data
            this.loadingParameters = false
            const instance = this.getObjectFromSelection(this.studySelection)
            if (!forceLoading && instance) {
              this.showParametersFromObject(instance)
            }
          })
      } catch (error) {
        console.error(error)
      }
    },
    async submit() {
      const { valid } = await this.$refs.observer_2.validate()
      if (!valid) {
        this.$refs.form.working = false
        return
      }
      this.$refs.form.working = true
      this.$emit('submit', this.newTemplate, this.form, this.parameters)
    },
  },
}
</script>
