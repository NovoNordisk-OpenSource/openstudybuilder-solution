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
    :read-only="isReadOnly"
    @close="close"
    @save="submit"
  >
    <template #[`step.form`]="{ step }">
      <v-form :ref="`observer${step}`">
        <v-card elevation="1" class="mx-auto pa-4">
          <div class="text-headline-medium mb-4">
            {{ $t('CRFForms.definition') }}
          </div>
          <v-row v-if="showLibraryDropdown">
            <v-col>
              <v-select
                v-model="selectedLibraryName"
                :label="$t('CRFItems.library')"
                data-cy="crf-item-library"
                :items="editableLibraries"
                item-title="name"
                item-value="name"
                :disabled="isEdit() || !!props.libraryName"
                :rules="[formRules.required]"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="4">
              <v-text-field
                v-model="form.name"
                :label="$t('CRFItems.name') + '*'"
                data-cy="item-name"
                :rules="[formRules.required]"
                :clearable="!isReadOnly"
                :readonly="isReadOnly"
              />
            </v-col>
            <v-col cols="4">
              <v-text-field
                v-model="form.oid"
                :label="$t('CRFItems.oid')"
                data-cy="item-oid"
                :clearable="!isReadOnly"
                :readonly="isReadOnly"
              />
            </v-col>
            <v-col cols="4">
              <v-select
                v-model="form.datatype"
                :label="$t('CRFItems.data_type') + '*'"
                data-cy="item-data-type"
                :items="dataTypes"
                item-title="submission_value"
                item-value="term_uid"
                return-object
                :rules="[formRules.required]"
                :clearable="!isReadOnly"
                :readonly="isReadOnly"
                @update:model-value="checkIfNumeric()"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col v-if="lengthFieldCheck" cols="6">
              <v-text-field
                v-model="form.length"
                :label="$t('CRFItems.length')"
                data-cy="item-length"
                :rules="[lengthRequired]"
                :clearable="!isReadOnly"
                class="mt-3"
                type="number"
                :readonly="isReadOnly"
              />
            </v-col>
            <v-col v-if="digitsFieldCheck" cols="6">
              <v-text-field
                v-model="form.significant_digits"
                :label="$t('CRFItems.significant_digits')"
                data-cy="item-significant-digits"
                :rules="[significantDigitsRequired]"
                :clearable="!isReadOnly"
                class="mt-3"
                type="number"
                :readonly="isReadOnly"
              />
            </v-col>
          </v-row>
        </v-card>
        <v-card elevation="1" class="mx-auto mt-3 pa-4">
          <div class="text-headline-medium mb-4">
            {{ $t('CRFForms.annotations') }}
          </div>
          <v-row>
            <v-col cols="6">
              <v-text-field
                v-model="form.sas_field_name"
                :label="$t('CRFItems.sas_name')"
                data-cy="item-sas-name"
                :clearable="!isReadOnly"
                :readonly="isReadOnly"
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model="form.sds_var_name"
                :label="$t('CRFItems.sds_name')"
                data-cy="item-sds-name"
                :clearable="!isReadOnly"
                :readonly="isReadOnly"
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
                :clearable="!isReadOnly"
                :readonly="isReadOnly"
              />
            </v-col>
            <v-col cols="8">
              <v-text-field
                v-model="form.comment"
                :label="$t('CRFItems.comment')"
                data-cy="item-comment"
                :clearable="!isReadOnly"
                :readonly="isReadOnly"
              />
            </v-col>
          </v-row>
        </v-card>
      </v-form>
    </template>
    <template #[`step.translated_texts`]="{ step }">
      <v-form :ref="`observer${step}`">
        <CrfTranslatedTextSelection
          v-model="form.translated_texts"
          :read-only="isReadOnly"
        />
      </v-form>
    </template>
    <template #[`step.external_question`]="{ step }">
      <v-form :ref="`observer${step}`">
        <v-card elevation="1" class="mx-auto pa-4">
          <div class="text-headline-medium mb-4">
            {{ $t('CRFItems.external_question') }}
          </div>
          <v-row>
            <v-col cols="12">
              <v-autocomplete
                v-model="selectedExternalQuestionTerm"
                v-model:search="search"
                :label="$t('CRFItems.search_for_terms')"
                data-cy="item-external-question-term"
                :item-props="externalQuestionProps"
                :items="filteringTerms"
                :clearable="!isReadOnly"
                return-object
                :readonly="isReadOnly"
                hide-details
              >
                <template #no-data>
                  <v-list-item>
                    <v-list-item-title>
                      {{
                        !search
                          ? $t('_global.start_typing')
                          : $t('NNTable.no_data')
                      }}
                    </v-list-item-title>
                  </v-list-item>
                </template>
              </v-autocomplete>
            </v-col>
          </v-row>
          <v-row v-if="!_isEmpty(selectedExternalQuestionTerm)">
            <v-col cols="12">
              <v-radio-group
                v-model="selectedExternalQuestionCodelist"
                :label="$t('CRFItems.from_codelist')"
                :rules="[formRules.required]"
              >
                <v-radio
                  v-for="codelist in selectedExternalQuestionTerm.codelists"
                  :key="codelist.codelist_uid"
                  :label="codelist.codelist_name"
                  :value="codelist"
                >
                </v-radio>
              </v-radio-group>
            </v-col>
          </v-row>
        </v-card>
      </v-form>
    </template>
    <template #[`step.extensions`]>
      <CrfExtensionsManagementTable
        type="ItemDef"
        :read-only="isReadOnly"
        :edit-extensions="selectedExtensions"
        @set-extensions="setExtensions"
      />
    </template>
    <template #[`step.alias`]="{ step }">
      <v-form :ref="`observer${step}`">
        <CrfAliasSelection v-model="form.aliases" :read-only="isReadOnly" />
      </v-form>
    </template>
    <template #[`step.codelist`]="{ step }">
      <v-form :ref="`observer${step}`">
        <v-data-table
          height="135px"
          :headers="selectedCodelistHeaders"
          :items="selectedCodelists"
        >
          <template #[`item.allowsMultiChoice`]>
            <v-checkbox v-model="form.allows_multi_choice" class="mb-n4" />
          </template>
          <template #[`item.delete`]="{ item }">
            <v-btn
              icon="mdi-delete-outline"
              data-cy="remove-codelist"
              class="mt-1"
              size="small"
              variant="outlined"
              color="nnBaseBlue"
              :readonly="isReadOnly"
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
          table-id="crf-item-form-codelist"
          :headers="codelistHeaders"
          item-value="uid"
          :items="codelists"
          :server-items-length="total"
          hide-export-button
          hide-default-switches
          column-data-resource="ct/codelists"
          @filter="fetchCodelists"
        >
          <template #[`item.actions`]="{ item }">
            <v-btn
              icon="mdi-plus"
              data-cy="add-codelist"
              class="mt-1"
              size="small"
              variant="outlined"
              color="nnBaseBlue"
              :readonly="isReadOnly"
              @click="addCodelist(item)"
            />
          </template>
        </NNTable>
      </v-col>
    </template>
    <template #[`step.terms`]="{ step }">
      <v-form :ref="`observer${step}`">
        <v-data-table
          :headers="selectedTermsHeaders"
          :items="selectedTerms"
          hide-default-body
        >
          <template #tbody="{ items }">
            <tbody v-if="items.length > 0" ref="termsTable">
              <tr v-for="item in items" :key="item.term_uid">
                <td>
                  <v-icon
                    :style="isReadOnly ? '' : { cursor: 'pointer' }"
                    :readonly="isReadOnly"
                  >
                    mdi-arrow-up-down
                  </v-icon>
                </td>
                <td>{{ item.term_uid }}</td>
                <td v-if="isTermRemoved(item)" colspan="3">
                  <v-alert
                    variant="tonal"
                    type="warning"
                    icon="mdi-alert"
                    class="ma-0 pa-2"
                  >
                    {{
                      $t('CRFItems.disconnected_term', {
                        codelist: selectedCodelists[0]?.attributes?.name,
                      })
                    }}
                  </v-alert>
                </td>
                <td v-if="!isTermRemoved(item)">{{ item.name }}</td>
                <td v-if="!isTermRemoved(item)">
                  <v-checkbox v-model="item.mandatory" :readonly="isReadOnly" />
                </td>
                <td v-if="!isTermRemoved(item)">
                  <v-text-field
                    v-model="item.display_text"
                    :readonly="isReadOnly"
                  />
                </td>
                <td>
                  <v-btn
                    icon="mdi-delete-outline"
                    data-cy="remove-term"
                    class="mt-1"
                    variant="text"
                    :color="isTermRemoved(item) ? 'error' : ''"
                    :readonly="isReadOnly"
                    @click="removeTerm(item)"
                  />
                </td>
              </tr>
            </tbody>

            <tbody v-else>
              <tr>
                <td :colspan="selectedTermsHeaders.length" class="text-center">
                  {{ $t('CRFItems.no_terms_selected') }}
                </td>
              </tr>
            </tbody>
          </template>
        </v-data-table>
      </v-form>
    </template>
    <template #[`step.terms.after`]>
      <v-col class="pt-0 mt-0">
        <NNTable
          table-id="crf-item-form-terms"
          :headers="termsHeaders"
          item-value="uid"
          :items="termsList"
          :items-length="totalTerms"
          hide-export-button
          only-text-search
          :column-data-parameters="{ include_removed: false }"
          hide-default-switches
          @filter="getCodeListTerms"
        >
          <template #[`item.add`]="{ item }">
            <v-btn
              icon="mdi-plus"
              data-cy="add-term"
              class="mt-1"
              variant="text"
              :readonly="isReadOnly"
              :disabled="
                selectedTerms.find((e) => e.term_uid === item.term_uid)
              "
              @click="addTerm(item)"
            />
          </template>
        </NNTable>
      </v-col>
    </template>
    <template #[`step.unit`]="{ step }">
      <v-form :ref="`observer${step}`">
        <NNTable
          table-id="crf-item-form-unit"
          :headers="unitHeaders"
          item-value="uid"
          disable-filtering
          :items="chosenUnits"
          :items-length="chosenUnits.length"
          hide-export-button
          hide-default-switches
        >
          <template #actions="">
            <v-btn
              class="ml-2"
              data-cy="add-unit"
              icon
              size="small"
              variant="outlined"
              color="nnBaseBlue"
              :readonly="isReadOnly"
              @click.stop="addUnit"
            >
              <v-icon>mdi-plus</v-icon>
              <v-tooltip activator="parent" location="top">
                {{ $t('CRFItems.add_unit') }}
              </v-tooltip>
            </v-btn>
          </template>
          <template #[`item.name`]="{ index }">
            <v-autocomplete
              v-model="chosenUnits[index].name"
              :items="units"
              :label="$t('CRFItems.unit_name')"
              data-cy="item-unit-name"
              class="mt-3"
              item-title="name"
              item-value="name"
              return-object
              :readonly="isReadOnly"
              @update:model-value="setUnit(index)"
            />
          </template>
          <template #[`item.mandatory`]="{ item }">
            <v-checkbox v-model="item.mandatory" :readonly="isReadOnly" />
          </template>
          <template #[`item.delete`]="{ index }">
            <v-btn
              icon="mdi-delete-outline"
              class="mt-n5"
              data-cy="remove-unit"
              variant="text"
              :readonly="isReadOnly"
              @click="removeUnit(index)"
            />
          </template>
        </NNTable>
      </v-form>
    </template>
    <template #[`step.activity_instance_links`]="{ step }">
      <v-form :ref="`observer${step}`">
        <CrfActivityInstanceManagement
          v-model="form.activity_instances"
          :form-view="formView"
          :read-only="isReadOnly"
        />
      </v-form>
    </template>
    <template #[`step.change_description`]="{ step }">
      <v-form :ref="`observer${step}`">
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.change_description"
              :label="$t('CRFItems.change_desc')"
              data-cy="item-change-description"
              :rules="[formRules.required]"
              :clearable="!isReadOnly"
              :readonly="isReadOnly"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #actions>
      <ActionsMenu
        v-if="selectedItem && checkPermission($roles.LIBRARY_WRITE)"
        :actions="actions"
        :item="form"
      />
    </template>
  </HorizontalStepperForm>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  <CrfApprovalSummaryConfirmDialog ref="confirmApproval" />
  <CrfNewVersionSummaryConfirmDialog ref="confirmNewVersion" />
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useI18n } from 'vue-i18n'
import crfs from '@/api/crfs'
import codelistApi from '@/api/controlledTerminology/codelists'
import NNTable from '@/components/tools/NNTable.vue'
import terms from '@/api/controlledTerminology/terms'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import controlledTerminology from '@/api/controlledTerminology'
import CrfAliasSelection from '@/components/library/crfs/CrfAliasSelection.vue'
import CrfTranslatedTextSelection from '@/components/library/crfs/CrfTranslatedTextSelection.vue'
import '@vueup/vue-quill/dist/vue-quill.snow.css'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import actionTypes from '@/constants/actions'
import libConstants from '@/constants/libraries'
import CrfExtensionsManagementTable from '@/components/library/crfs/CrfExtensionsManagementTable.vue'
import CrfNewVersionSummaryConfirmDialog from '@/components/library/crfs/CrfNewVersionSummaryConfirmDialog.vue'
import CrfApprovalSummaryConfirmDialog from '@/components/library/crfs/CrfApprovalSummaryConfirmDialog.vue'
import CrfActivityInstanceManagement from '@/components/library/crfs/CrfActivityInstanceManagement.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import { useUnitsStore } from '@/stores/units'
import filteringParameters from '@/utils/filteringParameters'
import _isEmpty from 'lodash/isEmpty'
import { useAccessGuard } from '@/composables/accessGuard'
import { useEditableLibraries } from '@/composables/editableLibraries'
import { useDragAndDrop } from '@formkit/drag-and-drop/vue'

const notificationHub = inject('notificationHub')
const formRules = inject('formRules')
const roles = inject('roles')

const props = defineProps({
  selectedItem: {
    type: Object,
    default: null,
  },
  startStep: {
    type: String,
    default: null,
  },
  readOnlyProp: {
    type: Boolean,
    default: false,
  },
  formView: {
    type: Boolean,
    default: true,
  },
  libraryName: {
    type: String,
    default: null,
  },
})

const emit = defineEmits(['updateItem', 'close', 'linkItem'])

const { t } = useI18n()
const { checkPermission } = useAccessGuard()

const unitsStore = useUnitsStore()
const { units } = storeToRefs(unitsStore)

const stepper = ref(null)
const confirm = ref(null)
const confirmApproval = ref(null)
const confirmNewVersion = ref(null)

const observer1 = ref(null)
const observer2 = ref(null)
const observer3 = ref(null)
const observer4 = ref(null)
const observer5 = ref(null)
const observer6 = ref(null)
const observer7 = ref(null)
const observer8 = ref(null)
const observer9 = ref(null)

function getObserver(step) {
  const observers = {
    1: observer1,
    2: observer2,
    3: observer3,
    4: observer4,
    5: observer5,
    6: observer6,
    7: observer7,
    8: observer8,
    9: observer9,
  }
  return observers[step]?.value
}

function isTermRemoved(term) {
  return !(term.name ?? term.submission_value)
}

const helpItems = [
  'CRFItems.name',
  'CRFItems.oid',
  'CRFItems.data_type',
  'CRFItems.length',
  'CRFItems.significant_digits',
  'CRFItems.sas_name',
  'CRFItems.sds_name',
  'CRFItems.origin',
  'CRFItems.comment',
  'CRFItems.context',
]

function createEmptyForm() {
  return {
    oid: 'I.',
    aliases: [],
    translated_texts: [],
    activity_instances: [
      {
        activity_instance_uid: '',
        activity_item_class_uid: '',
        order: 1,
        preset_response_value: '',
        primary: false,
        value_condition: '',
        value_dependent_map: '',
        availableActivityItemClasses: [],
      },
    ],
    external_question: {
      codelist_uid: '',
      term_uid: '',
    },
  }
}

const [termsTable, selectedTerms] = useDragAndDrop([], {
  disabled: props.readOnlyProp,
})

const form = ref(createEmptyForm())
const originalForm = ref({})
const selectedExtensions = ref([])

const { libraries: editableLibraries, showDropdown: showLibraryDropdown } =
  useEditableLibraries()
const selectedLibraryName = ref(libConstants.LIBRARY_SPONSOR)

const selectedCodelists = ref([])
const chosenUnits = ref([{ name: '', mandatory: true }])

const codelists = ref([])
const options = ref({})
const total = ref(0)
const filters = ref('')
const filtersUpdated = ref(false)

const selectedExternalQuestionTerm = ref(null)
const selectedExternalQuestionCodelist = ref(null)

const origins = ref([])
const dataTypes = ref([])
const termsList = ref([])
const totalTerms = ref(0)

const lengthFieldCheck = ref(false)
const digitsFieldCheck = ref(false)
const originFieldCheck = ref(true)

const loading = ref(false)
const readOnly = ref(props.readOnlyProp)

const filteringTerms = ref([])
const selectedFilteringTerms = ref([])
const search = ref('')
const termsFilterOperator = ref('or')

const selectedCodelistHeaders = ref([
  { title: t('CtCatalogueTable.concept_id'), key: 'codelist_uid' },
  { title: t('CtCatalogueTable.cd_name'), key: 'attributes.name' },
  {
    title: t('CtCatalogueTable.submission_value'),
    key: 'attributes.submission_value',
  },
  {
    title: t('CtCatalogueTable.nci_pref_name'),
    key: 'attributes.nci_preferred_name',
  },
  {
    title: t('CRFItems.multiple_choice'),
    key: 'allowsMultiChoice',
  },
  { title: '', key: 'delete' },
])

const codelistHeaders = ref([
  { title: t('CtCatalogueTable.concept_id'), key: 'codelist_uid' },
  { title: t('CtCatalogueTable.cd_name'), key: 'attributes.name' },
  {
    title: t('CtCatalogueTable.submission_value'),
    key: 'attributes.submission_value',
  },
  {
    title: t('CtCatalogueTable.nci_pref_name'),
    key: 'attributes.nci_preferred_name',
  },
  { title: '', key: 'actions' },
])

const unitHeaders = ref([
  { title: t('CRFItemGroups.name'), key: 'name', width: '25%' },
  { title: t('CRFItems.sponsor_unit'), key: 'oid', width: '20%' },
  { title: t('UnitTable.ucum_unit'), key: 'ucum' },
  { title: t('UnitTable.ct_units'), key: 'terms', width: '30%' },
  { title: t('_global.mandatory'), key: 'mandatory' },
  { title: '', key: 'delete' },
])

const termsHeaders = ref([
  { title: t('CtCatalogueTable.concept_id'), key: 'term_uid' },
  { title: t('_global.name'), key: 'sponsor_preferred_name' },
  { title: '', key: 'add' },
])

const selectedTermsHeaders = ref([
  {
    title: '',
    key: 'order',
  },
  {
    title: t('CtCatalogueTable.concept_id'),
    key: 'term_uid',
    width: '10%',
  },
  {
    title: t('CRFItems.sponsor_pref_name'),
    key: 'name',
    width: '40%',
  },
  { title: t('_global.mandatory'), key: 'mandatory', width: '5%' },
  {
    title: t('CRFItems.displayed_name'),
    key: 'display_text',
    width: '40%',
  },
  { title: '', key: 'delete', width: '1%' },
])

const steps = ref([])

function buildCreateSteps() {
  return [
    { name: 'form', title: t('CRFItems.item_details') },
    {
      name: 'translated_texts',
      title: t('CRFItems.translated_text_details'),
    },
    {
      name: 'external_question',
      title: t('CRFItems.external_question'),
    },
    {
      name: 'extensions',
      title: t('CRFForms.vendor_extensions'),
    },
    { name: 'alias', title: t('CRFItemGroups.alias_details') },
  ]
}

function buildEditSteps() {
  return [
    { name: 'form', title: t('CRFItems.item_details') },
    {
      name: 'translated_texts',
      title: t('CRFItems.translated_text_details'),
    },
    {
      name: 'external_question',
      title: t('CRFItems.external_question'),
    },
    {
      name: 'extensions',
      title: t('CRFForms.vendor_extensions'),
    },
    { name: 'alias', title: t('CRFItemGroups.alias_details') },
    {
      name: 'activity_instance_links',
      title: t('CRFItems.activity_instance_links'),
    },
    { name: 'change_description', title: t('CRFForms.change_desc') },
  ]
}

function dedupeSteps() {
  const unique = Array.from(new Set(steps.value.map((a) => a.name))).map(
    (name) => {
      return steps.value.find((a) => a.name === name)
    }
  )
  steps.value = unique
}

function isEdit() {
  if (props.selectedItem) {
    return Object.keys(props.selectedItem).length !== 0
  }
  return false
}

const externalQuestionProps = (term) => {
  let codelist_names = []

  if (!_isEmpty(term)) {
    codelist_names = term.codelists.map((cl) => cl.codelist_name)
  }

  return {
    title: term?.name?.sponsor_preferred_name,
    subtilte: codelist_names.join(', '),
    value: term,
  }
}

watch(
  () => props.readOnlyProp,
  (value) => {
    readOnly.value = value
  }
)

watch(
  () => props.libraryName,
  (value) => {
    if (value) selectedLibraryName.value = value
  },
  { immediate: true }
)

watch(
  () => selectedExternalQuestionTerm.value,
  (value) => {
    if (
      form.value.external_question?.uid ==
        selectedExternalQuestionTerm.value.term_uid &&
      form.value.external_question?.codelist_uid
    ) {
      selectedExternalQuestionCodelist.value =
        selectedExternalQuestionTerm.value.codelists.find(
          (cl) => cl.codelist_uid == form.value.external_question.codelist_uid
        )
    } else {
      selectedExternalQuestionCodelist.value = value.codelists[0]
    }
  }
)

watch(
  selectedCodelists,
  () => {
    getCodeListTerms()
  },
  { deep: true }
)

watch(
  () => props.selectedItem,
  (value) => {
    if (isEdit() && value) {
      steps.value = buildEditSteps()
      initForm(value)
    } else {
      steps.value = buildCreateSteps()
    }
    dedupeSteps()
  },
  { immediate: true }
)

watch(
  options,
  () => {
    fetchCodelists()
  },
  { deep: true }
)

watch(search, () => {
  fetchTerms()
})

watch(
  selectedFilteringTerms,
  () => {
    fetchCodelists()
  },
  { deep: true }
)

watch(termsFilterOperator, () => {
  fetchCodelists()
})

const isReadOnly = computed(() => {
  return readOnly.value || !checkPermission(roles.LIBRARY_WRITE)
})

const title = computed(() => {
  if (!isEdit()) {
    return t('CRFItems.add_item')
  }

  const prefix = readOnly.value
    ? t('CRFItems.crf_item')
    : t('CRFItems.edit_item')
  return `${prefix} - ${form.value.name}`
})

const formUrl = computed(() => {
  if (!isEdit()) {
    return null
  }
  return `${window.location.href.replace('crf-tree', 'items')}/item/${props.selectedItem.uid}`
})

const actions = computed(() => [
  {
    label: t('_global.approve'),
    icon: 'mdi-check-decagram',
    iconColor: () => 'success',
    condition: () => !readOnly.value,
    click: approve,
  },
  {
    label: t('_global.new_version'),
    icon: 'mdi-plus-circle-outline',
    iconColor: 'primary',
    condition: () => readOnly.value,
    click: newVersion,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: (item) =>
      item.possible_actions
        ? item.possible_actions.find((action) => action === actionTypes.DELETE)
        : false,
    click: deleteItem,
  },
])

onMounted(async () => {
  if (props.startStep) {
    stepper.value?.goToStep(props.startStep)
  }

  fetchCodelists()

  terms.getTermsByCodelist('originType').then((resp) => {
    origins.value = resp.data.items
  })

  terms.getTermsByCodelist('codmdt').then((resp) => {
    dataTypes.value = resp.data.items.sort((a, b) =>
      a.submission_value.localeCompare(b.submission_value)
    )
  })

  unitsStore.fetchUnits({ page_size: 0 })
})

function lengthRequired(value) {
  if (
    ['string', 'text'].includes(
      form.value.datatype.submission_value?.toLowerCase()
    ) ||
    (form.value.significant_digits !== null &&
      form.value.significant_digits !== undefined)
  ) {
    return formRules.required(value)
  }
  return true
}

function significantDigitsRequired(value) {
  if (form.value.length !== null && form.value.length !== undefined) {
    return formRules.required(value)
  }
  return true
}

function checkFieldAvailable(dataType) {
  digitsFieldCheck.value = false
  originFieldCheck.value = true
  lengthFieldCheck.value = true

  if (
    !['text', 'string', 'integer', 'float'].includes(
      dataType.submission_value?.toLowerCase()
    )
  ) {
    lengthFieldCheck.value = false
    form.value.length = null
  }

  if (dataType === 'float') {
    digitsFieldCheck.value = true
  }

  if (dataType === 'comment') {
    originFieldCheck.value = false
  }
}

function getItem() {
  crfs.getItem(props.selectedItem.uid).then((resp) => {
    initForm(resp.data)
  })
}

async function newVersion() {
  if (
    await confirmNewVersion.value.open({
      agreeLabel: t('CRFItems.create_new_version'),
      item: props.selectedItem,
    })
  ) {
    crfs.newVersion('items', props.selectedItem.uid).then((resp) => {
      emit('updateItem', resp.data)
      readOnly.value = false
      getItem()

      notificationHub.add({
        msg: t('_global.new_version_success'),
      })
    })
  }
}

async function approve() {
  if (
    await confirmApproval.value.open({
      agreeLabel: t('CRFItems.approve_item'),
      item: props.selectedItem,
    })
  ) {
    crfs.approve('items', props.selectedItem.uid).then((resp) => {
      emit('updateItem', resp.data)
      readOnly.value = true
      close()
      getItem()

      notificationHub.add({
        msg: t('CRFItems.approved'),
      })
    })
  }
}

async function deleteItem() {
  let relationships = 0
  await crfs.getRelationships(props.selectedItem.uid, 'items').then((resp) => {
    if (resp.data.OdmItemGroup && resp.data.OdmItemGroup.length > 0) {
      relationships = resp.data.OdmItemGroup.length
    }
  })

  const options = {
    type: 'warning',
    cancelLabel: t('_global.cancel'),
    agreeLabel: t('_global.continue'),
  }

  let shouldDelete = relationships === 0
  if (relationships > 0) {
    shouldDelete = await confirm.value.open(
      `${t('CRFItems.delete_warning', { count: relationships })}`,
      options
    )
  }
  if (shouldDelete) {
    crfs.delete('items', props.selectedItem.uid).then(() => {
      emit('close')
    })
  }

  if (
    relationships > 0 &&
    (await confirm.value?.open(
      `${t('CRFItems.delete_warning', { count: relationships })}`,
      options
    ))
  ) {
    crfs.delete('items', props.selectedItem.uid).then(() => {
      emit('close')
    })
  } else if (relationships === 0) {
    crfs.delete('items', props.selectedItem.uid).then(() => {
      emit('close')
    })
  }
}

function checkIfNumeric() {
  if (form.value.datatype) {
    if (
      form.value.datatype.submission_value?.includes('integer') ||
      form.value.datatype.submission_value?.includes('float') ||
      form.value.datatype.submission_value?.includes('double')
    ) {
      steps.value.splice(3, 0, {
        name: 'unit',
        title: t('CRFItems.unit_details'),
      })
      steps.value = steps.value.filter((obj) => {
        return obj.name !== 'codelist' && obj.name !== 'terms'
      })
    } else if (form.value.datatype.submission_value?.includes('string')) {
      steps.value = steps.value.filter((obj) => {
        return obj.name !== 'unit'
      })
      steps.value.splice(3, 0, {
        name: 'codelist',
        title: t('CRFItems.codelist_details'),
      })
      steps.value.splice(4, 0, {
        name: 'terms',
        title: t('CRFItems.codelist_subset'),
      })
    }

    if (
      !form.value.datatype.submission_value?.includes('string') &&
      !form.value.datatype.submission_value?.includes('text')
    ) {
      steps.value = steps.value.filter((obj) => {
        return obj.name !== 'codelist' && obj.name !== 'terms'
      })
    }
    if (
      !form.value.datatype.submission_value?.includes('integer') &&
      !form.value.datatype.submission_value?.includes('float') &&
      !form.value.datatype.submission_value?.includes('double')
    ) {
      steps.value = steps.value.filter((obj) => {
        return obj.name !== 'unit'
      })
    }
  } else {
    steps.value = steps.value.filter((obj) => {
      return (
        obj.name !== 'unit' && obj.name !== 'codelist' && obj.name !== 'terms'
      )
    })
  }

  dedupeSteps()
  checkFieldAvailable(form.value.datatype)
}

function close() {
  notificationHub.clearErrors()
  form.value = {
    oid: 'I.',
    aliases: [],
    translated_texts: [],
  }
  chosenUnits.value = [{ name: '', mandatory: true }]
  selectedCodelists.value = []
  selectedTerms.value = []
  selectedExtensions.value = []
  stepper.value?.reset()
  emit('close')
}

function getCodeListTerms(filtersArg, optionsArg, filtersUpdatedArg) {
  const params = filteringParameters.prepareParameters(
    optionsArg,
    filtersArg,
    filtersUpdatedArg
  )
  params.include_removed = false

  if (selectedCodelists.value[0]) {
    params.codelist_uid = selectedCodelists.value[0].codelist_uid
    codelistApi.getCodelistTerms(params.codelist_uid, params).then((resp) => {
      termsList.value = resp.data.items
      if (form.value.terms) {
        selectedTerms.value = form.value.terms
      }
      totalTerms.value = resp.data.total
    })
  } else {
    termsList.value = []
  }
}

function addTerm(item) {
  item.mandatory = true
  if (!selectedTerms.value.some((el) => el.term_uid === item.term_uid)) {
    const itemToAdd = { ...item }
    itemToAdd.name = itemToAdd.sponsor_preferred_name
    selectedTerms.value.push(itemToAdd)
  }
}

function removeTerm(item) {
  selectedTerms.value = selectedTerms.value.filter(
    (el) => el.term_uid !== item.term_uid
  )
}

async function submit() {
  if (isReadOnly.value) {
    close()
    return
  }

  notificationHub.clearErrors()

  form.value.library_name = props.libraryName || selectedLibraryName.value
  if (form.value.oid === 'I.') {
    form.value.oid = null
  }

  chosenUnits.value = chosenUnits.value.filter((el) => {
    return el.name !== ''
  })

  form.value.unit_definitions =
    chosenUnits.value.length === 0
      ? []
      : chosenUnits.value.map((e) => ({
          uid: e.uid ? e.uid : e.name.uid,
          mandatory: e.mandatory,
        }))

  if (
    !['base64float', 'double', 'float', 'hexfloat', 'integer'].includes(
      form.value.datatype.submission_value?.toLowerCase()
    )
  ) {
    form.value.unit_definitions = []
  }

  if (form.value.datatype.submission_value === 'string') {
    if (
      !_isEmpty(selectedCodelists.value) &&
      selectedCodelists.value[0].codelist_uid
    ) {
      form.value.codelist = {
        uid: selectedCodelists.value[0].codelist_uid,
        allows_multi_choice: form.value.allows_multi_choice,
      }
    } else {
      form.value.codelist = null
    }
    form.value.terms = selectedTerms.value.map((el, idx) => ({
      uid: el.term_uid,
      mandatory: el.mandatory,
      display_text: el.display_text,
      order: idx + 1,
    }))
  } else {
    form.value.codelist = null
    form.value.terms = []
  }

  if (form.value.length == '') {
    form.value.length = null
  }
  if (form.value.significant_digits == '') {
    form.value.significant_digits = null
  }

  const elements = []
  const attributes = []
  let elementAttributes = []

  selectedExtensions.value.forEach((ex) => {
    if (ex.type) {
      attributes.push(ex)
    } else {
      elements.push(ex)
      if (ex.vendor_attributes) {
        elementAttributes = [...elementAttributes, ...ex.vendor_attributes]
      }
    }
  })

  form.value.vendor_elements = elements
  form.value.vendor_element_attributes = elementAttributes
  form.value.vendor_attributes = attributes
  form.value.datatype_uid =
    form.value.datatype.uid || form.value.datatype.term_uid

  form.value.external_question = null
  if (
    selectedExternalQuestionTerm.value?.term_uid &&
    selectedExternalQuestionCodelist.value?.codelist_uid
  ) {
    form.value.external_question = {}
    form.value.external_question.term_uid =
      selectedExternalQuestionTerm.value?.term_uid
    form.value.external_question.codelist_uid =
      selectedExternalQuestionCodelist.value?.codelist_uid
  }

  try {
    if (isEdit()) {
      await crfs
        .updateItem(form.value, props.selectedItem.uid)
        .then(async (resp) => {
          notificationHub.add({
            msg: t('CRFItems.item_updated'),
          })
          emit('updateItem', resp.data)
          close()
        })
    } else {
      await crfs.createItem(form.value).then(async (resp) => {
        notificationHub.add({
          msg: t('CRFItems.item_created'),
        })
        emit('linkItem', resp)
        close()
      })
    }
  } finally {
    if (stepper.value) {
      stepper.value.loading = false
    }
  }
}

function setExtensions(extensions) {
  selectedExtensions.value = extensions
}

function addUnit() {
  chosenUnits.value.push({ name: '', mandatory: true })
}

function removeUnit(index) {
  chosenUnits.value.splice(index, 1)
}

function setUnit(index) {
  chosenUnits.value[index].ucum = chosenUnits.value[index].name.ucum
    ? chosenUnits.value[index].name.ucum.name
    : ''
  chosenUnits.value[index].oid = chosenUnits.value[index].name.name
  chosenUnits.value[index].terms = chosenUnits.value[index].name.ct_units[0]
    ? chosenUnits.value[index].name.ct_units[0].term_name
    : ''
  chosenUnits.value[index].uid = chosenUnits.value[index].name.uid
}

async function initForm(item) {
  loading.value = true
  originalForm.value = JSON.parse(JSON.stringify(item))

  form.value = item
  form.value.aliases = item.aliases
  form.value.translated_texts = item.translated_texts
  selectedLibraryName.value = item.library_name || libConstants.LIBRARY_SPONSOR

  if (!item.unit_definitions || item.unit_definitions.length === 0) {
    chosenUnits.value = [{ name: '', mandatory: true }]
  } else {
    item.unit_definitions.forEach((e) => {
      if (!chosenUnits.value.some((el) => el.uid === e.uid)) {
        chosenUnits.value.unshift({
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

  if (selectedCodelists.value.length === 0 && item.codelist) {
    selectedCodelists.value.push({
      codelist_uid: item.codelist.uid,
      attributes: {
        name: item.codelist.name,
        submission_value: item.codelist.submission_value,
        nci_preferred_name: item.codelist.preferred_term,
      },
    })
    form.value.allows_multi_choice = item.codelist.allows_multi_choice
  }

  if (item.terms) {
    selectedTerms.value = item.terms
  }

  form.value.change_description = t('_global.draft_change')
  checkIfNumeric()

  item.vendor_attributes.forEach((attr) => (attr.type = 'attr'))
  item.vendor_elements.forEach((element) => {
    element.vendor_attributes = item.vendor_element_attributes.filter(
      (attribute) => attribute.vendor_element_uid === element.uid
    )
  })

  selectedExtensions.value = [
    ...item.vendor_attributes,
    ...item.vendor_elements,
  ]

  if (!_isEmpty(item.external_question)) {
    controlledTerminology
      .getCodelistTerms({
        filters: JSON.stringify({
          term_uid: { v: [item.external_question.uid] },
        }),
      })
      .then((resp) => {
        const _term = resp.data.items[0]
        const _codelist = _term.codelists.find(
          (cl) => cl.codelist_uid == item.external_question.codelist_uid
        )

        selectedExternalQuestionTerm.value = _term
        selectedExternalQuestionCodelist.value = _codelist

        form.value.external_question.term_uid = _term.term_uid
        form.value.external_question.codelist_uid = _codelist.codelist_uid
      })
  }

  loading.value = false
}

function fetchCodelists(filtersArg, optionsArg, filtersUpdatedArg) {
  filters.value = filtersArg
  filtersUpdated.value = !!filtersUpdatedArg

  if (filtersUpdated.value) {
    options.value.page = 1
  }

  const params = {
    page_number: options.value.page,
    page_size: options.value.itemsPerPage,
    total_count: true,
  }

  if (filters.value !== undefined) {
    params.filters = filters.value
  }

  if (selectedFilteringTerms.value.length > 0) {
    params.term_filter = {
      term_uids: selectedFilteringTerms.value.map((term) => term.term_uid),
      operator: termsFilterOperator.value,
    }
  }

  controlledTerminology.getCodelists(params).then((resp) => {
    codelists.value = resp.data.items.filter(
      (ar) =>
        !selectedCodelists.value.some(
          (rm) => rm.codelist_uid === ar.codelist_uid
        )
    )
    total.value = resp.data.total
  })
}

function fetchTerms() {
  const params = {
    filters: {
      'name.sponsor_preferred_name': {
        v: [search.value ? search.value : ''],
        op: 'co',
      },
    },
    page_size: 20,
  }
  controlledTerminology.getCodelistTerms(params).then((resp) => {
    filteringTerms.value = [...resp.data.items, ...selectedFilteringTerms.value]
  })
}

function addCodelist(item) {
  if (selectedCodelists.value.length === 0) {
    selectedCodelists.value.push(item)
    codelists.value.splice(codelists.value.indexOf(item), 1)
  }
}

function removeCodelist(item) {
  selectedCodelists.value = []
  codelists.value.unshift(item)
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
