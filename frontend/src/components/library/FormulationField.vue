<template>
  <v-row>
    <v-col>
      <v-text-field
        v-model="form.formulation_name"
        :label="$t('Formulation.formulation')"
        @update:model-value="update()"
      />
    </v-col>
  </v-row>
  <v-row>
    <v-col>
      <v-autocomplete
        v-model="form.active_substance_uid"
        :label="$t('Formulation.active_substance')"
        :items="formulationsStore.activeSubstances"
        :item-title="getSubstanceTitle"
        item-value="uid"
        :filter-keys="[
          'raw.long_number',
          'raw.inn',
          'raw.short_number',
          'raw.unii.substance_unii',
          'raw.analyte_number',
        ]"
        :rules="[formRules.required]"
        @update:model-value="update()"
      >
        <template #item="{ props, internalItem: item }">
          <v-list-item v-bind="props" :title="getSubstanceTitle(item.raw)">
            <v-list-item-subtitle class="pa-2">
              {{ getSubstanceSubtitle(item.raw) }}
            </v-list-item-subtitle>
          </v-list-item>
        </template>
      </v-autocomplete>
    </v-col>
  </v-row>
  <v-row>
    <v-col cols="6">
      <NumericValueWithUnitField
        v-model="form.strength"
        :label="$t('Formulation.strength')"
        subset="Strength Unit"
        density="compact"
        @update:model-value="update()"
      />
    </v-col>
    <v-col cols="6">
      <NumericValueWithUnitField
        v-model="form.half_life"
        :label="$t('Formulation.half-life')"
        subset="Time Unit"
        density="compact"
        @update:model-value="update()"
      />
    </v-col>
  </v-row>
  <div class="text-body-large my-2 mt-6">
    {{ $t('CompoundForm.lag_times') }}
    <v-btn
      color="primary"
      size="x-small"
      icon="mdi-plus"
      variant="outlined"
      @click="addLagTime"
    />
  </div>
  <v-card
    v-for="(lag_time, index) in form.lag_times"
    :key="`lagtime-${index}`"
    style="position: relative"
    class="mb-6 border-b-thin"
    flat
  >
    <v-card-text class="lag-time">
      <v-row>
        <v-col cols="6">
          <v-autocomplete
            v-model="form.lag_times[index].sdtm_domain_uid"
            :label="$t('CompoundForm.sdtm_domain')"
            :items="formulationsStore.adverseEvents"
            item-title="sponsor_preferred_name"
            item-value="term_uid"
            clearable
            @update:model-value="update"
          />
        </v-col>
        <v-col cols="6">
          <NumericValueWithUnitField
            v-model="form.lag_times[index]"
            :label="$t('CompoundForm.lag_time')"
            subset="Time Unit"
            :initial-value="form.lag_times[index]"
            @update:model-value="update"
          />
        </v-col>
      </v-row>
    </v-card-text>
    <v-btn
      color="error"
      position="absolute"
      location="top right"
      size="x-small"
      icon="mdi-delete-outline"
      variant="outlined"
      @click="removeLagTime(index)"
    />
  </v-card>
</template>

<script setup>
import { inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useFormulationsStore } from '@/stores/library-formulations'
import NumericValueWithUnitField from '@/components/tools/NumericValueWithUnitField.vue'

const { t } = useI18n()

const formulationsStore = useFormulationsStore()
const formRules = inject('formRules')
const props = defineProps({
  modelValue: {
    type: Object,
    default: null,
  },
})
const emit = defineEmits(['update:modelValue'])

const form = ref({
  lag_times: [],
})

watch(
  () => props.modelValue,
  (value) => {
    if (value) {
      form.value = JSON.parse(JSON.stringify(value))
    } else {
      form.value = {
        lag_times: [],
      }
    }
  },
  { immediate: true }
)

function update() {
  emit('update:modelValue', form.value)
}

function addLagTime() {
  form.value.lag_times.push({})
  update()
}

function removeLagTime(index) {
  form.value.lag_times.splice(index, 1)
  update()
}

function getSubstanceTitle(item) {
  if (item.long_number) {
    return item.long_number
  }
  if (item.short_number) {
    return item.short_number
  }
  if (item.unii) {
    return item.unii.substance_unii
  }
  if (item.analyte_number) {
    return item.analyte_number
  }
  if (item.inn) {
    return item.inn
  }
  return '-'
}

function getSubstanceSubtitle(item) {
  let retVals = [
    `${t('ActiveSubstance.inn')}: ${item.inn ?? '-'}`,
    `${t('ActiveSubstance.analyte_number')}: ${item.analyte_number ?? '-'}`,
  ]
  return retVals.join(', ')
}
</script>

<style scoped>
.lag-time {
  position: relative;
  padding-left: 0px !important;
}
</style>
