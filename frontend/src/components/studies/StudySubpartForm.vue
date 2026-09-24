<template>
  <HorizontalStepperForm
    ref="stepper"
    :title="$t('StudySubparts.add_subpart')"
    :steps="steps"
    :form-observer-getter="getObserver"
    :extra-step-validation="extraValidation"
    @close="cancel"
    @save="submit"
  >
    <template #[`step.method`]>
      <v-radio-group v-model="method">
        <v-radio :label="$t('StudySubparts.create_new')" value="create" />
        <!-- Hidden for now due to the fact that creating a subpart from existing study removes that study.
             This will be handled in a separate feature.
             <v-radio :label="$t('StudySubparts.add_existing')" value="select" /> -->
      </v-radio-group>
    </template>
    <template #[`step.select`]>
      <v-form ref="selectFormRef">
        <v-card class="px-4 mb-2">
          <v-card-title class="dialog-title">
            {{ $t('StudySubparts.selected_substudy') }}
          </v-card-title>
          <v-card-text>
            <v-data-table
              key="uid"
              :headers="selectedHeaders"
              :items="[selectedSubstudy]"
              hide-default-footer
            />
          </v-card-text>
        </v-card>
        <v-card class="px-4 mb-2">
          <v-card-title class="dialog-title">
            {{ $t('StudySubparts.available_studies') }}
          </v-card-title>
          <v-card-text>
            <NNTable
              table-id="study-subpart-form-studies"
              item-value="uid"
              :modifiable-table="false"
              :headers="headers"
              :items="studies"
              :items-length="total"
              hide-default-switches
              column-data-resource="studies"
              @filter="fetchAvailableStudies"
            >
              <template #[`item.select`]="{ item }">
                <v-btn
                  icon="mdi-content-copy"
                  :title="$t('StudySelectionTable.copy_item')"
                  variant="text"
                  @click="selectStudy(item)"
                />
              </template>
            </NNTable>
          </v-card-text>
        </v-card>
      </v-form>
    </template>
    <template #[`step.create`]>
      <v-form ref="createFormRef">
        <v-row>
          <v-col cols="8">
            <v-text-field
              :label="$t('StudyForm.project_id')"
              :model-value="studiesGeneralStore.projectNumber"
              disabled
              hide-details
              data-cy="project-name"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="8">
            <v-text-field
              :label="$t('StudyForm.project_name')"
              :model-value="studiesGeneralStore.projectName"
              disabled
              hide-details
            />
          </v-col>
        </v-row>
        <!-- Brand name is not yet implemented in api -->
        <v-row>
          <v-col cols="8">
            <v-text-field
              :label="$t('StudyForm.brand_name')"
              disabled
              hide-details
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="8">
            <v-text-field
              :model-value="form.study_subpart_acronym"
              :label="$t('StudyForm.subpart_acronym')"
              clearable
              :rules="[
                formRules.required,
                formRules.uppercaseAlphanumeric,
                (v) => formRules.max(v, 10),
              ]"
              @update:model-value="
                form.study_subpart_acronym = $event?.toUpperCase().trim()
              "
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="8">
            <v-text-field
              v-model="form.study_acronym"
              :label="$t('StudyForm.acronym')"
              disabled
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="8">
            <v-textarea
              v-model="form.description"
              :label="$t('_global.description')"
              clearable
              auto-grow
              rows="3"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #[`step.define`]>
      <v-form ref="defineFormRef">
        <v-card v-if="method === 'select'" class="px-4 mb-2">
          <v-card-title class="dialog-title">
            {{ $t('StudySubparts.selected_substudy') }}
          </v-card-title>
          <v-card-text>
            <v-data-table
              key="uid"
              :headers="selectedHeaders"
              :items="[selectedSubstudy]"
            >
              <template #bottom />
            </v-data-table>
          </v-card-text>
        </v-card>
        <v-card class="px-4" flat>
          <v-card-title class="dialog-title">
            {{ $t('StudySubparts.subpart_attrs') }}
          </v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="3" class="text-headline-small dialog-title">
                {{ $t('StudySubparts.derived_subpart_id') }}
              </v-col>
              <v-col cols="4">
                <v-text-field
                  :model-value="form.study_number"
                  disabled
                  hide-details
                />
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="3" class="dialog-title text-headline-small">
                {{ $t('StudySubparts.study_subpart_acronym') }}
              </v-col>
              <v-col cols="4">
                <v-text-field
                  v-model="form.study_subpart_acronym"
                  :rules="[
                    formRules.required,
                    formRules.uppercaseAlphanumeric,
                    (v) => formRules.max(v, 10),
                  ]"
                />
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="8">
                <span class="dialog-title text-headline-small">
                  {{ $t('_global.description') }}
                </span>
                <v-textarea
                  v-model="form.description"
                  clearable
                  auto-grow
                  rows="3"
                />
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-form>
    </template>
  </HorizontalStepperForm>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import studiesApi from '@/api/study'
import _isEmpty from 'lodash/isEmpty'
import filteringParameters from '@/utils/filteringParameters'
import NNTable from '@/components/tools/NNTable.vue'
import { useFormStore } from '@/stores/form'
import { useStudiesManageStore } from '@/stores/studies-manage'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const notificationHub = inject('notificationHub')
const formRules = inject('formRules')

const emit = defineEmits(['close'])

const { t } = useI18n()
const formStore = useFormStore()
const studiesGeneralStore = useStudiesGeneralStore()
const studiesManageStore = useStudiesManageStore()

const addStudy = studiesManageStore.addStudy
const selectedStudy = computed(() => studiesGeneralStore.selectedStudy)

const form = ref({})
const steps = ref(getInitialSteps())
const selectSteps = [
  { name: 'method', title: t('StudySubparts.select_method') },
  {
    name: 'select',
    title: t('StudySubparts.select_study_subpart'),
  },
  { name: 'define', title: t('StudySubparts.define_subpart') },
]
const createSteps = ref([
  { name: 'method', title: t('StudySubparts.select_method') },
  { name: 'create', title: t('StudySubparts.create_subpart') },
])
const method = ref('create')
const headers = [
  { title: '', key: 'select', width: '5%' },
  {
    title: t('StudySubparts.study_id'),
    key: 'current_metadata.identification_metadata.study_id',
  },
  {
    title: t('StudyTable.acronym'),
    key: 'current_metadata.identification_metadata.study_acronym',
  },
  {
    title: t('StudyTable.title'),
    key: 'current_metadata.study_description.study_title',
  },
  {
    title: t('_global.description'),
    key: 'current_metadata.identification_metadata.description',
  },
]
const selectedHeaders = [
  {
    title: t('StudySubparts.study_id'),
    key: 'current_metadata.identification_metadata.study_id',
  },
  {
    title: t('StudyTable.acronym'),
    key: 'current_metadata.identification_metadata.study_acronym',
  },
  {
    title: t('StudyTable.title'),
    key: 'current_metadata.study_description.study_title',
  },
  {
    title: t('_global.description'),
    key: 'current_metadata.identification_metadata.description',
  },
]
const studies = ref([])
const selectedSubstudy = ref({})
const total = ref(0)
const stepper = ref()
const selectFormRef = ref()
const createFormRef = ref()
const defineFormRef = ref()

watch(method, (value) => {
  steps.value = value === 'select' ? selectSteps : createSteps
  if (value === 'select') {
    notificationHub.add({
      msg: t('StudySubparts.select_warning'),
      type: 'warning',
      timeout: 15000,
    })
  }
  form.value = {}
})

onMounted(() => {
  initForm()
})

const initForm = () => {
  form.value = {
    study_acronym: studiesGeneralStore.studyAcronym,
  }
  formStore.save(form.value)
}
function selectStudy(study) {
  selectedSubstudy.value = study
  form.value.description =
    study.current_metadata.identification_metadata?.description
  form.value.study_acronym =
    study.current_metadata.identification_metadata?.study_acronym
}
function fetchAvailableStudies(filters, options, filtersUpdated) {
  if (filters) {
    const filtersObj = JSON.parse(filters)
    filtersObj.study_subpart_uids = { v: [] }
    filtersObj.study_parent_part = { v: [] }
    filtersObj.uid = { v: [selectedStudy.value.uid], op: 'ne' }
    filtersObj['current_metadata.identification_metadata.project_number'] = {
      v: [studiesGeneralStore.projectNumber],
    }
    filters = filtersObj
  } else {
    filters = {
      uid: { v: [selectedStudy.value.uid], op: 'ne' },
      study_subpart_uids: { v: [] },
      study_parent_part: { v: [] },
      'current_metadata.identification_metadata.study_number': { v: [] },
    }
  }
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  studiesApi.get(params).then((resp) => {
    studies.value = resp.data.items
    total.value = resp.data.total
  })
}
async function extraValidation(step) {
  if (step !== 2) {
    return true
  }
  if (method.value === 'select' && _isEmpty(selectedSubstudy.value)) {
    notificationHub.add({
      msg: t('StudySubparts.select_study_warning'),
      type: 'info',
    })
    return false
  }
  return true
}
async function cancel() {
  close()
}
function close() {
  emit('close')
  notificationHub.clearErrors()
  method.value = 'create'
  steps.value = selectSteps
  form.value = {}
  selectedSubstudy.value = {}
  formStore.reset()
  stepper.value.reset()
  stepper.value.loading = false
}
function submit() {
  notificationHub.clearErrors()

  if (method.value === 'select') {
    selectedSubstudy.value.study_parent_part_uid = selectedStudy.value.uid
    selectedSubstudy.value.current_metadata.identification_metadata.description =
      form.value.description
    selectedSubstudy.value.current_metadata.identification_metadata.study_subpart_acronym =
      form.value.study_subpart_acronym
    studiesApi
      .updateStudy(selectedSubstudy.value.uid, selectedSubstudy.value)
      .then(() => {
        notificationHub.add({
          msg: t('StudySubparts.subpart_created'),
        })
        stepper.value.loading = false
        close()
      })
  } else {
    form.value.project_number = studiesGeneralStore.projectNumber
    form.value.study_parent_part_uid = selectedStudy.value.uid
    addStudy(form.value).then(() => {
      notificationHub.add({
        msg: t('StudySubparts.subpart_created'),
      })
      close()
    })
  }
}
function getObserver(step) {
  if (step === 2) {
    return method.value === 'select' ? selectFormRef.value : createFormRef.value
  }
  if (step === 3) {
    return defineFormRef.value
  }
}
function getInitialSteps() {
  return [
    { name: 'method', title: t('StudySubparts.select_method') },
    { name: 'create', title: t('StudySubparts.create_subpart') },
  ]
}
</script>
