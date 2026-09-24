<template>
  <HorizontalStepperForm
    ref="stepperRef"
    :title="$t('TrialSummaryParameterForm.edit_title')"
    :steps="steps"
    :form-observer-getter="getObserver"
    :edit-data="form"
    single-step-stepper
    @close="close"
    @save="submit"
  >
    <template #[`step.edit`]>
      <v-form ref="parametersForm" class="d-flex flex-column">
        <div>
          <span data-cy="required-attributes-title" class="section-title">
            {{ $t('OtherStudyAttributes.required_attributes') }}</span
          >
          <template v-for="(item, index) in requiredAttributes" :key="index">
            <div class="other-study-attribute-panel pa-6 mb-2">
              <table class="other-study-attribute-table">
                <tbody>
                  <tr>
                    <td class="table-cell table-cell--parameter">
                      <div class="panel-label text-body-1 mb-1">
                        {{ $t('OtherStudyAttributes.parameter') }}
                      </div>
                      <div class="panel-value text-h5 font-weight-bold">
                        <v-select
                          v-model="requiredAttributes[index].parameter"
                          item-title="sponsor_preferred_name"
                          item-value="sponsor_preferred_name"
                          return-object
                          :items="requiredParameters"
                          :rules="[formRules.required]"
                          :disabled="
                            !!requiredAttributes[index].ts_parameter_term_uid
                          "
                          :data-cy="`other-attr-required-parameter-${index}`"
                          @update:model-value="
                            (value) =>
                              setAttributeValues(value, index, 'required')
                          "
                        />
                      </div>
                    </td>
                    <td class="table-cell table-cell--field">
                      <div class="panel-label text-body-1 mb-1">
                        {{ $t('OtherStudyAttributes.parameter_value') }}
                      </div>
                      <v-radio-group
                        v-if="item.semantic_data_type === 'Boolean'"
                        v-model="item.parameter_value"
                        :disabled="!!item.null_flavor_term_uid"
                        class="boolean-radio-group"
                        inline
                        hide-details
                        :data-cy="`other-attr-required-value-${index}`"
                      >
                        <v-radio
                          v-for="option in booleanOptions"
                          :key="option.title"
                          :label="option.title"
                          :value="option.value"
                        />
                      </v-radio-group>
                      <div
                        v-else-if="
                          item.semantic_data_type === 'Duration Date Time'
                        "
                        class="duration-input-group"
                        :data-cy="`other-attr-required-value-${index}`"
                      >
                        <v-text-field
                          :model-value="
                            getDurationPart(item.parameter_value, 'years')
                          "
                          type="number"
                          min="0"
                          :label="$t('OtherStudyAttributes.years')"
                          hide-details
                          :disabled="!!item.null_flavor_term_uid"
                          @update:model-value="
                            (value) => updateDurationPart(item, 'years', value)
                          "
                        />
                        <v-text-field
                          :model-value="
                            getDurationPart(item.parameter_value, 'months')
                          "
                          type="number"
                          min="0"
                          :label="$t('OtherStudyAttributes.months')"
                          hide-details
                          :disabled="!!item.null_flavor_term_uid"
                          @update:model-value="
                            (value) => updateDurationPart(item, 'months', value)
                          "
                        />
                        <v-text-field
                          :model-value="
                            getDurationPart(item.parameter_value, 'days')
                          "
                          type="number"
                          min="0"
                          :label="$t('OtherStudyAttributes.days')"
                          hide-details
                          :disabled="!!item.null_flavor_term_uid"
                          @update:model-value="
                            (value) => updateDurationPart(item, 'days', value)
                          "
                        />
                      </div>
                      <v-text-field
                        v-else
                        v-model="item.parameter_value"
                        :disabled="!!item.null_flavor_term_uid"
                        hide-details
                        :data-cy="`other-attr-required-value-${index}`"
                      />
                    </td>
                    <td class="table-cell table-cell--field">
                      <div class="panel-label text-body-1 mb-1">
                        {{ $t('OtherStudyAttributes.null_flavor') }}
                      </div>
                      <v-select
                        v-model="item.null_flavor_term_uid"
                        item-title="sponsor_preferred_name"
                        item-value="term_uid"
                        :items="nullFlavorOptions"
                        clearable
                        hide-details
                        :data-cy="`other-attr-required-null-flavor-${index}`"
                        @update:model-value="
                          (value) => {
                            if (value) item.parameter_value = null
                          }
                        "
                      />
                    </td>
                    <td class="table-cell table-cell--actions">
                      <v-btn
                        class="remove-btn"
                        color="error"
                        min-width="110"
                        height="48"
                        :data-cy="`other-attr-required-remove-${index}`"
                        @click="removeItem(item, index, 'required')"
                      >
                        {{ $t('_global.remove') }}
                      </v-btn>
                    </td>
                  </tr>
                  <tr>
                    <td class="table-cell table-cell--parameter">
                      <div class="panel-label text-body-1 mb-1">
                        {{ $t('OtherStudyAttributes.semantic_data_type') }}
                      </div>
                      <div class="panel-value text-h5 font-weight-bold">
                        {{ displayValue(item.semantic_data_type) }}
                      </div>
                    </td>
                    <td class="table-cell table-cell--field">
                      <div class="panel-label text-body-1 mb-1">
                        {{ $t('OtherStudyAttributes.code_list') }}
                      </div>
                      <div class="panel-value text-h5 font-weight-bold">
                        {{ displayValue(item.response_codelist) }}
                      </div>
                    </td>
                    <td class="table-cell table-cell--field">
                      <div class="panel-label text-body-1 mb-1">
                        {{ $t('OtherStudyAttributes.notes') }}
                      </div>
                      <div class="panel-value text-h5 font-weight-bold">
                        {{ displayValue(item.notes) }}
                      </div>
                    </td>
                    <td class="table-cell table-cell--actions" />
                  </tr>
                </tbody>
              </table>
            </div>
          </template>

          <v-btn
            class="secondary-btn add-attribute-btn mt-2"
            data-cy="add-required-attribute"
            variant="outlined"
            rounded="xl"
            prepend-icon="mdi-plus"
            @click="addItem('required')"
          >
            {{ $t('OtherStudyAttributes.add_required') }}
          </v-btn>

          <span data-cy="optional-attributes-title" class="section-title">{{
            $t('OtherStudyAttributes.optional_attributes')
          }}</span>

          <template v-for="(item, index) in optionalAttributes" :key="index">
            <div class="other-study-attribute-panel pa-6 mb-2">
              <table class="other-study-attribute-table">
                <tbody>
                  <tr>
                    <td class="table-cell table-cell--parameter">
                      <div class="panel-label text-body-1 mb-1">
                        {{ $t('OtherStudyAttributes.parameter') }}
                      </div>
                      <div class="panel-value text-h5 font-weight-bold">
                        <v-select
                          v-model="optionalAttributes[index].parameter"
                          item-title="sponsor_preferred_name"
                          item-value="sponsor_preferred_name"
                          return-object
                          :items="optionalParameters"
                          :rules="[formRules.required]"
                          :disabled="
                            !!optionalAttributes[index].ts_parameter_term_uid
                          "
                          :data-cy="`other-attr-optional-parameter-${index}`"
                          @update:model-value="
                            (value) =>
                              setAttributeValues(value, index, 'optional')
                          "
                        />
                      </div>
                    </td>
                    <td class="table-cell table-cell--field">
                      <div class="panel-label text-body-1 mb-1">
                        {{ $t('OtherStudyAttributes.parameter_value') }}
                      </div>
                      <v-text-field
                        v-if="item.semantic_data_type === 'Text'"
                        v-model="item.parameter_value"
                        :disabled="!!item.null_flavor_term_uid"
                        hide-details
                        :data-cy="`other-attr-optional-value-${index}`"
                      />
                      <v-radio-group
                        v-else-if="item.semantic_data_type === 'Boolean'"
                        v-model="item.parameter_value"
                        :disabled="!!item.null_flavor_term_uid"
                        class="boolean-radio-group"
                        inline
                        hide-details
                        :data-cy="`other-attr-optional-value-${index}`"
                      >
                        <v-radio
                          v-for="option in booleanOptions"
                          :key="option.title"
                          :label="option.title"
                          :value="option.value"
                        />
                      </v-radio-group>
                      <div
                        v-else-if="item.semantic_data_type === 'Duration'"
                        class="duration-input-group"
                        :data-cy="`other-attr-optional-value-${index}`"
                      >
                        <v-text-field
                          :model-value="
                            getDurationPart(item.parameter_value, 'years')
                          "
                          type="number"
                          min="0"
                          :label="$t('OtherStudyAttributes.years')"
                          hide-details
                          :disabled="!!item.null_flavor_term_uid"
                          @update:model-value="
                            (value) => updateDurationPart(item, 'years', value)
                          "
                        />
                        <v-text-field
                          :model-value="
                            getDurationPart(item.parameter_value, 'months')
                          "
                          type="number"
                          min="0"
                          :label="$t('OtherStudyAttributes.months')"
                          hide-details
                          :disabled="!!item.null_flavor_term_uid"
                          @update:model-value="
                            (value) => updateDurationPart(item, 'months', value)
                          "
                        />
                        <v-text-field
                          :model-value="
                            getDurationPart(item.parameter_value, 'days')
                          "
                          type="number"
                          min="0"
                          :label="$t('OtherStudyAttributes.days')"
                          hide-details
                          :disabled="!!item.null_flavor_term_uid"
                          @update:model-value="
                            (value) => updateDurationPart(item, 'days', value)
                          "
                        />
                      </div>
                    </td>
                    <td class="table-cell table-cell--field">
                      <div class="panel-label text-body-1 mb-1">
                        {{ $t('OtherStudyAttributes.null_flavor') }}
                      </div>
                      <v-select
                        v-model="item.null_flavor_term_uid"
                        item-title="sponsor_preferred_name"
                        item-value="term_uid"
                        :items="nullFlavorOptions"
                        clearable
                        hide-details
                        :data-cy="`other-attr-optional-null-flavor-${index}`"
                        @update:model-value="
                          (value) => {
                            if (value) item.parameter_value = null
                          }
                        "
                      />
                    </td>
                    <td class="table-cell table-cell--actions">
                      <v-btn
                        class="remove-btn"
                        color="error"
                        min-width="110"
                        height="48"
                        :data-cy="`other-attr-optional-remove-${index}`"
                        @click="removeItem(item, index, 'optional')"
                      >
                        {{ $t('_global.remove') }}
                      </v-btn>
                    </td>
                  </tr>
                  <tr>
                    <td class="table-cell table-cell--parameter">
                      <div class="panel-label text-body-1 mb-1">
                        {{ $t('OtherStudyAttributes.semantic_data_type') }}
                      </div>
                      <div class="panel-value text-h5 font-weight-bold">
                        {{ displayValue(item.semantic_data_type) }}
                      </div>
                    </td>
                    <td class="table-cell table-cell--field">
                      <div class="panel-label text-body-1 mb-1">
                        {{ $t('OtherStudyAttributes.code_list') }}
                      </div>
                      <div class="panel-value text-h5 font-weight-bold">
                        {{ displayValue(item.response_codelist) }}
                      </div>
                    </td>
                    <td class="table-cell table-cell--field">
                      <div class="panel-label text-body-1 mb-1">
                        {{ $t('OtherStudyAttributes.notes') }}
                      </div>
                      <div class="panel-value text-h5 font-weight-bold">
                        {{ displayValue(item.notes) }}
                      </div>
                    </td>
                    <td class="table-cell table-cell--actions" />
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
        </div>

        <v-btn
          class="secondary-btn add-attribute-btn mt-2"
          data-cy="add-optional-attribute"
          variant="outlined"
          rounded="xl"
          prepend-icon="mdi-plus"
          @click="addItem('optional')"
        >
          {{ $t('OtherStudyAttributes.add_optional') }}
        </v-btn>
      </v-form>
    </template>
  </HorizontalStepperForm>
</template>

<script setup>
import { inject, ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import termsApi from '@/api/controlledTerminology/terms'
import codelistApi from '@/api/controlledTerminology/codelists'
import studyApi from '@/api/study'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const formRules = inject('formRules')
const studiesGeneralStore = useStudiesGeneralStore()

const props = defineProps({
  editData: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['close', 'updated'])

const stepperRef = ref()
const parametersForm = ref()
const form = ref({})
const nullFlavorOptions = ref([])
const requiredAttributes = ref([{}])
const optionalAttributes = ref([{}])
const requiredParameters = ref([])
const optionalParameters = ref([])
const paramsToDelete = ref([])

const booleanOptions = computed(() => [
  { title: t('_global.yes'), value: true },
  { title: t('_global.no'), value: false },
])

const steps = [{ title: 'edit', name: 'edit' }]

function getObserver(step) {
  if (step === 1) return parametersForm.value
  return null
}

function initForm() {
  const source = Array.isArray(props.editData) ? props.editData : []
  source.forEach((item) => {
    item.null_flavor_term_uid = item.null_flavor?.uid
  })
  const required = source.filter((item) => item.required_level === 'Required')
  const optional = source.filter((item) => item.required_level !== 'Required')
  requiredAttributes.value = required.length ? required : [{}]
  optionalAttributes.value = optional.length ? optional : [{}]
}

onMounted(() => {
  fetchParameters()
  termsApi.getTermsByCodelist('nullValues').then((resp) => {
    nullFlavorOptions.value = resp.data.items
  })
})

initForm()

function fetchParameters() {
  const params = {
    include_ts_parameters: true,
    page_size: 0,
    filters: { osb_field_name: { v: ['other_study_attributes'], op: 'eq' } },
  }
  codelistApi.getCodelistTerms('C66738', params).then((resp) => {
    requiredParameters.value = resp.data.items.filter(
      (item) => item.required_level === 'Required'
    )
    optionalParameters.value = resp.data.items.filter(
      (item) => item.required_level !== 'Required'
    )
  })
}

function setAttributeValues(value, index, type) {
  if (type === 'required') {
    requiredAttributes.value[index].notes = value.notes || ''
    requiredAttributes.value[index].response_codelist =
      value.response_codelist?.sponsor_preferred_name || ''
    requiredAttributes.value[index].semantic_data_type =
      value.semantic_data_type?.sponsor_preferred_name || ''
    requiredAttributes.value[index].parameter_value = undefined
    if (
      requiredAttributes.value[index].semantic_data_type === 'Boolean' &&
      requiredAttributes.value[index].parameter_value === undefined
    ) {
      requiredAttributes.value[index].parameter_value = true
    }
    if (requiredAttributes.value[index].semantic_data_type === 'Duration') {
      requiredAttributes.value[index].parameter_value = 'P0Y0M0D'
    }
  } else {
    optionalAttributes.value[index].notes = value.notes || ''
    optionalAttributes.value[index].response_codelist =
      value.response_codelist?.sponsor_preferred_name || ''
    optionalAttributes.value[index].semantic_data_type =
      value.semantic_data_type?.sponsor_preferred_name || ''
    optionalAttributes.value[index].parameter_value = undefined
    if (
      optionalAttributes.value[index].semantic_data_type === 'Boolean' &&
      optionalAttributes.value[index].parameter_value === undefined
    ) {
      optionalAttributes.value[index].parameter_value = true
    }
    if (optionalAttributes.value[index].semantic_data_type === 'Duration') {
      optionalAttributes.value[index].parameter_value = 'P0Y0M0D'
    }
  }
}

function sanitizeDurationPart(value) {
  const parsed = Number.parseInt(value, 10)
  if (!Number.isFinite(parsed) || parsed < 0) {
    return 0
  }
  return parsed
}

function parseDuration(value) {
  if (typeof value !== 'string') {
    return { years: 0, months: 0, days: 0 }
  }

  const match = value.match(/^P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)D)?$/)
  if (!match) {
    return { years: 0, months: 0, days: 0 }
  }

  return {
    years: sanitizeDurationPart(match[1]),
    months: sanitizeDurationPart(match[2]),
    days: sanitizeDurationPart(match[3]),
  }
}

function getDurationPart(duration, part) {
  return parseDuration(duration)[part]
}

function updateDurationPart(item, part, value) {
  const parsedDuration = parseDuration(item.parameter_value)
  parsedDuration[part] = sanitizeDurationPart(value)
  item.parameter_value = `P${parsedDuration.years}Y${parsedDuration.months}M${parsedDuration.days}D`
}

function displayValue(value) {
  if (value === null || value === undefined || value === '') {
    return '-'
  }
  if (typeof value === 'object') {
    return (
      value.sponsor_preferred_name ||
      value.submission_value ||
      value.name ||
      '-'
    )
  }
  return value
}

function addItem(type) {
  if (type === 'required') {
    requiredAttributes.value.push({})
  } else {
    optionalAttributes.value.push({})
  }
}

function removeItem(item, index, type) {
  if (item.ts_parameter_term_uid) {
    paramsToDelete.value.push(item.ts_parameter_term_uid)
  }
  if (type === 'required') {
    requiredAttributes.value.splice(index, 1)
  } else {
    optionalAttributes.value.splice(index, 1)
  }
}

function close() {
  initForm()
  emit('close')
}

function preparePayload() {
  const payload = [
    ...paramsToDelete.value.map((uid) => ({
      method: 'DELETE',
      content: { ts_parameter_term_uid: uid },
    })),
    ...requiredAttributes.value.map((attr) => {
      if (attr.ts_parameter_term_uid) {
        return {
          method: 'PATCH',
          content: {
            ts_parameter_term_uid: attr.ts_parameter_term_uid,
            parameter_value: attr.parameter_value,
            null_flavor_term_uid: attr.null_flavor_term_uid,
          },
        }
      }
      return {
        method: 'POST',
        content: {
          ts_parameter_term_uid: attr.parameter.term_uid,
          parameter_value: attr.parameter_value,
          null_flavor_term_uid: attr.null_flavor_term_uid,
        },
      }
    }),
    ...optionalAttributes.value.map((attr) => {
      if (attr.ts_parameter_term_uid) {
        return {
          method: 'PATCH',
          content: {
            ts_parameter_term_uid: attr.ts_parameter_term_uid,
            parameter_value: attr.parameter_value,
            null_flavor_term_uid: attr.null_flavor_term_uid,
          },
        }
      }
      return {
        method: 'POST',
        content: {
          ts_parameter_term_uid: attr.parameter.term_uid,
          parameter_value: attr.parameter_value,
          null_flavor_term_uid: attr.null_flavor_term_uid,
        },
      }
    }),
  ]
  return payload
}

async function submit() {
  stepperRef.value.loading = true
  try {
    await studyApi.batchUpdateOtherAttributes(
      studiesGeneralStore.selectedStudy.uid,
      preparePayload()
    )
    notificationHub.add({
      msg: t('OtherStudyAttributes.edit_success'),
      type: 'success',
    })
    emit('updated')
    emit('close')
  } catch (error) {
    console.error(error)
    notificationHub.add({
      msg: t('OtherStudyAttributes.edit_error'),
      type: 'error',
    })
  } finally {
    stepperRef.value.loading = false
  }
}
</script>

<style scoped lang="scss">
.other-study-attribute-panel {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 16px;
  background-color: rgb(var(--v-theme-dfltBackground));
  width: 85%;
}

.other-study-attribute-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.table-cell {
  vertical-align: top;
  padding: 8px 12px;
}

.table-cell--parameter {
  width: 34%;
  padding-left: 0;
}

.table-cell--field {
  width: 24%;
}

.table-cell--actions {
  width: 18%;
  text-align: right;
  padding-right: 0;
}

.panel-label {
  color: rgb(var(--v-theme-nnBaseBlue));
}

.panel-value {
  color: rgb(var(--v-theme-nnBaseBlue));
  line-height: 1.25;
}

.remove-btn {
  text-transform: none;
}

.add-attribute-btn {
  width: fit-content;
  align-self: flex-start;
}

.section-title {
  color: rgb(var(--v-theme-primary));
  font-size: 1.5rem !important;
  font-weight: 700;
  display: block;
  margin-top: 12px;
  margin-bottom: 12px;
}

.boolean-radio-group :deep(.v-selection-control-group) {
  column-gap: 24px;
}

.boolean-radio-group {
  margin-top: 12px;
}

.duration-input-group {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

@media (max-width: 992px) {
  .other-study-attribute-panel {
    padding: 20px !important;
  }

  .other-study-attribute-table,
  .other-study-attribute-table tbody,
  .other-study-attribute-table tr,
  .other-study-attribute-table td {
    display: block;
    width: 100%;
  }

  .other-study-attribute-table tr + tr {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  }

  .table-cell {
    padding: 8px 0;
  }

  .table-cell--parameter,
  .table-cell--field,
  .table-cell--actions {
    width: 100%;
    padding-left: 0;
    padding-right: 0;
  }

  .table-cell--actions {
    text-align: left;
    padding-top: 12px;
  }
}

@media (max-width: 600px) {
  .other-study-attribute-panel {
    padding: 14px !important;
    border-radius: 12px;
  }

  .panel-value {
    font-size: 1.5rem !important;
  }

  .remove-btn {
    width: 100%;
    min-width: 0;
  }
}
</style>
