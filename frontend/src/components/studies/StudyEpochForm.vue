<template>
  <HorizontalStepperForm
    ref="stepper"
    :title="title"
    :steps="steps"
    :help-items="helpItems"
    help-text=""
    :form-observer-getter="getObserver"
    :edit-data="editData"
    custom-actions
    @close="close"
  >
    <template #[`step.method`]>
      <div class="label mb-4">
        {{ $t('StudyEpochForm.select_method') }}
      </div>
      <v-radio-group v-model="creationMethod">
        <v-radio
          :label="$t('StudyEpochForm.create_from_scratch')"
          :value="methods.SCRATCH"
          data-cy="create-from-scratch"
        />
        <v-radio
          :label="$t('StudyEpochForm.select_from_studies')"
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
      <v-alert
        v-if="studyEpoch && studyEpoch.study_visit_count > 0"
        type="warning"
      >
        {{
          $t('StudyEpochForm.epoch_linked_to_visits_warning', {
            epoch: studyEpoch.epoch_name,
          })
        }}
      </v-alert>
      <v-form ref="observer">
        <v-row>
          <v-col cols="6">
            <v-autocomplete
              v-model="form.epoch_type"
              :label="$t('StudyEpochForm.epoch_type')"
              :items="uniqueTypeGroups"
              item-title="type_name"
              item-value="type"
              :rules="[formRules.required]"
              clearable
              data-cy="epoch-type"
              :disabled="studyEpoch ? true : false"
              class="required"
              @update:model-value="setEpochGroups()"
              @click:clear="setEpochGroups()"
            />
          </v-col>
          <v-col cols="6">
            <v-autocomplete
              v-model="form.epoch_subtype"
              :label="$t('StudyEpochForm.epoch_subtype')"
              :items="subtypeGroups"
              item-title="subtype_name"
              item-value="subtype"
              :rules="[formRules.required]"
              clearable
              data-cy="epoch-subtype"
              :disabled="studyEpoch ? true : false"
              class="required"
              @update:model-value="setEpochGroups()"
              @click:clear="setEpochGroups()"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              :key="typeTrigger"
              v-model="epochDisplay"
              :rules="[formRules.required]"
              data-cy="select-epoch"
              :label="$t('StudyEpochForm.name')"
              :loading="epochNameLoading"
              disabled
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-textarea
              id="startRule"
              v-model="form.start_rule"
              data-cy="epoch-start-rule"
              :label="$t('StudyEpochForm.start_rule')"
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
              data-cy="epoch-end-rule"
              :label="$t('StudyEpochForm.stop_rule')"
              rows="1"
              auto-grow
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-textarea
              id="description"
              v-model="form.description"
              data-cy="description"
              :label="$t('StudyEpochForm.description')"
              rows="1"
              auto-grow
            />
          </v-col>
        </v-row>
        <!-- Lag time only carries data migrated from MMA. -->
        <template v-if="showLagTime">
          <v-row v-for="field in lagTimeFields" :key="field">
            <v-col cols="6">
              <!-- type="text", not "number": a number input reports letters as
                   an empty value, so the rule never sees them and the bad input
                   is silently dropped instead of flagged. -->
              <v-text-field
                v-model="form[field]"
                :data-cy="field"
                :label="$t(`StudyEpochForm.${field}`)"
                :hint="$t('StudyEpochForm.lag_time_hint')"
                :rules="[lagTimeRule]"
                type="text"
                inputmode="numeric"
                persistent-hint
                clearable
              />
            </v-col>
            <v-col cols="6">
              <v-autocomplete
                v-model="form[`${field}_unit_uid`]"
                :data-cy="`${field}-unit`"
                :label="$t('StudyEpochForm.lag_time_unit')"
                :items="lagTimeUnits"
                item-title="name"
                item-value="uid"
                clearable
              />
            </v-col>
          </v-row>
        </template>
        <div v-if="studyEpoch">
          <label class="v-label required">{{
            $t('_global.change_description')
          }}</label>
          <v-textarea
            v-model="form.change_description"
            :rules="[formRules.required]"
            clearable
            rows="1"
            auto-grow
          />
        </div>
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
    <template #[`step.selectEpochs`]>
      <div class="label mb-4">
        {{ $t('StudyEpochForm.selected_epochs') }}
      </div>
      <v-data-table
        data-cy="selected-epochs-table"
        :headers="selectedEpochHeaders"
        :items="selectedEpochs"
      >
        <template #[`item.actions`]="{ item }">
          <v-btn
            icon="mdi-delete-outline"
            color="red"
            variant="text"
            data-cy="remove-selected-epoch"
            @click="unselectEpoch(item)"
          />
        </template>
      </v-data-table>
    </template>
    <template #[`step.selectEpochs.after`]>
      <p class="text-grey text-body-large font-weight-bold mb-0 ml-3">
        {{ $t('StudyEpochForm.copy_instructions') }}
      </p>
      <v-col cols="12" class="pt-0 mt-0">
        <v-data-table
          data-cy="source-epochs-table"
          :headers="sourceEpochHeaders"
          :items="sourceStudyEpochs"
          :loading="sourceEpochsLoading"
        >
          <template #[`item.actions`]="{ item }">
            <v-btn
              :data-cy="$t('StudySelectionTable.copy_item')"
              icon="mdi-content-copy"
              size="small"
              variant="text"
              :color="isEpochSelected(item) ? '' : 'primary'"
              :disabled="isEpochSelected(item)"
              :title="$t('StudySelectionTable.copy_item')"
              @click="selectEpoch(item)"
            />
          </template>
        </v-data-table>
      </v-col>
    </template>
    <template #[`step.preview`]>
      <div class="label mb-2">
        {{ $t('StudyEpochForm.preview_changes') }}
      </div>
      <v-alert
        type="info"
        variant="tonal"
        class="mb-6"
        data-cy="preview-summary"
        :text="
          $t('StudyEpochForm.preview_summary', {
            creates: previewCreates.length,
            affected: previewAffected.length,
          })
        "
      />
      <v-data-table
        data-cy="preview-table"
        :headers="previewHeaders"
        :items="previewRows"
        :loading="loading"
        :no-data-text="$t('StudyEpochForm.preview_nothing_to_create')"
      >
        <template #[`item.change`]="{ item }">
          <v-chip
            size="small"
            variant="tonal"
            :color="item.kind === 'create' ? 'success' : 'warning'"
          >
            <v-icon start size="small">
              {{
                item.kind === 'create'
                  ? 'mdi-plus-circle-outline'
                  : 'mdi-pencil-outline'
              }}
            </v-icon>
            {{
              item.kind === 'create'
                ? $t('StudyEpochForm.change_added')
                : $t('StudyEpochForm.change_updated')
            }}
          </v-chip>
        </template>
        <template #[`item.order`]="{ item }">
          <template v-if="item.kind === 'create'">{{ item.order }}</template>
          <template v-else>—</template>
        </template>
        <template #[`item.name`]="{ item }">
          <template v-if="item.kind === 'create'">{{ item.name }}</template>
          <template v-else>
            <span class="text-medium-emphasis">{{ item.currentName }}</span>
            <v-icon size="x-small" class="mx-1">mdi-arrow-right</v-icon>
            <span
              :class="item.nameChanged ? 'text-warning font-weight-bold' : ''"
            >
              {{ item.proposedName }}
            </span>
          </template>
        </template>
        <template #[`item.epoch_type`]="{ item }">
          {{ item.epoch_type || '—' }}
        </template>
        <template #[`item.epoch_subtype`]="{ item }">
          {{ item.epoch_subtype || '—' }}
        </template>
      </v-data-table>
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
</template>

<script setup>
import studyEpochsApi from '@/api/studyEpochs'
import study from '@/api/study'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import StudySelectorField from '@/components/studies/StudySelectorField.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useEpochsStore } from '@/stores/studies-epochs'
import { useFeatureFlagsStore } from '@/stores/feature-flags'
import unitConstants from '@/constants/units'
import { useI18n } from 'vue-i18n'
import { computed, inject, onMounted, ref, watch } from 'vue'

const methods = {
  SCRATCH: 'scratch',
  SELECT: 'select',
}

const notificationHub = inject('notificationHub')
const formRules = inject('formRules')

const props = defineProps({
  studyEpoch: {
    type: Object,
    default: undefined,
  },
})

const emit = defineEmits(['close'])

const { t } = useI18n()
const studiesGeneralStore = useStudiesGeneralStore()
const epochsStore = useEpochsStore()
const featureFlagsStore = useFeatureFlagsStore()

const stepper = ref()
const observer = ref()
const selectStudyForm = ref()

const colorHash = ref(null)
const form = ref({})
const editData = ref({})
const loading = ref(false)

const helpItems = [
  'StudyEpochForm.name',
  'StudyEpochForm.epoch_type',
  'StudyEpochForm.epoch_subtype',
  'StudyEpochForm.description',
  'StudyEpochForm.start_rule',
  'StudyEpochForm.stop_rule',
  'StudyEpochForm.epoch_time_unit',
  'StudyEpochForm.expected_epoch_duration',
  'StudyEpochForm.color',
]

const typeTrigger = ref(0)
const typeGroups = ref([])
const subtypeGroups = ref([])
const epochDisplay = ref('')
const epochNameLoading = ref(false)

const creationMethod = ref(methods.SCRATCH)
const studies = ref([])
const studiesLoading = ref(false)
const selectedSourceStudy = ref(null)
const sourceStudyEpochs = ref([])
const sourceEpochsLoading = ref(false)
const selectedEpochs = ref([])
const previewCreates = ref([])
const previewAffected = ref([])

const selectedStudy = computed(() => studiesGeneralStore.selectedStudy)
const groups = computed(() => epochsStore.allowedConfigs)
const isEdit = computed(() => Boolean(props.studyEpoch))

// Lag time only exists to carry legacy MMA data, so it is hidden unless the
// installation turns the flag on.
const showLagTime = computed(() =>
  featureFlagsStore.getFeatureFlag('study_epoch_lag_time')
)
// Same picker the study visit form uses for its time units, minus the singular
// day and week and minus year and years. The store's list is shared with the
// visit forms, where those are valid, so filter here rather than in the store.
const lagTimeUnits = computed(() =>
  epochsStore.studyTimeUnits.filter((unit) =>
    unitConstants.LAG_TIME_UNIT_NAMES.includes(unit.name)
  )
)
const lagTimeFields = ['ae_lag_time', 'hypo_lag_time', 'ce_lag_time']

// Emptying the field with the keyboard leaves '', and the clear button leaves
// null. Both mean "no value". Lag time is a duration, so negatives are rejected
// with the same message the rest of the app uses for a lower bound. Anything
// else must be digits only: formRules.numeric tests /^[0-9]+$/, so decimals and
// text both fail here.
function lagTimeRule(value) {
  if (value === '' || value === null || value === undefined) {
    return true
  }
  if (Number(value) < 0) {
    return t('_errors.min_value_reached', { min: 0 })
  }
  return formRules.numeric(value) === true || t('_errors.numeric')
}

// The input is text, so the form holds strings. Send numbers, or null when the
// field was left empty.
function normalizeLagTimes(data) {
  for (const field of lagTimeFields) {
    const value = data[field]
    data[field] =
      value === '' || value === null || value === undefined
        ? null
        : Number(value)
  }
}

const uniqueTypeGroups = computed(() => {
  const result = []
  for (let group of typeGroups.value) {
    if (!result.find((item) => item.type === group.type)) {
      result.push(group)
    }
  }
  return result
})

const selectedEpochHeaders = [
  { title: '', key: 'actions', width: '1%' },
  { title: t('Study.study_id'), key: 'study_id' },
  {
    title: t('StudyEpochTable.name'),
    key: 'epoch_ctterm.sponsor_preferred_name',
  },
  {
    title: t('StudyEpochTable.type'),
    key: 'epoch_type_ctterm.sponsor_preferred_name',
  },
  {
    title: t('StudyEpochTable.sub_type'),
    key: 'epoch_subtype_ctterm.sponsor_preferred_name',
  },
]
const sourceEpochHeaders = selectedEpochHeaders

// A single table renders both new and updated epochs. The `change`/`order`/
// `name` columns are custom-rendered, so their keys are just slot anchors.
const previewHeaders = [
  {
    title: t('StudyEpochForm.change'),
    key: 'change',
    width: '12%',
    sortable: false,
  },
  {
    title: t('StudyEpochTable.number'),
    key: 'order',
    width: '16%',
    sortable: false,
  },
  { title: t('StudyEpochTable.name'), key: 'name', sortable: false },
  { title: t('StudyEpochTable.type'), key: 'epoch_type', sortable: false },
  {
    title: t('StudyEpochTable.sub_type'),
    key: 'epoch_subtype',
    sortable: false,
  },
]

const detailsStep = {
  name: 'details',
  title: t('StudyEpochForm.epoch_details'),
}
const methodStep = { name: 'method', title: t('StudyEpochForm.select_method') }
const selectStep = {
  name: 'selectEpochs',
  title: t('StudyEpochForm.select_epochs'),
}
const previewStep = {
  name: 'preview',
  title: t('StudyEpochForm.preview_step'),
}

const steps = computed(() => {
  if (isEdit.value) {
    return [detailsStep]
  }
  if (creationMethod.value === methods.SELECT) {
    return [methodStep, selectStep, previewStep]
  }
  return [methodStep, detailsStep]
})

const currentStepName = computed(() => {
  const step = stepper.value ? stepper.value.currentStep : 1
  return steps.value[step - 1] ? steps.value[step - 1].name : ''
})

const continueLabel = computed(() => {
  if (
    currentStepName.value === 'method' ||
    currentStepName.value === 'selectEpochs'
  ) {
    return t('_global.continue')
  }
  return t('_global.save')
})

const checkContinueDisabled = computed(() => {
  if (epochNameLoading.value) {
    return true
  }
  if (
    currentStepName.value === 'method' &&
    creationMethod.value === methods.SELECT &&
    !selectedSourceStudy.value
  ) {
    return true
  }
  if (
    currentStepName.value === 'selectEpochs' &&
    selectedEpochs.value.length === 0
  ) {
    return true
  }
  if (
    currentStepName.value === 'preview' &&
    previewCreates.value.length === 0
  ) {
    return true
  }
  return false
})

const title = computed(() =>
  isEdit.value ? t('StudyEpochForm.edit_title') : t('StudyEpochForm.add_title')
)

// Merge the two preview lists into one set of rows: new epochs first, then the
// existing epochs that get renumbered/renamed. The `kind` drives per-row
// rendering (a single value for creates, a before -> after for updates).
const previewRows = computed(() => {
  const creates = previewCreates.value.map((item) => ({
    kind: 'create',
    order: item.order,
    name: item.epoch_name,
    epoch_type: item.epoch_type,
    epoch_subtype: item.epoch_subtype,
  }))
  // affected_existing no longer carries order info; it only describes the
  // rename (epoch_name / epoch CT term) applied to existing epochs.
  const updates = previewAffected.value.map((item) => ({
    kind: 'update',
    currentName: item.current_epoch_name,
    proposedName: item.proposed_epoch_name,
    nameChanged: item.proposed_epoch_name !== item.current_epoch_name,
  }))
  return [...creates, ...updates]
})

watch(groups, () => {
  typeGroups.value = groups.value
  subtypeGroups.value = groups.value
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

onMounted(async () => {
  epochsStore.fetchAllowedConfigs()
  if (showLagTime.value) {
    epochsStore.fetchStudyTimeUnits()
  }
  if (isEdit.value) {
    const resp = await studyEpochsApi.getStudyEpoch(
      selectedStudy.value.uid,
      props.studyEpoch.uid
    )
    loadFromStudyEpoch(resp.data)
    setEpochGroups()
    editData.value = JSON.parse(JSON.stringify(form.value))
  } else {
    // Load the studies an epoch may be copied from (all but the current).
    studiesLoading.value = true
    study
      .getAllList()
      .then((resp) => {
        studies.value = resp.data.filter(
          (item) => item.uid !== selectedStudy.value.uid
        )
      })
      .finally(() => {
        studiesLoading.value = false
      })
  }
})

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

async function setEpochGroups() {
  epochNameLoading.value = true

  try {
    let type = ''
    let subtype = ''

    if (!form.value.epoch_subtype && !form.value.epoch_type) {
      form.value.epoch = ''
      subtypeGroups.value = groups.value
      typeGroups.value = groups.value
      epochDisplay.value = ''
      return
    }

    if (!form.value.epoch_subtype) {
      form.value.epoch = ''
      type = form.value.epoch_type
      subtypeGroups.value = groups.value
      typeGroups.value = groups.value
      subtypeGroups.value = groups.value.filter(function (value) {
        return value.type === type
      })
      epochDisplay.value = ''
      return
    }

    if (!form.value.epoch_type) {
      form.value.epoch = ''
      subtype = form.value.epoch_subtype
      typeGroups.value = groups.value
      subtypeGroups.value = groups.value
      typeGroups.value = groups.value.filter(function (value) {
        return value.subtype === subtype
      })
      epochDisplay.value = ''
      return
    }

    subtype = form.value.epoch_subtype
    type = form.value.epoch_type
    typeGroups.value = groups.value.filter(function (value) {
      return value.subtype === subtype
    })
    subtypeGroups.value = groups.value.filter(function (value) {
      return value.type === type
    })

    const data = {
      study_uid: selectedStudy.value.uid,
      epoch_subtype: subtype,
    }
    const resp = await studyEpochsApi.getPreviewEpoch(
      selectedStudy.value.uid,
      data
    )
    form.value.epoch = resp.data.epoch
    epochDisplay.value = resp.data.epoch_name
  } finally {
    epochNameLoading.value = false
  }
}

async function primaryAction() {
  if (!(await stepper.value.validateStepObserver(stepper.value.currentStep))) {
    return
  }
  if (currentStepName.value === 'method') {
    if (creationMethod.value === methods.SELECT) {
      await loadSourceStudyEpochs()
    }
    stepper.value.currentStep += 1
    return
  }
  if (currentStepName.value === 'selectEpochs') {
    // Build a preview of the resulting changes before letting the user commit.
    loading.value = true
    try {
      await loadPreview()
      stepper.value.currentStep += 1
    } finally {
      loading.value = false
    }
    return
  }
  if (currentStepName.value === 'preview') {
    submitSelectedEpochs()
    return
  }
  // details step
  if (isEdit.value) {
    update()
  } else {
    create()
  }
}

function previousStep() {
  stepper.value.currentStep -= 1
}

async function create() {
  notificationHub.clearErrors()
  loading.value = true
  try {
    const data = JSON.parse(JSON.stringify(form.value))
    normalizeLagTimes(data)
    data.color_hash = colorHash.value ? colorHash.value : '#BDBDBD'
    data.study_uid = selectedStudy.value.uid
    await epochsStore.addStudyEpoch({
      studyUid: selectedStudy.value.uid,
      input: data,
    })
    epochsStore.fetchStudyEpochs({ studyUid: selectedStudy.value.uid })
    notificationHub.add({ msg: t('StudyEpochForm.add_success') })
    close()
  } finally {
    loading.value = false
  }
}

async function update() {
  notificationHub.clearErrors()
  loading.value = true
  try {
    const data = JSON.parse(JSON.stringify(form.value))
    normalizeLagTimes(data)
    data.color_hash = colorHash.value
      ? colorHash.value.hexa !== undefined
        ? colorHash.value.hexa
        : colorHash.value
      : '#BDBDBD'
    await epochsStore.updateStudyEpoch({
      studyUid: selectedStudy.value.uid,
      studyEpochUid: props.studyEpoch.uid,
      input: data,
    })
    epochsStore.fetchStudyEpochs({ studyUid: selectedStudy.value.uid })
    notificationHub.add({ msg: t('StudyEpochForm.update_success') })
    close()
  } finally {
    loading.value = false
  }
}

async function loadSourceStudyEpochs() {
  selectedEpochs.value = []
  sourceStudyEpochs.value = []
  previewCreates.value = []
  previewAffected.value = []
  if (!selectedSourceStudy.value) {
    return
  }
  const studyId =
    selectedSourceStudy.value.id ??
    selectedSourceStudy.value.current_metadata?.identification_metadata
      ?.study_id
  sourceEpochsLoading.value = true
  await studyEpochsApi
    .getStudyEpochs(selectedSourceStudy.value.uid)
    .then((resp) => {
      sourceStudyEpochs.value = resp.data.items.map((epoch) => ({
        ...epoch,
        study_id: studyId,
      }))
    })
    .finally(() => {
      sourceEpochsLoading.value = false
    })
}

function isEpochSelected(epoch) {
  return selectedEpochs.value.some((item) => item.uid === epoch.uid)
}
function selectEpoch(epoch) {
  if (!isEpochSelected(epoch)) {
    selectedEpochs.value.push(epoch)
  }
}
function unselectEpoch(epoch) {
  selectedEpochs.value = selectedEpochs.value.filter(
    (item) => item.uid !== epoch.uid
  )
}

// Build the list of StudyEpochCreateInput specs for the selected epochs.
// study_uid and epoch_subtype are required; the target study's epoch
// names/codes/orders are computed server-side. This flat list is what
// batch/preview expects directly.
function buildEpochCreateInputs() {
  const targetUid = selectedStudy.value.uid
  return selectedEpochs.value.map((epoch) => ({
    study_uid: targetUid,
    epoch_subtype: epoch.epoch_subtype_ctterm.term_uid,
    start_rule: epoch.start_rule,
    end_rule: epoch.end_rule,
    description: epoch.description,
    color_hash: epoch.color_hash ?? '#BDBDBD',
  }))
}

// Each StudyEpochBatchPreviewItemOutput carries a per-item `response_code` and
// `content`, which is the computed StudyEpoch on success (200) or a
// BatchErrorResponse on failure; flatten the epoch into a "to create" row.
function mapPreviewCreate(item) {
  const epoch = item?.content ?? {}
  return {
    order: epoch.order ?? '',
    epoch_name:
      epoch.epoch_name ?? epoch.epoch_ctterm?.sponsor_preferred_name ?? '',
    epoch_type: epoch.epoch_type_ctterm?.sponsor_preferred_name ?? '',
    epoch_subtype: epoch.epoch_subtype_ctterm?.sponsor_preferred_name ?? '',
    start_rule: epoch.start_rule ?? '',
    end_rule: epoch.end_rule ?? '',
  }
}

async function loadPreview() {
  previewCreates.value = []
  previewAffected.value = []
  notificationHub.clearErrors()
  const resp = await studyEpochsApi.studyEpochsBatchPreview(
    selectedStudy.value.uid,
    buildEpochCreateInputs()
  )
  // StudyEpochBatchPreviewResponse: { items: [...], affected_existing: [...] }.
  // Each item wraps the computed epoch under `content` with a `response_code`;
  // surface any per-item failure and only preview the successful ones.
  const items = resp.data?.items ?? []
  reportBatchErrors(items)
  previewCreates.value = items
    .filter((item) => (item?.response_code ?? 200) < 400)
    .map(mapPreviewCreate)
  // affected_existing items carry current_*/proposed_* name fields, used
  // directly by the table to show the before -> after rename.
  previewAffected.value = resp.data?.affected_existing ?? []
}

// The batch endpoint replies with a multi-status array; surface any per-item
// failure as an error notification (its HTTP status stays 200).
function reportBatchErrors(responseData) {
  if (!Array.isArray(responseData)) {
    return false
  }
  let hasError = false
  for (const subResponse of responseData) {
    if (subResponse.response_code >= 400) {
      hasError = true
      notificationHub.add({
        msg: subResponse.content?.message,
        type: 'error',
        timeout: 0,
      })
    }
  }
  return hasError
}

async function submitSelectedEpochs() {
  if (!selectedEpochs.value.length) {
    return
  }
  notificationHub.clearErrors()
  loading.value = true
  const targetUid = selectedStudy.value.uid
  try {
    // The batch (commit) endpoint expects StudyEpochBatchInput entries, i.e.
    // each create spec wrapped as { method: 'POST', content }.
    const payload = buildEpochCreateInputs().map((content) => ({
      method: 'POST',
      content,
    }))
    const resp = await studyEpochsApi.studyEpochsBatchActions(
      targetUid,
      payload
    )
    if (reportBatchErrors(resp.data)) {
      return
    }
    epochsStore.fetchStudyEpochs({ studyUid: targetUid })
    notificationHub.add({
      msg: t('StudyEpochForm.epochs_created', {
        count: previewCreates.value.length || selectedEpochs.value.length,
      }),
    })
    close()
  } finally {
    loading.value = false
  }
}

function loadFromStudyEpoch(studyEpoch) {
  typeGroups.value = [
    {
      type: studyEpoch.epoch_type_ctterm.term_uid,
      type_name: studyEpoch.epoch_type_ctterm.sponsor_preferred_name,
    },
  ]
  subtypeGroups.value = [
    {
      subtype: studyEpoch.epoch_subtype_ctterm.term_uid,
      subtype_name: studyEpoch.epoch_subtype_ctterm.sponsor_preferred_name,
    },
  ]

  form.value = { ...studyEpoch }
  form.value.epoch_type = uniqueTypeGroups.value.find(
    (group) => group.type_name === form.value.epoch_type_name
  )
  form.value.epoch_subtype = subtypeGroups.value.find(
    (group) => group.subtype_name === form.value.epoch_subtype_name
  ).subtype
  epochDisplay.value = studyEpoch.epoch_name
  if (studyEpoch.color_hash) {
    colorHash.value = studyEpoch.color_hash
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

<style>
.v-color-picker__controls {
  display: none;
}
</style>

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
