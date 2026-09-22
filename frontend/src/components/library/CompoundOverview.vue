<template>
  <v-card elevation="0" class="rounded-0">
    <v-card-text>
      <v-row>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('_global.definition') }}
        </v-col>
        <v-col cols="10">
          <div
            v-html="sanitizeHTMLHandler(getHtmlLineBreaks(compound.definition))"
          />
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('CompoundOverview.compound_aliases') }}
        </v-col>
        <v-col cols="10">
          <v-table>
            <thead>
              <tr class="text-left">
                <th scope="col">
                  {{ $t('_global.name') }}
                </th>
                <th scope="col">
                  {{ $t('CompoundAlias.is_preferred_synonym') }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="alias in aliases" :key="alias.uid">
                <td>{{ alias.name }}</td>
                <td>{{ $filters.yesno(alias.is_preferred_synonym) }}</td>
              </tr>
            </tbody>
          </v-table>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('CompoundOverview.medicinal_products') }}
        </v-col>
        <v-col cols="10">
          <v-table>
            <thead>
              <tr class="text-left">
                <th scope="col">
                  {{ $t('_global.name') }}
                </th>
                <th scope="col">
                  {{ $t('MedicinalProduct.dose') }}
                </th>
                <th scope="col">
                  {{ $t('MedicinalProduct.frequency') }}
                </th>
                <th scope="col">
                  {{ $t('MedicinalProduct.delivery_device') }}
                </th>
                <th scope="col">
                  {{ $t('MedicinalProduct.dispenser') }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="product in medicinalProducts" :key="product.uid">
                <td>{{ product.name }}</td>
                <td>{{ displayDoseValues(product) }}</td>
                <td>{{ displayDoseFrequencies(product) }}</td>
                <td>{{ product.delivery_device?.name }}</td>
                <td>{{ product.dispenser?.name }}</td>
              </tr>
            </tbody>
          </v-table>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, watch } from 'vue'
import { sanitizeHTML } from '@/utils/sanitize'
import compoundAliasesApi from '@/api/concepts/compoundAliases'
import medicinalProductsApi from '@/api/concepts/medicinalProducts'
import dataFormating from '@/utils/dataFormating'

const props = defineProps({
  compound: {
    type: Object,
    default: null,
  },
})

const aliases = ref([])
const medicinalProducts = ref([])

watch(
  () => props.compound,
  (value) => {
    const params_mp = {
      filters: {
        'compound.uid': { v: [value.uid] },
      },
      page_size: 0,
    }
    const params_aliases = {
      filters: {
        compound_uid: { v: [value.uid] },
      },
      page_size: 0,
    }
    medicinalProductsApi.getFiltered(params_mp).then((resp) => {
      medicinalProducts.value = resp.data.items
    })
    compoundAliasesApi.getFiltered(params_aliases).then((resp) => {
      aliases.value = resp.data.items
    })
  }
)

function getHtmlLineBreaks(value) {
  return value ? value.replaceAll('\n', '<br />') : ''
}

function displayDoseValues(product) {
  return product.dose_values
    .map((dose) => `${dose.value} ${dose.unit_label}`)
    .join(', ')
}

function displayDoseFrequencies(product) {
  return dataFormating.names(product.dose_frequencies || [])
}

function sanitizeHTMLHandler(html) {
  return sanitizeHTML(html)
}
</script>

<style lang="scss" scoped>
.substance {
  border-bottom: 1px solid rgb(var(--v-theme-greyBackground));
  border-top: 1px solid rgb(var(--v-theme-greyBackground));
}
</style>
