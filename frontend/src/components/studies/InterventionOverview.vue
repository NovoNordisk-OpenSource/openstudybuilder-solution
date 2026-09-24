<template>
  <div style="overflow-x: auto">
    <v-skeleton-loader
      v-if="studiesCompoundsStore.studyCompounds__Loading"
      class="mx-auto"
      max-width="800px"
      type="table-heading, table-thead, table-tbody"
    />
    <div
      v-if="
        !studiesCompoundsStore.studyCompounds__Loading &&
        !studiesCompoundsStore.studyCompounds.length
      "
      class="mx-4 my-8"
    >
      {{ $t('InterventionOverview.no_intervention_selected') }}
    </div>
    <table
      v-if="
        !studiesCompoundsStore.studyCompounds__Loading &&
        studiesCompoundsStore.studyCompounds.length
      "
      class="mt-4"
      :aria-label="$t('InterventionOverview.table_caption')"
    >
      <thead>
        <tr>
          <th class="no-border" scope="col" />
          <th :colspan="cols" scope="col">
            {{ $t('InterventionOverview.study_compounds') }}
          </th>
        </tr>
        <tr>
          <th scope="col">
            {{ $t('InterventionOverview.first_col_title') }}
          </th>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`header-${index}`"
          >
            <template v-if="studyCompound.compound">
              {{ studyCompound.compound.name }}
            </template>
          </td>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>{{ $t('InterventionOverview.compound_aliases') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`alias-${index}`"
            class="no-padding"
          >
            <table v-if="studyCompound.compound" class="no-border">
              <tbody>
                <tr
                  v-for="(alias, aliasIndex) in compoundAliases[
                    studyCompound.compound.uid
                  ]"
                  :key="`alias-${index}-${aliasIndex}`"
                  class="no-padding"
                  :class="{ 'border-top': aliasIndex > 0 }"
                >
                  <td class="no-border">
                    {{ alias.name }} ({{
                      $filters.yesno(alias.is_preferred_synonym)
                    }})
                  </td>
                </tr>
              </tbody>
            </table>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.compound_def') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`def-${index}`"
          >
            <template v-if="studyCompound.compound">
              {{ studyCompound.compound.definition }}
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.medicinal_product') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`mp-${index}`"
          >
            {{
              studyCompound.medicinal_product
                ? studyCompound.medicinal_product.name
                : '-'
            }}
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.type_of_treatment') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`tot-${index}`"
          >
            {{
              studyCompound.type_of_treatment
                ? studyCompound.type_of_treatment.term_name
                : ''
            }}
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.reason_for_missing') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`rfm-${index}`"
          >
            <template v-if="studyCompound.reason_for_missing_null_value">
              {{ studyCompound.reason_for_missing_null_value.term_name }}
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.compound_dosing') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`dosing-${index}`"
            class="no-padding"
          >
            <table
              v-if="studiesCompoundsStore.studyCompoundDosings"
              class="no-border"
            >
              <tr
                v-for="(
                  compoundDosing, dosingIndex
                ) in studiesCompoundsStore.studyCompoundDosings.filter(
                  (d) =>
                    d.study_compound.study_compound_uid ===
                    studyCompound.study_compound_uid
                )"
                :key="`lg-${index}-${dosingIndex}`"
                :class="{ 'border-top': dosingIndex > 0 }"
              >
                <td class="no-border half-size">
                  {{ compoundDosing.study_element.short_name }}:
                  <template v-if="compoundDosing.dose_value">
                    {{ compoundDosing.dose_value.value }}
                    {{ compoundDosing.dose_value.unit_label }},
                  </template>

                  <template v-if="displayDoseFrequencies(compoundDosing)">
                    {{ displayDoseFrequencies(compoundDosing) }}
                  </template>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.dispensed_in') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`dispensed-${index}`"
          >
            {{ studyCompound.medicinal_product.dispenser?.name }}
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.delivery_device') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`device-${index}`"
          >
            {{ studyCompound.medicinal_product.delivery_device?.name }}
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.pharmaceutical_dosage_form') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`dosage-${index}`"
          >
            <template
              v-if="pharmaceuticalProducts[studyCompound.medicinal_product.uid]"
            >
              {{
                pharmaceuticalProducts[
                  studyCompound.medicinal_product.uid
                ].dosage_forms
                  .map((form) => form.term_name)
                  .join(', ')
              }}
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.route_of_admin') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`roa-${index}`"
          >
            <template
              v-if="pharmaceuticalProducts[studyCompound.medicinal_product.uid]"
            >
              {{
                pharmaceuticalProducts[
                  studyCompound.medicinal_product.uid
                ].routes_of_administration
                  .map((x) => x.term_name)
                  .join(', ')
              }}
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.active_substances') }}</td>
          <td
            v-for="(
              studyCompound, index
            ) in studiesCompoundsStore.studyCompounds"
            :key="`sub-${index}`"
            class="no-padding"
          >
            <template
              v-if="pharmaceuticalProducts[studyCompound.medicinal_product.uid]"
            >
              <table
                v-for="(ingredient, ingrIndex) in getPharmaProductIngredients(
                  pharmaceuticalProducts[studyCompound.medicinal_product.uid]
                )"
                :key="`ingredient-${index}-${ingredient.id}`"
                :class="{ 'border-top': ingrIndex > 0 }"
              >
                <tbody class="ingredient">
                  <tr>
                    <td class="no-border half-size">
                      {{ ingredient.title }}<br />
                      <span>{{ $t('InterventionOverview.half_life') }}</span
                      >: {{ ingredient.halfLife }}<br />
                      <span>{{ $t('InterventionOverview.lag_time') }}</span
                      >: {{ ingredient.lagTimes }}<br />
                      <span>{{
                        $t('InterventionOverview.analyte_number')
                      }}</span
                      >: {{ ingredient.analyte_number }}<br />
                      <span>{{
                        $t('InterventionOverview.compound_number_long')
                      }}</span
                      >: {{ ingredient.long_number }}<br />
                      <span>{{
                        $t('InterventionOverview.compound_number_short')
                      }}</span
                      >: {{ ingredient.short_number }}<br />
                      <span>{{ $t('InterventionOverview.inn') }}</span
                      >: {{ ingredient.inn }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </template>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import { computed } from 'vue'
import compoundAliases from '@/api/concepts/compoundAliases'
import { useStudiesCompoundsStore } from '@/stores/studies-compounds'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import pharmaceuticalProductsApi from '@/api/concepts/pharmaceuticalProducts'
import { usePharmaceuticalProducts } from '@/composables/pharmaceuticalProducts'
const { getIngredientName } = usePharmaceuticalProducts()

export default {
  setup() {
    const studiesCompoundsStore = useStudiesCompoundsStore()
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
      studiesCompoundsStore,
    }
  },
  data() {
    return {
      compoundAliases: {},
      pharmaceuticalProducts: [],
    }
  },
  computed: {
    cols() {
      return this.studiesCompoundsStore.studyCompounds.length
        ? this.studiesCompoundsStore.studyCompounds.length
        : 1
    },
  },
  watch: {
    studyCompounds() {
      this.getAllCompoundAliases()
    },
  },
  mounted() {
    this.studiesCompoundsStore
      .fetchStudyCompounds({
        studyUid: this.selectedStudy.uid,
        page_size: 0,
      })
      .then(() => {
        this.getAllCompoundAliases()
        this.getAllPharmaProducts()
      })
    this.studiesCompoundsStore.fetchStudyCompoundDosings(
      this.selectedStudy.uid,
      0
    )
  },
  methods: {
    displayDoseFrequencies(compoundDosing) {
      return compoundDosing.dose_frequency?.term_name
        ? compoundDosing.dose_frequency.term_name
        : ''
    },
    getCompoundAliases(compoundUid) {
      const params = {
        filters: {
          compound_uid: { v: [compoundUid], op: 'eq' },
        },
      }
      compoundAliases.getFiltered(params).then((resp) => {
        this.compoundAliases[compoundUid] = resp.data.items.sort((a, b) =>
          a.is_preferred_synonym > b.is_preferred_synonym ? -1 : 1
        )
      })
    },
    getAllCompoundAliases() {
      for (const studyCompound of this.studiesCompoundsStore.studyCompounds) {
        if (
          !studyCompound.compound ||
          this.compoundAliases[studyCompound.compound.uid] !== undefined
        ) {
          continue
        }
        this.compoundAliases[studyCompound.compound.uid] = []
        this.getCompoundAliases(studyCompound.compound.uid)
      }
    },
    getAllPharmaProducts() {
      for (const studyCompound of this.studiesCompoundsStore.studyCompounds) {
        if (!studyCompound.medicinal_product) {
          continue
        }

        this.pharmaceuticalProducts = {}
        for (const item of studyCompound.medicinal_product
          .pharmaceutical_products) {
          pharmaceuticalProductsApi.getObject(item.uid).then((resp) => {
            this.pharmaceuticalProducts[studyCompound.medicinal_product.uid] =
              resp.data
          })
        }
      }
    },
    getPharmaProductIngredients(pharmaProduct) {
      let productIngredients = pharmaProduct.formulations.map((formulation) => {
        return formulation.ingredients?.map((ingredient) => {
          return {
            id: `${pharmaProduct.uid}-ingredient-${ingredient.active_substance.uid}`,
            title: getIngredientName(ingredient),
            halfLife:
              ingredient.half_life?.value != null
                ? `${ingredient.half_life.value} ${ingredient.half_life.unit_label}`
                : '',
            lagTimes: ingredient.lag_times
              .map(
                (lag_time) =>
                  `${lag_time?.value} ${lag_time?.unit_label} (${lag_time?.sdtm_domain_label})`
              )
              .join(', '),
            strength: `${ingredient.strength?.value} ${ingredient.strength?.unit_label}`,
            long_number: ingredient.active_substance.long_number
              ? ingredient.active_substance.long_number
              : '-',
            short_number: ingredient.active_substance.short_number
              ? ingredient.active_substance.short_number
              : '-',
            inn: ingredient.active_substance.inn
              ? ingredient.active_substance.inn
              : '-',
            analyte_number: ingredient.active_substance.analyte_number
              ? ingredient.active_substance.analyte_number
              : '-',
          }
        })
      })
      productIngredients = productIngredients
        .flatMap((x) => x)
        .sort((a, b) => a.title.localeCompare(b.title))
      return productIngredients
    },
  },
}
</script>

<style scoped lang="scss">
table {
  width: 100%;
  text-align: left;

  border-spacing: 0px;
  border-collapse: collapse;
}
.no-border {
  border: 0 !important;
}
.border-left {
  border: 0;
  border-left: 1px solid black;
}
.border-top {
  border: 0;
  border-top: 1px solid black;
}
.no-padding {
  padding: 0;
}
.half-size {
  width: 50%;
}
tr {
  padding: 4px;
}
td,
th {
  border: 1px solid black;
  padding: 4px 8px;
  vertical-align: top;
}

.ingredient span {
  font-weight: 500;
  padding-left: 12px;
}
</style>
