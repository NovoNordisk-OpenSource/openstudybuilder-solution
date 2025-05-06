<template>
  <HorizontalStepperForm
    ref="stepper"
    :title="title"
    :help-items="helpItems"
    :steps="steps"
    :form-observer-getter="getObserver"
    :form-url="formUrl"
    :editable="isEdit()"
    :save-from-any-step="isEdit()"
    @close="close"
    @save="submit"
  >
    <template #[`step.form`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-card elevation="4" class="mx-auto pa-4">
          <div class="text-h5 mb-4">
            {{ $t('CRFForms.definition') }}
          </div>
          <v-row>
            <v-col cols="7">
              <v-text-field
                v-model="form.name"
                :label="$t('CRFItemGroups.name') + '*'"
                data-cy="item-group-name"
                density="compact"
                clearable
                :readonly="readOnly"
                :rules="[formRules.required]"
              />
            </v-col>
            <v-col cols="5">
              <v-text-field
                v-model="form.oid"
                :label="$t('CRFItemGroups.oid')"
                data-cy="item-group-oid"
                density="compact"
                clearable
                :readonly="readOnly"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="2">
              <v-radio-group
                v-model="form.repeating"
                class="mt-2"
                :label="$t('CRFItemGroups.repeating')"
                :readonly="readOnly"
              >
                <v-radio :label="$t('_global.yes')" value="Yes" />
                <v-radio :label="$t('_global.no')" value="No" />
              </v-radio-group>
            </v-col>
            <v-col cols="5">
              <div class="subtitle-2 text--disabled">
                {{ $t('_global.description') }}
              </div>
              <div v-show="readOnly">
                <QuillEditor
                  v-model:content="engDescription.description"
                  content-type="html"
                  :toolbar="customToolbar"
                  :options="quillOptions"
                />
              </div>
              <div v-show="!readOnly">
                <QuillEditor
                  v-model:content="engDescription.description"
                  content-type="html"
                  :toolbar="customToolbar"
                  :placeholder="$t('_global.description')"
                />
              </div>
            </v-col>
            <v-col cols="5">
              <div class="subtitle-2 text--disabled">
                {{ $t('CRFItemGroups.impl_notes') }}
              </div>
              <div v-show="readOnly">
                <QuillEditor
                  v-model:content="engDescription.sponsor_instruction"
                  content-type="html"
                  :toolbar="customToolbar"
                  data-cy="crf-item-group-help-for-sponsor"
                  :options="quillOptions"
                />
              </div>
              <div v-show="!readOnly">
                <QuillEditor
                  v-model:content="engDescription.sponsor_instruction"
                  content-type="html"
                  :toolbar="customToolbar"
                  :placeholder="$t('CRFItemGroups.impl_notes')"
                  data-cy="crf-item-group-help-for-sponsor"
                />
              </div>
            </v-col>
          </v-row>
        </v-card>
        <v-card elevation="4" class="mx-auto mt-3 pa-4">
          <div class="text-h5 mb-4">
            {{ $t('CRFForms.display') }}
          </div>
          <v-row>
            <v-col cols="3">
              <v-text-field
                v-model="engDescription.name"
                :label="$t('CRFForms.displayed_text')"
                data-cy="crf-item-group-displayed-text"
                density="compact"
                clearable
                :readonly="readOnly"
              />
            </v-col>
            <v-col cols="9">
              <div class="subtitle-2 text--disabled">
                {{ $t('CRFItemGroups.compl_instructions') }}
              </div>
              <div v-show="readOnly">
                <QuillEditor
                  v-model:content="engDescription.instruction"
                  content-type="html"
                  :toolbar="customToolbar"
                  data-cy="crf-item-group-help-for-site"
                  :options="quillOptions"
                />
              </div>
              <div v-show="!readOnly">
                <QuillEditor
                  v-model:content="engDescription.instruction"
                  content-type="html"
                  :toolbar="customToolbar"
                  :placeholder="$t('CRFItemGroups.compl_instructions')"
                  data-cy="crf-item-group-help-for-site"
                />
              </div>
            </v-col>
          </v-row>
        </v-card>
        <v-card elevation="4" class="mx-auto mt-3 pa-4">
          <div class="text-h5 mb-4">
            {{ $t('CRFForms.annotations') }}
          </div>
          <v-row>
            <v-col cols="6">
              <v-select
                v-model="form.sdtm_domain_uids"
                :label="$t('CRFItemGroups.domain')"
                data-cy="item-group-domain"
                :items="domains"
                :item-title="getDomainDisplay"
                item-value="term_uid"
                density="compact"
                clearable
                multiple
                :readonly="readOnly"
              >
                <template #selection="{ index }">
                  <div v-if="index === 0">
                    <span>{{ getFirstDomainDisplay() }}</span>
                  </div>
                  <span v-if="index === 1" class="grey--text text-caption mr-1">
                    (+{{ form.sdtm_domain_uids.length - 1 }})
                  </span>
                </template>
              </v-select>
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model="form.sas_dataset_name"
                :label="$t('CRFItemGroups.sas_dataset')"
                data-cy="item-group-sas-dataset-name"
                density="compact"
                clearable
                :readonly="readOnly"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="2">
              <v-radio-group
                v-model="form.is_reference_data"
                class="mt-2"
                :label="$t('CRFItemGroups.is_referential')"
                :readonly="readOnly"
              >
                <v-radio :label="$t('_global.yes')" value="Yes" />
                <v-radio :label="$t('_global.no')" value="No" />
              </v-radio-group>
            </v-col>
            <v-col cols="4">
              <v-select
                v-model="form.origin"
                :label="$t('CRFItemGroups.origin')"
                data-cy="item-group-origin"
                :items="origins"
                item-title="nci_preferred_name"
                item-value="nci_preferred_name"
                density="compact"
                clearable
                :readonly="readOnly"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="6">
              <v-text-field
                v-model="form.purpose"
                :label="$t('CRFItemGroups.purpose')"
                data-cy="item-group-purpose"
                density="compact"
                clearable
                :readonly="readOnly"
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model="form.comment"
                :label="$t('CRFItemGroups.comment')"
                data-cy="item-group-comment"
                density="compact"
                clearable
                :readonly="readOnly"
              />
            </v-col>
          </v-row>
        </v-card>
      </v-form>
    </template>
    <template #[`step.extensions`]>
      <CrfExtensionsManagementTable
        type="ItemGroupDef"
        :read-only="readOnly"
        :edit-extensions="selectedExtensions"
        @set-extensions="setExtensions"
      />
    </template>
    <template #[`step.alias`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <div class="mb-5">
          {{ $t('CRFItemGroups.create') }}
        </div>
        <v-row>
          <v-col>
            <v-text-field
              v-model="alias.context"
              :label="$t('CRFItemGroups.context')"
              data-cy="item-group-alias-context"
              density="compact"
              clearable
              :readonly="readOnly"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="10">
            <v-text-field
              v-model="alias.name"
              :label="$t('CRFItemGroups.name')"
              data-cy="item-group-alias-name"
              density="compact"
              clearable
              :readonly="readOnly"
            />
          </v-col>
          <v-col>
            <v-btn
              data-cy="save-button"
              color="secondary"
              class="mr-2"
              :disabled="readOnly"
              @click="createAlias"
            >
              {{ $t('_global.save') }}
            </v-btn>
          </v-col>
        </v-row>
        <div class="mb-5">
          {{ $t('CRFItemGroups.select') }}
        </div>
        <v-select
          v-model="form.alias_uids"
          :items="aliases"
          multiple
          :label="$t('CRFItemGroups.aliases')"
          density="compact"
          clearable
          :item-title="getAliasDisplay"
          item-value="uid"
          :error-messages="errors"
          :readonly="readOnly"
        >
          <template #selection="{ item, index }">
            <div v-if="index === 0" data-cy="item-group-selected-alias">
              <span>{{ item.title }}</span>
            </div>
            <span v-if="index === 1" class="grey--text text-caption">
              (+{{ form.alias_uids.length - 1 }})
            </span>
          </template>
        </v-select>
      </v-form>
    </template>
    <template #[`step.description`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <CrfDescriptionTable
          :edit-descriptions="desc"
          :read-only="readOnly"
          @set-desc="setDesc"
        />
      </v-form>
    </template>
    <template #[`step.change_description`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.change_description"
              :label="$t('CRFForms.change_desc')"
              data-cy="item-group-change-description"
              clearable
              :readonly="readOnly"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #actions>
      <ActionsMenu v-if="selectedGroup" :actions="actions" :item="form" />
    </template>
  </HorizontalStepperForm>
  <CrfActivitiesModelsLinkForm
    :open="linkForm"
    :item-to-link="selectedGroup"
    item-type="itemGroup"
    @close="closeLinkForm"
  />
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
</template>

<script>
import crfs from '@/api/crfs'
import terms from '@/api/controlledTerminology/terms'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import libraries from '@/constants/libraries'
import CrfDescriptionTable from '@/components/library/crfs/CrfDescriptionTable.vue'
import { QuillEditor } from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import CrfActivitiesModelsLinkForm from '@/components/library/crfs/CrfActivitiesModelsLinkForm.vue'
import actions from '@/constants/actions'
import parameters from '@/constants/parameters'
import CrfExtensionsManagementTable from '@/components/library/crfs/CrfExtensionsManagementTable.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import crfTypes from '@/constants/crfTypes'
import { useAppStore } from '@/stores/app'
import { computed } from 'vue'

export default {
  components: {
    HorizontalStepperForm,
    CrfDescriptionTable,
    QuillEditor,
    ActionsMenu,
    CrfActivitiesModelsLinkForm,
    CrfExtensionsManagementTable,
    ConfirmDialog,
  },
  inject: ['eventBusEmit', 'formRules'],
  props: {
    selectedGroup: {
      type: Object,
      default: null,
    },
    readOnlyProp: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['updateItemGroup', 'close', 'linkGroup'],
  setup() {
    const appStore = useAppStore()

    return {
      userData: computed(() => appStore.userData),
    }
  },
  data() {
    return {
      helpItems: [
        'CRFItemGroups.name',
        'CRFItemGroups.oid',
        'CRFItemGroups.repeating',
        'CRFItemGroups.description',
        'CRFItemGroups.impl_notes',
        'CRFItemGroups.displayed_text',
        'CRFItemGroups.compl_instructions',
        'CRFItemGroups.aliases',
        'CRFItemGroups.context',
      ],
      form: {
        oid: 'G.',
        repeating: 'No',
        isReferenceData: 'No',
        alias_uids: [],
        sdtm_domain_uids: [],
      },
      desc: [],
      aliases: [],
      alias: {},
      steps: [],
      selectedExtensions: [],
      createSteps: [
        { name: 'form', title: this.$t('CRFItemGroups.group_details') },
        {
          name: 'extensions',
          title: this.$t('CRFForms.vendor_extensions'),
        },
        {
          name: 'description',
          title: this.$t('CRFItemGroups.description_details'),
        },
        { name: 'alias', title: this.$t('CRFItemGroups.alias_details') },
      ],
      editSteps: [
        { name: 'form', title: this.$t('CRFItemGroups.group_details') },
        {
          name: 'extensions',
          title: this.$t('CRFForms.vendor_extensions'),
        },
        {
          name: 'description',
          title: this.$t('CRFItemGroups.description_details'),
        },
        { name: 'alias', title: this.$t('CRFItemGroups.alias_details') },
        { name: 'change_description', title: this.$t('CRFForms.change_desc') },
      ],
      origins: [],
      domains: [],
      engDescription: { library_name: 'Sponsor', language: parameters.ENG },
      customToolbar: [
        ['bold', 'italic', 'underline'],
        [{ script: 'sub' }, { script: 'super' }],
        [{ list: 'ordered' }, { list: 'bullet' }],
      ],
      quillOptions: {
        readOnly: true,
      },
      readOnly: this.readOnlyProp,
      linkForm: false,
      actions: [
        {
          label: this.$t('_global.approve'),
          icon: 'mdi-check-decagram',
          iconColor: 'success',
          condition: () => !this.readOnly,
          click: this.approve,
        },
        {
          label: this.$t('_global.new_version'),
          icon: 'mdi-plus-circle-outline',
          iconColor: 'primary',
          condition: () => this.readOnly,
          click: this.newVersion,
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete-outline',
          iconColor: 'error',
          condition: (item) =>
            item.possible_actions
              ? item.possible_actions.find(
                  (action) => action === actions.DELETE
                )
              : false,
          click: this.delete,
        },
        {
          label: this.$t('CrfLinikingForm.link_activity_sub_groups'),
          icon: 'mdi-plus',
          iconColor: 'primary',
          condition: () => this.readOnly,
          click: this.openLinkForm,
        },
      ],
    }
  },
  computed: {
    title() {
      return this.isEdit()
        ? this.readOnly
          ? this.$t('CRFItemGroups.item_group') + ' - ' + this.form.name
          : this.$t('CRFItemGroups.edit_group') + ' - ' + this.form.name
        : this.$t('CRFItemGroups.add_group')
    },
    formUrl() {
      if (this.isEdit()) {
        return `${window.location.href.replace('crf-tree', 'item-groups')}/item-group/${this.selectedGroup.uid}`
      }
      return null
    },
  },
  watch: {
    readOnlyProp(value) {
      this.readOnly = value
    },
    userData: {
      handler() {
        if (!this.userData.multilingual) {
          this.steps = this.steps.filter(function (obj) {
            return obj.name !== 'description'
          })
        } else {
          this.steps = this.createSteps
        }
      },
    },
    selectedGroup: {
      handler(value) {
        if (this.isEdit()) {
          this.steps = this.readOnly ? this.createSteps : this.editSteps
          this.initForm(value)
        } else {
          this.steps = this.createSteps
        }
        if (!this.userData.multilingual) {
          this.steps = this.steps.filter(function (obj) {
            return obj.name !== 'description'
          })
        }
      },
      immediate: true,
    },
  },
  mounted() {
    terms.getAttributesByCodelist('originType').then((resp) => {
      this.origins = resp.data.items
    })
    terms.getAttributesByCodelist('sdtmDomainAbbreviation').then((resp) => {
      this.domains = resp.data.items.sort(function (a, b) {
        return a.nci_preferred_name.localeCompare(b.nci_preferred_name)
      })
    })
    crfs.getAliases().then((resp) => {
      this.aliases = resp.data.items
    })
    if (this.isEdit()) {
      this.steps = this.readOnly ? this.createSteps : this.editSteps
    } else {
      this.steps = this.createSteps
    }
    if (!this.userData.multilingual) {
      this.steps = this.steps.filter(function (obj) {
        return obj.name !== 'description'
      })
    }
  },
  methods: {
    getGroup() {
      crfs.getItemGroup(this.selectedGroup.uid).then((resp) => {
        this.initForm(resp.data)
      })
    },
    openLinkForm() {
      this.linkForm = true
    },
    closeLinkForm() {
      this.linkForm = false
      this.getGroup()
    },
    async newVersion() {
      let relationships = 0
      await crfs
        .getRelationships(this.selectedGroup.uid, 'item-groups')
        .then((resp) => {
          if (resp.data.OdmForm && resp.data.OdmForm.length > 0) {
            relationships = resp.data.OdmForm.length
          }
        })
      const options = {
        type: 'warning',
        cancelLabel: this.$t('_global.cancel'),
        agreeLabel: this.$t('_global.continue'),
      }
      if (
        relationships > 1 &&
        (await this.$refs.confirm.open(
          `${this.$t('CRFForms.new_version_warning')}`,
          options
        ))
      ) {
        crfs.newVersion('item-groups', this.selectedGroup.uid).then((resp) => {
          this.$emit('updateItemGroup', {
            type: crfTypes.GROUP,
            element: resp.data,
          })
          this.readOnly = false
          this.getGroup()
        })
      } else if (relationships <= 1) {
        crfs.newVersion('item-groups', this.selectedGroup.uid).then((resp) => {
          this.$emit('updateItemGroup', {
            type: crfTypes.GROUP,
            element: resp.data,
          })
          this.readOnly = false
          this.getGroup()
        })
      }
    },
    approve() {
      crfs.approve('item-groups', this.selectedGroup.uid).then(() => {
        this.readOnly = true
        this.getGroup()
      })
    },
    async delete() {
      let relationships = 0
      await crfs
        .getRelationships(this.selectedGroup.uid, 'item-groups')
        .then((resp) => {
          if (resp.data.OdmForm && resp.data.OdmForm.length > 0) {
            relationships = resp.data.OdmForm.length
          }
        })
      const options = {
        type: 'warning',
        cancelLabel: this.$t('_global.cancel'),
        agreeLabel: this.$t('_global.continue'),
      }
      if (
        relationships > 0 &&
        (await this.$refs.confirm.open(
          `${this.$t('CRFItemGroups.delete_warning_1')} ${relationships} ${this.$t('CRFItemGroups.delete_warning_2')}`,
          options
        ))
      ) {
        crfs.delete('item-groups', this.selectedGroup.uid).then(() => {
          this.$emit('close')
        })
      } else if (relationships === 0) {
        crfs.delete('item-groups', this.selectedGroup.uid).then(() => {
          this.$emit('close')
        })
      }
    },
    setDesc(desc) {
      this.desc = desc
    },
    getDomainDisplay(item) {
      return `${item.nci_preferred_name} (${item.code_submission_value})`
    },
    getFirstDomainDisplay() {
      if (
        this.domains.find((el) => el.term_uid === this.form.sdtm_domain_uids[0])
      ) {
        return this.domains.find(
          (el) => el.term_uid === this.form.sdtm_domain_uids[0]
        ).nci_preferred_name
      }
    },
    getObserver(step) {
      return this.$refs[`observer_${step}`]
    },
    close() {
      this.form = {
        oid: 'G.',
        repeating: 'No',
        isReferenceData: 'No',
        alias_uids: [],
        sdtm_domain_uids: [],
      }
      this.desc = []
      this.selectedExtensions = []
      this.engDescription = {
        library_name: 'Sponsor',
        language: parameters.ENG,
      }
      this.$refs.stepper.reset()
      this.$emit('close')
    },
    async submit() {
      if (this.readOnly) {
        this.close()
        return
      }
      await this.createOrUpdateDescription()
      this.form.library_name = libraries.LIBRARY_SPONSOR
      if (this.form.oid === 'G.') {
        this.form.oid = null
      }
      try {
        if (this.isEdit()) {
          this.form.alias_uids = this.form.alias_uids.map((alias) =>
            alias.uid ? alias.uid : alias
          )
          await crfs
            .updateItemGroup(this.form, this.selectedGroup.uid)
            .then(async () => {
              await this.linkExtensions(this.selectedGroup.uid)
              this.eventBusEmit('notification', {
                msg: this.$t('CRFItemGroups.group_updated'),
              })
              this.close()
            })
        } else {
          await crfs.createItemGroup(this.form).then(async (resp) => {
            await this.linkExtensions(resp.data.uid)
            this.eventBusEmit('notification', {
              msg: this.$t('CRFItemGroups.group_created'),
            })
            this.$emit('linkGroup', resp)
            this.close()
          })
        }
      } finally {
        this.$refs.stepper.loading = false
      }
    },
    setExtensions(extensions) {
      this.selectedExtensions = extensions
    },
    async linkExtensions(uid) {
      let elements = []
      let attributes = []
      let eleAttributes = []
      this.selectedExtensions = this.selectedExtensions.filter((ex) => {
        return ex.library_name
      })
      this.selectedExtensions.forEach((ex) => {
        if (ex.type) {
          attributes.push(ex)
        } else {
          elements.push(ex)
          if (ex.vendor_attributes) {
            eleAttributes = [...eleAttributes, ...ex.vendor_attributes]
          }
        }
      })
      const data = {
        elements: elements,
        element_attributes: eleAttributes,
        attributes: attributes,
      }
      await crfs.setExtensions('item-groups', uid, data)
    },
    async createAlias() {
      this.alias.library_name = libraries.LIBRARY_SPONSOR
      await crfs.createAlias(this.alias).then((resp) => {
        this.form.alias_uids.push(resp.data.uid)
        crfs.getAliases().then((resp) => {
          this.aliases = resp.data.items
          this.alias = {}
          this.eventBusEmit('notification', {
            msg: this.$t('CRFItemGroups.alias_created'),
          })
        })
      })
    },
    async createOrUpdateDescription() {
      const descArray = []
      this.desc.forEach((e) => {
        if (e.uid) {
          e.change_description = this.$t(
            'CRFItemGroups.description_change_description'
          )
          descArray.push(e)
        } else {
          e.library_name = libraries.LIBRARY_SPONSOR
          descArray.push(e)
        }
      })
      if (!this.engDescription.name) {
        this.engDescription.name = this.form.name
      }
      this.engDescription.change_description = this.$t(
        'CRFItemGroups.description_change_description'
      )
      descArray.push(this.engDescription)
      this.form.descriptions = descArray
    },
    async initForm(item) {
      this.form = item
      this.form.alias_uids = item.aliases
      this.form.sdtm_domain_uids = item.sdtm_domains.map((el) => el.uid)
      this.form.change_description = this.$t('_global.draft_change')
      if (item.descriptions.find((el) => el.language === parameters.ENG)) {
        this.engDescription = item.descriptions.find(
          (el) => el.language === parameters.ENG
        )
      }
      this.desc = item.descriptions.filter(
        (el) => el.language !== parameters.ENG
      )
      item.vendor_attributes.forEach((attr) => (attr.type = 'attr'))
      this.selectedExtensions = [
        ...item.vendor_attributes,
        ...item.vendor_element_attributes,
        ...item.vendor_elements,
      ]
    },
    getAliasDisplay(item) {
      return `${item.context} - ${item.name}`
    },
    isEdit() {
      if (this.selectedGroup) {
        return Object.keys(this.selectedGroup).length !== 0
      }
      return false
    },
  },
}
</script>
