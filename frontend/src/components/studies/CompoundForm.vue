<template>
  <HorizontalStepperForm
    ref="stepper"
    :title="title"
    :steps="steps"
    :form-observer-getter="getObserver"
    :editable="studyCompound !== undefined && studyCompound !== null"
    :help-items="helpItems"
    :edit-data="form"
    @close="close"
    @save="submit"
  >
    <template #[`step.type_of_treatment`]>
      <v-form ref="observer_1">
        <NotApplicableField
          ref="naField"
          :clean-function="cleanTypeOfTreatment"
          :disabled="typeOfTreatment_uidNADisabled"
          :checked="studyCompound && !studyCompound.compound"
        >
          <template #mainField="{ notApplicable }">
            <v-autocomplete
              v-model="form.type_of_treatment"
              data-cy="type-of-treatment"
              :label="$t('StudyCompoundForm.type_of_treatment')"
              :items="typeOfTreatments"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              return-object
              :rules="[
                (value) => formRules.requiredIfNotNA(value, notApplicable),
              ]"
              clearable
              class="required"
            />
          </template>
        </NotApplicableField>
      </v-form>
    </template>
    <template #[`step.compoundAlias`]>
      <v-form ref="observer_2">
        <div v-if="showAlerts" class="mx-0">
          <v-alert
            v-if="!form.compound_alias && form.compoundSimple"
            type="warning"
            density="compact"
            class="mb-8 text-white"
            :text="$t('StudyCompoundForm.compound_no_preferred_synonym')"
          />
          <v-alert
            v-if="medicinalProducts.length === 0 && form.compoundSimple"
            type="warning"
            density="compact"
            class="mb-8 text-white"
            :text="$t('StudyCompoundForm.compound_no_medicinal_product')"
          />
        </div>
        <v-row>
          <v-col cols="6">
            <v-autocomplete
              v-model="form.compoundSimple"
              :label="$t('StudyCompoundForm.compound')"
              :items="compounds"
              data-cy="compound"
              item-title="name"
              item-value="uid"
              return-object
              :rules="[formRules.required]"
              clearable
              class="required"
            />
          </v-col>
          <v-col cols="6">
            <v-autocomplete
              v-model="form.compound_alias"
              :label="$t('StudyCompoundForm.compound_alias')"
              :items="compoundAliases"
              data-cy="compound-alias"
              item-title="name"
              item-value="uid"
              return-object
              :rules="[formRules.required]"
              readonly
              disabled
              class="required"
            />
          </v-col>
        </v-row>
        <template v-if="form.compound">
          <v-card class="mt-2 mb-8 pt-0 pb-4 px-2">
            <v-card-text>
              <v-row>
                <v-col cols="6">
                  <v-text-field
                    :model-value="preferedSynonym"
                    :label="$t('StudyCompoundForm.preferred_alias')"
                    data-cy="preffered-alias"
                    disabled
                    hide-details
                  />
                </v-col>
                <v-col cols="6">
                  <v-text-field
                    :model-value="otherSynonyms"
                    :label="$t('StudyCompoundForm.other_aliases')"
                    data-cy="other-aliases"
                    disabled
                    hide-details
                  />
                </v-col>
              </v-row>
              <v-row>
                <v-col cols="12">
                  <v-textarea
                    :model-value="
                      form.compound.definition ? form.compound.definition : '-'
                    "
                    :label="$t('StudyCompoundForm.compound_definition')"
                    data-cy="compound-definition"
                    auto-grow
                    rows="1"
                    disabled
                    hide-details
                  />
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </template>

        <v-row class="mt-8">
          <v-col cols="12">
            <v-autocomplete
              v-model="form.medicinalProduct"
              :label="$t('StudyCompoundForm.medicinal_product')"
              :items="medicinalProducts"
              data-cy="medicinal-product"
              item-title="name"
              item-value="uid"
              return-object
              :rules="[formRules.required]"
              clearable
              class="required"
            />
          </v-col>
        </v-row>

        <template v-if="form.medicinalProduct">
          <v-card class="mt-2 mb-8 pt-0 pb-4 px-2">
            <v-card-text>
              <v-row>
                <v-col cols="6">
                  <v-text-field
                    :model-value="form.medicinalProduct.dispenser.name"
                    :label="$t('StudyCompoundForm.dispensed_in')"
                    data-cy="dispensed-in"
                    disabled
                    hide-details
                  />
                </v-col>
                <v-col cols="6">
                  <v-text-field
                    :model-value="form.medicinalProduct.delivery_device.name"
                    :label="$t('StudyCompoundForm.device')"
                    data-cy="device"
                    disabled
                    hide-details
                  />
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
          <v-card
            v-for="activeSubstance in activeSubstances"
            :key="activeSubstance.uid"
            class="mt-2 mb-8 py-4 px-2"
          >
            <v-card-subtitle class="mb-2">{{
              $t('StudyCompoundForm.active_substance')
            }}</v-card-subtitle>
            <v-card-text>
              <v-row>
                <v-col cols="3">
                  <v-text-field
                    :model-value="
                      activeSubstance.inn ? activeSubstance.inn : '-'
                    "
                    :label="$t('ActiveSubstance.inn')"
                    data-cy="active-substance"
                    disabled
                    hide-details
                  />
                </v-col>
                <v-col cols="3">
                  <v-text-field
                    :model-value="
                      activeSubstance.analyte_number
                        ? activeSubstance.analyte_number
                        : '-'
                    "
                    :label="$t('ActiveSubstance.analyte_number')"
                    data-cy="analyte-number"
                    disabled
                    hide-details
                  />
                </v-col>
                <v-col cols="3">
                  <v-text-field
                    :model-value="
                      activeSubstance.long_number
                        ? activeSubstance.long_number
                        : '-'
                    "
                    :label="$t('ActiveSubstance.long_number')"
                    data-cy="long-number"
                    disabled
                    hide-details
                  />
                </v-col>
                <v-col cols="3">
                  <v-text-field
                    :model-value="
                      activeSubstance.short_number
                        ? activeSubstance.short_number
                        : '-'
                    "
                    :label="$t('ActiveSubstance.short_number')"
                    data-cy="short-number"
                    disabled
                    hide-details
                  />
                </v-col>
              </v-row>

              <v-row>
                <v-col cols="6">
                  <v-text-field
                    :model-value="
                      activeSubstance.unii?.substance_unii
                        ? activeSubstance.unii.substance_unii
                        : '-'
                    "
                    :label="$t('CompoundAliasForm.substance')"
                    data-cy="substance"
                    disabled
                    hide-details
                  />
                </v-col>
                <v-col cols="6">
                  <v-text-field
                    :model-value="getPclassLabel(activeSubstance)"
                    :label="$t('CompoundAliasForm.pharmacological_class')"
                    data-cy="pharmacological-class"
                    disabled
                    hide-details
                  />
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </template>
      </v-form>
    </template>
    <template #[`step.compound`]>
      <v-form v-if="form.compound" ref="observer_3">
        <v-row>
          <v-col>
            <v-textarea
              v-model="form.other_info"
              :label="$t('StudyCompoundForm.other')"
              data-cy="other-information"
              auto-grow
              rows="1"
              clearable
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </HorizontalStepperForm>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import compoundAliasesApi from '@/api/concepts/compoundAliases'
import compoundsApi from '@/api/concepts/compounds'
import compoundsSimple from '@/api/concepts/compoundsSimple'
import constants from '@/constants/studyCompounds'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import NotApplicableField from '@/components/tools/NotApplicableField.vue'
import statuses from '@/constants/statuses'
import studyConstants from '@/constants/study'
import terms from '@/api/controlledTerminology/terms'
import { useStudiesCompoundsStore } from '@/stores/studies-compounds'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import medicinalProductsApi from '@/api/concepts/medicinalProducts'
import pharmaceuticalProducts from '@/api/concepts/pharmaceuticalProducts'
import dataFormating from '@/utils/dataFormating'

const notificationHub = inject('notificationHub')
const formRules = inject('formRules')

const props = defineProps({
  studyCompound: {
    type: Object,
    default: undefined,
  },
})
const emit = defineEmits(['added', 'close'])

const { t } = useI18n()
const studiesCompoundsStore = useStudiesCompoundsStore()
const studiesGeneralStore = useStudiesGeneralStore()

const showAlerts = ref(false)
const compoundAliases = ref([])
const medicinalProducts = ref([])
const activeSubstances = ref([])
const compounds = ref([])
const helpItems = [
  'StudyCompoundForm.type_of_treatment',
  'StudyCompoundForm.compound',
  'StudyCompoundForm.medicinal_product',
  'StudyCompoundForm.other',
]
const form = ref(getInitialForm())
const typeOfTreatments = ref([])
const steps = ref(getInitialSteps())
const naField = ref()
const stepper = ref()
const observer_1 = ref()
const observer_2 = ref()
const observer_3 = ref()

const preferedSynonym = computed(() => {
  const preferedSynonym = compoundAliases.value.find(
    (item) => item.is_preferred_synonym
  )
  return preferedSynonym ? preferedSynonym.name : '-'
})
const otherSynonyms = computed(() => {
  const otherSynonyms = compoundAliases.value.filter(
    (item) => !item.is_preferred_synonym
  )
  return otherSynonyms.length
    ? otherSynonyms.map((item) => item.name).join(', ')
    : '-'
})
const title = computed(() => {
  if (props.studyCompound) {
    return t('StudyCompoundForm.edit_title')
  }
  return t('StudyCompoundForm.add_title')
})
const typeOfTreatment_uidNADisabled = computed(() => {
  if (
    (naField.value && naField.value.notApplicable) ||
    (props.studyCompound && !props.studyCompound.compound)
  ) {
    return false
  }
  if (!form.value.type_of_treatment) {
    return true
  }
  const types = [
    constants.TYPE_OF_TREATMENT_INVESTIGATIONAL_PRODUCT,
    constants.TYPE_OF_TREATMENT_CURRENT_TREATMENT,
    constants.TYPE_OF_TREATMENT_COMPARATIVE_TREATMENT,
  ]
  if (
    !types.find(
      (item) => item === form.value.type_of_treatment.sponsor_preferred_name
    )
  ) {
    return true
  }
  const studyCompounds =
    studiesCompoundsStore.getStudyCompoundsByTypeOfTreatment(
      form.value.type_of_treatment.term_uid
    )
  if (studyCompounds.length) {
    return true
  }
  const NAstudyCompounds =
    studiesCompoundsStore.getNAStudyCompoundsByTypeOfTreatment(
      form.value.type_of_treatment.term_uid
    )
  return !!NAstudyCompounds.length
})

watch(
  () => props.studyCompound,
  (val) => {
    if (val) {
      form.value.type_of_treatment = {
        term_uid: val.type_of_treatment.term_uid,
        sponsor_preferred_name: val.type_of_treatment.term_name,
      }
      form.value.other_info = val.other_info
      if (val.compound) {
        form.value.compound = val.compound
        form.value.compoundSimple = {
          uid: val.compound.uid,
          name: val.compound.name,
        }
        let params = {
          filters: {
            compound_uid: { v: [val.compound.uid] },
            status: { v: [statuses.FINAL] },
          },
          page_size: 0,
        }
        compoundAliasesApi.getFiltered(params).then((resp) => {
          compoundAliases.value = resp.data.items
        })
        params = {
          filters: {
            'compound.uid': { v: [val.compound.uid] },
            status: { v: [statuses.FINAL] },
          },
          page_size: 0,
        }
        medicinalProductsApi.getFiltered(params).then((resp) => {
          medicinalProducts.value = resp.data.items.map((item) => {
            item.name = `${item.name} (${dataFormating.names(item.dose_frequencies || [])})`
            return item
          })
        })
      } else {
        steps.value = [
          {
            name: 'type_of_treatment',
            title: t('StudyCompoundForm.step1_title'),
          },
        ]
      }
      if (val.compound_alias) {
        form.value.compound_alias = val.compound_alias
      }
      if (val.medicinal_product) {
        form.value.medicinalProduct = val.medicinal_product
      }
      if (val.dosage_form) {
        form.value.dosage_form_uid = val.dosage_form.term_uid
      }
      if (val.route_of_administration) {
        form.value.route_of_administration_uid =
          val.route_of_administration.term_uid
      }
      if (val.dispensed_in) {
        form.value.dispenser_uid = val.dispensed_in.term_uid
      }
      if (val.device) {
        form.value.delivery_device_uid = val.device.term_uid
      }
      if (val.strength_value) {
        form.value.strength_value_uid = val.strength_value.uid
      }
    }
  },
  { immediate: true }
)

watch(compoundAliases, (newValue) => {
  if (newValue) {
    // Auto-select preferred alias only for Create form.
    // Edit form should preserve the current value of compound alias.
    if (!props.studyCompound) {
      const preferedSynonym = compoundAliases.value.find(
        (item) => item.is_preferred_synonym
      )
      form.value.compound_alias = preferedSynonym
    }
  }
})

watch(
  () => form.value.compoundSimple,
  (newValue) => {
    showAlerts.value = false
    if (newValue) {
      if (
        !props.studyCompound ||
        props.studyCompound.compound.uid !== newValue.uid
      ) {
        form.value.compound_alias = null
      }
      form.value.medicinalProduct = null
      let params = {
        filters: {
          compound_uid: { v: [newValue.uid] },
          status: { v: [statuses.FINAL] },
        },
        page_size: 0,
      }
      compoundAliasesApi.getFiltered(params).then((resp) => {
        compoundAliases.value = resp.data.items
        showAlerts.value = true
      })
      params = {
        filters: {
          'compound.uid': { v: [newValue.uid] },
          status: { v: [statuses.FINAL] },
        },
        page_size: 0,
      }
      medicinalProductsApi.getFiltered(params).then((resp) => {
        medicinalProducts.value = resp.data.items.map((item) => {
          item.name = `${item.name} (${dataFormating.names(item.dose_frequencies || [])})`
          return item
        })
        showAlerts.value = true
      })
      if (newValue.uid) {
        compoundsApi.getObject(newValue.uid).then((resp) => {
          form.value.compound = resp.data
        })
      }
    }
  }
)
watch(
  () => form.value.medicinalProduct,
  (newValue) => {
    if (newValue) {
      activeSubstances.value = []
      medicinalProductsApi.getObject(newValue.uid).then((resp) => {
        resp.data.pharmaceutical_products.forEach((item) =>
          pharmaceuticalProducts.getObject(item.uid).then((resp) => {
            const ingredients = resp.data.formulations
              .map((formulation) => formulation.ingredients)
              .flat()
              .map((ingredient) => ingredient.active_substance)
              .flat()
            activeSubstances.value = activeSubstances.value.concat(ingredients)
          })
        )
      })
    }
  },
  { immediate: true }
)

onMounted(() => {
  const params = {
    filters: {
      status: { v: [statuses.FINAL] },
    },
    page_size: 0,
  }
  compoundsSimple.getFiltered(params).then((resp) => {
    compounds.value = resp.data.items
  })
  terms.getTermsByCodelist('typeOfTreatment').then((resp) => {
    typeOfTreatments.value = resp.data.items
  })
})

function close() {
  emit('close')
  notificationHub.clearErrors()
  form.value = getInitialForm()
  stepper.value.reset()
  naField.value.reset()
}
function getInitialForm() {
  return {
    compound: null,
    compoundSimple: null,
    compound_alias: null,
    medicinalProduct: null,
    type_of_treatment: null,
    dosage_form_uid: null,
    strength_value_uid: null,
    route_of_administration_uid: null,
    dispenser_uid: null,
    delivery_device_uid: null,
    other_info: null,
  }
}
function getInitialSteps() {
  return [
    {
      name: 'type_of_treatment',
      title: t('StudyCompoundForm.step1_title'),
    },
    {
      name: 'compoundAlias',
      title: t('StudyCompoundForm.step2_title'),
    },
    { name: 'compound', title: t('StudyCompoundForm.step3_title') },
  ]
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
}
function cleanTypeOfTreatment(value) {
  if (value) {
    steps.value = [
      {
        name: 'type_of_treatment',
        title: t('StudyCompoundForm.step1_title'),
      },
    ]
  } else {
    steps.value = getInitialSteps()
  }
}
function getPclassLabel(activeSubstance) {
  const labels = []
  if (activeSubstance.unii && activeSubstance.unii.pclass_name) {
    labels.push(activeSubstance.unii.pclass_name)
  }

  if (activeSubstance.unii && activeSubstance.unii.pclass_id) {
    labels.push(`(${activeSubstance.unii.pclass_id})`)
  }
  return labels.length ? labels.join(' ') : '-'
}
async function submit() {
  notificationHub.clearErrors()

  const data = JSON.parse(JSON.stringify(form.value))
  data.type_of_treatment_uid = data.type_of_treatment.term_uid
  delete data.type_of_treatment
  delete data.compound

  if (data.medicinalProduct) {
    data.medicinal_product_uid = data.medicinalProduct.uid
  }

  if (data.compound_alias) {
    data.compound_alias_uid = data.compound_alias.uid || null
  } else {
    data.reason_for_missing_null_value_uid = studyConstants.TERM_NOT_APPLICABLE
  }

  let action = null
  let notification = null
  let args = null
  let event
  if (!props.studyCompound) {
    action = 'addStudyCompound'
    notification = 'add_success'
    event = 'added'
    args = { studyUid: studiesGeneralStore.selectedStudy.uid, data }
  } else {
    action = 'updateStudyCompound'
    notification = 'update_success'
    args = {
      studyUid: studiesGeneralStore.selectedStudy.uid,
      studyCompoundUid: props.studyCompound.study_compound_uid,
      data,
    }
  }
  try {
    await studiesCompoundsStore[action](args)
    notificationHub.add({
      msg: t(`StudyCompoundForm.${notification}`),
    })
    if (event) {
      emit(event)
    }
    close()
  } finally {
    stepper.value.loading = false
  }
}
</script>

<style scoped>
.text-white {
  color: white !important;
}
</style>
