<template>
  <HorizontalStepperForm
    ref="stepperRef"
    :title="$t('TrialSummaryParameterForm.edit_title')"
    :steps="steps"
    :form-observer-getter="getObserver"
    :edit-data="form"
    @close="close"
    @save="submit"
  >
    <template #[`step.parameters`]>
      <v-form ref="parametersForm" class="d-flex flex-column">
        <div :style="{ order: section === 'sponsor' ? 0 : 2 }">
          <div
            data-cy="term-sponsor-values-title"
            class="text-subtitle-1 font-weight-bold mb-2"
          >
            {{ $t('TrialSummaryParameterForm.term_sponsor_values') }}
          </div>
          <v-row>
            <v-col cols="3">
              <v-select
                v-model="form.required_level"
                :label="$t('TrialSummaryParameterForm.required_level')"
                :items="requiredLevelOptions"
                :rules="[formRules.required]"
                :disabled="section === 'attributes'"
                data-cy="ts-param-required-level"
              />
            </v-col>
            <v-col cols="3">
              <v-select
                v-model="form.semantic_data_type"
                :label="$t('TrialSummaryParameterForm.semantic_data_type')"
                item-title="sponsor_preferred_name"
                item-value="uid"
                :items="semanticDataTypeOptions"
                clearable
                return-object
                :disabled="section === 'attributes'"
                data-cy="ts-param-semantic-data-type"
                @update:model-value="onSemanticDataTypeChange"
              />
            </v-col>
            <v-col cols="3">
              <v-select
                v-model="form.valid_null_flavor_terms"
                item-value="uid"
                item-title="sponsor_preferred_name"
                :label="$t('TrialSummaryParameterForm.valid_null_flavor')"
                :items="validNullFlavorOptions"
                :disabled="section === 'attributes'"
                return-object
                clearable
                data-cy="ts-param-valid-null-flavor"
              />
            </v-col>
            <v-col cols="3">
              <v-select
                v-model="form.cardinality"
                :label="$t('TrialSummaryParameterForm.cardinality')"
                :items="cardinalityOptions"
                :disabled="section === 'attributes'"
                data-cy="ts-param-cardinality"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="3">
              <v-select
                v-model="form.osb_page_reference"
                :label="$t('TrialSummaryParameterForm.osb_page_reference')"
                :items="osbPageReferenceOptions"
                clearable
                :disabled="section === 'attributes'"
                data-cy="ts-param-osb-page-reference"
                @update:model-value="onOsbPageReferenceChange"
              />
            </v-col>
            <v-col cols="3">
              <v-select
                v-model="form.osb_field_name"
                :label="$t('TrialSummaryParameterForm.osb_field_name')"
                :items="osbFieldNameOptions"
                clearable
                :disabled="section === 'attributes'"
                data-cy="ts-param-osb-field-name"
                @update:model-value="onOsbFieldNameChange"
              />
            </v-col>
            <v-col cols="3" class="d-flex">
              <v-text-field
                :model-value="
                  form.response_codelist?.sponsor_preferred_name || ''
                "
                :label="$t('TrialSummaryParameterForm.codelist')"
                readonly
                clearable
                :disabled="section === 'attributes'"
                data-cy="ts-param-codelist"
                @click:clear="form.response_codelist = null"
              />
              <v-btn
                color="primary"
                variant="outlined"
                icon="mdi-text-box-search-outline"
                size="small"
                class="ml-2"
                :disabled="!isCtTermDataType || section === 'attributes'"
                data-cy="ts-param-codelist-search"
                @click="showCodelistSelectionForm = true"
              />
            </v-col>
            <v-col cols="3">
              <v-text-field
                v-model="form.notes"
                :label="$t('TrialSummaryParameterForm.notes')"
                :disabled="section === 'attributes'"
                data-cy="ts-param-notes"
              />
            </v-col>
          </v-row>
        </div>

        <v-divider class="my-4" :style="{ order: 1 }" />
        <div :style="{ order: section === 'sponsor' ? 2 : 0 }">
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
                disabled
                data-cy="ts-param-library"
              />
            </v-col>
            <v-col cols="3">
              <v-text-field
                v-model="form.concept_id"
                :label="$t('TrialSummaryParameterForm.concept_id')"
                :disabled="section === 'sponsor'"
                data-cy="ts-param-concept-id"
              />
            </v-col>
            <v-col cols="3">
              <v-text-field
                v-model="form.nci_preferred_name"
                :label="$t('TrialSummaryParameterForm.nci_preferred_term')"
                :disabled="section === 'sponsor'"
                data-cy="ts-param-nci-preferred-name"
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
                :disabled="section === 'sponsor'"
                data-cy="ts-param-definition"
              />
            </v-col>
          </v-row>
        </div>
      </v-form>
    </template>
  </HorizontalStepperForm>
  <CodelistSelectionForm
    v-model:codelist="form.response_codelist"
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
import { useEditableLibraries } from '@/composables/editableLibraries'
import trialSummaryParameterConstants from '@/constants/trialSummaryParameters'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const formRules = inject('formRules')
const formStore = useFormStore()

const props = defineProps({
  section: {
    type: String,
    required: true,
  },
  editData: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['close', 'updated'])

const stepperRef = ref()
const parametersForm = ref()
const form = ref({})
const showCodelistSelectionForm = ref(false)

const steps = [
  { title: t('TrialSummaryParameterForm.edit_title'), name: 'parameters' },
]

const isCtTermDataType = computed(() => {
  if (!form.value.semantic_data_type) return false
  const selected = semanticDataTypeOptions.value.find(
    (dt) =>
      dt.term_uid === form.value.semantic_data_type.term_uid ||
      dt.term_uid === form.value.semantic_data_type.uid
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
  const selectedPage = form.value.osb_page_reference
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
    form.value.osb_page_reference =
      match.osb_page_reference === null ? NULL_VALUE : match.osb_page_reference
  }
}

function onOsbPageReferenceChange() {
  form.value.osb_field_name = null
}

function onSemanticDataTypeChange() {
  form.value.response_codelist = null
}

function getTermUid(item) {
  if (!item || typeof item !== 'object') return null
  return item.term_uid || item.uid || null
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
    ...props.editData,
  }
  formStore.reset()
  formStore.save({ ...form.value })
}

watch(
  () => props.editData,
  () => initForm(),
  { deep: true }
)

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

function close() {
  initForm()
  emit('close')
}

async function submit() {
  try {
    if (props.section === 'sponsor') {
      const payload = {
        ...form.value,
        semantic_data_type_uid: getTermUid(form.value.semantic_data_type),
        response_codelist_uid: getTermUid(form.value.response_codelist),
        valid_null_flavor_term_uids: getValidNullFlavorTermUids(
          form.value.valid_null_flavor_terms
        ),
      }
      await codelists.updateTrialSummaryParameters(form.value.term_uid, payload)
    } else {
      await codelists.updateAttributes(form.value.term_uid, form.value)
    }
    notificationHub.add({
      msg: t('TrialSummaryParameterForm.edit_success'),
    })
    emit('updated')
    emit('close')
  } catch (error) {
    console.error(error)
    notificationHub.add({
      msg: t('TrialSummaryParameterForm.edit_error'),
      type: 'error',
    })
  } finally {
    stepperRef.value.loading = false
  }
  initForm()
}
</script>
