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
            <v-col cols="6">
              <v-text-field
                v-model="form.name"
                :label="$t('CRFItems.name') + '*'"
                data-cy="item-name"
                :rules="[formRules.required]"
                density="compact"
                clearable
                :readonly="readOnly"
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model="form.oid"
                :label="$t('CRFItems.oid')"
                data-cy="item-oid"
                density="compact"
                clearable
                :readonly="readOnly"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="4">
              <v-select
                v-model="form.datatype"
                :label="$t('CRFItems.data_type') + '*'"
                data-cy="item-data-type"
                :items="dataTypes"
                item-title="code_submission_value"
                item-value="code_submission_value"
                :rules="[formRules.required]"
                density="compact"
                clearable
                class="mt-3"
                :readonly="readOnly"
                @update:model-value="checkIfNumeric()"
              />
            </v-col>
            <v-col v-if="lengthFieldCheck" cols="4">
              <v-text-field
                v-if="form.datatype !== crfTypes.COMMENT"
                v-model="form.length"
                :label="$t('CRFItems.length')"
                data-cy="item-length"
                density="compact"
                clearable
                class="mt-3"
                type="number"
                :readonly="readOnly"
              />
            </v-col>
            <v-col v-if="digitsFieldCheck" cols="4">
              <v-text-field
                v-model="form.significant_digits"
                :label="$t('CRFItems.significant_digits')"
                data-cy="item-significant-digits"
                density="compact"
                clearable
                class="mt-3"
                type="number"
                :readonly="readOnly"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="6">
              <div class="subtitle-2 text--disabled">
                {{ $t('_global.description') }}
              </div>
              <div v-show="readOnly">
                <QuillEditor
                  v-show="readOnly"
                  v-model:content="engDescription.description"
                  content-type="html"
                  :toolbar="customToolbar"
                  :disabled="readOnly"
                />
              </div>
              <div v-show="!readOnly">
                <QuillEditor
                  v-show="!readOnly"
                  v-model:content="engDescription.description"
                  content-type="html"
                  :toolbar="customToolbar"
                  :placeholder="$t('_global.description')"
                  :disabled="readOnly"
                />
              </div>
            </v-col>
            <v-col cols="6">
              <div class="subtitle-2 text--disabled">
                {{ $t('CRFItems.impl_notes') }}
              </div>
              <div v-show="readOnly">
                <QuillEditor
                  v-show="readOnly"
                  v-model:content="engDescription.sponsor_instruction"
                  content-type="html"
                  :toolbar="customToolbar"
                  :disabled="readOnly"
                />
              </div>
              <div v-show="!readOnly">
                <QuillEditor
                  v-show="!readOnly"
                  v-model:content="engDescription.sponsor_instruction"
                  content-type="html"
                  :toolbar="customToolbar"
                  :placeholder="$t('CRFItems.impl_notes')"
                  :disabled="readOnly"
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
                data-cy="form-oid-name"
                density="compact"
                clearable
                :readonly="readOnly"
              />
            </v-col>
            <v-col cols="9">
              <div class="subtitle-2 text--disabled">
                {{ $t('CRFItems.compl_instructions') }}
              </div>
              <div v-show="readOnly">
                <QuillEditor
                  v-show="readOnly"
                  v-model:content="engDescription.instruction"
                  content-type="html"
                  :toolbar="customToolbar"
                  :disabled="readOnly"
                />
              </div>
              <div v-show="!readOnly">
                <QuillEditor
                  v-show="!readOnly"
                  v-model:content="engDescription.instruction"
                  content-type="html"
                  :toolbar="customToolbar"
                  :placeholder="$t('CRFItems.compl_instructions')"
                  :disabled="readOnly"
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
              <v-text-field
                v-model="form.sas_field_name"
                :label="$t('CRFItems.sas_name')"
                data-cy="item-sas-name"
                density="compact"
                clearable
                :readonly="readOnly"
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model="form.sds_var_name"
                :label="$t('CRFItems.sds_name')"
                data-cy="item-sds-name"
                density="compact"
                clearable
                :readonly="readOnly"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col v-if="originFieldCheck" cols="4">
              <v-select
                v-model="form.origin"
                :label="$t('CRFItems.origin')"
                data-cy="item-origin"
                :items="origins"
                item-title="nci_preferred_name"
                item-value="nci_preferred_name"
                density="compact"
                clearable
                :readonly="readOnly"
              />
            </v-col>
            <v-col cols="8">
              <v-text-field
                v-model="form.comment"
                :label="$t('CRFItems.comment')"
                data-cy="item-comment"
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
        type="ItemDef"
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
              :label="$t('CRFItems.context')"
              data-cy="item-aliast-context"
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
              :label="$t('CRFItems.name')"
              data-cy="item-alias-name"
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
          data-cy="item-aliases"
          density="compact"
          clearable
          :item-title="getAliasDisplay"
          item-value="uid"
          :readonly="readOnly"
        >
          <template #selection="{ item, index }">
            <div v-if="index === 0">
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
    <template #[`step.codelist`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-data-table
          :headers="selectedCodelistHeaders"
          :items="selectedCodelists"
        >
          <template #[`item.allowsMultiChoice`]>
            <v-checkbox v-model="form.allows_multi_choice" />
          </template>
          <template #[`item.delete`]="{ item }">
            <v-btn
              icon="mdi-delete-outline"
              class="mt-1"
              :disabled="readOnly"
              @click="removeCodelist(item)"
            />
          </template>
        </v-data-table>
      </v-form>
    </template>
    <template #[`step.codelist.after`]>
      <v-col class="pt-0 mt-0">
        <NNTable
          v-model:options="options"
          :headers="codelistHeaders"
          item-value="uid"
          :items="codelists"
          :server-items-length="total"
          hide-export-button
          hide-default-switches
          column-data-resource="ct/codelists"
          @filter="fetchCodelists"
        >
          <template #afterFilter="">
            <v-autocomplete
              v-model="selectedFilteringTerms"
              v-model:search-input="search"
              :label="$t('CodelistTable.search_with_terms')"
              :items="filteringTerms"
              item-title="name.sponsor_preferred_name"
              item-value="term_uid"
              density="compact"
              class="mt-5 max-width-300"
              clearable
              return-object
              multiple
            >
              <template #selection="{ index }">
                <div v-if="index === 0">
                  <span class="items-font-size">{{
                    selectedFilteringTerms[0].name.sponsor_preferred_name.substring(
                      0,
                      12
                    )
                  }}</span>
                </div>
                <span v-if="index === 1" class="grey--text text-caption mr-1">
                  (+{{ selectedFilteringTerms.length - 1 }})
                </span>
              </template>
            </v-autocomplete>
            <v-select
              v-model="termsFilterOperator"
              :items="operators"
              :label="$t('_global.operator')"
              class="mt-5 max-width-100"
            />
          </template>
          <template #[`item.add`]="{ item }">
            <v-btn
              icon="mdi-plus"
              class="mt-1"
              :disabled="readOnly"
              @click="addCodelist(item)"
            />
          </template>
        </NNTable>
      </v-col>
    </template>
    <template #[`step.terms`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-data-table :headers="selectedTermsHeaders" :items="selectedTerms">
          <template #[`item.mandatory`]="{ item }">
            <v-checkbox v-model="item.mandatory" :readonly="readOnly" />
          </template>
          <template #[`item.display_text`]="{ item }">
            <v-text-field
              v-model="item.display_text"
              :readonly="readOnly"
              density="compact"
            />
          </template>
          <template #[`item.delete`]="{ item }">
            <v-btn
              icon="mdi-delete-outline"
              class="mt-1"
              variant="text"
              :disabled="readOnly"
              @click="removeTerm(item)"
            />
          </template>
        </v-data-table>
      </v-form>
    </template>
    <template #[`step.terms.after`]>
      <v-col class="pt-0 mt-0">
        <NNTable
          :headers="termsHeaders"
          item-value="uid"
          :items="terms"
          :items-length="totalTerms"
          hide-export-button
          only-text-search
          hide-default-switches
          @filter="getCodeListTerms"
        >
          <template #[`item.add`]="{ item }">
            <v-btn
              icon="mdi-plus"
              class="mt-1"
              variant="text"
              :disabled="
                readOnly ||
                selectedTerms.find((e) => e.term_uid === item.term_uid)
              "
              @click="addTerm(item)"
            />
          </template>
        </NNTable>
      </v-col>
    </template>
    <template #[`step.unit`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <NNTable
          :headers="unitHeaders"
          item-value="uid"
          disable-filtering
          :items="choosenUnits"
          hide-export-button
          hide-default-switches
        >
          <template #actions="">
            <v-btn
              class="ml-2"
              size="small"
              variant="outlined"
              color="nnBaseBlue"
              :label="$t('CRFItemGroups.new_translation')"
              :disabled="readOnly"
              icon="mdi-plus"
              @click.stop="addUnit"
            />
          </template>
          <template #[`item.name`]="{ index }">
            <v-autocomplete
              v-model="choosenUnits[index].name"
              :items="units"
              :label="$t('CRFItems.unit_name')"
              data-cy="item-unit-name"
              density="compact"
              class="mt-3"
              item-title="name"
              item-value="name"
              return-object
              :readonly="readOnly"
              @change="setUnit(index)"
            />
          </template>
          <template #[`item.mandatory`]="{ item }">
            <v-checkbox v-model="item.mandatory" :readonly="readOnly" />
          </template>
          <template #[`item.delete`]="{ index }">
            <v-btn
              icon="mdi-delete-outline"
              class="mt-n5"
              variant="text"
              :disabled="readOnly"
              @click="removeUnit(index)"
            />
          </template>
        </NNTable>
      </v-form>
    </template>
    <template #[`step.change_description`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.change_description"
              :label="$t('CRFItems.change_desc')"
              data-cy="item-change-description"
              :rules="[formRules.required]"
              clearable
              :readonly="readOnly"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #actions>
      <ActionsMenu v-if="selectedItem" :actions="actions" :item="form" />
    </template>
  </HorizontalStepperForm>
  <CrfActivitiesModelsLinkForm
    :open="linkForm"
    :item-to-link="selectedItem"
    item-type="item"
    @close="closeLinkForm"
  />
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
</template>

<script>
import crfs from '@/api/crfs'
import NNTable from '@/components/tools/NNTable.vue'
import terms from '@/api/controlledTerminology/terms'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import controlledTerminology from '@/api/controlledTerminology'
import constants from '@/constants/libraries'
import CrfDescriptionTable from '@/components/library/crfs/CrfDescriptionTable.vue'
import { QuillEditor } from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css'
import crfTypes from '@/constants/crfTypes'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import CrfActivitiesModelsLinkForm from '@/components/library/crfs/CrfActivitiesModelsLinkForm.vue'
import actions from '@/constants/actions'
import parameters from '@/constants/parameters'
import CrfExtensionsManagementTable from '@/components/library/crfs/CrfExtensionsManagementTable.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import { useAppStore } from '@/stores/app'
import { computed } from 'vue'
import { useUnitsStore } from '@/stores/units'
import filteringParameters from '@/utils/filteringParameters'

export default {
  components: {
    NNTable,
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
    selectedItem: {
      type: Object,
      default: null,
    },
    readOnlyProp: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['updateItem', 'close', 'linkItem'],
  setup() {
    const appStore = useAppStore()
    const unitsStore = useUnitsStore()

    return {
      fetchUnits: unitsStore.fetchUnits,
      userData: computed(() => appStore.userData),
      units: computed(() => unitsStore.units),
    }
  },
  data() {
    return {
      helpItems: [
        'CRFItems.name',
        'CRFItems.oid',
        'CRFItems.data_type',
        'CRFItems.length',
        'CRFItems.significant_digits',
        'CRFItems.impl_notes',
        'CRFItems.compl_instructions',
        'CRFItems.sas_name',
        'CRFItems.sds_name',
        'CRFItems.origin',
        'CRFItems.comment',
        'CRFItems.context',
        'CRFItems.name',
      ],
      form: {
        oid: 'I.',
        alias_uids: [],
      },
      desc: [],
      selectedExtensions: [],
      selectedCodelistHeaders: [
        { title: this.$t('CtCatalogueTable.concept_id'), key: 'codelist_uid' },
        { title: this.$t('CtCatalogueTable.cd_name'), key: 'attributes.name' },
        {
          title: this.$t('CtCatalogueTable.submission_value'),
          key: 'attributes.submission_value',
        },
        {
          title: this.$t('CtCatalogueTable.nci_pref_name'),
          key: 'attributes.nci_preferred_name',
        },
        {
          title: this.$t('CRFItems.multiple_choice'),
          key: 'allowsMultiChoice',
        },
        { title: '', key: 'delete' },
      ],
      codelistHeaders: [
        { title: this.$t('CtCatalogueTable.concept_id'), key: 'codelist_uid' },
        { title: this.$t('CtCatalogueTable.cd_name'), key: 'attributes.name' },
        {
          title: this.$t('CtCatalogueTable.submission_value'),
          key: 'attributes.submission_value',
        },
        {
          title: this.$t('CtCatalogueTable.nci_pref_name'),
          key: 'attributes.nci_preferred_name',
        },
        { title: '', key: 'add' },
      ],
      unitHeaders: [
        { title: this.$t('CRFItemGroups.name'), key: 'name', width: '25%' },
        { title: this.$t('CRFItems.sponsor_unit'), key: 'oid', width: '20%' },
        { title: this.$t('UnitTable.ucum_unit'), key: 'ucum' },
        { title: this.$t('UnitTable.ct_units'), key: 'terms', width: '30%' },
        { title: this.$t('_global.mandatory'), key: 'mandatory' },
        { title: '', key: 'delete' },
      ],
      termsHeaders: [
        { title: this.$t('CtCatalogueTable.concept_id'), key: 'term_uid' },
        { title: this.$t('_global.name'), key: 'name.sponsor_preferred_name' },
        { title: '', key: 'add' },
      ],
      selectedTermsHeaders: [
        {
          title: this.$t('CtCatalogueTable.concept_id'),
          key: 'term_uid',
          width: '10%',
        },
        {
          title: this.$t('CRFItems.sponsor_pref_name'),
          key: 'name',
          width: '40%',
        },
        { title: this.$t('_global.mandatory'), key: 'mandatory', width: '5%' },
        {
          title: this.$t('CRFItems.displayed_name'),
          key: 'display_text',
          width: '40%',
        },
        { title: '', key: 'delete', width: '1%' },
      ],
      aliases: [],
      alias: {},
      steps: [],
      createSteps: [
        { name: 'form', title: this.$t('CRFItems.item_details') },
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
        { name: 'form', title: this.$t('CRFItems.item_details') },
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
      choosenUnits: [{ name: '', mandatory: true }],
      codelists: [],
      selectedCodelists: [],
      options: {},
      total: 0,
      filters: '',
      dataTypes: [],
      descKey: 0,
      customToolbar: [
        ['bold', 'italic', 'underline'],
        [{ script: 'sub' }, { script: 'super' }],
        [{ list: 'ordered' }, { list: 'bullet' }],
      ],
      engDescription: {
        library_name: constants.LIBRARY_SPONSOR,
        language: parameters.ENG,
      },
      terms: [],
      selectedTerms: [],
      readOnly: this.readOnlyProp,
      linkForm: false,
      actions: [
        {
          label: this.$t('_global.approve'),
          icon: 'mdi-check-decagram',
          iconColor: 'success',
          condition: () => !this.readOnly,
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.approve,
        },
        {
          label: this.$t('_global.new_version'),
          icon: 'mdi-plus-circle-outline',
          iconColor: 'primary',
          condition: () => this.readOnly,
          accessRole: this.$roles.LIBRARY_WRITE,
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
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.delete,
        },
        {
          label: this.$t('CrfLinikingForm.link_activities'),
          icon: 'mdi-plus',
          iconColor: 'primary',
          condition: () => this.readOnly,
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.openLinkForm,
        },
      ],
      lengthFieldCheck: false,
      digitsFieldCheck: false,
      originFieldCheck: true,
      filteringTerms: [],
      selectedFilteringTerms: [],
      search: '',
      operators: ['or', 'and'],
      termsFilterOperator: 'or',
      totalTerms: 0,
    }
  },
  computed: {
    title() {
      return this.isEdit()
        ? this.readOnly
          ? this.$t('CRFItems.crf_item') + ' - ' + this.form.name
          : this.$t('CRFItems.edit_item') + ' - ' + this.form.name
        : this.$t('CRFItems.add_item')
    },
    formUrl() {
      if (this.isEdit()) {
        return `${window.location.href.replace('crf-tree', 'items')}/item/${this.selectedItem.uid}`
      }
      return null
    },
  },
  watch: {
    readOnlyProp(value) {
      this.readOnly = value
    },
    selectedCodelists() {
      this.getCodeListTerms()
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
    selectedItem: {
      handler(value) {
        if (this.isEdit()) {
          this.steps = this.readOnly ? this.createSteps : this.editSteps
          if (value.datatype.indexOf('STRING') !== -1) {
            this.steps.splice(1, 0, {
              name: 'codelist',
              title: this.$t('CRFItems.codelist_details'),
            })
            this.steps.splice(2, 0, {
              name: 'terms',
              title: this.$t('CRFItems.codelist_subset'),
            })
          }
          this.initForm(value)
        } else {
          this.steps = this.createSteps
        }
        if (!this.userData.multilingual) {
          this.steps = this.steps.filter(function (obj) {
            return obj.name !== 'description'
          })
        }
        const uniqueSteps = Array.from(
          new Set(this.steps.map((a) => a.name))
        ).map((name) => {
          return this.steps.find((a) => a.name === name)
        })
        this.steps = uniqueSteps
      },
      immediate: true,
    },
    options: {
      handler() {
        this.fetchCodelists()
      },
      deep: true,
    },
    search() {
      this.fetchTerms()
    },
    selectedFilteringTerms() {
      this.fetchCodelists()
    },
    termsFilterOperator() {
      this.fetchCodelists()
    },
  },
  created() {
    this.crfTypes = crfTypes
  },
  mounted() {
    this.fetchCodelists()
    terms.getAttributesByCodelist('originType').then((resp) => {
      this.origins = resp.data.items
    })
    terms.getAttributesByCodelist('dataType').then((resp) => {
      this.dataTypes = resp.data.items
    })
    crfs.getAliases().then((resp) => {
      this.aliases = resp.data.items
    })
    this.fetchUnits({ page_size: 0 })
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
    checkFieldAvailable(dataType) {
      this.lengthFieldCheck = false
      this.digitsFieldCheck = false
      this.originFieldCheck = true
      switch (dataType) {
        case 'BOOLEAN':
        case 'URI':
          break
        case 'COMMENT':
          this.originFieldCheck = false
          break
        case 'FLOAT':
        case 'DOUBLE':
        case 'HEXBINARY':
        case 'BASE64BINARY':
        case 'HEXFLOAT':
        case 'BASE64FLOAT':
          this.lengthFieldCheck = true
          this.digitsFieldCheck = true
          break
        case 'DATE':
          this.lengthFieldCheck = true
          this.form.length = 10
          break
        case 'TIME':
          this.lengthFieldCheck = true
          this.form.length = 5
          break
        case 'DATETIME':
          this.lengthFieldCheck = true
          this.form.length = 16
          break
        default:
          this.lengthFieldCheck = true
      }
    },
    getItem() {
      crfs.getItem(this.selectedItem.uid).then((resp) => {
        this.initForm(resp.data)
      })
    },
    openLinkForm() {
      this.linkForm = true
    },
    closeLinkForm() {
      this.linkForm = false
      this.getItem()
    },
    async newVersion() {
      let relationships = 0
      await crfs
        .getRelationships(this.selectedItem.uid, 'items')
        .then((resp) => {
          if (resp.data.OdmItemGroup && resp.data.OdmItemGroup.length > 0) {
            relationships = resp.data.OdmItemGroup.length
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
        crfs.newVersion('items', this.selectedItem.uid).then((resp) => {
          this.$emit('updateItem', { type: crfTypes.ITEM, element: resp.data })
          this.readOnly = false
          this.getItem()
        })
      } else if (relationships <= 1) {
        crfs.newVersion('items', this.selectedItem.uid).then((resp) => {
          this.$emit('updateItem', { type: crfTypes.ITEM, element: resp.data })
          this.readOnly = false
          this.getItem()
        })
      }
    },
    async approve() {
      crfs.approve('items', this.selectedItem.uid).then(() => {
        this.readOnly = true
        this.getItem()
      })
    },
    async delete() {
      let relationships = 0
      await crfs
        .getRelationships(this.selectedItem.uid, 'items')
        .then((resp) => {
          if (resp.data.OdmItemGroup && resp.data.OdmItemGroup.length > 0) {
            relationships = resp.data.OdmItemGroup.length
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
          `${this.$t('CRFItems.delete_warning_1')} ${relationships} ${this.$t('CRFItems.delete_warning_2')}`,
          options
        ))
      ) {
        crfs.delete('items', this.selectedItem.uid).then(() => {
          this.$emit('close')
        })
      } else if (relationships === 0) {
        crfs.delete('items', this.selectedItem.uid).then(() => {
          this.$emit('close')
        })
      }
    },
    setDesc(desc) {
      this.desc = desc
    },
    getObserver(step) {
      return this.$refs[`observer_${step}`]
    },
    checkIfNumeric() {
      if (this.form.datatype) {
        if (
          this.form.datatype.indexOf('INTEGER') !== -1 ||
          this.form.datatype.indexOf('FLOAT') !== -1 ||
          this.form.datatype.indexOf('DOUBLE') !== -1
        ) {
          this.steps.splice(1, 0, {
            name: 'unit',
            title: this.$t('CRFItems.unit_details'),
          })
          this.steps = this.steps.filter(function (obj) {
            return obj.name !== 'codelist' && obj.name !== 'terms'
          })
        } else if (this.form.datatype.indexOf('STRING') !== -1) {
          this.steps = this.steps.filter(function (obj) {
            return obj.name !== 'unit'
          })
          this.steps.splice(1, 0, {
            name: 'codelist',
            title: this.$t('CRFItems.codelist_details'),
          })
          this.steps.splice(2, 0, {
            name: 'terms',
            title: this.$t('CRFItems.codelist_subset'),
          })
        }
        if (
          this.form.datatype.indexOf('STRING') === -1 &&
          this.form.datatype.indexOf('TEXT') === -1
        ) {
          this.steps = this.steps.filter(function (obj) {
            return obj.name !== 'codelist' && obj.name !== 'terms'
          })
        }
        if (
          this.form.datatype.indexOf('INTEGER') === -1 &&
          this.form.datatype.indexOf('FLOAT') === -1 &&
          this.form.datatype.indexOf('DOUBLE') === -1
        ) {
          this.steps = this.steps.filter(function (obj) {
            return obj.name !== 'unit'
          })
        }
      } else {
        this.steps = this.steps.filter(function (obj) {
          return (
            obj.name !== 'unit' &&
            obj.name !== 'codelist' &&
            obj.name !== 'terms'
          )
        })
      }
      const uniqueSteps = Array.from(
        new Set(this.steps.map((a) => a.name))
      ).map((name) => {
        return this.steps.find((a) => a.name === name)
      })
      this.steps = uniqueSteps
      this.checkFieldAvailable(this.form.datatype)
    },
    close() {
      this.form = {
        oid: 'I.',
        alias_uids: [],
      }
      this.desc = []
      this.choosenUnits = [{ name: '', mandatory: true }]
      this.selectedCodelists = []
      this.selectedTerms = []
      this.selectedExtensions = []
      this.engDescription = {
        library_name: constants.LIBRARY_SPONSOR,
        language: parameters.ENG,
      }
      this.$refs.stepper.reset()
      this.$emit('close')
    },
    getCodeListTerms(filters, options, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      if (this.selectedCodelists[0]) {
        params.codelist_uid = this.selectedCodelists[0].codelist_uid
        terms.getTermsByCodelistUid(params).then((resp) => {
          this.terms = resp.data.items
          if (this.form.terms) {
            this.selectedTerms = this.form.terms
          }
          this.totalTerms = resp.data.total
        })
      } else {
        this.terms = []
      }
    },
    addTerm(item) {
      item.mandatory = true
      if (!this.selectedTerms.some((el) => el.term_uid === item.term_uid)) {
        const itemToAdd = Object.assign({}, item)
        itemToAdd.name = itemToAdd.name.sponsor_preferred_name
        this.selectedTerms.push(itemToAdd)
      }
    },
    removeTerm(item) {
      this.selectedTerms = this.selectedTerms.filter(
        (el) => el.term_uid !== item.term_uid
      )
    },
    async submit() {
      if (this.readOnly) {
        this.close()
        return
      }
      await this.createOrUpdateDescription()
      this.form.library_name = constants.LIBRARY_SPONSOR
      if (this.form.oid === 'I.') {
        this.form.oid = null
      }
      this.choosenUnits = this.choosenUnits.filter((el) => {
        return el.name !== ''
      })
      this.form.unit_definitions =
        this.choosenUnits.length === 0
          ? []
          : this.choosenUnits.map((e) => ({
              uid: e.uid ? e.uid : e.name.uid,
              mandatory: e.mandatory,
            }))
      if (this.form.datatype !== 'STRING') {
        this.form.codelist_uid = null
        this.form.terms = []
      } else {
        this.form.codelist_uid = this.selectedCodelists[0]
          ? this.selectedCodelists[0].codelist_uid
          : null
        this.form.terms = this.selectedTerms.map((el) => ({
          uid: el.term_uid,
          mandatory: el.mandatory,
          display_text: el.display_text,
        }))
      }
      try {
        if (this.isEdit()) {
          this.form.alias_uids = this.form.alias_uids.map((alias) =>
            alias.uid ? alias.uid : alias
          )
          await crfs
            .updateItem(this.form, this.selectedItem.uid)
            .then(async () => {
              await this.linkExtensions(this.selectedItem.uid)
              this.eventBusEmit('notification', {
                msg: this.$t('CRFItems.item_updated'),
              })
              this.close()
            })
        } else {
          await crfs.createItem(this.form).then(async (resp) => {
            await this.linkExtensions(resp.data.uid)
            this.eventBusEmit('notification', {
              msg: this.$t('CRFItems.item_created'),
            })
            this.$emit('linkItem', resp)
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
      await crfs.setExtensions('items', uid, data)
    },
    addUnit() {
      this.choosenUnits.push({ name: '', mandatory: true })
    },
    removeUnit(index) {
      this.choosenUnits.splice(index, 1)
    },
    setUnit(index) {
      this.choosenUnits[index].ucum = this.choosenUnits[index].name.ucum
        ? this.choosenUnits[index].name.ucum.name
        : ''
      this.choosenUnits[index].oid = this.choosenUnits[index].name.name
      this.choosenUnits[index].terms = this.choosenUnits[index].name.ct_units[0]
        ? this.choosenUnits[index].name.ct_units[0].name
        : ''
      this.choosenUnits[index].uid = this.choosenUnits[index].name.uid
    },
    async createAlias() {
      this.alias.library_name = constants.LIBRARY_SPONSOR
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
            'CRFItems.description_change_description'
          )
          descArray.push(e)
        } else {
          e.library_name = constants.LIBRARY_SPONSOR
          descArray.push(e)
        }
      })
      if (!this.engDescription.name) {
        this.engDescription.name = this.form.name
      }
      this.engDescription.change_description = this.$t(
        'CRFItems.description_change_description'
      )
      descArray.push(this.engDescription)
      this.form.descriptions = descArray
    },
    async initForm(item) {
      this.form = item
      this.form.alias_uids = item.aliases
      if (item.descriptions.find((el) => el.language === parameters.ENG)) {
        this.engDescription = item.descriptions.find(
          (el) => el.language === parameters.ENG
        )
      }
      this.desc = item.descriptions.filter(
        (el) => el.language !== parameters.ENG
      )
      if (!item.unit_definitions || item.unit_definitions.length === 0) {
        this.choosenUnits = []
      } else {
        item.unit_definitions.forEach((e) => {
          if (!this.choosenUnits.some((el) => el.uid === e.uid)) {
            this.choosenUnits.unshift({
              uid: e.uid,
              oid: e.name,
              name: e.name,
              ucum: e.ucum ? e.ucum.name : '',
              terms: e.ct_units[0] ? e.ct_units[0].name : '',
              mandatory: e.mandatory,
            })
          }
        })
      }
      if (this.selectedCodelists.length === 0 && item.codelist) {
        this.selectedCodelists.push({
          codelist_uid: item.codelist.uid,
          attributes: {
            name: item.codelist.name,
            submission_value: item.codelist.submission_value,
            nci_preferred_name: item.codelist.preferred_term,
          },
        })
      }
      this.form.change_description = this.$t('_global.draft_change')
      this.checkIfNumeric()
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
      if (this.selectedItem) {
        return Object.keys(this.selectedItem).length !== 0
      }
      return false
    },
    fetchCodelists(filters) {
      this.filters = filters
      if (this.filtersUpdated) {
        this.options.page = 1
      }
      const params = {
        page_number: this.options.page,
        page_size: this.options.itemsPerPage,
        total_count: true,
        library_name: this.library,
      }
      if (this.filters !== undefined) {
        params.filters = this.filters
      }
      if (this.selectedFilteringTerms.length > 0) {
        params.term_filter = {
          term_uids: this.selectedFilteringTerms.map((term) => term.term_uid),
          operator: this.termsFilterOperator,
        }
      }
      controlledTerminology.getCodelists(params).then((resp) => {
        this.codelists = resp.data.items.filter(
          (ar) =>
            !this.selectedCodelists.find(
              (rm) => rm.codelist_uid === ar.codelist_uid
            )
        )
        this.total = resp.data.total
      })
    },
    fetchTerms() {
      const params = {
        filters: {
          'name.sponsor_preferred_name': {
            v: [this.search ? this.search : ''],
            op: 'co',
          },
        },
        page_size: 20,
      }
      controlledTerminology.getCodelistTerms(params).then((resp) => {
        this.filteringTerms = [
          ...resp.data.items,
          ...this.selectedFilteringTerms,
        ]
      })
    },
    addCodelist(item) {
      if (this.selectedCodelists.length === 0) {
        this.selectedCodelists.push(item)
        this.codelists.splice(this.codelists.indexOf(item), 1)
      }
    },
    removeCodelist(item) {
      this.selectedCodelists = []
      this.codelists.unshift(item)
    },
  },
}
</script>
<style scoped>
.max-width-100 {
  max-width: 100px;
}
.max-width-300 {
  max-width: 300px;
}
</style>
