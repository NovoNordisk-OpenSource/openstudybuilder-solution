<template>
  <HorizontalStepperForm
    ref="stepper"
    :title="title"
    :steps="steps"
    :help-items="helpItems"
    :help-text="$t('_help.StudyDefineForm.general')"
    :form-observer-getter="getObserver"
    :edit-data="editData"
    custom-actions
    @close="close"
  >
    <template #[`step.method`]>
      <div class="label mb-4">
        {{ $t('StudyElements.select_method') }}
      </div>
      <v-radio-group v-model="creationMethod">
        <v-radio
          :label="$t('StudyElements.create_from_scratch')"
          :value="methods.SCRATCH"
          data-cy="create-from-scratch"
        />
        <v-radio
          :label="$t('StudyElements.select_from_studies')"
          :value="methods.SELECT"
          data-cy="select-from-studies"
        />
      </v-radio-group>
      <v-form ref="selectStudyForm">
        <v-row v-if="creationMethod === methods.SELECT">
          <v-col cols="6">
            <StudySelectorField
              v-model="selectedSourceStudy"
              :data="studies"
              :loading="studiesLoading"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #[`step.details`]>
      <v-form ref="observer">
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="form.code"
              :label="$t('StudyElements.el_type')"
              :items="elementTypes"
              item-title="type_name"
              item-value="type"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="form.element_subtype_uid"
              :label="$t('StudyElements.el_sub_type')"
              item-title="subtype_name"
              item-value="subtype"
              :items="elementSubTypes"
              :rules="[formRules.required]"
              clearable
              class="required"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.name"
              :label="$t('StudyElements.el_name')"
              :rules="[formRules.required, formRules.max(form.name, 200)]"
              clearable
              class="required"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.short_name"
              :label="$t('StudyElements.el_short_name')"
              :rules="[formRules.required, formRules.max(form.short_name, 20)]"
              clearable
              class="required"
            />
          </v-col>
        </v-row>
        <div class="label ml-1">
          {{ $t('StudyElements.planned_duration_time') }}
          <DurationField v-model="form.planned_duration" />
        </div>
        <v-row>
          <v-col>
            <v-textarea
              id="startRule"
              v-model="form.start_rule"
              :label="$t('StudyElements.el_start_rule')"
              rows="1"
              auto-grow
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-textarea
              id="endRule"
              v-model="form.end_rule"
              :label="$t('StudyElements.el_end_rule')"
              rows="1"
              auto-grow
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.description"
              :label="$t('_global.description')"
              clearable
            />
          </v-col>
        </v-row>
        <div class="mt-4">
          <label class="v-label">{{ $t('StudyEpochForm.color') }}</label>
          <v-color-picker
            v-model="colorHash"
            data-cy="epoch-color-picker"
            clearable
            show-swatches
            hide-canvas
            hide-sliders
            swatches-max-height="300px"
          />
        </div>
      </v-form>
    </template>
    <template #[`step.selectElements`]>
      <div class="label mb-4">
        {{ $t('StudyElements.selected_elements') }}
      </div>
      <v-data-table
        data-cy="selected-elements-table"
        :headers="selectedElementHeaders"
        :items="selectedElements"
      >
        <template #[`item.actions`]="{ item }">
          <v-btn
            icon="mdi-delete-outline"
            color="red"
            variant="text"
            data-cy="remove-selected-element"
            @click="unselectElement(item)"
          />
        </template>
      </v-data-table>
    </template>
    <template #[`step.selectElements.after`]>
      <p class="text-grey text-body-large font-weight-bold mb-0 ml-3">
        {{ $t('StudyElements.copy_instructions') }}
      </p>
      <v-col cols="12" class="pt-0 mt-0">
        <v-data-table
          data-cy="source-elements-table"
          :headers="sourceElementHeaders"
          :items="sourceStudyElements"
          :loading="sourceElementsLoading"
        >
          <template #[`header.actions`]>
            <v-checkbox
              v-model="selectAllSourceElements"
              :title="$t('_global.select_all')"
              :disabled="!sourceStudyElements.length"
              density="compact"
              hide-details
              data-cy="select-all-source-elements"
              @update:model-value="toggleSelectAllSourceElements"
            />
          </template>
          <template #[`item.actions`]="{ item }">
            <v-btn
              :data-cy="$t('StudySelectionTable.copy_item')"
              icon="mdi-content-copy"
              size="small"
              variant="text"
              :color="isElementSelected(item) ? '' : 'primary'"
              :disabled="isElementSelected(item)"
              :title="$t('StudySelectionTable.copy_item')"
              @click="selectElement(item)"
            />
          </template>
        </v-data-table>
      </v-col>
    </template>
    <template #customActions>
      <v-btn
        class="secondary-btn my-2 ml-2"
        variant="outlined"
        width="120px"
        rounded="xl"
        data-cy="cancel-stepper"
        :loading="loading"
        @click="cancel"
      >
        {{ $t('_global.cancel') }}
      </v-btn>
      <v-spacer />
      <v-btn
        v-if="stepper && stepper.currentStep > 1"
        class="secondary-btn"
        variant="outlined"
        width="120px"
        rounded="xl"
        :loading="loading"
        data-cy="previous-stepper"
        @click="previousStep()"
      >
        {{ $t('_global.previous') }}
      </v-btn>
      <v-btn
        class="mr-2"
        color="secondary"
        variant="flat"
        rounded="xl"
        data-cy="continue-stepper"
        :loading="loading"
        :disabled="checkContinueDisabled"
        @click="primaryAction()"
      >
        {{ continueLabel }}
      </v-btn>
    </template>
  </HorizontalStepperForm>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import armsApi from '@/api/arms'
import study from '@/api/study'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import StudySelectorField from '@/components/studies/StudySelectorField.vue'
import DurationField from '@/components/tools/DurationField.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const methods = {
  SCRATCH: 'scratch',
  SELECT: 'select',
}

const { t } = useI18n()
const formRules = inject('formRules')
const notificationHub = inject('notificationHub')
const studiesGeneralStore = useStudiesGeneralStore()

const props = defineProps({
  editedElement: {
    type: Object,
    default: () => ({}),
  },
})
const emit = defineEmits(['close'])

const selectedStudy = studiesGeneralStore.selectedStudy

const stepper = ref()
const confirm = ref()
const observer = ref()
const selectStudyForm = ref()

const form = ref({ planned_duration: {} })
const editData = ref({})
const colorHash = ref(null)
const allowedConfigs = ref([])
const loading = ref(false)

const helpItems = ref([
  'StudyElements.el_name',
  'StudyElements.el_short_name',
  'StudyElements.el_sub_type',
  'StudyElements.el_type',
])

const creationMethod = ref(methods.SCRATCH)
const studies = ref([])
const studiesLoading = ref(false)
const selectedSourceStudy = ref(null)
const sourceStudyElements = ref([])
const sourceElementsLoading = ref(false)
const selectedElements = ref([])
const selectAllSourceElements = ref(false)

const isEdit = computed(() => Object.keys(props.editedElement).length !== 0)

const selectedElementHeaders = [
  { title: '', key: 'actions', width: '1%' },
  { title: t('Study.study_id'), key: 'study_id' },
  { title: t('StudyElements.el_name'), key: 'name' },
  { title: t('StudyElements.el_short_name'), key: 'short_name' },
  { title: t('StudyElements.el_sub_type'), key: 'element_subtype.term_name' },
]
const sourceElementHeaders = selectedElementHeaders

const detailsStep = {
  name: 'details',
  title: t('StudyElements.element_details'),
}
const methodStep = { name: 'method', title: t('StudyElements.select_method') }
const selectStep = {
  name: 'selectElements',
  title: t('StudyElements.select_elements'),
}

const steps = computed(() => {
  if (isEdit.value) {
    return [detailsStep]
  }
  if (creationMethod.value === methods.SELECT) {
    return [methodStep, selectStep]
  }
  return [methodStep, detailsStep]
})

const currentStepName = computed(() => {
  const step = stepper.value ? stepper.value.currentStep : 1
  return steps.value[step - 1] ? steps.value[step - 1].name : ''
})

const continueLabel = computed(() => {
  switch (currentStepName.value) {
    case 'method':
      return t('_global.continue')
    default:
      return t('_global.save')
  }
})

const checkContinueDisabled = computed(() => {
  if (
    currentStepName.value === 'method' &&
    creationMethod.value === methods.SELECT &&
    !selectedSourceStudy.value
  ) {
    return true
  }
  if (
    currentStepName.value === 'selectElements' &&
    selectedElements.value.length === 0
  ) {
    return true
  }
  return false
})

const title = computed(() =>
  isEdit.value ? t('StudyElements.edit_el') : t('StudyElements.add_element')
)

const elementTypes = computed(() => {
  if (!form.value.element_subtype_uid) {
    return [
      ...new Map(allowedConfigs.value.map((v) => [v.type_name, v])).values(),
    ]
  }
  return allowedConfigs.value.filter(
    (element) => element.subtype === form.value.element_subtype_uid
  )
})

const elementSubTypes = computed(() => {
  if (!form.value.code) {
    return allowedConfigs.value
  }
  return allowedConfigs.value.filter(
    (element) => element.type === form.value.code
  )
})

onMounted(async () => {
  armsApi.getStudyElementsAllowedConfigs().then((resp) => {
    allowedConfigs.value = resp.data
  })
  if (isEdit.value) {
    const resp = await armsApi.getStudyElement(
      selectedStudy.uid,
      props.editedElement.element_uid
    )
    form.value = JSON.parse(JSON.stringify(resp.data))
    if (!form.value.planned_duration) {
      form.value.planned_duration = {}
    }
    if (resp.data.element_subtype) {
      form.value.element_subtype_uid = resp.data.element_subtype.term_uid
    }
    if (form.value.element_colour) {
      colorHash.value = form.value.element_colour
    }
    editData.value = JSON.parse(JSON.stringify(form.value))
  } else {
    // Load the studies an element may be copied from (all but the current).
    studiesLoading.value = true
    study
      .getAllList()
      .then((resp) => {
        studies.value = resp.data.filter(
          (item) => item.uid !== selectedStudy.uid
        )
      })
      .finally(() => {
        studiesLoading.value = false
      })
  }
})

// Keep the form store (used by the stepper's cancel guard) in sync with edits.
watch(
  form,
  (value) => {
    if (!isEdit.value) {
      editData.value = JSON.parse(JSON.stringify(value))
    }
  },
  { immediate: true, deep: true }
)

function getObserver(step) {
  const name = steps.value[step - 1] ? steps.value[step - 1].name : ''
  if (name === 'method') {
    return selectStudyForm.value
  }
  if (name === 'details') {
    return observer.value
  }
  return undefined
}

async function primaryAction() {
  if (!(await stepper.value.validateStepObserver(stepper.value.currentStep))) {
    return
  }
  if (currentStepName.value === 'method') {
    if (creationMethod.value === methods.SELECT) {
      await loadSourceStudyElements()
    }
    stepper.value.currentStep += 1
    return
  }
  if (currentStepName.value === 'selectElements') {
    createSelectedElements()
    return
  }
  // details step
  if (isEdit.value) {
    edit()
  } else {
    create()
  }
}

function previousStep() {
  stepper.value.currentStep -= 1
}

// Resolve the colour and planned duration into the shape the API expects.
function buildPayload(source) {
  const payload = JSON.parse(JSON.stringify(source))
  if (!payload.planned_duration || !payload.planned_duration.duration_value) {
    payload.planned_duration = null
  }
  payload.element_colour = colorHash.value
    ? colorHash.value.hexa !== undefined
      ? colorHash.value.hexa
      : colorHash.value
    : '#BDBDBD'
  return payload
}

function create() {
  notificationHub.clearErrors()
  loading.value = true
  armsApi
    .addStudyElement(selectedStudy.uid, buildPayload(form.value))
    .then(() => {
      notificationHub.add({ msg: t('StudyElements.el_created') })
      close()
    })
    .finally(() => {
      loading.value = false
    })
}

function edit() {
  notificationHub.clearErrors()
  loading.value = true
  armsApi
    .editStudyElement(
      selectedStudy.uid,
      props.editedElement.element_uid,
      buildPayload(form.value)
    )
    .then(() => {
      notificationHub.add({ msg: t('StudyElements.el_edited') })
      close()
    })
    .finally(() => {
      loading.value = false
    })
}

async function loadSourceStudyElements() {
  selectedElements.value = []
  sourceStudyElements.value = []
  selectAllSourceElements.value = false
  if (!selectedSourceStudy.value) {
    return
  }
  const studyId =
    selectedSourceStudy.value.id ??
    selectedSourceStudy.value.current_metadata?.identification_metadata
      ?.study_id
  sourceElementsLoading.value = true
  await armsApi
    .getStudyElements(selectedSourceStudy.value.uid, {
      study_uid: selectedSourceStudy.value.uid,
    })
    .then((resp) => {
      sourceStudyElements.value = resp.data.items.map((element) => ({
        ...element,
        study_id: studyId,
      }))
    })
    .finally(() => {
      sourceElementsLoading.value = false
    })
}

function isElementSelected(element) {
  return selectedElements.value.some(
    (item) => item.element_uid === element.element_uid
  )
}
function selectElement(element) {
  if (!isElementSelected(element)) {
    selectedElements.value.push(element)
  }
}
function unselectElement(element) {
  selectedElements.value = selectedElements.value.filter(
    (item) => item.element_uid !== element.element_uid
  )
  // Removing an item means the selection is no longer "all".
  selectAllSourceElements.value = false
}
// "Select all" mirrors every available source element into the selection. When
// active, createSelectedElements() copies the whole source study in one call.
function toggleSelectAllSourceElements(value) {
  selectedElements.value = value ? [...sourceStudyElements.value] : []
}

async function createSelectedElements() {
  if (!selectedElements.value.length) {
    return
  }
  notificationHub.clearErrors()
  loading.value = true
  try {
    // When every available element is selected, let the backend copy the whole
    // source study in a single call instead of replaying each element.
    if (selectAllSourceElements.value) {
      await armsApi.copyElementsFromStudy(
        selectedStudy.uid,
        selectedSourceStudy.value.uid
      )
      notificationHub.add({ msg: t('StudyElements.el_created') })
      close()
      return
    }
    // Create each element independently and report the per-item outcome so a
    // single failure neither aborts the others nor masks the error.
    const results = await Promise.allSettled(
      selectedElements.value.map((element) =>
        armsApi.addStudyElement(selectedStudy.uid, {
          element_subtype_uid: element.element_subtype?.term_uid,
          code: element.code,
          name: element.name,
          short_name: element.short_name,
          planned_duration: element.planned_duration ?? null,
          start_rule: element.start_rule,
          end_rule: element.end_rule,
          description: element.description,
          element_colour: element.element_colour ?? '#BDBDBD',
        })
      )
    )
    const failures = results.filter((r) => r.status === 'rejected')
    const created = results.length - failures.length
    if (created > 0) {
      notificationHub.add({
        msg: t('StudyElements.elements_created', { count: created }),
      })
    }
    if (failures.length === 0) {
      close()
    }
  } finally {
    loading.value = false
  }
}

function cancel() {
  stepper.value.cancel()
}
function close() {
  notificationHub.clearErrors()
  emit('close')
}
</script>

<style scoped>
.label {
  font-weight: 700;
  font-size: 18px;
  line-height: 24px;
  letter-spacing: -0.02em;
  color: var(--semantic-system-brand, #001965);
  min-height: 24px;
}
</style>
