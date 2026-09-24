<template>
  <v-card color="nnSeaBlue200" flat>
    <v-card-text class="text-nnTrueBlue">
      <div class="d-flex align-start mb-2">
        <div style="width: 70px">
          <v-btn
            :icon="getExpandIcon(medProductExpanded)"
            variant="text"
            density="compact"
            @click="medProductExpanded = !medProductExpanded"
          />
          <slot name="prepend" />
        </div>
        <div style="width: 25%" class="mr-4">
          <div class="text-body-3">
            {{ $t('MedicinalProduct.medicinal_product') }}
          </div>
          <div class="text-body-medium font-weight-bold">
            {{ product.name }}
          </div>
        </div>
        <div style="width: 10%">
          <div class="text-body-3">{{ $t('MedicinalProduct.dose') }}</div>
          <div class="text-body-3 font-weight-bold">{{ doseValues }}</div>
        </div>
        <div style="width: 10%">
          <div class="text-body-3">{{ $t('MedicinalProduct.frequency') }}</div>
          <div class="text-body-3 font-weight-bold">{{ frequency }}</div>
        </div>
        <div style="width: 10%">
          <div class="text-body-3">
            {{ $t('MedicinalProduct.delivery_device') }}
          </div>
          <div class="text-body-3 font-weight-bold">{{ deliveryDevice }}</div>
        </div>
        <div style="width: 10%">
          <div class="text-body-3">{{ $t('MedicinalProduct.dispenser') }}</div>
          <div class="text-body-3 font-weight-bold">{{ dispenser }}</div>
        </div>
        <div style="width: 18%">
          <div class="text-body-3">{{ $t('_global.modified') }}</div>
          <div class="text-body-3 font-weight-bold">
            {{ $filters.date(product.start_date) }}
          </div>
        </div>
        <div style="width: 7%">
          <div class="text-body-3">{{ $t('_global.version') }}</div>
          <div class="text-body-3 font-weight-bold">{{ product.version }}</div>
        </div>
        <div class="flex-grow-1">
          <div class="text-body-3">{{ $t('_global.status') }}</div>
          <StatusChip :status="product.status" :outlined="false" label />
        </div>
      </div>
      <template v-if="medProductExpanded">
        <v-progress-linear v-if="loading" color="primary" indeterminate />
        <v-card
          v-for="pharmaProduct in pharmaceuticalProducts"
          :key="pharmaProduct.uid"
          color="nnSeaBlue100"
          flat
          class="mb-2"
        >
          <v-card-text class="text-nnTrueBlue">
            <div class="d-flex align-start mb-2">
              <div style="width: 50px">
                <v-btn
                  :icon="getExpandIcon(pharmaProductStates[pharmaProduct.uid])"
                  variant="text"
                  density="compact"
                  @click="
                    pharmaProductStates[pharmaProduct.uid] =
                      !pharmaProductStates[pharmaProduct.uid]
                  "
                />
              </div>
              <div style="width: 40%">
                <div class="text-body-3">
                  {{ $t('PharmaceuticalProduct.title') }}
                </div>
                <div class="text-body-medium font-weight-bold">
                  {{ getPharmaProductName(pharmaProduct) }}
                </div>
              </div>
              <div style="width: 23%">
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
            <template v-if="pharmaProductStates[pharmaProduct.uid]">
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
            </template>
          </v-card-text>
        </v-card>
      </template>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { usePharmaceuticalProducts } from '@/composables/pharmaceuticalProducts'
import pharmaceuticalProductsApi from '@/api/concepts/pharmaceuticalProducts'
import dataFormating from '@/utils/dataFormating'
import StatusChip from '@/components/tools/StatusChip.vue'

const { getIngredientName } = usePharmaceuticalProducts()

const props = defineProps({
  product: {
    type: Object,
    default: null,
  },
})

const medProductExpanded = ref(false)
const pharmaProductStates = ref({})
const pharmaceuticalProducts = ref(null)
const loading = ref(false)
const doseValues = computed(() => {
  const result = props.product.dose_values
    .map((dose) => `${dose.value} ${dose.unit_label}`)
    .join(', ')
  return result || '-'
})

const frequency = computed(() => {
  return dataFormating.names(props.product.dose_frequencies || []) || '-'
})

const deliveryDevice = computed(() => {
  return props.product.delivery_device?.name || '-'
})

const dispenser = computed(() => {
  return props.product.dispenser?.name || '-'
})

function getExpandIcon(value) {
  return value ? 'mdi-chevron-down' : 'mdi-chevron-right'
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

function getPharmaProductName(pharmaProduct) {
  const ingredientNames = getPharmaProductIngredients(pharmaProduct).map(
    (ingredient) => ingredient.title
  )
  return ingredientNames.join(', ')
}

watch(medProductExpanded, async (value) => {
  if (value && !pharmaceuticalProducts.value) {
    pharmaceuticalProducts.value = []
    loading.value = true
    for (const item of props.product.pharmaceutical_products) {
      const resp = await pharmaceuticalProductsApi.getObject(item.uid)
      pharmaceuticalProducts.value.push(resp.data)
      pharmaProductStates.value[resp.data.uid] = true
    }
    loading.value = false
  }
})
</script>
