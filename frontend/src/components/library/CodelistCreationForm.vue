<template>
  <StepperForm
    ref="stepper"
    :title="$t('CodelistCreationForm.title')"
    :steps="steps"
    :form-observer-getter="getObserver"
    :help-items="helpItems"
    @close="cancel"
    @save="submit"
  >
    <template #[`step.codelist_type_selection`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-row>
          <v-col>
            <v-radio-group
              v-model="codelistCreationType"
              data-cy="codelist-creation-type"
              :rules="[formRules.required]"
            >
              <v-radio
                :label="$t('CodelistCreationForm.regular_codelist')"
                value="regular"
              />
              <v-radio
                :label="$t('CodelistCreationForm.paired_codelists')"
                value="paired"
              />
            </v-radio-group>
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #[`step.catalogue`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-row v-if="showLibraryDropdown">
          <v-col>
            <v-select
              v-model="form.library_name"
              data-cy="library-dropdown"
              :label="$t('CodelistCreationForm.library')"
              :items="editableLibraries"
              item-title="name"
              item-value="name"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-select
              v-model="form.catalogue_names"
              data-cy="catalogue-dropdown"
              :label="$t('CodelistCreationForm.catalogue')"
              :items="catalogues"
              item-title="name"
              item-value="name"
              multiple
              clearable
              persistent-hint
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #[`step.names`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-row v-if="codelistCreationType === 'paired'" no-gutters>
          <v-col cols="12">
            <v-text-field
              v-model="nameCodelistForm.sponsor_preferred_name"
              data-cy="name-sponsor-preffered-name"
              :label="$t('CodelistSponsorValuesForm.name_pref_name')"
              clearable
              class="mt-2"
              :rules="[formRules.required]"
            />
          </v-col>
          <v-col cols="12">
            <v-text-field
              v-model="codeCodelistForm.sponsor_preferred_name"
              data-cy="code-sponsor-preffered-name"
              :label="$t('CodelistSponsorValuesForm.code_pref_name')"
              clearable
              class="mt-2"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row v-else>
          <v-col>
            <v-text-field
              v-model="form.sponsor_preferred_name"
              data-cy="sponsor-preffered-name"
              :label="$t('CodelistSponsorValuesForm.pref_name')"
              clearable
              class="mt-2"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-switch
              v-model="form.template_parameter"
              :label="$t('CodelistSponsorValuesForm.tpl_parameter')"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #[`step.attributes`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-row>
          <v-col>
            <v-select
              v-model="form.codelist_type"
              data-cy="codelist-type"
              :label="$t('CodelistAttributesForm.codelist_type')"
              :items="codelistTypes"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <!-- Name fields -->
        <v-row v-if="codelistCreationType === 'paired'" no-gutters class="mb-4">
          <v-col cols="12">
            <v-text-field
              v-model="nameCodelistForm.name"
              data-cy="name-codelist-name"
              :label="$t('CodelistAttributesForm.name_name')"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
          <v-col cols="12">
            <v-text-field
              v-model="codeCodelistForm.name"
              data-cy="code-codelist-name"
              :label="$t('CodelistAttributesForm.code_name')"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row v-else>
          <v-col>
            <v-text-field
              v-model="form.name"
              data-cy="codelist-name"
              :label="$t('CodelistAttributesForm.name')"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <!-- Submission value fields -->
        <v-row v-if="codelistCreationType === 'paired'" no-gutters class="mb-4">
          <v-col cols="12">
            <v-text-field
              v-model="nameCodelistForm.submission_value"
              data-cy="name-submission-value"
              :label="$t('CodelistAttributesForm.name_subm_value')"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
          <v-col cols="12">
            <v-text-field
              v-model="codeCodelistForm.submission_value"
              data-cy="code-submission-value"
              :label="$t('CodelistAttributesForm.code_subm_value')"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row v-else>
          <v-col>
            <v-text-field
              v-model="form.submission_value"
              data-cy="submission-value"
              :label="$t('CodelistAttributesForm.subm_value')"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <!-- NCI preferred name fields -->
        <v-row v-if="codelistCreationType === 'paired'" no-gutters class="mb-4">
          <v-col cols="12">
            <v-text-field
              v-model="nameCodelistForm.nci_preferred_name"
              data-cy="name-nci-preffered-name"
              :label="$t('CodelistAttributesForm.name_nci_pref_name')"
              clearable
            />
          </v-col>
          <v-col cols="12">
            <v-text-field
              v-model="codeCodelistForm.nci_preferred_name"
              data-cy="code-nci-preffered-name"
              :label="$t('CodelistAttributesForm.code_nci_pref_name')"
              clearable
            />
          </v-col>
        </v-row>
        <v-row v-else>
          <v-col>
            <v-text-field
              v-model="form.nci_preferred_name"
              data-cy="nci-preffered-name"
              :label="$t('CodelistAttributesForm.nci_pref_name')"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-switch
              v-model="form.extensible"
              data-cy="extensible-toggle"
              :label="$t('CodelistAttributesForm.extensible')"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-switch
              v-model="form.is_ordinal"
              data-cy="ordinal-toggle"
              :label="$t('CodelistAttributesForm.is_ordinal')"
            />
          </v-col>
        </v-row>
        <!-- Definition fields -->
        <v-row v-if="codelistCreationType === 'paired'" no-gutters>
          <v-col cols="12">
            <v-textarea
              v-model="nameCodelistForm.definition"
              data-cy="name-definition"
              :label="$t('CodelistAttributesForm.name_definition')"
              rows="1"
              clearable
              auto-grow
              :rules="[formRules.required]"
            />
          </v-col>
          <v-col cols="12">
            <v-textarea
              v-model="codeCodelistForm.definition"
              data-cy="code-definition"
              :label="$t('CodelistAttributesForm.code_definition')"
              rows="1"
              clearable
              auto-grow
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row v-else>
          <v-col>
            <v-textarea
              v-model="form.definition"
              data-cy="definition"
              :label="$t('CodelistAttributesForm.definition')"
              rows="1"
              clearable
              auto-grow
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </StepperForm>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
</template>

<script setup>
import { computed, inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useCtCataloguesStore } from '@/stores/library-ctcatalogues'
import controlledTerminology from '@/api/controlledTerminology'
import pairedCodelistsApi from '@/api/controlledTerminology/pairedCodelists'
import { useEditableLibraries } from '@/composables/editableLibraries'
import libConstants from '@/constants/libraries'
import StepperForm from '@/components/tools/StepperForm.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'

const emit = defineEmits(['close', 'created'])

const props = defineProps({
  // The library of the page the form was opened from (e.g. the current
  // CT library tab), used to pre-select the Library dropdown in the
  // "select catalogue" step instead of always defaulting to Sponsor.
  defaultLibraryName: {
    type: String,
    default: null,
  },
})

const formRules = inject('formRules')

const ctCataloguesStore = useCtCataloguesStore()
const { t } = useI18n()

const catalogues = computed(() => ctCataloguesStore.catalogues)
const { libraries: editableLibraries, showDropdown: showLibraryDropdown } =
  useEditableLibraries()

const codelistCreationType = ref('regular')

function resolveDefaultLibraryName() {
  return props.defaultLibraryName || libConstants.LIBRARY_SPONSOR
}

const form = ref({
  extensible: false,
  is_ordinal: false,
  library_name: resolveDefaultLibraryName(),
  template_parameter: false,
  codelist_type: 'Standard',
})

const nameCodelistForm = ref({
  sponsor_preferred_name: null,
  name: null,
  submission_value: null,
  nci_preferred_name: null,
  definition: null,
})

const codeCodelistForm = ref({
  sponsor_preferred_name: null,
  name: null,
  submission_value: null,
  nci_preferred_name: null,
  definition: null,
})
const confirm = ref()
const observer_1 = ref()
const observer_2 = ref()
const observer_3 = ref()
const observer_4 = ref()
const stepper = ref()

const codelistTypes = ['Response', 'Standard']
const helpItems = [
  'CodelistCreationForm.codelist_creation_type',
  'CodelistCreationForm.catalogue',
  'CodelistSponsorValuesForm.pref_name',
  'CodelistSponsorValuesForm.tpl_parameter',
  'CodelistAttributesForm.name',
  'CodelistAttributesForm.subm_value',
  'CodelistAttributesForm.nci_pref_name',
  'CodelistAttributesForm.extensible',
  'CodelistAttributesForm.is_ordinal',
  'CodelistAttributesForm.definition',
]
const steps = [
  {
    name: 'codelist_type_selection',
    title: t('CodelistCreationForm.step1_title'),
  },
  {
    name: 'catalogue',
    title: t('CodelistCreationForm.step2_title'),
  },
  { name: 'names', title: t('CodelistCreationForm.step3_title') },
  {
    name: 'attributes',
    title: t('CodelistCreationForm.step4_title'),
  },
]

async function cancel() {
  const options = {
    type: 'warning',
    cancelLabel: t('_global.cancel'),
    agreeLabel: t('_global.continue'),
  }
  if (await confirm.value.open(t('_global.cancel_changes'), options)) {
    close()
  }
}

function close() {
  emit('close')
  form.value = {
    extensible: false,
    is_ordinal: false,
    library_name: resolveDefaultLibraryName(),
    template_parameter: false,
    codelist_type: 'Standard',
  }
  stepper.value.reset()
}

function getObserver(step) {
  if (step === 1) {
    return observer_1.value
  }
  if (step === 2) {
    return observer_2.value
  }
  if (step === 3) {
    return observer_3.value
  }
  return observer_4.value
}

async function submit() {
  form.value.terms = []
  const data = JSON.parse(JSON.stringify(form.value))
  try {
    let resp
    if (codelistCreationType.value === 'regular') {
      resp = await controlledTerminology.createCodelist(data)
      emit('created', {
        codelist_uid: resp.data.codelist_uid,
        catalogue_name: resp.data.catalogue_names[0],
      })
    } else {
      data.name_information = { ...nameCodelistForm.value }
      data.code_information = { ...codeCodelistForm.value }
      resp = await pairedCodelistsApi.create(data)
      emit('created', {
        codelist_uid: resp.data.names.codelist_uid,
        catalogue_name: resp.data.names.catalogue_names[0],
      })
    }
    close()
  } finally {
    stepper.value.loading = false
  }
}
</script>
