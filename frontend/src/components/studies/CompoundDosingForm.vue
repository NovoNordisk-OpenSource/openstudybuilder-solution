<template>
  <HorizontalStepperForm
    ref="stepper"
    :title="title"
    :steps="steps"
    :form-observer-getter="getObserver"
    :editable="
      studyCompoundDosing !== undefined && studyCompoundDosing !== null
    "
    :help-items="helpItems"
    :edit-data="form"
    :debug="false"
    @close="close"
    @save="submit"
  >
    <template #[`step.element`]>
      <v-form ref="elementForm">
        <v-row>
          <v-col cols="12">
            <v-autocomplete
              v-model="form.study_element"
              :label="$t('StudyCompoundDosingForm.element')"
              :items="studyElements"
              data-cy="study-element"
              item-title="name"
              return-object
              :rules="[formRules.required]"
              clearable
              class="required"
            />
          </v-col>
        </v-row>
        <template v-if="form.study_element">
          <v-row>
            <v-col cols="6">
              <v-text-field
                v-if="form.study_element"
                v-model="form.study_element.order"
                :label="$t('StudyCompoundDosingForm.element_order')"
                data-cy="study-element-order"
                row
                disabled
                hide-details
              />
            </v-col>
            <v-col cols="6" />
          </v-row>
          <v-row>
            <v-col cols="6">
              <v-text-field
                v-model="form.study_element.element_type.term_name"
                :label="$t('StudyCompoundDosingForm.element_type')"
                data-cy="study-element-type"
                row
                disabled
                hide-details
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model="form.study_element.element_subtype.term_name"
                :label="$t('StudyCompoundDosingForm.element_subtype')"
                data-cy="study-element-subtype"
                row
                disabled
                hide-details
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="6">
              <v-text-field
                v-model="form.study_element.name"
                :label="$t('StudyCompoundDosingForm.element_name')"
                data-cy="study-element-name"
                row
                disabled
                hide-details
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model="form.study_element.short_name"
                :label="$t('StudyCompoundDosingForm.element_short_name')"
                data-cy="study-element-short-name"
                row
                disabled
                hide-details
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="12">
              <v-text-field
                v-model="form.study_element.description"
                :label="$t('StudyCompoundDosingForm.element_description')"
                data-cy="study-element-description"
                row
                disabled
                hide-details
              />
            </v-col>
          </v-row>
        </template>
      </v-form>
    </template>
    <template #[`step.compound`]>
      <v-form ref="compoundForm">
        <v-row>
          <v-col cols="12">
            <v-autocomplete
              v-model="form.study_compound"
              :label="$t('StudyCompoundDosingForm.compound')"
              :items="studiesCompoundsStore.studyCompounds"
              :item-title="
                (item) => `#${item.order} ${item.compound_alias.name}`
              "
              item-value="study_compound_uid"
              data-cy="select-compound"
              return-object
              :rules="[formRules.required]"
              clearable
              class="required"
            >
              <template #item="{ internalItem: item, props }">
                <v-list-item v-bind="props">
                  <v-list-item-subtitle>{{
                    item.raw.medicinal_product?.name ||
                    $t('StudyCompoundDosingForm.no_product_name')
                  }}</v-list-item-subtitle>
                </v-list-item>
              </template>
            </v-autocomplete>
          </v-col>
        </v-row>
      </v-form>
      <template v-if="form.study_compound">
        <v-row>
          <v-col cols="6">
            <v-text-field
              v-model="form.study_compound.order"
              :label="$t('StudyCompoundDosingForm.compound_order')"
              data-cy="compound-order"
              row
              disabled
              hide-details
            />
          </v-col>
          <v-col cols="6">
            <v-text-field
              v-model="form.study_compound.type_of_treatment.term_name"
              :label="$t('StudyCompoundDosingForm.type_of_treatment')"
              data-cy="type-of-treatment"
              row
              disabled
              hide-details
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6">
            <v-text-field
              v-model="form.study_compound.compound.name"
              :label="$t('StudyCompoundDosingForm.compound_name')"
              data-cy="compound-name"
              row
              disabled
              hide-details
            />
          </v-col>
          <v-col cols="6">
            <v-text-field
              v-model="form.study_compound.compound_alias.name"
              :label="$t('StudyCompoundDosingForm.compound_alias_name')"
              data-cy="compound-alias-name"
              row
              disabled
              hide-details
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6"></v-col>
          <v-col cols="6">
            <YesNoField
              v-model="form.study_compound.compound_alias.is_preferred_synonym"
              :label="$t('StudyCompoundForm.is_preferred_synonym')"
              data-cy="is-preffered-synonym"
              row
              disabled
              hide-details
            />
          </v-col>
        </v-row>

        <v-card
          v-for="activeSubstance in allIngredients
            .map((ingredient) => ingredient.active_substance)
            .flat()"
          :key="activeSubstance.uid"
          class="mt-8 mb-2 py-4 px-2"
        >
          <v-card-subtitle class="mb-2">Active Substance</v-card-subtitle>
          <v-card-text>
            <v-row>
              <v-col cols="3">
                <v-text-field
                  :model-value="activeSubstance.inn"
                  :label="$t('ActiveSubstance.inn')"
                  data-cy="compound-inn"
                  readonly
                  hide-details
                />
              </v-col>
              <v-col cols="3">
                <v-text-field
                  :model-value="activeSubstance.analyte_number"
                  :label="$t('ActiveSubstance.analyte_number')"
                  data-cy="compound-analyte-number"
                  readonly
                  hide-details
                />
              </v-col>
              <v-col cols="3">
                <v-text-field
                  :model-value="activeSubstance.long_number"
                  :label="$t('ActiveSubstance.long_number')"
                  data-cy="compound-long-number"
                  readonly
                  hide-details
                />
              </v-col>
              <v-col cols="3">
                <v-text-field
                  :model-value="activeSubstance.short_number"
                  :label="$t('ActiveSubstance.short_number')"
                  data-cy="compound-short-number"
                  readonly
                  hide-details
                />
              </v-col>
            </v-row>

            <v-row>
              <v-col cols="6">
                <v-text-field
                  :model-value="
                    activeSubstance.unii.substance_unii
                      ? activeSubstance.unii.substance_unii
                      : '-'
                  "
                  :label="$t('CompoundAliasForm.substance')"
                  data-cy="compound-substance-unii"
                  readonly
                  hide-details
                />
              </v-col>
              <v-col cols="6">
                <v-text-field
                  :model-value="
                    activeSubstance.unii.pclass_name
                      ? activeSubstance.unii.pclass_name
                      : '-'
                  "
                  :label="$t('CompoundAliasForm.pharmacological_class')"
                  data-cy="compound-pharmacological-class"
                  readonly
                  hide-details
                />
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </template>
    </template>

    <template #[`step.compound_dosing`]>
      <v-form ref="compoundDosingForm">
        <v-row>
          <v-col cols="6">
            <v-autocomplete
              v-if="form.study_compound"
              v-model="form.dose_value_uid"
              :label="$t('StudyCompoundDosingForm.dose_value')"
              :items="form.study_compound.medicinal_product.dose_values"
              :item-title="(item) => `${item.value} ${item.unit_label}`"
              data-cy="dose-value"
              item-value="uid"
              density="compact"
              clearable
            />
          </v-col>
          <v-col cols="6">
            <v-autocomplete
              v-if="form.study_compound"
              v-model="form.dose_frequency_uid"
              :label="$t('StudyCompoundDosingForm.dose_frequency')"
              :items="
                form.study_compound.medicinal_product.dose_frequencies || []
              "
              item-title="name"
              data-cy="dose-frequency"
              item-value="term_uid"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.composition"
              :label="$t('StudyCompoundDosingForm.composition')"
              data-cy="composition"
              clearable
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </HorizontalStepperForm>
</template>

<script setup>
import { computed, inject, ref, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import arms from '@/api/arms'
import terms from '@/api/controlledTerminology/terms'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import YesNoField from '@/components/tools/YesNoField.vue'
import { useStudiesCompoundsStore } from '@/stores/studies-compounds'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import pharmaceuticalProducts from '@/api/concepts/pharmaceuticalProducts'
import compoundAliases from '@/api/concepts/compoundAliases'
import { usePharmaceuticalProducts } from '@/composables/pharmaceuticalProducts'

const { getIngredientName } = usePharmaceuticalProducts()

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const formRules = inject('formRules')
const props = defineProps({
  studyCompoundDosingUid: {
    type: String,
    default: undefined,
  },
})
const emit = defineEmits(['close'])
const studiesCompoundsStore = useStudiesCompoundsStore()
const studiesGeneralStore = useStudiesGeneralStore()

const helpItems = [
  'StudyCompoundDosingForm.element',
  'StudyCompoundDosingForm.compound',
  'StudyCompoundDosingForm.dose_value',
  'StudyCompoundDosingForm.dose_frequency',
]

const form = ref({})
const steps = ref(getInitialSteps())
const studyElements = ref([])
const studyElementTypes = ref([])
const allIngredients = ref([])
const compoundAlias = ref({})
const studyCompoundDosing = ref(null)
const stepper = ref()
const elementForm = ref()
const compoundForm = ref()
const compoundDosingForm = ref()

const title = computed(() => {
  if (
    studyCompoundDosing.value !== undefined &&
    studyCompoundDosing.value !== null
  ) {
    return t('StudyCompoundDosingForm.edit_title')
  }
  return t('StudyCompoundDosingForm.add_title')
})

function updateDefaultComposition() {
  if (
    !form.value.dose_value_uid ||
    !form.value.study_compound ||
    allIngredients.value.length === 0
  )
    return
  const selectedDoseValue =
    form.value.study_compound.medicinal_product.dose_values.find(
      (dv) => dv.uid === form.value.dose_value_uid
    )
  if (!selectedDoseValue) return
  const compositions = allIngredients.value
    .filter((ing) => {
      if (!ing.strength || !ing.strength.unit_label) return false
      const parts = ing.strength.unit_label.split('/')
      if (parts.length === 2) {
        return parts[1].trim() === selectedDoseValue.unit_label
      }
      return ing.strength.unit_label === selectedDoseValue.unit_label
    })
    .map((ing) => {
      const parts = ing.strength.unit_label.split('/')
      const resultUnit =
        parts.length === 2 ? parts[0].trim() : ing.strength.unit_label
      const resultValue = selectedDoseValue.value * ing.strength.value
      return `${getIngredientName(ing, true)} ${resultValue} ${resultUnit}`
    })

  form.value.composition =
    compositions.length > 0 ? compositions.sort().join(' / ') : ''
}

watch(
  () => form.value.dose_value_uid,
  () => {
    updateDefaultComposition()
  }
)

watch(
  () => form.value.study_compound,
  () => {
    getAllProductIngredients()
  }
)

watch(
  () => props.studyCompoundDosingUid,
  (value) => {
    if (value) {
      const selectedItem =
        studiesCompoundsStore.getStudyCompoundDosingsByStudyCompoundDosingUid(
          value.study_compound_dosing_uid
        )
      studyCompoundDosing.value = selectedItem
    }
  }
)

watch(
  studyCompoundDosing,
  (value) => {
    if (value) {
      form.value = { ...value }
      if (value.dose_value) {
        form.value.dose_value_uid = value.dose_value.uid
      }
      if (value.dose_frequency) {
        form.value.dose_frequency_uid = value.dose_frequency.term_uid
      }
      compoundAliases
        .getObject(value.study_compound.compound_alias.uid)
        .then((resp) => {
          compoundAlias.value = resp.data
        })
      getAllProductIngredients()
    }
  },
  { immediate: true }
)

onMounted(() => {
  studiesCompoundsStore.fetchStudyCompounds({
    studyUid: studiesGeneralStore.selectedStudy.uid,
    page_size: 0,
  })
  const params = {
    page_size: 0,
  }
  arms
    .getStudyElements(studiesGeneralStore.selectedStudy.uid, params)
    .then((resp) => {
      studyElements.value = resp.data.items
      const selectedItem =
        studiesCompoundsStore.getStudyCompoundDosingsByStudyCompoundDosingUid(
          props.studyCompoundDosingUid
        )
      studyCompoundDosing.value = selectedItem
    })
  terms.getTermsByCodelist('elementTypes').then((resp) => {
    studyElementTypes.value = resp.data.items
  })
})

function getAllProductIngredients() {
  form.value.study_compound.medicinal_product.pharmaceutical_products.forEach(
    (item) =>
      pharmaceuticalProducts.getObject(item.uid).then((resp) => {
        const ingredients = resp.data.formulations
          .map((formulation) => formulation.ingredients)
          .flat()
        allIngredients.value = ingredients
      })
  )
}

function close() {
  emit('close')
  notificationHub.clearErrors()
  form.value = {}
  stepper.value.reset()
}
function getInitialSteps() {
  return [
    {
      name: 'element',
      title: t('StudyCompoundDosingForm.step1_title'),
    },
    {
      name: 'compound',
      title: t('StudyCompoundDosingForm.step2_title'),
    },
    {
      name: 'compound_dosing',
      title: t('StudyCompoundDosingForm.step3_title'),
    },
  ]
}
function getObserver(step) {
  if (step === 1) {
    return elementForm.value
  }
  if (step === 2) {
    return compoundForm.value
  }
  return compoundDosingForm.value
}
async function submit() {
  notificationHub.clearErrors()

  const data = { ...form.value }
  data.study_element_uid = data.study_element.element_uid
  delete data.study_element
  data.study_compound_uid = data.study_compound.study_compound_uid

  let action = null
  let notification = null
  let args = null
  if (!studyCompoundDosing.value) {
    action = 'addStudyCompoundDosing'
    notification = 'add_success'
    args = { studyUid: studiesGeneralStore.selectedStudy.uid, data }
  } else {
    action = 'updateStudyCompoundDosing'
    notification = 'update_success'
    args = {
      studyUid: studiesGeneralStore.selectedStudy.uid,
      studyCompoundDosingUid: props.studyCompoundDosingUid,
      data,
    }
  }

  try {
    await studiesCompoundsStore[action](args)
    notificationHub.add({
      msg: t(`StudyCompoundDosingForm.${notification}`),
    })
    close()
  } finally {
    stepper.value.loading = false
  }
}
</script>
