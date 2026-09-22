<template>
  <v-card bg-color="dfltBackground" rounded="xl">
    <v-card-title class="d-flex align-center">
      <span class="dialog-title">{{
        $t('ProtocolFlowchart.soa_settings')
      }}</span>
    </v-card-title>
    <v-card-text class="mt-4">
      <div class="bg-white">
        <v-row>
          <label class="v-label ml-6">
            {{ $t('ProtocolFlowchart.time_unit') }}
          </label>
        </v-row>
        <v-row>
          <v-radio-group
            v-model="preferredTimeUnit"
            class="ml-4"
            hide-details
            :disabled="!accessGuard.checkPermission($roles.STUDY_WRITE)"
          >
            <v-radio :label="$t('ProtocolFlowchart.day')" value="day" />
            <v-radio :label="$t('ProtocolFlowchart.week')" value="week" />
          </v-radio-group>
        </v-row>
        <v-row>
          <v-switch
            v-model="baselineAsZero"
            :label="$t('ProtocolFlowchart.baseline_as_time_zero')"
            hide-details
            class="ml-6"
            :disabled="!accessGuard.checkPermission($roles.STUDY_WRITE)"
          />
        </v-row>
        <v-alert
          density="compact"
          type="info"
          elevation="1"
          class="text-white mt-4"
          :text="$t('ProtocolFlowchart.soa_settings_message')"
        />
      </div>
    </v-card-text>
    <v-card-actions class="mb-2 px-6 py-2">
      <v-spacer />
      <v-btn
        class="secondary-btn"
        variant="outlined"
        rounded
        elevation="1"
        width="120px"
        @click="cancel"
      >
        {{ $t('_global.cancel') }}
      </v-btn>
      <v-btn
        color="secondary"
        variant="flat"
        rounded
        elevation="1"
        width="120px"
        @click="submit"
      >
        {{ $t('_global.save') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>
<script setup>
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useAccessGuard } from '@/composables/accessGuard'
import { watch, computed, onMounted, ref } from 'vue'
import units from '@/api/units'
import unitConstants from '@/constants/units'

const studiesGeneralStore = useStudiesGeneralStore()
const accessGuard = useAccessGuard()
const emit = defineEmits(['close'])

const preferredTimeUnits = ref([])
const preferredTimeUnit = ref(null)
const baselineAsZero = ref(null)

const soaPreferredTimeUnit = computed(() => {
  return studiesGeneralStore.soaPreferredTimeUnit
})
const soaPreferences = computed(() => {
  return studiesGeneralStore.soaPreferences
})

watch(soaPreferences, () => {
  units
    .getBySubset(unitConstants.TIME_UNIT_SUBSET_STUDY_PREFERRED_TIME_UNIT)
    .then((resp) => {
      preferredTimeUnits.value = resp.data.items
    })
  if (soaPreferredTimeUnit.value) {
    preferredTimeUnit.value = soaPreferredTimeUnit.value.time_unit_name
  }
  baselineAsZero.value = soaPreferences.value.baseline_as_time_zero
})

onMounted(() => {
  studiesGeneralStore.getSoaPreferences()
})

async function submit() {
  await updatePreferredTimeUnit()
  await updateSoaPreferences()
  emit('close')
}
function cancel() {
  emit('close')
}

async function updatePreferredTimeUnit() {
  if (soaPreferredTimeUnit.value.time_unit_name === preferredTimeUnit.value) {
    return
  }
  for (const timeUnit of preferredTimeUnits.value) {
    if (timeUnit.name === preferredTimeUnit.value) {
      await studiesGeneralStore.setStudyPreferredTimeUnit({
        timeUnitUid: timeUnit.uid,
        protocolSoa: true,
      })
      break
    }
  }
}

async function updateSoaPreferences() {
  await studiesGeneralStore.setSoaPreferences({
    baseline_as_time_zero: baselineAsZero.value,
  })
}
</script>
