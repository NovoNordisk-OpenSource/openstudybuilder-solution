<template>
  <v-card color="dfltBackground">
    <v-card-title class="d-flex align-center">
      <span class="dialog-title">{{ getTitle() }}</span>
      <HelpButtonWithPanels :title="$t('_global.help')" :items="helpItems" />
    </v-card-title>
    <v-card-text class="mt-4">
      <v-form ref="observer">
        <v-row>
          <v-col cols="12">
            <div class="pa-6 bg-white">
              <NNTemplateInputField
                v-model="form.name"
                :items="parameterTypes"
                :show-drop-down-early="true"
                :label="$t(translationObject + '.name')"
                :rules="[formRules.required]"
              />
            </div>
          </v-col>
        </v-row>
        <slot name="extraFields" :form="form" />
        <v-row v-if="template">
          <v-col cols="12">
            <v-textarea
              v-model="form.change_description"
              :label="$t('HistoryTable.change_description')"
              rows="1"
              clearable
              auto-grow
              class="bg-white pa-5"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>

        <v-expansion-panels
          v-if="withClassificationAttributes"
          v-model="panel"
          flat
          class="mt-6"
        >
          <v-expansion-panel>
            <v-expansion-panel-title>
              {{ $t('GenericTemplateForm.template_properties') }}
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <NotApplicableField
                :clean-function="updateIndicationsNA"
                :checked="template && !template.indications"
              >
                <template #mainField="{ notApplicable }">
                  <MultipleSelect
                    v-model="form.indications"
                    :label="$t('GenericTemplateForm.study_indication')"
                    data-cy="template-indication-dropdown"
                    :items="indications"
                    return-object
                    item-title="name"
                    item-value="termUid"
                    :disabled="notApplicable"
                    :rules="[
                      (value) =>
                        formRules.requiredIfNotNA(value, notApplicable),
                    ]"
                  />
                </template>
              </NotApplicableField>
              <slot name="templateFields" :form="form" />
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-form>
    </v-card-text>
    <v-card-actions class="pb-6 px-6">
      <v-spacer />
      <v-btn
        class="secondary-btn"
        color="white"
        data-cy="cancel-button"
        variant="elevated"
        @click="cancel"
      >
        {{ $t('_global.cancel') }}
      </v-btn>
      <v-btn
        class="secondary-btn"
        color="white"
        data-cy="verify-syntax-button"
        variant="elevated"
        @click="verifySyntax"
      >
        {{ $t('_global.verify_syntax') }}
      </v-btn>
      <v-btn
        color="secondary"
        data-cy="save-button"
        variant="elevated"
        :loading="loading"
        @click="submit"
      >
        {{ $t('_global.save') }}
      </v-btn>
    </v-card-actions>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  </v-card>
</template>

<script>
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import dictionaries from '@/api/dictionaries'
import libraries from '@/api/libraries'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import MultipleSelect from '@/components/tools/MultipleSelect.vue'
import NNTemplateInputField from '@/components/tools/NNTemplateInputField.vue'
import NotApplicableField from '@/components/tools/NotApplicableField.vue'
import statuses from '@/constants/statuses'
import templatesApi from '@/api/templates'
import templateParameterTypes from '@/api/templateParameterTypes'
import { useFormStore } from '@/stores/form'

export default {
  components: {
    HelpButtonWithPanels,
    MultipleSelect,
    NNTemplateInputField,
    NotApplicableField,
    ConfirmDialog,
  },
  inject: ['notificationHub', 'formRules'],
  props: {
    template: {
      type: Object,
      default: null,
    },
    urlPrefix: {
      type: String,
      default: '',
    },
    translationType: {
      type: String,
      default: '',
    },
    objectType: {
      type: String,
      default: '',
    },
    withClassificationAttributes: {
      type: Boolean,
      default: true,
    },
    openClassificationAttributes: {
      type: Boolean,
      default: false,
    },
    loadFormFunction: {
      type: Function,
      default: null,
      required: false,
    },
    preparePayloadFunction: {
      type: Function,
      default: null,
      required: false,
    },
    getHelpFunction: {
      type: Function,
      default: null,
    },
    title: {
      type: String,
      default: null,
      required: false,
    },
    typeUid: {
      type: String,
      default: null,
    },
  },
  emits: ['close', 'templateAdded', 'templateUpdated'],
  setup() {
    const formStore = useFormStore()
    return {
      formStore,
    }
  },
  data() {
    return {
      api: null,
      form: this.getInitialFormContent(),
      libraries: [],
      loading: false,
      panel: null,
      parameterTypes: [],
      indications: [],
    }
  },
  computed: {
    translationObject() {
      return this.translationType.replace('Table', 'Form')
    },
    helpItems() {
      const items = [
        `${this.translationObject}.name`,
        'GenericTemplateForm.study_indication',
      ]
      if (this.getHelpFunction) {
        return items.concat(this.getHelpFunction())
      }
      return items
    },
  },
  watch: {
    template: {
      handler: function (value) {
        if (value) {
          if (!this.api) {
            this.api = templatesApi(this.urlPrefix)
          }
          this.api.getTemplate(value.uid).then((resp) => {
            this.loadFormFromTemplate(resp.data)
          })
        }
      },
      immediate: true,
    },
  },
  created() {
    if (!this.api) {
      this.api = templatesApi(this.urlPrefix)
    }
    libraries.getEditable().then((resp) => {
      this.libraries = resp.data
    })
    this.loadParameterTypes()
    if (this.openClassificationAttributes) {
      this.panel = 0
    }
  },
  mounted() {
    if (this.template) {
      this.loadFormFromTemplate()
    }
    dictionaries.getCodelists('SNOMED').then((resp) => {
      /* FIXME: we need a direct way to retrieve the terms here */
      dictionaries
        .getTerms({ codelist_uid: resp.data.items[0].codelist_uid })
        .then((resp) => {
          this.indications = resp.data.items
        })
    })
  },
  methods: {
    getInitialFormContent() {
      return {
        library: {
          name: 'Sponsor',
        },
      }
    },
    getTitle() {
      if (this.title) {
        return this.title
      }
      return this.template
        ? this.$t(this.translationObject + '.edit_title')
        : this.$t(this.translationObject + '.add_title')
    },
    loadParameterTypes() {
      templateParameterTypes.getTypes().then((resp) => {
        this.parameterTypes = resp.data
      })
    },
    addTemplate() {
      const data = { ...this.form }
      data.library_name = data.library?.name
      delete data.library
      if (this.typeUid) {
        data.type_uid = this.typeUid
      }
      if (data.indications && data.indications.length > 0) {
        data.indication_uids = data.indications.map((item) => item.term_uid)
      }
      if (this.preparePayloadFunction) {
        this.preparePayloadFunction(data)
      }
      return this.api.create(data).then(() => {
        this.$emit('templateAdded')
        this.notificationHub.add({
          msg: this.$t(this.translationObject + '.add_success'),
        })
        this.close()
      })
    },
    updateIndicationsNA(value) {
      if (value) {
        this.form.indications = null
      }
    },
    injectParameter(parameter) {
      if (this.form.name === undefined) {
        this.form.name = ''
      }
      this.form.name = this.form.name + ` [${parameter.name}]`
    },
    updateTemplate() {
      const data = { ...this.form }
      if (data.indications && data.indications.length > 0) {
        data.indication_uids = data.indications.map((item) => item.term_uid)
        delete data.indications
      }
      if (this.preparePayloadFunction) {
        this.preparePayloadFunction(data)
      }
      return this.api.update(this.template.uid, data).then((resp) => {
        this.$emit('templateUpdated', resp.data)
        this.notificationHub.add({
          msg: this.$t(this.translationObject + '.update_success'),
        })
        this.close()
      })
    },
    async submit() {
      const { valid } = await this.$refs.observer.validate()
      if (!valid) {
        return
      }

      this.notificationHub.clearErrors()

      this.loading = true
      try {
        if (!this.template) {
          await this.addTemplate()
        } else {
          await this.updateTemplate()
        }
      } catch (error) {
        if (error.response.status === 403) {
          this.$refs.observer.setErrors({ name: [error.response.data.message] })
        }
      } finally {
        this.loading = false
      }
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
          await this.$refs.confirm.open(
            this.$t('_global.cancel_changes'),
            options
          )
        ) {
          this.close()
        }
      }
    },
    close() {
      this.notificationHub.clearErrors()
      this.form = this.getInitialFormContent()
      this.formStore.reset()
      this.$refs.observer.reset()
      this.$emit('close')
    },
    verifySyntax() {
      if (!this.form.name) {
        return
      }
      const data = { name: this.form.name }
      this.api.preValidate(data).then(() => {
        this.notificationHub.add({
          msg: this.$t('_global.valid_syntax'),
        })
      })
    },
    /**
     * Do a step by step loading of the form using the given template because we don't want to include every fields.
     */
    loadFormFromTemplate(template) {
      this.form = {
        name: template ? template.name : null,
        library: template ? template.library : { name: 'Sponsor' },
        indications: template ? template.indications : null,
      }
      if (template.status === statuses.DRAFT) {
        this.form.change_description = this.$t('_global.work_in_progress')
      }
      if (this.loadFormFunction) {
        this.loadFormFunction(this.form)
      } else {
        this.formStore.save(this.form)
      }
    },
  },
}
</script>

<style scoped>
.v-expansion-panel-header {
  font-size: 1.1rem !important;
}
</style>
