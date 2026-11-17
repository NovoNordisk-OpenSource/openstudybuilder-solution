<template>
  <SimpleFormDialog
    ref="formRef"
    :title="
      $t('StudyVisitForm.duplicate_visit', {
        visit_name: props.studyVisit?.visit_name,
        visit_short_name: props.studyVisit?.visit_short_name,
        timing: props.studyVisit?.time_value,
        time_unit: props.studyVisit?.time_unit_name,
      })
    "
    :open="open"
    max-width="900px"
    :help-items="helpItems"
    :cancel-label="cancelLabel"
    :no-saving="disableSaving"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <div
          v-for="(visit, index) in form.visits"
          :key="visit.id"
          class="d-flex align-start ga-2"
        >
          <v-text-field
            v-if="manualMode"
            v-model="visit.visit_name"
            style="flex: 2 1 0"
            :label="$t('StudyVisitForm.visit_name')"
            :rules="[formRules.required]"
            data-cy="duplicate-visit-name"
          />
          <v-text-field
            v-if="manualMode"
            v-model="visit.visit_short_name"
            style="flex: 1 1 0"
            :label="$t('StudyVisitForm.visit_short_name')"
            :rules="[formRules.required]"
            data-cy="duplicate-visit-short-name"
          />
          <v-text-field
            v-if="manualMode"
            v-model="visit.unique_visit_number"
            style="flex: 1 1 0"
            :label="$t('StudyVisitForm.unique_visit_number')"
            :rules="[formRules.required]"
            type="number"
            autocomplete="off"
            data-cy="duplicate-visit-unique-number"
          />
          <v-text-field
            v-model="visit.timing"
            style="flex: 1 1 0"
            :label="$t('StudyVisitForm.time_value')"
            :rules="[formRules.required]"
            type="number"
            data-cy="duplicate-visit-timing"
          />
          <v-autocomplete
            v-model="visit.time_unit_uid"
            style="flex: 1 1 0"
            :label="$t('StudyVisitForm.time_unit_name')"
            data-cy="time-unit"
            :items="epochsStore.studyTimeUnits"
            item-title="name"
            item-value="uid"
            :rules="[formRules.required]"
            clearable
          />

          <div
            v-if="visit.status"
            class="d-flex align-center justify-center"
            style="width: 36px; height: 56px"
          >
            <v-tooltip
              v-if="visit.status === 'loading'"
              location="top"
              :text="$t('StudyVisitForm.duplicate_in_progress')"
            >
              <template #activator="{ props }">
                <v-progress-circular
                  v-bind="props"
                  indeterminate
                  size="22"
                  width="2"
                  class="mb-3"
                  color="primary"
                />
              </template>
            </v-tooltip>
            <v-tooltip
              v-else-if="visit.status === 'success'"
              location="top"
              :text="$t('StudyVisitForm.duplicate_saved')"
            >
              <template #activator="{ props }">
                <v-icon v-bind="props" color="success" class="mb-3">
                  mdi-check-circle
                </v-icon>
              </template>
            </v-tooltip>
            <v-tooltip
              v-else-if="visit.status === 'error'"
              location="top"
              :text="
                $t('StudyVisitForm.duplicate_error', { message: visit.message })
              "
            >
              <template #activator="{ props }">
                <v-icon v-bind="props" color="error" class="mb-3">
                  mdi-alert-circle
                </v-icon>
              </template>
            </v-tooltip>
          </div>
          <v-btn
            v-else
            icon="mdi-delete-outline"
            variant="text"
            color="error"
            size="small"
            :disabled="form.visits.length === 1"
            :title="$t('_global.remove')"
            data-cy="remove-duplicate-visit"
            @click="removeVisit(index)"
          />
          <v-tooltip
            v-if="visit.status === 'error'"
            location="top"
            :text="$t('StudyVisitForm.duplicate_try_again_tooltip')"
          >
            <template #activator="{ props }">
              <v-btn
                v-bind="props"
                color="secondary"
                variant="flat"
                rounded
                size="small"
                class="mt-2"
                data-cy="retry-duplicate-visit"
                @click="tryAgain(visit)"
              >
                {{ $t('StudyVisitForm.duplicate_try_again') }}
              </v-btn>
            </template>
          </v-tooltip>
        </div>
        <v-btn
          v-if="!disableSaving"
          variant="text"
          color="primary"
          prepend-icon="mdi-plus"
          data-cy="add-duplicate-visit"
          @click="addVisit"
        >
          {{ $t('_global.add') }}
        </v-btn>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import epochs from '@/api/studyEpochs'
import visitConstants from '@/constants/visits'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useEpochsStore } from '@/stores/studies-epochs'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const formRules = inject('formRules')
const props = defineProps({
  studyVisit: {
    type: Object,
    default: undefined,
  },
  open: Boolean,
})
const emit = defineEmits(['close'])
const studiesGeneralStore = useStudiesGeneralStore()
const epochsStore = useEpochsStore()

let visitIdCounter = 0
function createVisit() {
  return {
    id: visitIdCounter++,
    timing: null,
    time_unit_uid: props.studyVisit?.time_unit_uid ?? null,
    visit_name: null,
    visit_short_name: null,
    unique_visit_number: null,
    status: null,
  }
}

// Only manual-mode studies take typed names and numbers (see canDuplicateVisit)
const manualMode = computed(() => epochsStore.manualVisitMode)

const form = ref({
  visits: [createVisit()],
})
const formRef = ref()
const observer = ref()
const disableSaving = ref(false)
const cancelLabel = ref(t('_global.cancel'))

const helpItems = [
  'StudyVisitDuplicate.time_value',
  'StudyVisitDuplicate.time_unit',
]

watch(
  () => props.studyVisit,
  (newVal) => {
    if (newVal) {
      form.value.visits.forEach((visit) => {
        if (!visit.time_unit_uid) {
          visit.time_unit_uid = newVal.time_unit_uid
        }
      })
    }
  },
  { immediate: true }
)

function addVisit() {
  form.value.visits.push(createVisit())
}

function removeVisit(index) {
  form.value.visits.splice(index, 1)
}

async function saveVisit(visit) {
  const newVisit = JSON.parse(JSON.stringify(props.studyVisit))
  newVisit.time_value = visit.timing
  newVisit.time_unit_uid = visit.time_unit_uid
  delete newVisit.visit_number
  // A grouped visit's suffix belongs to its group, so the copy starts without one
  if (
    [
      visitConstants.SUBCLASS_ANCHOR_VISIT_IN_GROUP_OF_SUBV,
      visitConstants.SUBCLASS_ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV,
    ].includes(newVisit.visit_subclass)
  ) {
    newVisit.visit_suffix = ''
  }
  if (manualMode.value) {
    newVisit.visit_name = visit.visit_name
    newVisit.visit_short_name = visit.visit_short_name
    newVisit.unique_visit_number = Number(visit.unique_visit_number)
  } else {
    delete newVisit.visit_name
    delete newVisit.visit_short_name
    delete newVisit.unique_visit_number
  }
  const resp = await epochs.getStudyVisitPreview(
    studiesGeneralStore.selectedStudy.uid,
    newVisit,
    { ignoreErrors: true }
  )
  const fields = [
    'study_day_label',
    'study_week_label',
    'study_day_number',
    'study_week_number',
    'duration_time',
  ]
  for (const field of fields) {
    newVisit[field] = resp.data[field]
  }
  await epochsStore.addStudyVisit({
    studyUid: studiesGeneralStore.selectedStudy.uid,
    input: newVisit,
  })
}

async function submit() {
  notificationHub.clearErrors()

  try {
    formRef.value.working = true
    form.value.visits.forEach((visit) => {
      visit.status = 'loading'
    })
    for (const visit of form.value.visits) {
      try {
        await saveVisit(visit)
        visit.status = 'success'
      } catch (error) {
        visit.message = error.response?.data?.message
        visit.status = 'error'
        continue
      }
    }
    cancelLabel.value = t('_global.close')
    disableSaving.value = true
  } finally {
    formRef.value.working = false
  }
}

async function tryAgain(visit) {
  try {
    visit.status = 'loading'
    await saveVisit(visit)
    visit.status = 'success'
  } catch (error) {
    visit.message = error.response?.data?.message
    visit.status = 'error'
  }
}

function close() {
  notificationHub.clearErrors()
  form.value = { visits: [createVisit()] }
  disableSaving.value = false
  cancelLabel.value = t('_global.cancel')
  observer.value.reset()
  emit('close')
}
</script>
