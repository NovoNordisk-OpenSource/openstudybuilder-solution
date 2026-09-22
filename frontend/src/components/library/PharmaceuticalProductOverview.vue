<template>
  <v-card elevation="0" class="rounded-0">
    <v-card-text>
      <v-row>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('PharmaceuticalProduct.dosage_form') }}
        </v-col>
        <v-col cols="2">
          {{ props.pharmaceuticalProduct.dosage_forms[0].term_name }}
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('PharmaceuticalProduct.route_of_administration') }}
        </v-col>
        <v-col cols="2">
          {{ pharmaceuticalProduct.routes_of_administration[0].term_name }}
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('PharmaceuticalProduct.ingredients') }}
        </v-col>
        <v-col cols="10">
          <v-table>
            <thead>
              <tr class="text-left">
                <th scope="col">
                  {{ $t('Formulation.active_substance') }}
                </th>
                <th scope="col">
                  {{ $t('Formulation.strength') }}
                </th>
                <th scope="col">
                  {{ $t('Formulation.half-life') }}
                </th>
                <th scope="col">
                  {{ $t('Formulation.lag_times') }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="ingredient in pharmaceuticalProduct.formulations[0]
                  .ingredients"
                :key="ingredient.uid"
              >
                <td>
                  {{ getActiveSubstanceName(ingredient.active_substance) }}
                </td>
                <td>
                  {{ ingredient.strength?.value }}
                  {{ ingredient.strength?.unit_label }}
                </td>
                <td>
                  {{ ingredient.half_life?.value }}
                  {{ ingredient.half_life?.unit_label }}
                </td>
                <td>{{ displayLagTimes(ingredient) }}</td>
              </tr>
            </tbody>
          </v-table>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup>
const props = defineProps({
  pharmaceuticalProduct: {
    type: Object,
    default: null,
  },
})

function getActiveSubstanceName(item) {
  return item.inn || item.long_number
}

function displayLagTimes(item) {
  return item.lag_times
    .map(
      (lag_time) =>
        `${lag_time?.value} ${lag_time?.unit_label} (${lag_time?.sdtm_domain_label})`
    )
    .join(', ')
}
</script>
