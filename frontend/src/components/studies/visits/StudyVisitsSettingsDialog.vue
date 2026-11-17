<template>
  <SimpleFormDialog
    ref="formRef"
    :title="t('StudyVisitsSettings.title')"
    :open="open"
    max-width="700px"
    :no-saving="readOnly"
    :action-label="
      mode === 'assisted' || props.manualVisitMode
        ? t('_global.save')
        : t('StudyVisitsSettings.use_manual_mode')
    "
    @close="close"
    @submit="save"
  >
    <template #body>
      <v-form ref="observer">
        <v-btn-toggle
          v-model="mode"
          mandatory
          density="compact"
          color="nnBaseBlue"
          divided
          variant="outlined"
          class="mb-8"
          :disabled="readOnly"
          data-cy="visit-mode-toggle"
        >
          <v-btn value="assisted" class="px-6" data-cy="assisted-mode-btn">
            {{ t('StudyVisitsSettings.assisted_mode') }}
          </v-btn>

          <v-btn value="manual" class="px-6" data-cy="manual-mode-btn">
            {{ t('StudyVisitsSettings.manual_mode') }}
          </v-btn>
        </v-btn-toggle>

        <v-alert
          type="info"
          variant="tonal"
          icon="mdi-information-outline"
          class="info-box mb-10"
        >
          <div class="text-body-1">
            <p
              class="mb-5"
              v-html="sanitizeHTML(t('StudyVisitsSettings.assisted_mode_info'))"
            />

            <p
              class="mb-0"
              v-html="sanitizeHTML(t('StudyVisitsSettings.manual_mode_info'))"
            />
          </div>
        </v-alert>

        <v-checkbox
          v-if="mode === 'manual' && !props.manualVisitMode"
          v-model="manualModeConfirmed"
          :label="t('StudyVisitsSettings.manual_mode_checkbox')"
          :rules="[(v) => !!v || t('_errors.required')]"
          data-cy="manual-mode-confirm-checkbox"
        />

        <v-alert
          v-if="mode === 'assisted' && props.manualVisitMode"
          type="warning"
          variant="tonal"
          icon="mdi-alert-outline"
          class="mb-6"
        >
          {{ t('StudyVisitsSettings.assisted_mode_switch_back_info') }}
        </v-alert>

        <v-switch
          v-model="baselineAsZero"
          :label="t('ProtocolFlowchart.baseline_as_time_zero')"
          hide-details
          :disabled="readOnly"
          data-cy="baseline-as-time-zero-switch"
        />
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useEpochsStore } from '@/stores/studies-epochs'
import { useAccessGuard } from '@/composables/accessGuard'
import { sanitizeHTML } from '@/utils/sanitize'

const { t } = useI18n()
const studiesGeneralStore = useStudiesGeneralStore()
const epochsStore = useEpochsStore()
const accessGuard = useAccessGuard()
const roles = inject('roles')

// Same write gate as the visit toolbar's buttons
const readOnly = computed(
  () =>
    !accessGuard.checkPermission(roles.STUDY_WRITE) ||
    studiesGeneralStore.selectedStudyVersion !== null
)

const formRef = ref(null)
const mode = ref('assisted')
const manualModeConfirmed = ref(false)
const baselineAsZero = ref(false)

const emit = defineEmits(['close'])

const props = defineProps({
  open: Boolean,
  manualVisitMode: Boolean,
})

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      mode.value = props.manualVisitMode ? 'manual' : 'assisted'
      manualModeConfirmed.value = false
      baselineAsZero.value =
        studiesGeneralStore.soaPreferences?.baseline_as_time_zero ?? false
    }
  }
)

// Only changed settings are sent, so a retry after a partial failure sends just the remainder
async function save() {
  try {
    const manualVisitMode = mode.value === 'manual'
    if (manualVisitMode !== props.manualVisitMode) {
      await epochsStore.setStudyVisitMode(
        studiesGeneralStore.selectedStudy.uid,
        manualVisitMode
      )
    }
    const savedBaselineAsZero =
      studiesGeneralStore.soaPreferences?.baseline_as_time_zero ?? false
    if (baselineAsZero.value !== savedBaselineAsZero) {
      await studiesGeneralStore.setSoaPreferences({
        baseline_as_time_zero: baselineAsZero.value,
      })
    }
    emit('close')
  } catch (error) {
    // The error toast is already shown; the dialog stays open showing what is saved
    console.error('Failed to save the study visits settings', error)
  } finally {
    formRef.value.working = false
  }
}

function close() {
  emit('close')
}
</script>

<style scoped>
.info-box {
  border-radius: 16px;
}

.info-box :deep(.v-alert__content) {
  line-height: 1.55;
}
</style>
