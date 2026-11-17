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
          <v-col cols="12">
            <v-sheet border rounded="lg" class="px-6 pt-4 pb-6">
              <div class="text-title mb-4">
                {{ $t('StudyCompoundDosingForm.dose_value') }}
              </div>
              <v-radio-group
                v-model="doseValueSource"
                class="dose-source-group mb-6"
                data-cy="dose-value-source"
                inline
                hide-details
                @update:model-value="updateDefaultComposition"
              >
                <v-radio
                  :label="$t('StudyCompoundDosingForm.dose_value_from_library')"
                  :value="doseSources.LIBRARY"
                  class="ml-0"
                  data-cy="dose-value-from-library"
                />
                <v-radio
                  :label="
                    $t(
                      'StudyCompoundDosingForm.dose_value_study_specific_library_unit'
                    )
                  "
                  :value="doseSources.STUDY_SPECIFIC_LIBRARY_UNIT"
                  class="ml-6"
                  data-cy="dose-value-study-specific-library-unit"
                />
                <v-radio
                  :label="
                    $t(
                      'StudyCompoundDosingForm.dose_value_study_specific_free_text'
                    )
                  "
                  :value="doseSources.STUDY_SPECIFIC_FREE_TEXT"
                  class="ml-6"
                  data-cy="dose-value-study-specific-free-text"
                />
              </v-radio-group>
              <v-autocomplete
                v-if="
                  form.study_compound && doseValueSource === doseSources.LIBRARY
                "
                v-model="form.dose_value_uid"
                :label="$t('StudyCompoundDosingForm.dose_value')"
                :items="form.study_compound.medicinal_product.dose_values"
                :item-title="(item) => `${item.value} ${item.unit_label}`"
                data-cy="dose-value"
                item-value="uid"
                density="compact"
                class="mt-4"
                hide-details
                clearable
              />
              <div
                v-else-if="
                  doseValueSource === doseSources.STUDY_SPECIFIC_LIBRARY_UNIT
                "
                class="d-flex align-start mt-4"
              >
                <v-text-field
                  v-model="libraryUnitDose.value"
                  :label="$t('_global.value')"
                  :rules="[requiredWith(libraryUnitDose.unit)]"
                  data-cy="library-unit-dose-value"
                  hide-details="auto"
                  clearable
                  @update:model-value="updateDefaultComposition"
                />
                <v-autocomplete
                  v-model="libraryUnitDose.unit"
                  :label="$t('_global.unit')"
                  :items="doseUnits"
                  :rules="[requiredWith(libraryUnitDose.value)]"
                  item-title="name"
                  item-value="name"
                  data-cy="library-unit-dose-unit"
                  class="ml-4"
                  hide-details="auto"
                  clearable
                  @update:model-value="updateDefaultComposition"
                />
              </div>
              <v-text-field
                v-else-if="
                  doseValueSource === doseSources.STUDY_SPECIFIC_FREE_TEXT
                "
                v-model="form.free_text_dose_value"
                :label="$t('StudyCompoundDosingForm.free_text_dose_value')"
                data-cy="free-text-dose-value"
                class="mt-4"
                hide-details
                clearable
              />
            </v-sheet>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.composition"
              :label="$t('StudyCompoundDosingForm.composition')"
              data-cy="composition"
              hide-details
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-autocomplete
              v-if="form.study_compound"
              v-model="form.dose_frequency_uid"
              :label="$t('StudyCompoundDosingForm.dose_frequency')"
              :items="groupedDoseFrequencies"
              item-title="name"
              data-cy="dose-frequency"
              item-value="term_uid"
              hide-details
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-autocomplete
              v-model="form.study_activity_instance_uid"
              :label="
                $t('StudyCompoundDosingForm.dose_collection_activity_instance')
              "
              :items="studyActivityInstances"
              :item-title="
                (item) => item.activity_instance?.name || item.activity?.name
              "
              data-cy="dose-collection-activity-instance"
              item-value="study_activity_instance_uid"
              hide-details
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
import study from '@/api/study'
import terms from '@/api/controlledTerminology/terms'
import unitsApi from '@/api/units'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import YesNoField from '@/components/tools/YesNoField.vue'
import { useStudiesCompoundsStore } from '@/stores/studies-compounds'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import pharmaceuticalProducts from '@/api/concepts/pharmaceuticalProducts'
import compoundAliases from '@/api/concepts/compoundAliases'
import { usePharmaceuticalProducts } from '@/composables/pharmaceuticalProducts'
import activityInstanceClasses from '@/constants/activityInstanceClasses'

// A dosing's dose value is either picked from the library (at medicinal product
// level) or given as a study level free text one — the API rejects a payload
// carrying both — so the user picks which of the two they are filling in.
//
// The study level one comes in two forms. STUDY_SPECIFIC_FREE_TEXT is plain
// free text. STUDY_SPECIFIC_LIBRARY_UNIT is a UI-only variant: a free text value
// paired with a unit from the Dose Unit subset. The API has no such field — the
// two parts are joined with a space and sent as the free text dose value, and
// split back apart on load when the text ends in a known dose unit.
const doseSources = {
  LIBRARY: 'library',
  STUDY_SPECIFIC_LIBRARY_UNIT: 'study_specific_library_unit',
  STUDY_SPECIFIC_FREE_TEXT: 'study_specific_free_text',
}

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
  'StudyCompoundDosingForm.library_unit_dose_value',
  'StudyCompoundDosingForm.free_text_dose_value',
  'StudyCompoundDosingForm.dose_frequency',
  'StudyCompoundDosingForm.dose_collection_activity_instance',
]

const form = ref({})
// UI state only — which of the dose value sources the user is filling in, and
// the two halves of a library unit one. Deliberately kept out of `form`, which
// is spread straight into the payload.
const doseValueSource = ref(doseSources.LIBRARY)
const libraryUnitDose = ref({ value: null, unit: null })
const doseUnits = ref([])
const steps = ref(getInitialSteps())
const studyElements = ref([])
const studyElementTypes = ref([])
const studyActivityInstances = ref([])
// Every term of the dose frequency codelist, not just the medicinal product's own
const doseFrequencyTerms = ref([])
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

// The medicinal product's own frequencies first, then the rest of the codelist,
// under two subheaders. `type: 'subheader'` / `type: 'divider'` are Vuetify's own
// pseudo-items, so no #item slot is needed.
//
// The two sources disagree on the title field — the medicinal product returns
// `{ term_uid, name }` while the codelist endpoint returns `sponsor_preferred_name`
// — so the codelist half is normalized to `name`. The subheaders carry `name` too,
// rather than `title`: Vuetify resolves every item's title through `item-title`
// and falls back to the raw object when the key is missing, which would render
// "[object Object]" as the header text.
const groupedDoseFrequencies = computed(() => {
  const productFrequencies =
    form.value.study_compound?.medicinal_product?.dose_frequencies || []
  const productUids = new Set(productFrequencies.map((item) => item.term_uid))
  const otherFrequencies = doseFrequencyTerms.value
    .filter((term) => !productUids.has(term.term_uid))
    .map((term) => ({
      term_uid: term.term_uid,
      name: term.sponsor_preferred_name,
    }))

  const grouped = []
  if (productFrequencies.length > 0) {
    grouped.push(
      {
        type: 'subheader',
        name: t('StudyCompoundDosingForm.medicinal_product_frequencies_header'),
      },
      ...productFrequencies
    )
  }
  if (otherFrequencies.length > 0) {
    if (grouped.length > 0) {
      grouped.push({ type: 'divider' })
    }
    grouped.push(
      {
        type: 'subheader',
        name: t('StudyCompoundDosingForm.other_frequencies_header'),
      },
      ...otherFrequencies
    )
  }
  return grouped
})

// The value and unit of a library unit dose only make sense together: once
// either is set, the other is required.
function requiredWith(other) {
  return (value) => !other || formRules.required(value)
}

// Splits a free text dose value into a value and a known dose unit, or returns
// null when it does not end in one. Only an exact, lossless split counts —
// joining the parts back with a single space must reproduce the text — so
// saving an untouched dosing never rewrites its dose value. The longest match
// wins, so a unit that is a suffix of another cannot shadow it.
function parseLibraryUnitDose(text) {
  if (!text) return null
  let match = null
  for (const unit of doseUnits.value) {
    const suffix = ` ${unit.name}`
    if (!text.endsWith(suffix)) continue
    const value = text.slice(0, -suffix.length)
    if (!value || value.trim() !== value) continue
    if (!match || unit.name.length > match.unit.length) {
      match = { value, unit: unit.name }
    }
  }
  return match
}

function initDoseValueSource(dosing) {
  const parsed = parseLibraryUnitDose(dosing.free_text_dose_value)
  if (parsed) {
    doseValueSource.value = doseSources.STUDY_SPECIFIC_LIBRARY_UNIT
    libraryUnitDose.value = parsed
  } else {
    doseValueSource.value = dosing.free_text_dose_value
      ? doseSources.STUDY_SPECIFIC_FREE_TEXT
      : doseSources.LIBRARY
    libraryUnitDose.value = { value: null, unit: null }
  }
}

// Pre-fills the composition from the dose value and each ingredient's strength.
// A library dose value and a library unit one are both multiplied out; a free
// text one cannot be, so every ingredient gets a "?" placeholder.
function updateDefaultComposition() {
  if (!form.value.study_compound || allIngredients.value.length === 0) return
  let dose = null
  if (doseValueSource.value === doseSources.LIBRARY) {
    if (!form.value.dose_value_uid) return
    dose = form.value.study_compound.medicinal_product.dose_values.find(
      (dv) => dv.uid === form.value.dose_value_uid
    )
    if (!dose) return
  } else if (
    doseValueSource.value === doseSources.STUDY_SPECIFIC_LIBRARY_UNIT
  ) {
    // Only a plain number can be multiplied out. Anything else — an incomplete
    // pair, or a value such as the range "0.5-1" — gets the placeholders.
    const { value, unit } = libraryUnitDose.value
    const number = value?.trim() ? Number(value) : NaN
    if (unit && Number.isFinite(number)) {
      dose = { value: number, unit_label: unit }
    }
  }
  const compositions = allIngredients.value.map((ing) => {
    const ingredientName = getIngredientName(ing, true)
    if (!dose || !ing.strength || !ing.strength.unit_label) {
      return `${ingredientName} ?`
    }
    const parts = ing.strength.unit_label.split('/')
    const denominatorUnit =
      parts.length === 2 ? parts[1].trim() : ing.strength.unit_label
    if (denominatorUnit !== dose.unit_label) {
      return `${ingredientName} ?`
    }
    const resultUnit =
      parts.length === 2 ? parts[0].trim() : ing.strength.unit_label
    const rawResultValue = dose.value * ing.strength.value
    const resultValue =
      Math.round((rawResultValue + Number.EPSILON) * 1000) / 1000
    return `${ingredientName} ${resultValue} ${resultUnit}`
  })

  form.value.composition = compositions.sort().join(' / ')
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
      if (value.study_activity_instance) {
        form.value.study_activity_instance_uid =
          value.study_activity_instance.study_activity_instance_uid
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

// Parsing needs the dose units, which may arrive after the dosing, so this
// re-runs once they do.
watch(
  [studyCompoundDosing, doseUnits],
  ([dosing]) => {
    if (dosing) {
      initDoseValueSource(dosing)
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
  // `all: true` lifts the default page size so the whole codelist comes back;
  // results arrive sorted by sponsor_preferred_name.
  terms.getTermsByCodelist('frequency', { all: true }).then((resp) => {
    doseFrequencyTerms.value = resp.data.items
  })
  unitsApi.getBySubset('Dose Unit').then((resp) => {
    doseUnits.value = resp.data.items
  })
  study
    .getStudyActivityInstances(studiesGeneralStore.selectedStudy.uid, {
      page_size: 0,
      has_activity_instance: true,
      filters: JSON.stringify({
        'activity_instance.activity_instance_class.name': {
          v: [activityInstanceClasses.INTERVENTIONS],
        },
      }),
    })
    .then((resp) => {
      studyActivityInstances.value = (resp.data.items || []).sort((a, b) => {
        const nameA = a.activity_instance?.name || a.activity?.name || ''
        const nameB = b.activity_instance?.name || b.activity?.name || ''
        return nameA.localeCompare(nameB)
      })
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
  doseValueSource.value = doseSources.LIBRARY
  libraryUnitDose.value = { value: null, unit: null }
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
  delete data.study_activity_instance

  // Each pair — dose_value_uid/free_text_dose_value and
  // dose_frequency_uid/free_text_dose_frequency — is mutually exclusive server
  // side (both non-null is a 400), and a PATCH back-fills every field missing
  // from the body from the record's current state. JSON.stringify drops keys set
  // to `undefined`, which looks exactly like a missing field and back-fills the
  // value we are dropping — so the abandoned field is sent as an explicit null.
  if (doseValueSource.value === doseSources.STUDY_SPECIFIC_FREE_TEXT) {
    data.dose_value_uid = null
    data.free_text_dose_value = data.free_text_dose_value || null
  } else if (
    doseValueSource.value === doseSources.STUDY_SPECIFIC_LIBRARY_UNIT
  ) {
    const { value, unit } = libraryUnitDose.value
    data.dose_value_uid = null
    data.free_text_dose_value = value && unit ? `${value.trim()} ${unit}` : null
  } else {
    data.free_text_dose_value = null
  }
  // The form offers no free text frequency, but an existing dosing may still
  // carry one. It is kept as is, and only cleared once a library frequency
  // replaces it.
  if (data.dose_frequency_uid) {
    data.free_text_dose_frequency = null
  }

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

<style scoped>
/* Vuetify renders the radio's icon and its label as adjacent siblings with no
   gap between them, so the text sits tight against the button. */
.dose-source-group :deep(.v-selection-control .v-label) {
  margin-inline-start: 4px;
}
</style>
