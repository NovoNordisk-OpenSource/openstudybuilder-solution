<template>
  <HorizontalStepperForm
    ref="stepperRef"
    :title="$t('TrialSummaryParameterForm.add_title')"
    :steps="steps"
    :form-observer-getter="getObserver"
    :edit-data="form"
    single-step-stepper
    @close="close"
    @save="submit"
  >
    <template #[`step.parameters`]>
      <v-form ref="parametersForm">
        <div
          data-cy="term-sponsor-values-title"
          class="text-subtitle-1 font-weight-bold mb-2"
        >
          {{ $t('TrialSummaryParameterForm.term_sponsor_values') }}
        </div>
        <v-row>
          <v-col cols="3">
            <v-text-field
              v-model="form.sponsor_preferred_name"
              :label="$t('TrialSummaryParameterForm.sponsor_name')"
              :rules="[formRules.required]"
              clearable
              data-cy="ts-param-sponsor-name"
              @update:model-value="setSentenceCase"
            />
          </v-col>
          <v-col cols="3">
            <v-text-field
              v-model="form.sponsor_preferred_name_sentence_case"
              :label="
                $t('TrialSummaryParameterForm.sponsor_sentence_case_name')
              "
              :rules="[
                formRules.required,
                (value) => formRules.sameAs(value, form.sponsor_preferred_name),
              ]"
              clearable
              data-cy="ts-param-sentence-case-name"
            />
          </v-col>
          <v-col cols="3">
            <v-select
              v-model="form.ts_parameter.required_level"
              :label="$t('TrialSummaryParameterForm.required_level')"
              :items="requiredLevelOptions"
              :rules="[formRules.required]"
              data-cy="ts-param-required-level"
            />
          </v-col>
          <v-col cols="3">
            <v-select
              v-model="form.ts_parameter.semantic_data_type_uid"
              :label="$t('TrialSummaryParameterForm.semantic_data_type')"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              :items="semanticDataTypeOptions"
              clearable
              data-cy="ts-param-semantic-data-type"
              @update:model-value="onSemanticDataTypeChange"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="3">
            <v-select
              v-model="form.ts_parameter.valid_null_flavor"
              item-value="term_uid"
              item-title="sponsor_preferred_name"
              :label="$t('TrialSummaryParameterForm.valid_null_flavor')"
              :items="validNullFlavorOptions"
              return-object
              clearable
              data-cy="ts-param-valid-null-flavor"
            />
          </v-col>
          <v-col cols="3">
            <v-select
              v-model="form.ts_parameter.cardinality"
              :label="$t('TrialSummaryParameterForm.cardinality')"
              :items="cardinalityOptions"
              data-cy="ts-param-cardinality"
            />
          </v-col>
          <v-col cols="3">
            <v-select
              v-model="form.ts_parameter.osb_page_reference"
              :label="$t('TrialSummaryParameterForm.osb_page_reference')"
              :items="osbPageReferenceOptions"
              clearable
              data-cy="ts-param-osb-page-reference"
              @update:model-value="onOsbPageReferenceChange"
            />
          </v-col>
          <v-col cols="3">
            <v-select
              v-model="form.ts_parameter.osb_field_name"
              :label="$t('TrialSummaryParameterForm.osb_field_name')"
              :items="osbFieldNameOptions"
              clearable
              data-cy="ts-param-osb-field-name"
              @update:model-value="onOsbFieldNameChange"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="3" class="d-flex">
            <v-text-field
              :model-value="
                form.ts_parameter.response_codelist?.submission_value || ''
              "
              :label="$t('TrialSummaryParameterForm.codelist')"
              readonly
              clearable
              data-cy="ts-param-codelist"
              @click:clear="form.ts_parameter.response_codelist = null"
            />
            <v-btn
              color="primary"
              variant="outlined"
              icon="mdi-text-box-search-outline"
              size="small"
              class="ml-2"
              :disabled="!isCtTermDataType"
              data-cy="ts-param-codelist-search"
              @click="showCodelistSelectionForm = true"
            />
          </v-col>
          <v-col cols="3">
            <v-text-field
              v-model="form.ts_parameter.notes"
              :label="$t('TrialSummaryParameterForm.notes')"
              data-cy="ts-param-notes"
            />
          </v-col>
        </v-row>

        <v-divider class="my-4" />

        <div
          data-cy="term-attributes-values-title"
          class="text-subtitle-1 font-weight-bold mb-2"
        >
          {{ $t('TrialSummaryParameterForm.term_attributes_values') }}
        </div>
        <v-row>
          <v-col cols="3">
            <v-select
              v-model="form.library_name"
              :label="$t('TrialSummaryParameterForm.library')"
              :items="editableLibraries"
              item-title="name"
              item-value="name"
              :rules="[formRules.required]"
              clearable
              data-cy="ts-param-library"
            />
          </v-col>
          <v-col cols="3">
            <v-text-field
              v-model="form.concept_id"
              :label="$t('TrialSummaryParameterForm.concept_id')"
              clearable
              data-cy="ts-param-concept-id"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="3">
            <v-text-field
              v-model="form.nci_preferred_name"
              :label="$t('TrialSummaryParameterForm.nci_preferred_term')"
              clearable
              data-cy="ts-param-nci-preferred-name"
            />
          </v-col>
          <v-col cols="3">
            <v-text-field
              v-model="form.submission_value"
              :label="$t('TrialSummaryParameterForm.submission_value')"
              :rules="[formRules.required]"
              clearable
              data-cy="ts-param-submission-value"
            />
          </v-col>
          <v-col cols="3">
            <v-text-field
              v-model="form.ts_parameter.order"
              :label="$t('TrialSummaryParameterForm.order')"
              type="number"
              clearable
              data-cy="ts-param-order"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6">
            <v-textarea
              v-model="form.definition"
              :label="$t('TrialSummaryParameterForm.definition')"
              counter="300"
              maxlength="300"
              rows="5"
              :rules="[formRules.required]"
              clearable
              data-cy="ts-param-definition"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </HorizontalStepperForm>
  <CodelistSelectionForm
    v-model:codelist="form.ts_parameter.response_codelist"
    :open="showCodelistSelectionForm"
    :title="$t('TrialSummaryParameterForm.select_codelists')"
    max-width="1200px"
    @close="showCodelistSelectionForm = false"
  />
</template>

<script setup>
import { inject, ref, onMounted, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useFormStore } from '@/stores/form'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import codelists from '@/api/controlledTerminology/terms'
import studyFields from '@/api/controlledTerminology/studyFields'
import CodelistSelectionForm from '@/components/library/CodelistSelectionForm.vue'
import controlledTerminology from '@/api/controlledTerminology'
import { useEditableLibraries } from '@/composables/editableLibraries'
import trialSummaryParameterConstants from '@/constants/trialSummaryParameters'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const formRules = inject('formRules')
const formStore = useFormStore()

const emit = defineEmits(['close', 'added'])

const stepperRef = ref()
const parametersForm = ref()
const form = ref({})
const showCodelistSelectionForm = ref(false)

const steps = [
  { title: t('TrialSummaryParameterForm.add_title'), name: 'parameters' },
]

const isCtTermDataType = computed(() => {
  const selected = semanticDataTypeOptions.value.find(
    (dt) => dt.term_uid === form.value.ts_parameter.semantic_data_type_uid
  )
  return selected?.sponsor_preferred_name === 'CT Term'
})

function getObserver(step) {
  if (step === 1) return parametersForm.value
  return null
}

const requiredLevelOptions =
  trialSummaryParameterConstants.REQUIRED_LEVEL_OPTIONS
const validNullFlavorOptions = ref([])
const cardinalityOptions = trialSummaryParameterConstants.CARDINALITY_OPTIONS
const osbFieldsOptions = ref([])
const semanticDataTypeOptions = ref([])
const { libraries: editableLibraries } = useEditableLibraries()

const DEFAULT_LIBRARY_NAME = 'Sponsor'

function getDefaultLibraryName() {
  return editableLibraries.value.some(
    (library) => library.name === DEFAULT_LIBRARY_NAME
  )
    ? DEFAULT_LIBRARY_NAME
    : null
}

// editableLibraries loads asynchronously (see useEditableLibraries), so the
// default may not be available yet when initForm() first runs.
watch(editableLibraries, () => {
  if (!form.value.library_name) {
    form.value.library_name = getDefaultLibraryName()
  }
})

const NULL_VALUE = '__null__'

function toOption(value) {
  return {
    title: value === null ? t('TrialSummaryParameterForm.none_option') : value,
    value: value === null ? NULL_VALUE : value,
  }
}

const osbPageReferenceOptions = computed(() => {
  const seen = new Set()
  const options = []
  for (const item of osbFieldsOptions.value) {
    const key = item.osb_page_reference
    if (seen.has(key)) continue
    seen.add(key)
    options.push(toOption(key))
  }
  return options
})

const osbFieldNameOptions = computed(() => {
  const selectedPage = form.value.ts_parameter.osb_page_reference
  const items =
    selectedPage === null || selectedPage === undefined
      ? osbFieldsOptions.value
      : osbFieldsOptions.value.filter((item) => {
          const pageValue =
            item.osb_page_reference === null
              ? NULL_VALUE
              : item.osb_page_reference
          return pageValue === selectedPage
        })
  return items.map((item) => toOption(item.osb_field_name))
})

function onOsbFieldNameChange(value) {
  if (value === null || value === undefined) return
  const realValue = value === NULL_VALUE ? null : value
  const match = osbFieldsOptions.value.find(
    (item) => item.osb_field_name === realValue
  )
  if (match) {
    form.value.ts_parameter.osb_page_reference =
      match.osb_page_reference === null ? NULL_VALUE : match.osb_page_reference
  }
}

function onOsbPageReferenceChange() {
  form.value.ts_parameter.osb_field_name = null
}

function onSemanticDataTypeChange() {
  form.value.ts_parameter.response_codelist = null
}

function getTermUid(item) {
  if (!item || typeof item !== 'object') return null
  return item.term_uid || item.uid || item.codelist_uid || null
}

function getValidNullFlavorTermUids(value) {
  if (!value) return []

  if (Array.isArray(value)) {
    return value.map(getTermUid).filter(Boolean)
  }

  const uid = getTermUid(value)
  return uid ? [uid] : []
}

function initForm() {
  form.value = {
    ts_parameter: {},
    library_name: getDefaultLibraryName(),
  }
  formStore.reset()
}

onMounted(() => {
  codelists.getTermsByCodelist('nullValues').then((resp) => {
    validNullFlavorOptions.value = resp.data.items
  })
  codelists.getTermsByCodelist('semanticDataType').then((resp) => {
    semanticDataTypeOptions.value = resp.data.items
  })
  studyFields.get().then((resp) => {
    osbFieldsOptions.value = resp.data.filter(
      (item) => item.osb_field_name !== null || item.osb_page_reference !== null
    )
  })
})

initForm()
formStore.save({ ...form.value })

function close() {
  initForm()
  emit('close')
}

async function submit() {
  try {
    const payload = {
      ...form.value,
      catalogue_names: ['SDTM CT'],
      codelists: [
        {
          codelist_uid: 'C66738',
          submission_value: form.value.submission_value,
        },
        {
          codelist_uid: 'C67152',
          submission_value: form.value.submission_value,
        },
      ],
      ts_parameter: {
        ...form.value.ts_parameter,
        response_codelist_uid: getTermUid(
          form.value.ts_parameter?.response_codelist
        ),
        semantic_data_type_uid: getTermUid(
          semanticDataTypeOptions.value.find(
            (item) =>
              item.term_uid === form.value.ts_parameter.semantic_data_type_uid
          ) || { term_uid: form.value.ts_parameter.semantic_data_type_uid }
        ),
        valid_null_flavor_term_uids: getValidNullFlavorTermUids(
          form.value.ts_parameter.valid_null_flavor
        ),
      },
    }

    await controlledTerminology.createCodelistTerm(payload)
    notificationHub.add({
      msg: t('TrialSummaryParameterForm.add_success'),
    })
    emit('added')
    emit('close')
  } catch (error) {
    console.error(error)
  } finally {
    stepperRef.value.loading = false
  }
}

function setSentenceCase(value) {
  if (value) {
    form.value.sponsor_preferred_name_sentence_case = value.toLowerCase()
  }
}
</script>
