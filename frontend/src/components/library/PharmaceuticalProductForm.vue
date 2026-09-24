<template>
  <SimpleFormDialog
    ref="formRef"
    :title="title"
    :help-items="helpItems"
    :open="open"
    max-width="900px"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="form.dosage_form_uid"
              :label="$t('PharmaceuticalProduct.dosage_form')"
              :items="dosageForms"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="form.route_of_administration_uid"
              :label="$t('PharmaceuticalProduct.route_of_administration')"
              :items="routesOfAdministration"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <div class="text-headline-small mb-2">
              {{ $t('PharmaceuticalProductForm.ingredients') }}
              <v-btn
                color="primary"
                size="x-small"
                icon="mdi-plus"
                variant="outlined"
                @click="addIngredient"
              />
            </div>
            <v-card
              v-for="(formulation, index) in form.formulations"
              :key="`formulation-${index}`"
              class="mb-6"
              style="position: relative"
            >
              <v-card-text>
                <FormulationField v-model="form.formulations[index]" />
              </v-card-text>
              <v-btn
                v-if="index !== 0"
                color="error"
                position="absolute"
                location="top right"
                size="x-small"
                icon="mdi-delete-outline"
                variant="outlined"
                @click="removeIngredient(index)"
              />
            </v-card>
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useNumericValues } from '@/composables/numericValues'
import { useFormulationsStore } from '@/stores/library-formulations'
import _isEmpty from 'lodash/isEmpty'
import FormulationField from '@/components/library/FormulationField.vue'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import libConstants from '@/constants/libraries'
import lagTimes from '@/api/concepts/lagTimes'
import termsApi from '@/api/controlledTerminology/terms'
import api from '@/api/concepts/pharmaceuticalProducts'

const { t } = useI18n()
const formulationsStore = useFormulationsStore()
const notificationHub = inject('notificationHub')
const formRules = inject('formRules')
const { createNumericValue } = useNumericValues()
const props = defineProps({
  pharmaceuticalProductUid: {
    type: String,
    default: undefined,
  },
  open: Boolean,
})
const emit = defineEmits(['close', 'created', 'updated'])

const form = ref(getInitialForm())
const formRef = ref()
const dosageForms = ref([])
const routesOfAdministration = ref([])

const title = computed(() => {
  return props.pharmaceuticalProductUid
    ? t('PharmaceuticalProductForm.edit_title')
    : t('PharmaceuticalProductForm.add_title')
})

const helpItems = [
  'PharmaceuticalProduct.dosage_form',
  'PharmaceuticalProduct.route_of_administration',
  'PharmaceuticalProductForm.ingredients',
]

watch(
  () => props.pharmaceuticalProductUid,
  (value) => {
    if (value) {
      loadPharmaceuticalProduct(value)
    } else {
      form.value = getInitialForm()
    }
  },
  { immediate: true }
)

function getInitialForm() {
  return {
    formulations: [
      {
        lag_times: [],
      },
    ],
  }
}

function loadPharmaceuticalProduct(uid) {
  api.getObject(uid).then((resp) => {
    if (resp.data.dosage_forms && resp.data.dosage_forms.length) {
      form.value.dosage_form_uid = resp.data.dosage_forms[0].term_uid
    }
    if (
      resp.data.routes_of_administration &&
      resp.data.routes_of_administration.length
    ) {
      form.value.route_of_administration_uid =
        resp.data.routes_of_administration[0].term_uid
    }
    if (resp.data.formulations && resp.data.formulations.length) {
      form.value.formulations = []
      for (const ingredient of resp.data.formulations[0].ingredients) {
        form.value.formulations.push({
          formulation_name: ingredient.formulation_name,
          active_substance_uid: ingredient.active_substance.uid,
          lag_times: ingredient.lag_times.length ? ingredient.lag_times : [{}],
          strength: ingredient.strength,
          half_life: ingredient.half_life,
        })
      }
    }
  })
}

function addIngredient() {
  form.value.formulations.push({ lag_times: [] })
}

function removeIngredient(index) {
  form.value.formulations.splice(index, 1)
}

async function createLagTime(item) {
  item.library_name = libConstants.LIBRARY_SPONSOR
  const resp = await lagTimes.create(item)
  return resp.data.uid
}

function close() {
  emit('close')
  notificationHub.clearErrors()
  form.value = getInitialForm()
}

async function addProduct(data) {
  data.library_name = libConstants.LIBRARY_SPONSOR
  await api.create(data)
  emit('created')
  notificationHub.add({
    msg: t('PharmaceuticalProductForm.add_success'),
    type: 'success',
  })
}

async function updateProduct(data) {
  data.change_description = t('_global.work_in_progress')
  await api.update(props.pharmaceuticalProductUid, data)
  emit('updated')
  notificationHub.add({
    msg: t('PharmaceuticalProductForm.update_success'),
    type: 'success',
  })
}

async function submit() {
  notificationHub.clearErrors()

  const data = {}
  if (form.value.dosage_form_uid) {
    data.dosage_form_uids = [form.value.dosage_form_uid]
  }
  if (form.value.route_of_administration_uid) {
    data.route_of_administration_uids = [form.value.route_of_administration_uid]
  }
  const ingredients = []
  for (const ingredient of form.value.formulations) {
    if (_isEmpty(ingredient)) {
      continue
    }
    const finalIngredient = {}
    finalIngredient.formulation_name = ingredient.formulation_name
    finalIngredient.active_substance_uid = ingredient.active_substance_uid
    if (ingredient.strength) {
      if (
        ingredient.strength.value &&
        ingredient.strength.unit_definition_uid
      ) {
        finalIngredient.strength_uid = await createNumericValue(
          ingredient.strength
        )
      }
    }
    if (ingredient.half_life) {
      if (
        ingredient.half_life.value &&
        ingredient.half_life.unit_definition_uid
      ) {
        finalIngredient.half_life_uid = await createNumericValue(
          ingredient.half_life
        )
      }
    }
    finalIngredient.lag_time_uids = []
    if (ingredient.lag_times) {
      for (const item of ingredient.lag_times) {
        if (item.value && item.unit_definition_uid && item.sdtm_domain_uid) {
          finalIngredient.lag_time_uids.push(await createLagTime(item))
        }
      }
    }
    ingredients.push(finalIngredient)
  }
  data.formulations = [{ ingredients }]
  try {
    if (!props.pharmaceuticalProductUid) {
      await addProduct(data)
    } else {
      await updateProduct(data)
    }
    close()
  } finally {
    formRef.value.working = false
  }
}

formulationsStore.initialize()
termsApi.getTermsByCodelist('dosageForm', { all: true }).then((resp) => {
  dosageForms.value = resp.data.items
})
termsApi
  .getTermsByCodelist('routeOfAdministration', { all: true })
  .then((resp) => {
    routesOfAdministration.value = resp.data.items
  })
</script>

<style lang="scss" scoped>
.sub-v-card {
  margin-bottom: 25px;
}
</style>
