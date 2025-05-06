<template>
  <HorizontalStepperForm
    ref="stepper"
    :title="title"
    :steps="steps"
    :form-observer-getter="getObserver"
    :help-items="helpItems"
    @close="close"
    @step-loaded="initStep"
    @save="submit"
  >
    <template #[`step.activities`]>
      <div class="dialog-title">
        {{ $t('ActivityInstanceForm.step1_long_title') }}
      </div>
      <v-alert
        color="nnLightBlue200"
        icon="$info"
        class="mt-4 text-nnTrueBlue"
        type="info"
        rounded="lg"
        :text="$t('ActivityInstanceForm.step1_help')"
      />
      <v-form ref="step1FormRef">
        <v-radio-group v-model="selectedActivity" :rules="[formRules.required]">
          <NNTable
            hide-default-switches
            hide-export-button
            no-padding
            column-data-resource="concepts/activities/activities"
            :modifiable-table="false"
            :headers="activitiesHeaders"
            :items="activities"
            :items-length="totalActivities"
            @filter="fetchActivities"
          >
            <template #[`item.selection`]="{ item }">
              <v-radio
                color="primary"
                :value="getFullActivityUid(item)"
              ></v-radio>
            </template>
            <template #[`item.activity_instances`]="{ item }">
              <div v-html="showInstances(item)"></div>
            </template>
          </NNTable>
        </v-radio-group>
      </v-form>
    </template>
    <template #[`step.required`]>
      <v-form ref="step2FormRef">
        <div class="d-flex w-50">
          <v-select
            v-model="step2Form.activity_instance_class"
            :label="$t('ActivityInstanceForm.activity_instance_class')"
            :items="activityInstanceClasses"
            item-title="name"
            item-value="uid"
            return-object
            variant="outlined"
            density="compact"
            class="w-50"
            :loading="loadingActivityInstances"
            :disabled="activityInstanceUid !== null"
            :rules="[formRules.required]"
            @update:model-value="fetchActivityItemClasses"
          />
          <v-select
            v-model="step2Form.data_domain"
            :label="$t('ActivityInstanceForm.data_domain')"
            :items="dataDomains"
            variant="outlined"
            density="compact"
            class="ml-4 w-50"
            item-title="code_submission_value"
            item-value="uid"
            return-object
            @update:model-value="filterActivityInstanceClasses"
          />
        </div>
        <template
          v-if="
            mandatoryActivityItemClasses.length &&
            step2Form.activityItems.length &&
            step2Form.data_domain
          "
        >
          <div class="dialog-title mb-4">
            {{ $t('ActivityInstanceForm.step2_long_title') }}
          </div>
          <template v-if="!testCodeAic && !testNameAic">
            <ActivityItemClassField
              v-for="(activityItemClass, index) in mandatoryActivityItemClasses"
              :key="activityItemClass.uid"
              v-model="step2Form.activityItems[index]"
              :all-activity-item-classes="availableActivityItemClasses"
              :compatible-activity-item-classes="[activityItemClass]"
              :unit-dimension="selectedUnitDimension"
              :adam-specific="activityItemClass.is_adam_param_specific_enabled"
              :disabled="
                props.activityInstanceUid !== undefined &&
                props.activityInstanceUid !== null
              "
              :data-domain="step2Form.data_domain?.code_submission_value"
              select-value-only
              class="mb-4 w-50"
            />
          </template>
          <template v-else>
            <TestActivityItemClassField
              v-model="testValue"
              :test-code-aic="testCodeAic"
              :test-name-aic="testNameAic"
              :data-domain="step2Form.data_domain?.code_submission_value"
              class="w-50 mb-4"
            />

            <ActivityItemClassField
              v-for="(
                activityItemClass, index
              ) in remainingMdActivityItemClasses"
              :key="activityItemClass.uid"
              v-model="step2Form.activityItems[index]"
              :all-activity-item-classes="availableActivityItemClasses"
              :compatible-activity-item-classes="[activityItemClass]"
              :unit-dimension="selectedUnitDimension"
              :adam-specific="activityItemClass.is_adam_param_specific_enabled"
              :disabled="
                props.activityInstanceUid !== undefined &&
                props.activityInstanceUid !== null
              "
              :data-domain="step2Form.data_domain?.code_submission_value"
              select-value-only
              class="mb-4 w-50"
            />
          </template>
        </template>
        <template v-if="showMolecularWeight">
          <div class="dialog-title mb-4">
            {{ $t('ActivityInstanceForm.attributes') }}
          </div>
          <v-text-field
            v-model="step2Form.molecular_weight"
            :label="$t('ActivityInstanceForm.molecular_weight')"
            variant="outlined"
            density="compact"
            class="w-50"
            suffix="g/mol"
          />
        </template>
      </v-form>
    </template>
    <template #[`step.optional`]>
      <div class="dialog-title mb-4">
        {{ $t('ActivityInstanceForm.step3_long_title') }}
      </div>
      <v-form ref="step3FormRef">
        <ActivityItemClassField
          v-for="(activityItemClass, index) in step3Form.activityItems"
          :key="activityItemClass.uid"
          v-model="step3Form.activityItems[index]"
          :all-activity-item-classes="availableActivityItemClasses"
          :compatible-activity-item-classes="optionalActivityItemClasses"
          :disabled="props.activityInstanceUid !== null"
          :data-domain="step2Form.data_domain?.code_submission_value"
          adam-specific
          class="mb-4 w-50"
        >
          <template v-if="!props.activityInstanceUid" #append>
            <v-btn
              color="red"
              variant="flat"
              class="ml-4"
              @click="removeOptionalActivityItemClass(index)"
            >
              {{ $t('_global.remove') }}
            </v-btn>
          </template>
        </ActivityItemClassField>
        <v-btn
          v-if="!props.activityInstanceUid"
          color="secondary"
          variant="outlined"
          rounded="xl"
          prepend-icon="mdi-plus"
          class="mb-4"
          @click="addOptionalActivityItemClass"
        >
          {{ $t('ActivityInstanceForm.add_activity_item_class') }}
        </v-btn>
        <div class="dialog-title my-4">
          {{ $t('ActivityInstanceForm.step3_second_title') }}
          <v-btn
            icon="mdi-refresh"
            variant="flat"
            :title="$t('ActivityInstanceForm.refresh_title')"
            @click="sendPreviewRequest"
          />
        </div>
        <div class="d-flex w-50">
          <v-text-field
            v-model="step3Form.name"
            :label="$t('ActivityInstancePreview.activity_instance_name')"
            variant="outlined"
            density="compact"
            class="mr-4"
            :rules="[formRules.required]"
          />
          <v-text-field
            v-model="step3Form.name_sentence_case"
            :label="$t('ActivityInstancePreview.sentence_case_name')"
            variant="outlined"
            density="compact"
            class="mr-4"
            :rules="[formRules.required]"
          />
          <v-text-field
            v-model="step3Form.nci_concept_name"
            :label="$t('ActivityInstancePreview.nci_preferred_name')"
            variant="outlined"
            density="compact"
          />
        </div>
        <div class="d-flex w-50">
          <v-text-field
            v-model="step3Form.topic_code"
            :label="$t('ActivityInstancePreview.topic_code')"
            variant="outlined"
            density="compact"
            class="mr-4"
            :rules="[formRules.required]"
          />
          <v-text-field
            v-model="step3Form.adam_param_code"
            :label="$t('ActivityInstancePreview.adam_param_code')"
            variant="outlined"
            density="compact"
            class="mr-4"
            :rules="[formRules.required]"
          />
          <v-text-field
            v-model="step3Form.nci_code"
            :label="$t('ActivityInstancePreview.nci_code')"
            variant="outlined"
            density="compact"
          />
        </div>
        <div class="d-flex">
          <v-checkbox
            v-model="step3Form.is_research_lab"
            :label="$t('ActivityInstanceForm.data_from_research_lab')"
            color="primary"
          >
            <template #append>
              <v-icon
                icon="$info"
                size="small"
                color="primary"
                :title="$t('ActivityInstanceForm.data_from_research_lab_help')"
              />
            </template>
          </v-checkbox>
        </div>
      </v-form>
    </template>
    <template #[`step.dataspec`]>
      <div class="dialog-title mb-4">
        {{ $t('ActivityInstanceForm.step4_long_title') }}
      </div>
      <v-form ref="step4FormRef">
        <div class="d-flex w-50">
          <v-select
            v-model="step4Form.data_category"
            :label="$t('ActivityInstanceForm.data_category')"
            :items="domainDataCategories"
            item-title="name"
            item-value="term_uid"
            variant="outlined"
            density="compact"
          />
          <v-select
            v-model="step4Form.data_subcategory"
            :label="$t('ActivityInstanceForm.data_subcategory')"
            :items="dataSubcategories"
            item-title="name"
            item-value="term_uid"
            variant="outlined"
            density="compact"
            class="ml-4"
          />
        </div>
        <v-alert
          color="nnLightBlue200"
          icon="$info"
          class="my-4 text-nnTrueBlue"
          type="info"
          rounded="lg"
          width="fit-content"
          :text="$t('ActivityInstanceForm.step4_help')"
        />
        <ActivityItemClassField
          v-for="(activityItemClass, index) in step4Form.activityItems"
          :key="activityItemClass.uid"
          v-model="step4Form.activityItems[index]"
          :all-activity-item-classes="availableActivityItemClasses"
          :compatible-activity-item-classes="otherAvailableActivityItemClasses"
          :data-domain="step2Form.data_domain?.code_submission_value"
          class="mb-4 w-50"
          multiple
        >
          <template #append>
            <v-btn
              color="red"
              variant="flat"
              class="ml-4"
              @click="removeDataSpecActivityItemClass(index)"
            >
              {{ $t('_global.remove') }}
            </v-btn>
          </template>
        </ActivityItemClassField>
        <v-btn
          color="secondary"
          variant="outlined"
          rounded="xl"
          prepend-icon="mdi-plus"
          class="mb-4"
          @click="addDataSpecActivityItemClass"
        >
          {{ $t('ActivityInstanceForm.add_activity_item_class') }}
        </v-btn>
        <div class="dialog-title my-4">
          {{ $t('ActivityInstanceForm.step3_second_title') }}
        </div>
        <div class="d-flex">
          <v-checkbox
            v-model="step4Form.is_required_for_activity"
            :label="$t('ActivityInstanceForm.required_for_activity')"
            color="primary"
            class="mr-4"
          >
            <template #append>
              <v-icon
                icon="$info"
                size="small"
                color="primary"
                :title="$t('ActivityInstanceForm.required_for_activity_help')"
              />
            </template>
          </v-checkbox>
          <v-checkbox
            v-model="step4Form.is_data_sharing"
            :label="$t('ActivityInstanceForm.data_sharing')"
            color="primary"
            class="mr-4"
          >
            <template #append>
              <v-icon
                icon="$info"
                size="small"
                color="primary"
                :title="$t('ActivityInstanceForm.data_sharing_help')"
              />
            </template>
          </v-checkbox>
          <v-checkbox
            v-model="step4Form.is_default_selected_for_activity"
            :label="$t('ActivityInstanceForm.default_selected')"
            color="primary"
            class="mr-4"
          >
            <template #append>
              <v-icon
                icon="$info"
                size="small"
                color="primary"
                :title="$t('ActivityInstanceForm.default_selected_help')"
              />
            </template>
          </v-checkbox>
        </div>
      </v-form>
    </template>
  </HorizontalStepperForm>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import ActivityItemClassField from './ActivityItemClassField.vue'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import NNTable from '@/components/tools/NNTable.vue'
import TestActivityItemClassField from './TestActivityItemClassField.vue'
import activitiesApi from '@/api/activities'
import activityInstanceClassesApi from '@/api/activityInstanceClasses'
import activityItemClassesApi from '@/api/activityItemClasses'
import activityItemClassesConstants from '@/constants/activityItemClasses'
import libraryConstants from '@/constants/libraries.js'
import filteringParameters from '@/utils/filteringParameters'

const emit = defineEmits(['close'])
const props = defineProps({
  activityInstanceUid: {
    type: String,
    default: null,
  },
})

const { t } = useI18n()
const eventBusEmit = inject('eventBusEmit')
const formRules = inject('formRules')

const activityInstanceClasses = ref([])
const activities = ref([])
const activityInstance = ref(null)
const dataCategories = ref([])
const dataSubcategories = ref([])
const dataDomainsPerParentClass = ref({})
const loadingActivityInstances = ref(false)
const step2Form = ref({})
const step3Form = ref({})
const step4Form = ref({})
const selectedActivity = ref(null)
const stepper = ref()
const totalActivities = ref(0)
const testValue = ref(null)

const step1FormRef = ref()
const step2FormRef = ref()
const step3FormRef = ref()
const step4FormRef = ref()

const title = computed(() => {
  return props.activityInstanceUid
    ? t('ActivityInstanceForm.edit_title')
    : t('ActivityInstanceForm.add_title')
})

const allowedInstanceClasses = [
  'CategoricFindings',
  'NumericFindings',
  'TextualFindings',
]

const dataDomains = computed(() => {
  const aic = step2Form.value.activity_instance_class
  if (aic) {
    if (
      aic.parent_class &&
      dataDomainsPerParentClass.value[aic.parent_class.uid]
    ) {
      return dataDomainsPerParentClass.value[aic.parent_class.uid]
    }
    return []
  }
  const allDomains = new Set()
  for (const uid in dataDomainsPerParentClass.value) {
    for (const domain of dataDomainsPerParentClass.value[uid]) {
      if (!allDomains.has(domain)) {
        allDomains.add(domain)
      }
    }
  }
  return Array.from(allDomains.values())
})

const availableActivityItemClasses = computed(() => {
  if (!step2Form.value.activity_instance_class) {
    return []
  }
  let result = []
  if (
    step2Form.value.activity_instance_class?.parent_class?.activity_item_classes
  ) {
    result = result.concat(
      step2Form.value.activity_instance_class.parent_class.activity_item_classes
    )
  }
  if (step2Form.value.activity_instance_class.activity_item_classes) {
    result = result.concat(
      step2Form.value.activity_instance_class.activity_item_classes
    )
  }
  return result
})

const mandatoryActivityItemClasses = computed(() => {
  return availableActivityItemClasses.value.filter((item) => {
    return item.mandatory
  })
})
// Mandatory Activity Item Classes without test_code and test_name
const remainingMdActivityItemClasses = computed(() => {
  const result = availableActivityItemClasses.value.filter((item) => {
    return item.mandatory && !['test_code', 'test_name'].includes(item.name)
  })
  if (step2Form.value.activity_instance_class?.name === 'NumericFindings') {
    // FIXME: This is ugly... The API should be responsible for the sorting
    return [
      result.find((item) => item.name === 'unit_dimension'),
      result.find((item) => item.name === 'standard_unit'),
    ]
  }
  return result
})
const optionalActivityItemClasses = computed(() => {
  return availableActivityItemClasses.value.filter(
    (item) =>
      !item.mandatory &&
      item.is_adam_param_specific_enabled &&
      step3Form.value.activityItems.find(
        (selection) => selection.activity_item_class_uid === item.uid
      ) === undefined
  )
})
const otherAvailableActivityItemClasses = computed(() => {
  return availableActivityItemClasses.value.filter(
    (item) =>
      !item.mandatory &&
      step3Form.value.activityItems.find(
        (selection) => selection.activity_item_class_uid === item.uid
      ) === undefined &&
      step4Form.value.activityItems.find(
        (selection) => selection.activity_item_class_uid === item.uid
      ) === undefined
  )
})

const testCodeAic = computed(() => {
  return mandatoryActivityItemClasses.value.find(
    (aic) => aic.name === 'test_code'
  )
})
const testNameAic = computed(() => {
  return mandatoryActivityItemClasses.value.find(
    (aic) => aic.name === 'test_name'
  )
})

const selectedUnitDimension = computed(() => {
  let result = null
  const itemClasses =
    testCodeAic.value && testNameAic.value
      ? remainingMdActivityItemClasses.value
      : mandatoryActivityItemClasses.value
  itemClasses.forEach((aic, index) => {
    if (aic.name === 'unit_dimension') {
      result = step2Form.value.activityItems[index].ct_term_name
    }
  })
  return result
})

const showMolecularWeight = computed(() => {
  if (!selectedUnitDimension.value) {
    return false
  }
  return selectedUnitDimension.value.toLowerCase().includes('concentration')
})

watch(showMolecularWeight, (value) => {
  if (!value) {
    delete step2Form.value.molecular_weight
  }
})

const categoryAic = computed(() => {
  const aicName = step2Form.value.activity_instance_class?.name
  return availableActivityItemClasses.value.find(
    (item) =>
      item.name ===
      activityItemClassesConstants.categoryActivityItemClasses[aicName]
  )
})
const subcategoryAic = computed(() => {
  const aicName = step2Form.value.activity_instance_class?.name
  return availableActivityItemClasses.value.find(
    (item) =>
      item.name ===
      activityItemClassesConstants.subcategoryActivityItemClasses[aicName]
  )
})

const domainDataCategories = computed(() => {
  if (!step2Form.value.data_domain) {
    return []
  }
  return dataCategories.value.filter((item) => {
    const codelists =
      activityItemClassesConstants.codelistsPerDomain[
        step2Form.value.data_domain.code_submission_value
      ][categoryAic.value.name]
    if (codelists) {
      return codelists.includes(item.codelist_submission_value)
    }
    return false
  })
})

const activitiesHeaders = [
  { title: '', key: 'selection', noFilter: true },
  {
    title: t('ActivityInstanceForm.activity_group'),
    key: 'activity_groupings.0.activity_group_name',
    filteringName: 'activity_groupings.activity_group_name',
  },
  {
    title: t('ActivityInstanceForm.activity_subgroup'),
    key: 'activity_groupings.0.activity_subgroup_name',
    filteringName: 'activity_groupings.activity_subgroup_name',
  },
  {
    title: t('ActivityInstanceForm.activity_name'),
    key: 'name',
  },
  {
    title: t('ActivityInstanceForm.activity_instances'),
    key: 'activity_instances',
    filteringName: 'activity_instances.name',
    noFilter: true,
  },
]
const steps = [
  { name: 'activities', title: t('ActivityInstanceForm.step1_title') },
  { name: 'required', title: t('ActivityInstanceForm.step2_title') },
  { name: 'optional', title: t('ActivityInstanceForm.step3_title') },
  { name: 'dataspec', title: t('ActivityInstanceForm.step4_title') },
]
const helpItems = [
  'ActivityInstanceForm.general',
  'ActivityInstanceForm.step1_description',
  'ActivityInstanceForm.step2_description',
  'ActivityInstanceForm.step3_description',
  'ActivityInstanceForm.step4_description',
]

function fetchActivities(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  params.group_by_groupings = false
  activitiesApi.get(params, 'activities').then((resp) => {
    activities.value = resp.data.items
    totalActivities.value = resp.data.total
  })
}

async function fetchActivityItemClasses(activityInstanceClass) {
  if (activityInstanceClass) {
    step2Form.value.activityItems = []
    mandatoryActivityItemClasses.value.forEach((aic) => {
      let activityItem
      if (['test_code', 'test_name'].includes(aic.name)) {
        return
      }
      if (activityInstance.value) {
        const matched = activityInstance.value.activity_items.find(
          (item) => item.activity_item_class.uid === aic.uid
        )
        activityItem = {
          activity_item_class_uid: matched.activity_item_class.uid,
          ct_term_uids: matched.ct_terms.map((ct_term) => ct_term.uid),
        }
      } else {
        activityItem = { activity_item_class_uid: aic.uid }
      }
      step2Form.value.activityItems.push(activityItem)
    })
    const aicName = activityInstanceClass.name
    if (!activityItemClassesConstants.categoryActivityItemClasses[aicName]) {
      return
    }
    let resp = await activityItemClassesApi.getTerms(categoryAic.value.uid, {
      page_size: 0,
    })
    dataCategories.value = resp.data.items
    resp = await activityItemClassesApi.getTerms(subcategoryAic.value.uid, {
      page_size: 0,
    })
    dataSubcategories.value = resp.data.items
  } else {
    step2Form.value.activityItems = []
  }
}

function filterActivityInstanceClasses(dataDomainUid) {
  if (step2Form.value.activity_instance_class) {
    return
  }
  const filters = {
    'parent_class.data_domains.uid': { v: [dataDomainUid] },
    name: { v: allowedInstanceClasses },
    level: { v: [3] },
  }
  loadingActivityInstances.value = true
  activityInstanceClassesApi
    .getAll({
      filters,
      page_size: 0,
    })
    .then((resp) => {
      activityInstanceClasses.value = resp.data.items
      loadingActivityInstances.value = false
    })
}

function getFullActivityUid(activity) {
  const grouping = activity.activity_groupings[0]
  return `${grouping.activity_group_uid}|${grouping.activity_subgroup_uid}|${activity.uid}`
}

function addOptionalActivityItemClass() {
  step3Form.value.activityItems.push({})
}

function removeOptionalActivityItemClass(index) {
  step3Form.value.activityItems.splice(index, 1)
}

function addDataSpecActivityItemClass() {
  step4Form.value.activityItems.push({})
}

function removeDataSpecActivityItemClass(index) {
  step4Form.value.activityItems.splice(index, 1)
}

function resetForms() {
  selectedActivity.value = null
  step2Form.value = {
    activityItems: [],
  }
  step3Form.value = {
    activityItems: [],
  }
  step4Form.value = {
    activityItems: [],
  }
}

function showInstances(item) {
  return item.activity_instances.map((instance) => instance.name).join('<br/>')
}

function close() {
  resetForms()
  emit('close')
}

function getObserver(step) {
  const observers = {
    1: step1FormRef,
    2: step2FormRef,
    3: step3FormRef,
    4: step4FormRef,
  }
  return observers[step]?.value
}

function prepareCreationPayload(forPreview) {
  const [activityGroupUid, activitySubgroupUid, activityUid] =
    selectedActivity.value.split('|')
  const activityItems = step2Form.value.activityItems.concat(
    step3Form.value.activityItems,
    step4Form.value.activityItems
  )

  function addActivityItem(uid, term_uids) {
    activityItems.push({
      activity_item_class_uid: uid,
      ct_term_uids: term_uids,
      odm_item_uids: [],
      unit_definition_uids: [],
      is_adam_param_specific: false,
    })
  }

  if (testValue.value) {
    addActivityItem(testCodeAic.value.uid, [testValue.value])
    addActivityItem(testNameAic.value.uid, [testValue.value])
  }

  if (step4Form.value.data_category) {
    const uid = otherAvailableActivityItemClasses.value.find(
      (item) =>
        item.name ===
        activityItemClassesConstants.categoryActivityItemClasses[
          step2Form.value.activity_instance_class.name
        ]
    ).uid
    addActivityItem(uid, [step4Form.value.data_category])
  }
  if (step4Form.value.data_subcategory) {
    const uid = otherAvailableActivityItemClasses.value.find(
      (item) =>
        item.name ===
        activityItemClassesConstants.subcategoryActivityItemClasses[
          step2Form.value.activity_instance_class.name
        ]
    ).uid
    addActivityItem(uid, [step4Form.value.data_subcategory])
  }

  const result = {
    library_name: libraryConstants.LIBRARY_SPONSOR,
    nci_concept_name: step3Form.value.nci_concept_name,
    nci_code: step3Form.value.nci_code,
    activity_instance_class_uid: step2Form.value.activity_instance_class.uid,
    activity_items: activityItems,
    is_required_for_activity: step4Form.value.is_required_for_activity,
    is_default_selected_for_activity:
      step4Form.value.is_default_selected_for_activity,
    is_data_sharing: step4Form.value.is_data_sharing,
    is_research_lab: step3Form.value.is_research_lab,
    activity_groupings: [
      {
        activity_group_uid: activityGroupUid,
        activity_subgroup_uid: activitySubgroupUid,
        activity_uid: activityUid,
      },
    ],
  }
  if (step2Form.value.molecular_weight) {
    result.molecular_weight = step2Form.value.molecular_weight
  }
  if (!forPreview) {
    result.name = step3Form.value.name
    result.name_sentence_case = step3Form.value.name_sentence_case
    result.adam_param_code = step3Form.value.adam_param_code
    result.topic_code = step3Form.value.topic_code
  }
  return result
}

async function sendPreviewRequest() {
  const payload = prepareCreationPayload(true)
  const resp = await activitiesApi.getPreview(payload, 'activity-instances')
  step3Form.value.name = resp.data.name
  step3Form.value.name_sentence_case = resp.data.name_sentence_case
  step3Form.value.topic_code = resp.data.topic_code
  step3Form.value.adam_param_code = resp.data.adam_param_code
}

async function initStep(step) {
  if (step === 3 && !step3Form.value.name && !activityInstance.value) {
    await sendPreviewRequest()
  }
}

async function submit() {
  const payload = prepareCreationPayload()
  try {
    await activitiesApi.create(payload, 'activity-instances')
    eventBusEmit('notification', {
      msg: t('ActivityInstanceForm.add_success'),
    })
    close()
  } finally {
    stepper.value.loading = false
  }
}

resetForms()

let resp = await activityInstanceClassesApi.getAll({
  filters: {
    name: { v: allowedInstanceClasses },
    level: { v: [3] },
  },
  page_size: 0,
})
for (const aic of resp.data.items) {
  activityInstanceClasses.value.push(aic)
  if (aic.parent_class && aic.parent_class.data_domains) {
    dataDomainsPerParentClass.value[aic.parent_class.uid] =
      aic.parent_class.data_domains
  }
}

if (props.activityInstanceUid) {
  resp = await activitiesApi.getObject(
    'activity-instances',
    props.activityInstanceUid
  )
  activityInstance.value = resp.data
  // FIXME: Can we have imported activity instances linked to multiple groupings?
  const grouping = activityInstance.value.activity_groupings[0]
  selectedActivity.value = `${grouping.activity_group.uid}|${grouping.activity_subgroup.uid}|${grouping.activity.uid}`
  step2Form.value.activity_instance_class = activityInstanceClasses.value.find(
    (item) => item.uid === activityInstance.value.activity_instance_class.uid
  )
  await fetchActivityItemClasses(step2Form.value.activity_instance_class)
  step3Form.value.name = activityInstance.value.name
  step3Form.value.name_sentence_case = activityInstance.value.name_sentence_case
  step3Form.value.nci_concept_name = activityInstance.value.nci_concept_name
  step3Form.value.topic_code = activityInstance.value.topic_code
  step3Form.value.adam_param_code = activityInstance.value.adam_param_code
  step3Form.value.nci_code = activityInstance.value.nci_code

  for (const activityItem of activityInstance.value.activity_items) {
    let matched = optionalActivityItemClasses.value.find(
      (aic) => aic.uid === activityItem.activity_item_class.uid
    )
    if (matched) {
      step3Form.value.activityItems.push({
        activity_item_class_uid: matched.uid,
        ct_term_uids: activityItem.ct_terms.map((ct_term) => ct_term.uid),
      })
      continue
    }
    matched = otherAvailableActivityItemClasses.value.find(
      (aic) => aic.uid === activityItem.activity_item_class.uid
    )
    if (matched) {
      step4Form.value.activityItems.push({
        activity_item_class_uid: matched.uid,
        ct_term_uids: activityItem.ct_terms.map((ct_term) => ct_term.uid),
      })
    }
  }
}
</script>
