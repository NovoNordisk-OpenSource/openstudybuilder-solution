<template>
  <div>
    <div class="d-flex page-title">
      {{ $t('StudyCompoundTable.study_compound') }}
      <v-spacer />
      <v-btn
        size="small"
        :title="$t('_global.close')"
        class="ml-2"
        icon="mdi-close"
        variant="text"
        @click="close"
      />
    </div>
    <v-card color="nnSeaBlue200" flat class="pl-4">
      <v-card-text class="text-nnTrueBlue">
        <div class="d-flex align-start mb-10">
          <div style="width: 40%" class="mr-4">
            <div class="text-body-3">
              {{ $t('StudyCompoundTable.compound') }}
            </div>
            <div class="text-body-medium font-weight-bold">
              {{ product.compound.name }}
            </div>
          </div>
          <div style="width: 60%" class="mr-4">
            <div class="text-body-3">
              {{ $t('StudyCompoundTable.type_of_treatment') }}
            </div>
            <div class="text-body-3 font-weight-bold">
              {{ compound.type_of_treatment.term_name }}
            </div>
          </div>
        </div>

        <div class="d-flex align-start mb-3">
          <div style="width: 40%" class="mr-4">
            <div class="text-body-3">
              {{ $t('MedicinalProduct.medicinal_product') }}
            </div>
            <div class="text-body-medium font-weight-bold">
              {{ product.name }}
            </div>
          </div>
          <div style="width: 15%">
            <div class="text-body-3">{{ $t('MedicinalProduct.dose') }}</div>
            <div class="text-body-3 font-weight-bold">{{ doseValues }}</div>
          </div>
          <div style="width: 15%">
            <div class="text-body-3">
              {{ $t('MedicinalProduct.frequency') }}
            </div>
            <div class="text-body-3 font-weight-bold">{{ frequency }}</div>
          </div>
          <div style="width: 15%">
            <div class="text-body-3">
              {{ $t('MedicinalProduct.delivery_device') }}
            </div>
            <div class="text-body-3 font-weight-bold">{{ deliveryDevice }}</div>
          </div>
          <div style="width: 15%">
            <div class="text-body-3">
              {{ $t('MedicinalProduct.dispenser') }}
            </div>
            <div class="text-body-3 font-weight-bold">{{ dispenser }}</div>
          </div>
        </div>
        <v-card
          v-for="pharmaProduct in pharmaceuticalProducts"
          :key="pharmaProduct.uid"
          color="nnSeaBlue100"
          flat
          class="mb-2 pl-4"
        >
          <v-card-text class="text-nnTrueBlue">
            <div class="d-flex align-start mb-3">
              <div style="width: 40%">
                <div class="text-body-3">
                  {{ $t('PharmaceuticalProduct.title') }}
                </div>
                <div class="text-body-medium font-weight-bold">
                  {{ pharmaProduct.uid }}
                </div>
              </div>
              <div style="width: 20%">
                <div class="text-body-3">
                  {{ $t('PharmaceuticalProduct.dosage_form') }}
                </div>
                <div class="text-body-3 font-weight-bold">
                  {{ getDosageForms(pharmaProduct) }}
                </div>
              </div>
              <div>
                <div class="text-body-3">
                  {{ $t('PharmaceuticalProduct.route_of_administration') }}
                </div>
                <div class="text-body-3 font-weight-bold">
                  {{ getRoutesOfAdmin(pharmaProduct) }}
                </div>
              </div>
            </div>
            <v-card
              v-for="ingredient in getPharmaProductIngredients(pharmaProduct)"
              :key="ingredient.id"
              flat
              class="mb-2"
            >
              <v-card-text class="text-nnTrueBlue">
                <div class="d-flex align-start">
                  <div style="width: 40px">
                    <v-icon icon="mdi-flask" color="nnTrueBlue" />
                  </div>
                  <div style="width: 40%">
                    <div class="text-body-3">
                      {{ $t('Formulation.active_substance') }}
                    </div>
                    <div class="text-body-medium font-weight-bold">
                      {{ ingredient.title }}
                    </div>
                  </div>
                  <div style="width: 12%">
                    <div class="text-body-3">
                      {{ $t('Formulation.strength') }}
                    </div>
                    <div class="text-body-3 font-weight-bold">
                      {{ ingredient.strength || '-' }}
                    </div>
                  </div>
                  <div style="width: 12%">
                    <div class="text-body-3">
                      {{ $t('Formulation.half-life') }}
                    </div>
                    <div class="text-body-3 font-weight-bold">
                      {{ ingredient.halfLife }}
                    </div>
                  </div>
                  <div>
                    <div class="text-body-3">
                      {{ $t('Formulation.lag_times') }}
                    </div>
                    <div class="text-body-3 font-weight-bold">
                      {{ ingredient.lagTimes || '-' }}
                    </div>
                  </div>
                </div>
              </v-card-text>
            </v-card>
          </v-card-text>
        </v-card>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import study from '@/api/study'
import { computed, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { usePharmaceuticalProducts } from '@/composables/pharmaceuticalProducts'
import pharmaceuticalProductsApi from '@/api/concepts/pharmaceuticalProducts'
import dataFormating from '@/utils/dataFormating'

const route = useRoute()
const router = useRouter()
const product = ref({})
const compound = ref({})
const pharmaceuticalProducts = ref([])
const loaded = ref(false)
const { getIngredientName } = usePharmaceuticalProducts()

const doseValues = computed(() => {
  const result = product.value.dose_values
    .map((dose) => `${dose.value} ${dose.unit_label}`)
    .join(', ')
  return result || '-'
})

const frequency = computed(() => {
  return dataFormating.names(product.value.dose_frequencies || []) || '-'
})

const deliveryDevice = computed(() => {
  return product.value.delivery_device?.name || '-'
})

const dispenser = computed(() => {
  return product.value.dispenser?.name || '-'
})

study.getStudyCompound(route.params.study_id, route.params.id).then((resp) => {
  compound.value = resp.data
  product.value = compound.value.medicinal_product
  loaded.value = true

  pharmaceuticalProducts.value = []
  for (const item of product.value.pharmaceutical_products) {
    pharmaceuticalProductsApi.getObject(item.uid).then((resp) => {
      pharmaceuticalProducts.value.push(resp.data)
    })
  }
})

function close() {
  router.go(-1)
}

function getDosageForms(pharmaProduct) {
  const result = pharmaProduct.dosage_forms
    ?.map((form) => form.term_name)
    .join(', ')
  return result || '-'
}

function getRoutesOfAdmin(pharmaProduct) {
  const result = pharmaProduct.routes_of_administration
    ?.map((route) => route.term_name)
    .join(', ')
  return result || '-'
}

function getPharmaProductIngredients(pharmaProduct) {
  let productIngredients = pharmaProduct.formulations.map((formulation) => {
    return formulation.ingredients?.map((ingredient) => {
      return {
        id: `${pharmaProduct.uid}-ingredient-${ingredient.active_substance.long_number}`,
        title: getIngredientName(ingredient),
        halfLife: ingredient.half_life
          ? `${ingredient.half_life.value} ${ingredient.half_life.unit_label}`
          : '-',
        lagTimes: ingredient.lag_times
          .map(
            (lag_time) =>
              `${lag_time?.value} ${lag_time?.unit_label} (${lag_time?.sdtm_domain_label})`
          )
          .join(', '),
        strength: ingredient.strength
          ? `${ingredient.strength.value} ${ingredient.strength.unit_label}`
          : '-',
      }
    })
  })

  productIngredients = productIngredients
    .flatMap((x) => x)
    .sort((a, b) => a.title.localeCompare(b.title))
  return productIngredients
}
</script>
