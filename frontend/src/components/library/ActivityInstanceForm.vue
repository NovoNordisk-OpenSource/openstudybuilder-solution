<template>
  <HorizontalStepperForm
    ref="stepper"
    :title="title"
    :steps="steps"
    :form-observer-getter="getObserver"
    :extra-step-validation="extraStepValidation"
    :help-items="helpItems"
    @close="close"
    @step-loaded="initStep"
    @save="submit"
  >
    <template #header>
      <v-alert v-if="!selectedActivity.length" type="info" variant="tonal">
        {{ $t('ActivityInstanceForm.no_grouping_selected') }}
      </v-alert>
      <v-alert
        v-if="selectedActivity.length"
        :type="hasMixedActivitySelection ? 'warning' : 'info'"
        variant="tonal"
      >
        <template v-if="hasMixedActivitySelection">
          <div>{{ $t('ActivityInstanceForm.activity_mixed_selection') }}</div>
          <div
            v-for="(
              activityGroupings, activityName
            ) in selectedActivityDetails.groupingsByActivity"
            :key="activityName"
            class="mt-2"
          >
            <div>
              {{ $t('ActivityInstanceForm.selected_activity') }}
              {{ activityName }}
            </div>
            <div
              v-for="grouping in activityGroupings"
              :key="grouping.selectionUid"
              class="d-flex align-center"
            >
              {{ $t('ActivityInstanceForm.activity_group') }}:
              {{ grouping.activityGroupName }},
              {{ $t('ActivityInstanceForm.activity_subgroup') }}:
              {{ grouping.activitySubgroupName }}
              <v-btn
                v-if="isOnFirstStep"
                icon="mdi-delete"
                variant="text"
                size="x-small"
                density="compact"
                class="ml-2"
                :title="$t('_global.remove')"
                @click="removeGroupingSelection(grouping.selectionUid)"
              />
            </div>
          </div>
        </template>
        <template v-else>
          <div>
            {{ $t('ActivityInstanceForm.selected_activity') }}
            {{ selectedActivityDetails.activityName }}
          </div>
          <div
            v-for="grouping in selectedActivityDetails.groupings"
            :key="grouping.selectionUid"
            class="d-flex align-center"
          >
            {{ $t('ActivityInstanceForm.activity_group') }}:
            {{ grouping.activityGroupName }},
            {{ $t('ActivityInstanceForm.activity_subgroup') }}:
            {{ grouping.activitySubgroupName }}
            <v-btn
              v-if="isOnFirstStep"
              icon="mdi-delete"
              variant="text"
              size="x-small"
              density="compact"
              class="ml-2"
              :title="$t('_global.remove')"
              @click="removeGroupingSelection(grouping.selectionUid)"
            />
          </div>
        </template>
      </v-alert>
    </template>
    <template #[`step.activities`]>
      <div class="dialog-title">
        {{
          props.editMode === 'groupings'
            ? $t('ActivityInstanceForm.step1_long_title_edit_groupings')
            : $t('ActivityInstanceForm.step1_long_title')
        }}
      </div>
      <v-alert
        color="nnLightBlue200"
        icon="$info"
        class="my-4 text-nnTrueBlue"
        type="info"
        rounded="lg"
        :text="$t('ActivityInstanceForm.step1_help')"
      />
      <v-form ref="step1FormRef">
        <NNTable
          table-id="activity-instance-form-activities"
          hide-default-switches
          hide-export-button
          no-padding
          column-data-resource="concepts/activities/activities"
          :item-value="(item) => getFullActivityUid(item)"
          :modifiable-table="false"
          :headers="activitiesHeaders"
          :items="activities"
          :items-length="totalActivities"
          @filter="fetchActivities"
        >
          <template #[`item.selection`]="{ item }">
            <v-checkbox
              v-model="selectedActivity"
              :value="getFullActivityUid(item)"
              hide-details
            />
          </template>
          <template #[`item.activity_instances`]="{ item }">
            <div v-html="sanitizeHTML(showInstances(item))"></div>
          </template>
        </NNTable>
      </v-form>
    </template>
    <template #[`step.required`]>
      <v-form ref="step2FormRef">
        <div class="d-flex w-50">
          <v-select
            v-model="step2Form.activity_instance_class"
            :label="$t('ActivityInstanceForm.activity_instance_class')"
            :items="activityInstanceClassOptions"
            item-title="name"
            item-value="uid"
            return-object
            class="w-50"
            :loading="loadingActivityInstances"
            :disabled="activityInstanceUid !== null"
            :rules="[formRules.required]"
            :error-messages="activityInstanceClassWarningMessages"
            @update:model-value="fetchActivityItemClasses"
          />
          <v-select
            v-model="step2Form.data_domain"
            :label="$t('ActivityInstanceForm.data_domain')"
            :items="filteredDataDomains"
            item-title="title"
            item-value="value"
            class="ml-4 w-50"
            :rules="[formRules.required]"
            :disabled="
              props.activityInstanceUid !== undefined &&
              props.activityInstanceUid !== null &&
              hasExistingDataDomain
            "
            @update:model-value="filterActivityInstanceClasses"
          >
            <template #menu-header>
              <SelectMenuSearch
                v-model="domainSearch"
                :placeholder="$t('_global.search')"
              />
            </template>
          </v-select>
        </div>
        <div class="d-flex w-50">
          <SelectCTTermField
            v-model="step2Form.data_category"
            :label="$t('ActivityInstanceForm.data_category')"
            :codelist="categoryCodelistName"
            item-title="submission_value"
            class="mr-4 w-50"
            clearable
            hide-details="auto"
          />
          <SelectCTTermField
            v-model="step2Form.data_subcategory"
            :label="$t('ActivityInstanceForm.data_subcategory')"
            :codelist="subcategoryCodelistName"
            item-title="submission_value"
            class="w-50"
            clearable
            hide-details
          />
        </div>
        <template
          v-if="
            ((testCodeAic && testNameAic) ||
              mandatoryActivityItemClasses.length) &&
            (step2Form.data_domain || hasExistingMandatoryItems)
          "
        >
          <div class="dialog-title my-4">
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
              :data-domain="step2Form.data_domain"
              :preselected-unit-name="
                step2Form.activityItems[index]?.preselected_unit_name
              "
              select-value-only
              class="mb-4 w-50"
            />
          </template>
          <template v-else>
            <TestActivityItemClassField
              v-model="testValue"
              v-model:code-codelist="testCodeCodelistValue"
              v-model:name-codelist="testNameCodelistValue"
              :test-code-aic="testCodeAic"
              :test-name-aic="testNameAic"
              :data-domain="step2Form.data_domain"
              class="w-50 mb-4"
            />

            <ActivityItemClassField
              v-for="(activityItemClass, index) in mandatoryActivityItemClasses"
              :key="activityItemClass.uid"
              v-model="step2Form.activityItems[index]"
              :all-activity-item-classes="availableActivityItemClasses"
              :compatible-activity-item-classes="[activityItemClass]"
              :unit-dimension="selectedUnitDimension"
              :adam-specific="activityItemClass.is_adam_param_specific_enabled"
              :data-domain="step2Form.data_domain"
              :preselected-unit-name="
                step2Form.activityItems[index]?.preselected_unit_name
              "
              select-value-only
              class="mb-4"
              :class="{
                'w-50':
                  activityItemClass.name !==
                  'categoric_finding_original_result',
              }"
              :with-advanced-search="
                activityItemClass.name === 'categoric_finding_original_result'
              "
              :multiple="
                activityItemClass.name === 'categoric_finding_original_result'
              "
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
            class="w-50"
            suffix="g/mol"
            :rules="[validateMolecularWeight]"
            :hint="$t('ActivityInstanceForm.molecular_weight_hint')"
            persistent-hint
          />
        </template>
      </v-form>
    </template>
    <template #[`step.optional`]>
      <v-form ref="step3FormRef">
        <div
          v-if="!props.activityInstanceUid || step3Form.activityItems?.length"
          class="dialog-title mb-4"
        >
          {{ step3LongTitle }}
        </div>
        <ActivityItemClassField
          v-for="(activityItemClass, index) in step3Form.activityItems"
          :key="activityItemClass.uid"
          v-model="step3Form.activityItems[index]"
          :all-activity-item-classes="filteredActivityItemClasses"
          :compatible-activity-item-classes="optionalActivityItemClasses"
          :disabled="
            props.activityInstanceUid !== null &&
            !step3EmptyItemIndices.has(index)
          "
          :data-domain="step2Form.data_domain"
          :unit-dimension="selectedUnitDimension"
          adam-specific
          class="mb-4 w-50"
          @update:model-value="updateAIFields"
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
        <div class="d-flex align-center dialog-title my-4">
          {{ $t('ActivityInstanceForm.step3_second_title') }}
          <v-btn
            icon="mdi-refresh"
            variant="flat"
            :title="$t('ActivityInstanceForm.refresh_title')"
            @click="sendPreviewRequest"
          />

          <v-switch
            v-if="!props.activityInstanceUid"
            v-model="allowManualEdit"
            :label="$t('ActivityInstanceForm.allow_manual_edit')"
            class="ml-4"
            hide-details
            @update:model-value="onAllowManualEditChange"
          />
        </div>
        <div class="d-flex">
          <v-text-field
            v-model="step3Form.name"
            :label="$t('ActivityInstancePreview.activity_instance_name')"
            class="mr-4 w-50"
            :disabled="!allowManualEdit"
            :loading="loadingPreview"
            :rules="[formRules.required]"
          />
          <v-text-field
            v-model="step3Form.name_sentence_case"
            :label="$t('ActivityInstancePreview.sentence_case_name')"
            class="mr-4 w-50"
            :disabled="!allowManualEdit"
            :loading="loadingPreview"
            :rules="[
              formRules.required,
              (value) => formRules.sameAs(value, step3Form.name),
            ]"
          />
        </div>
        <div class="d-flex">
          <v-text-field
            v-model="step3Form.topic_code"
            :label="$t('ActivityInstancePreview.topic_code')"
            class="mr-4 w-50"
            :disabled="
              !allowManualEdit ||
              (props.activityInstanceUid !== undefined &&
                props.activityInstanceUid !== null)
            "
            :loading="loadingPreview"
            :rules="[formRules.required]"
          />
          <v-text-field
            v-if="showAdamParamCode"
            v-model="step3Form.adam_param_code"
            :label="$t('ActivityInstancePreview.adam_param_code')"
            class="mr-4 w-50"
            :disabled="!allowManualEdit"
            :loading="loadingPreview"
            :rules="[formRules.required]"
          />
        </div>
        <div class="d-flex">
          <v-text-field
            v-model="step3Form.nci_concept_name"
            :label="$t('ActivityInstancePreview.nci_preferred_name')"
            class="mr-4 w-50"
          />
          <v-text-field
            v-model="step3Form.nci_concept_id"
            :label="$t('ActivityInstancePreview.nci_code')"
            class="mr-4 w-50"
          />
        </div>
        <div class="d-flex">
          <v-checkbox
            v-if="showIsResearchLab"
            v-model="step3Form.is_research_lab"
            :label="$t('ActivityInstanceForm.data_from_research_lab')"
            :disabled="activityInstanceUid !== null"
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
      <v-form ref="step4FormRef">
        <div class="dialog-title mb-4">
          {{ $t('ActivityInstanceForm.step3_second_title') }}
        </div>
        <div class="d-flex">
          <v-checkbox
            v-model="step4Form.is_required_for_activity"
            :label="$t('ActivityInstanceForm.required_for_activity')"
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
        <div class="dialog-title my-4">
          {{ $t('ActivityInstanceForm.step4_long_title') }}
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
        <v-card
          v-for="aic in defaultLinkedActivityItemClasses"
          :key="'default-' + aic.uid"
          class="bg-nnBaseLight mb-4 w-50"
          rounded="lg"
          border="sm"
          flat
        >
          <v-card-text>
            <div class="d-flex">
              <v-select
                :model-value="aic.uid"
                :label="$t('ActivityInstanceForm.activity_item_class')"
                :items="[aic]"
                item-title="display_name"
                item-value="uid"
                bg-color="white"
                class="w-50"
                disabled
              />
              <v-chip
                class="ml-4 mt-3"
                color="info"
                variant="tonal"
                size="small"
              >
                {{ $t('ActivityInstanceForm.default_linked') }}
              </v-chip>
            </div>
          </v-card-text>
        </v-card>
        <ActivityItemClassField
          v-for="(activityItemClass, index) in step4Form.activityItems"
          :key="activityItemClass.uid"
          v-model="step4Form.activityItems[index]"
          :all-activity-item-classes="filteredActivityItemClasses"
          :compatible-activity-item-classes="otherAvailableActivityItemClasses"
          :data-domain="step2Form.data_domain"
          :unit-dimension="selectedUnitDimension"
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
        <template v-if="props.activityInstanceUid">
          <div class="dialog-title my-4">
            {{ $t('_global.change_description') }}
          </div>
          <v-text-field
            v-model="step4Form.change_description"
            :rules="[formRules.required]"
            class="w-50"
          />
        </template>
      </v-form>
    </template>
    <template #[`step.groupings_change`]>
      <v-form ref="groupingsChangeFormRef">
        <div class="dialog-title my-4">
          {{ $t('_global.change_description') }}
        </div>
        <v-text-field
          v-model="groupingsChangeForm.change_description"
          :rules="[formRules.required]"
          class="w-50"
        />
      </v-form>
    </template>
  </HorizontalStepperForm>
</template>

<script setup>
import { computed, inject, ref, watch, watchEffect } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useFeatureFlagsStore } from '@/stores/feature-flags'
import _debounce from 'lodash/debounce'
import ActivityItemClassField from './ActivityItemClassField.vue'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import NNTable from '@/components/tools/NNTable.vue'
import SelectCTTermField from '@/components/tools/SelectCTTermField.vue'
import SelectMenuSearch from '@/components/tools/SelectMenuSearch.vue'
import TestActivityItemClassField from './TestActivityItemClassField.vue'
import activitiesApi from '@/api/activities'
import activityInstanceClassesApi from '@/api/activityInstanceClasses'
import codelistsApi from '@/api/controlledTerminology/codelists'
import ctApi from '@/api/controlledTerminology'
import activityItemClassesConstants from '@/constants/activityItemClasses'
import libraryConstants from '@/constants/libraries.js'
import statuses from '@/constants/statuses.js'
import filteringParameters from '@/utils/filteringParameters'
import { escapeHTML, sanitizeHTML } from '@/utils/sanitize'

const emit = defineEmits(['close'])
const props = defineProps({
  activityInstanceUid: {
    type: String,
    default: null,
  },
  editMode: {
    type: String,
    default: 'create',
    validator: (value) => ['create', 'groupings', 'attributes'].includes(value),
  },
  preselectedGroupings: {
    type: Array,
    default: () => [],
  },
})

const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const notificationHub = inject('notificationHub')
const formRules = inject('formRules')
const featureFlagsStore = useFeatureFlagsStore()

const activityInstanceClasses = ref([])
const activities = ref([])
const activityInstance = ref(null)
const allowManualEdit = ref(true)
const dataDomainCTTermUid = ref(null)
const datasets = ref([])
const domainNames = ref({})
const loadingActivityInstances = ref(false)
const loadingPreview = ref(false)
const isOnFirstStep = computed(() => stepper.value?.currentStep === 1)
const step2Form = ref({})
const step3Form = ref({})
const step4Form = ref({})
const selectedActivity = ref([])
const stepper = ref()
const totalActivities = ref(0)
const testValue = ref(null)
const testCodeCodelistValue = ref(null)
const testNameCodelistValue = ref(null)
const hasExistingDataDomain = ref(false)
const step3EmptyItemIndices = ref(new Set())
const selectionDetailsCache = ref(new Map())

const step1FormRef = ref()
const step2FormRef = ref()
const step3FormRef = ref()
const step4FormRef = ref()
const groupingsChangeFormRef = ref()
const groupingsChangeForm = ref({ change_description: '' })

const title = computed(() => {
  const instanceName = activityInstance.value?.name
  let base
  if (props.editMode === 'groupings') {
    base = t('ActivityInstanceForm.edit_groupings_title')
  } else if (props.editMode === 'attributes') {
    base = t('ActivityInstanceForm.edit_attributes_title')
  } else if (props.activityInstanceUid) {
    base = t('ActivityInstanceForm.edit_title')
  } else {
    return t('ActivityInstanceForm.add_title')
  }
  return instanceName ? `${base}: ${instanceName}` : base
})

const allowedInstanceClasses = []
if (
  featureFlagsStore.getFeatureFlag(
    'activity_instance_wizard_stepper_categoric_findings'
  ) === true
) {
  allowedInstanceClasses.push('CategoricFindings')
}
if (
  featureFlagsStore.getFeatureFlag(
    'activity_instance_wizard_stepper_events'
  ) === true
) {
  allowedInstanceClasses.push('Events')
}
allowedInstanceClasses.push('NumericFindings')
if (
  featureFlagsStore.getFeatureFlag(
    'activity_instance_wizard_stepper_textual_findings'
  ) === true
) {
  allowedInstanceClasses.push('TextualFindings')
}
if (
  featureFlagsStore.getFeatureFlag(
    'activity_instance_wizard_stepper_interventions'
  ) === true
) {
  allowedInstanceClasses.push('Interventions')
}

const domainSearch = ref('')

const dataDomains = computed(() => {
  let abbreviations
  if (!datasets.value.length) {
    return []
  }
  if (datasets.value.length === 1) {
    abbreviations = datasets.value[0].datasets
  } else {
    const allValues = new Set()
    for (const item of datasets.value) {
      for (const domain of item.datasets) {
        allValues.add(domain)
      }
    }
    abbreviations = Array.from(allValues.values())
  }
  return abbreviations.map((abbr) => {
    const name = domainNames.value[abbr]
    return {
      value: abbr,
      title: name ? `${abbr} - ${name}` : abbr,
    }
  })
})

const filteredDataDomains = computed(() => {
  if (!domainSearch.value) return dataDomains.value
  const query = domainSearch.value.toLowerCase()
  return dataDomains.value.filter((d) => d.title.toLowerCase().includes(query))
})

const step3LongTitle = computed(() => {
  if (step2Form.value.activity_instance_class?.name === 'Events') {
    return t('ActivityInstanceForm.step3_events_long_title')
  }
  if (step2Form.value.activity_instance_class?.name === 'Interventions') {
    return t('ActivityInstanceForm.step3_interventions_long_title')
  }
  return t('ActivityInstanceForm.step3_long_title')
})

function parseSelectedActivityUid(value) {
  const [activityGroupUid, activitySubgroupUid, activityUid] =
    value?.split('|') || []
  return {
    activityGroupUid: activityGroupUid || '',
    activitySubgroupUid: activitySubgroupUid || '',
    activityUid: activityUid || '',
  }
}

function getGroupingUids(grouping = {}) {
  return {
    activityGroupUid:
      grouping.activity_group_uid || grouping.activity_group?.uid || '',
    activitySubgroupUid:
      grouping.activity_subgroup_uid || grouping.activity_subgroup?.uid || '',
    activityUid: grouping.activity_uid || grouping.activity?.uid || '',
  }
}

function formatSelectedActivityDetails(
  grouping = {},
  fallbackActivityName = ''
) {
  const activityGroupName =
    grouping.activity_group_name || grouping.activity_group?.name || ''
  const activitySubgroupName =
    grouping.activity_subgroup_name || grouping.activity_subgroup?.name || ''
  const activityName =
    grouping.activity_name || grouping.activity?.name || fallbackActivityName

  return {
    activityName,
    activityGroupName,
    activitySubgroupName,
  }
}

const selectedActivityDetails = computed(() => {
  if (!selectedActivity.value.length) {
    return {
      activityName: '',
      groupings: [],
      distinctActivityNames: [],
      groupingsByActivity: {},
    }
  }

  let activityName = ''
  const groupings = []

  for (const selection of selectedActivity.value) {
    const cached = selectionDetailsCache.value.get(selection)
    if (cached) {
      if (!activityName && cached.activityName) {
        activityName = cached.activityName
      }
      groupings.push({ ...cached, selectionUid: selection })
      continue
    }

    // Fallback for entries not yet cached (should be rare)
    const details = formatSelectedActivityDetails()
    groupings.push({ ...details, selectionUid: selection })
  }

  const distinctActivityNames = [
    ...new Set(groupings.map((g) => g.activityName).filter(Boolean)),
  ]

  const groupingsByActivity = {}
  for (const g of groupings) {
    const name = g.activityName || ''
    if (!groupingsByActivity[name]) {
      groupingsByActivity[name] = []
    }
    groupingsByActivity[name].push(g)
  }

  return { activityName, groupings, distinctActivityNames, groupingsByActivity }
})

// Maintain a cache of selection details so names survive table re-fetches
watchEffect(() => {
  for (const selection of selectedActivity.value) {
    if (selectionDetailsCache.value.has(selection)) continue

    const { activityGroupUid, activitySubgroupUid, activityUid } =
      parseSelectedActivityUid(selection)

    const fromTable = activities.value.find(
      (item) => getFullActivityUid(item) === selection
    )
    if (fromTable) {
      const grouping =
        fromTable.activity_groupings?.find((item) => {
          const uids = getGroupingUids(item)
          return (
            uids.activityGroupUid === activityGroupUid &&
            uids.activitySubgroupUid === activitySubgroupUid
          )
        }) || fromTable.activity_groupings?.[0]
      selectionDetailsCache.value.set(
        selection,
        formatSelectedActivityDetails(grouping, fromTable.name)
      )
      continue
    }

    const fromInstance = activityInstance.value?.activity_groupings?.find(
      (item) => {
        const uids = getGroupingUids(item)
        return (
          uids.activityGroupUid === activityGroupUid &&
          uids.activitySubgroupUid === activitySubgroupUid &&
          uids.activityUid === activityUid
        )
      }
    )
    if (fromInstance) {
      selectionDetailsCache.value.set(
        selection,
        formatSelectedActivityDetails(fromInstance)
      )
    }
  }

  // Clean up deselected entries
  for (const key of selectionDetailsCache.value.keys()) {
    if (!selectedActivity.value.includes(key)) {
      selectionDetailsCache.value.delete(key)
    }
  }
})

const hasMixedActivitySelection = computed(() => {
  if (selectedActivity.value.length < 2) return false
  const activityUids = selectedActivity.value.map(
    (val) => parseSelectedActivityUid(val).activityUid
  )
  return new Set(activityUids).size > 1
})

const availableActivityItemClasses = ref([])
const filteredActivityItemClasses = ref([])

// List of activity item classes that should not be proposed to end users
const activityItemClassExceptions = computed(() => {
  const exceptions = ['domain']
  if (categoryAic.value) {
    exceptions.push(categoryAic.value.name)
  }
  if (subcategoryAic.value) {
    exceptions.push(subcategoryAic.value.name)
  }
  return exceptions
})

const mandatoryActivityItemClasses = computed(() => {
  const result = availableActivityItemClasses.value.filter((item) => {
    return (
      item.mandatory &&
      !activityItemClassExceptions.value.includes(item.name) &&
      !['test_code', 'test_name'].includes(item.name)
    )
  })
  if (step2Form.value.activity_instance_class?.name === 'NumericFindings') {
    // special sorting for NumericFindings
    return [
      result.find((item) => item.name === 'unit_dimension'),
      result.find((item) => item.name === 'standard_unit'),
    ].filter(Boolean) // Filter out undefined values
  }
  return result
})

const optionalActivityItemClasses = computed(() => {
  return filteredActivityItemClasses.value.filter(
    (item) =>
      !item.mandatory &&
      item.is_adam_param_specific_enabled &&
      !activityItemClassExceptions.value.includes(item.name) &&
      step3Form.value.activityItems.find(
        (selection) => selection.activity_item_class_uid === item.uid
      ) === undefined
  )
})
const otherAvailableActivityItemClasses = computed(() => {
  return filteredActivityItemClasses.value.filter(
    (item) =>
      item.is_additional_optional &&
      !activityItemClassExceptions.value.includes(item.name) &&
      step3Form.value.activityItems.find(
        (selection) => selection.activity_item_class_uid === item.uid
      ) === undefined &&
      step4Form.value.activityItems.find(
        (selection) => selection.activity_item_class_uid === item.uid
      ) === undefined
  )
})

const defaultLinkedActivityItemClasses = computed(() => {
  const result = filteredActivityItemClasses.value.filter(
    (item) => item.is_default_linked
  )
  return result
})

const testCodeAic = computed(() => {
  return availableActivityItemClasses.value.find(
    (aic) => aic.name === 'test_code'
  )
})
const testNameAic = computed(() => {
  return availableActivityItemClasses.value.find(
    (aic) => aic.name === 'test_name'
  )
})
const domainAic = computed(() => {
  return availableActivityItemClasses.value.find((aic) => aic.name === 'domain')
})

const selectedUnitDimension = computed(() => {
  let result = null
  mandatoryActivityItemClasses.value.forEach((aic, index) => {
    if (aic?.name === 'unit_dimension') {
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

const showAdamParamCode = computed(() => {
  return step2Form.value.activity_instance_class?.name !== 'Events'
})

const showIsResearchLab = computed(() => {
  return step2Form.value.activity_instance_class?.name !== 'Events'
})

// Helper to determine if we should show existing mandatory items when editing an instance,
// even if data domain is not selected yet
const hasExistingMandatoryItems = computed(() => {
  if (!activityInstance.value) return false
  if (testValue.value) return true
  return step2Form.value.activityItems?.some(
    (item) =>
      item &&
      item.activity_item_class_uid &&
      (item.ct_terms?.length > 0 ||
        item.unit_definition_uids?.length > 0 ||
        item.ct_term_name ||
        item.ct_codelist_uid)
  )
})

// ----- Helper methods for managing editing of instance classes that are not (yet) supported by this form -----

// Include the currently selected class in the options even if it's not in the fetched list
const activityInstanceClassOptions = computed(() => {
  const selectedClass = step2Form.value.activity_instance_class
  if (!selectedClass?.uid) {
    return activityInstanceClasses.value
  }

  const hasSelectedClassInOptions = activityInstanceClasses.value.some(
    (item) => item.uid === selectedClass.uid
  )
  if (hasSelectedClassInOptions) {
    return activityInstanceClasses.value
  }

  return [...activityInstanceClasses.value, selectedClass]
})

// Determine if the currently selected class is unsupported (not in the fetched list)
const isSelectedActivityInstanceClassUnsupported = computed(() => {
  const selectedClass = step2Form.value.activity_instance_class
  if (!selectedClass?.uid) {
    return false
  }

  return !activityInstanceClasses.value.some(
    (item) => item.uid === selectedClass.uid
  )
})

// Generate warning messages if the selected class is unsupported,
// but only when editing an existing instance (not during creation)
const activityInstanceClassWarningMessages = computed(() => {
  const selectedClass = step2Form.value.activity_instance_class
  const isEditing = !!props.activityInstanceUid
  if (!isEditing || !isSelectedActivityInstanceClassUnsupported.value) {
    return []
  }

  return [
    t('ActivityInstanceForm.activity_instance_class_not_supported', {
      name: selectedClass.name,
    }),
  ]
})

// ----- End of helper methods for unsupported instance classes -----
watch(showMolecularWeight, (value) => {
  if (!value) {
    delete step2Form.value.molecular_weight
  }
})

watch(
  () => step3Form.value.name,
  (newName) => {
    if (allowManualEdit.value && newName != null) {
      step3Form.value.name_sentence_case = newName.toLowerCase()
    }
  }
)

watch(
  () => step3Form.value.is_research_lab,
  () => {
    // Refresh preview when is_research_lab changes, but only if toggle is off
    if (!allowManualEdit.value && !activityInstance.value) {
      sendPreviewRequestDebounced()
    }
  }
)

const categoryAic = computed(() => {
  const aicName = step2Form.value.activity_instance_class?.name
  return filteredActivityItemClasses.value.find(
    (item) =>
      item.name ===
      activityItemClassesConstants.categoryActivityItemClasses[aicName]
  )
})
const subcategoryAic = computed(() => {
  const aicName = step2Form.value.activity_instance_class?.name
  return filteredActivityItemClasses.value.find(
    (item) =>
      item.name ===
      activityItemClassesConstants.subcategoryActivityItemClasses[aicName]
  )
})

const categoryCodelistName = computed(() => {
  const aicName = step2Form.value.activity_instance_class?.name
  if (!aicName) return null
  if (aicName === 'Events') return 'eventCategoryDefinition'
  if (aicName === 'Interventions') return 'interventionCategoryDefinition'
  return 'findingCategoryDefinition'
})
const subcategoryCodelistName = computed(() => {
  const aicName = step2Form.value.activity_instance_class?.name
  if (!aicName) return null
  if (aicName === 'Events') return 'eventSubCategoryDefinition'
  if (aicName === 'Interventions') return 'interventionSubCategoryDefinition'
  return 'findingSubCategoryDefinition'
})

const activitiesHeaders = [
  { title: '', key: 'selection', sortable: false, noFilter: true },
  {
    title: t('ActivityInstanceForm.activity_group'),
    key: 'activity_groupings.0.activity_group_name',
    externalFilterSource: 'concepts/activities/activity-groups$name',
    exludeFromHeader: ['name', 'activity_groupings.0.activity_subgroup_name'],
  },
  {
    title: t('ActivityInstanceForm.activity_subgroup'),
    key: 'activity_groupings.0.activity_subgroup_name',
    externalFilterSource: 'concepts/activities/activity-sub-groups$name',
    exludeFromHeader: ['name', 'activity_groupings.0.activity_group_name'],
  },
  {
    title: t('ActivityInstanceForm.activity_name'),
    key: 'name',
    exludeFromHeader: [
      'activity_groupings.0.activity_subgroup_name',
      'activity_groupings.0.activity_group_name',
    ],
  },
  {
    title: t('ActivityInstanceForm.activity_instances'),
    key: 'activity_instances',
    filteringName: 'activity_instances.name',
    noFilter: true,
  },
]
const stepDefinitions = [
  { name: 'activities', titleKey: 'ActivityInstanceForm.step1_title' },
  { name: 'required', titleKey: 'ActivityInstanceForm.step2_title' },
  { name: 'optional', titleKey: 'ActivityInstanceForm.step3_title' },
  { name: 'dataspec', titleKey: 'ActivityInstanceForm.step4_title' },
  { name: 'groupings_change', titleKey: '_global.change_description' },
]
const allHelpItems = [
  'ActivityInstanceForm.general',
  'ActivityInstanceForm.step1_description',
  'ActivityInstanceForm.step2_description',
  'ActivityInstanceForm.step3_description',
  'ActivityInstanceForm.step4_description',
  'ActivityInstanceForm.groupings_change_description',
]

function getStepTitle(stepName) {
  const className = step2Form.value.activity_instance_class?.name
  if (stepName === 'optional') {
    if (className === 'Events') {
      return t('ActivityInstanceForm.step3_events_title')
    }
    if (className === 'Interventions') {
      return t('ActivityInstanceForm.step3_interventions_title')
    }
  }
  const def = stepDefinitions.find((s) => s.name === stepName)
  return def ? t(def.titleKey) : ''
}

const allSteps = computed(() =>
  stepDefinitions.map((def) => ({
    name: def.name,
    title: getStepTitle(def.name),
  }))
)

const steps = computed(() => {
  if (props.editMode === 'groupings') {
    return [allSteps.value[0], allSteps.value[4]] // Groupings selection + change description
  }
  if (props.editMode === 'attributes') {
    return allSteps.value.slice(1, 4) // Steps 2-4: required, optional, dataspec
  }
  return allSteps.value.slice(0, 4) // All steps for creation (excludes groupings_change)
})
const helpItems = computed(() => {
  if (props.editMode === 'groupings') {
    return [allHelpItems[0], allHelpItems[1], allHelpItems[5]]
  }
  if (props.editMode === 'attributes') {
    return [allHelpItems[0], ...allHelpItems.slice(2, 5)]
  }
  return allHelpItems.slice(0, 5)
})

function fetchActivities(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  if (options?.sortBy?.length) {
    if (
      [
        'activity_groupings.0.activity_group_name',
        'activity_groupings.0.activity_subgroup_name',
      ].includes(options.sortBy[0].key)
    ) {
      const parts = options.sortBy[0].key.split('.')
      const sortKey = `${parts[0]}[0].${parts[2]}`
      params.sort_by = `{"${sortKey}":${options.sortBy[0].order === 'asc'}}`
    }
  }
  if (params.filters) {
    params.filters = JSON.parse(params.filters)
  } else {
    params.filters = {}
  }
  params.filters.status = { v: [statuses.FINAL] }
  params.filters.library_name = { v: [libraryConstants.LIBRARY_SPONSOR] }
  params.filters.is_data_collected = { v: [true] }
  if (props.editMode === 'groupings' && activityInstance.value) {
    const activityUid =
      activityInstance.value.activity_groupings?.[0]?.activity?.uid
    if (activityUid) {
      params.filters.uid = { v: [activityUid] }
    }
  } else if (props.preselectedGroupings.length > 0) {
    const activityUid = props.preselectedGroupings[0].activity_uid
    if (activityUid) {
      params.filters.uid = { v: [activityUid] }
    }
  }
  if (params.filters['activity_groupings.0.activity_group_name']) {
    params.activity_group_names = []
    params.filters['activity_groupings.0.activity_group_name'].v.forEach(
      (value) => {
        params.activity_group_names.push(value)
      }
    )
    delete params.filters['activity_groupings.0.activity_group_name']
  }
  if (params.filters['activity_groupings.0.activity_subgroup_name']) {
    params.activity_subgroup_names = []
    params.filters['activity_groupings.0.activity_subgroup_name'].v.forEach(
      (value) => {
        params.activity_subgroup_names.push(value)
      }
    )
    delete params.filters['activity_groupings.0.activity_subgroup_name']
  }
  params.group_by_groupings = false
  activitiesApi.get(params, 'activities').then((resp) => {
    activities.value = resp.data.items
    totalActivities.value = resp.data.total
  })
}

async function fetchActivityItemClasses(activityInstanceClass) {
  if (activityInstanceClass) {
    // Call 1: Get ALL items without dataset filter (for mandatory/Step 2)
    const respAll = await activityInstanceClassesApi.getActivityItemClasses(
      activityInstanceClass.uid
    )
    availableActivityItemClasses.value = respAll.data

    // Call 2: Get filtered items with dataset filter (for optional/Step 3 & 4)
    if (step2Form.value.data_domain) {
      const respFiltered =
        await activityInstanceClassesApi.getActivityItemClasses(
          activityInstanceClass.uid,
          {
            dataset_uid: step2Form.value.data_domain,
            ig_uid: 'SDTMIG',
          }
        )
      filteredActivityItemClasses.value = respFiltered.data
    } else {
      // No dataset selected yet, use unfiltered for optional items too
      filteredActivityItemClasses.value = respAll.data
    }

    // Initialize mandatory activity items for Step 2
    step2Form.value.activityItems = []
    mandatoryActivityItemClasses.value.forEach((aic) => {
      if (!aic) return // Skip if undefined
      let activityItem
      if (activityInstance.value) {
        // Handle mandatory activity items here because we must
        // respect the order of activity items classes received from the
        // API
        const existingActivityItems = Array.isArray(
          activityInstance.value.activity_items
        )
          ? activityInstance.value.activity_items
          : []
        const matched = existingActivityItems.find(
          (item) => item?.activity_item_class?.uid === aic.uid
        )
        if (matched) {
          activityItem = {
            activity_item_class_uid: matched.activity_item_class?.uid,
            is_adam_param_specific: matched.is_adam_param_specific,
            unit_definition_uids: [],
            ct_terms: [],
          }
          if (
            matched.ct_codelist?.uid &&
            (!matched.ct_terms || !matched.ct_terms.length)
          ) {
            activityItem.ct_codelist_uid = matched.ct_codelist.uid
          } else if (matched.activity_item_class?.name === 'standard_unit') {
            activityItem.unit_definition_uids = (matched.unit_definitions || [])
              .map((unit) => unit?.uid)
              .filter(Boolean)
            activityItem.preselected_unit_name =
              matched.unit_definitions?.[0]?.name || null
          } else {
            activityItem.ct_terms = matched.ct_terms || []
            if (
              matched.activity_item_class?.name === 'unit_dimension' &&
              matched.ct_terms?.[0]?.name
            ) {
              activityItem.ct_term_name = matched.ct_terms[0].name
            }
          }
        } else {
          activityItem = { activity_item_class_uid: aic.uid }
        }
      } else {
        activityItem = { activity_item_class_uid: aic.uid }
      }
      step2Form.value.activityItems.push(activityItem)
    })
    await fetchDatasets(activityInstanceClass.uid)
  } else {
    step2Form.value.activityItems = []
    availableActivityItemClasses.value = []
    filteredActivityItemClasses.value = []
  }
}

async function fetchDatasets(activityInstanceClassUid) {
  const params = {
    ig_uid: 'SDTMIG',
  }
  if (activityInstanceClassUid) {
    params.activity_instance_class_uid = activityInstanceClassUid
  }
  const resp = await activityInstanceClassesApi.getModelMappingDatasets(params)
  datasets.value = resp.data
  await fetchDomainNames()
}

async function fetchDomainNames() {
  const codelistUid =
    activityItemClassesConstants.sdtmDomainAbbreviationCodelistUid
  const resp = await codelistsApi.getCodelistTerms(codelistUid, {
    page_size: 0,
  })
  const names = {}
  for (const term of resp.data.items) {
    names[term.submission_value] = term.sponsor_preferred_name
  }
  domainNames.value = names
}

function filterActivityInstanceClasses(dataDomainUid) {
  const params = {
    filters: {
      submission_value: { v: [dataDomainUid], op: 'eq' },
    },
  }
  codelistsApi
    .getCodelistTerms(
      activityItemClassesConstants.sdtmDomainAbbreviationCodelistUid,
      params
    )
    .then((resp) => {
      if (resp.data.items.length > 0) {
        dataDomainCTTermUid.value = resp.data.items[0].term_uid
      }
    })

  if (step2Form.value.activity_instance_class) {
    // Re-fetch activity item classes with the dataset filter
    fetchActivityItemClasses(step2Form.value.activity_instance_class)
    return
  }
  const uids = datasets.value
    .filter(
      (item) =>
        item.datasets.includes(dataDomainUid) &&
        allowedInstanceClasses.includes(item.name)
    )
    .map((item) => item.uid)
  const filters = {
    uid: { v: uids },
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
  const grouping = activity?.activity_groupings?.[0]
  return `${grouping?.activity_group_uid || ''}|${grouping?.activity_subgroup_uid || ''}|${activity?.uid || ''}`
}

function removeGroupingSelection(selectionUid) {
  selectedActivity.value = selectedActivity.value.filter(
    (uid) => uid !== selectionUid
  )
}

function addOptionalActivityItemClass() {
  step3Form.value.activityItems.push({})
}

function removeOptionalActivityItemClass(index) {
  step3Form.value.activityItems.splice(index, 1)
  if (!allowManualEdit.value) {
    sendPreviewRequest()
  }
}

function addDataSpecActivityItemClass() {
  step4Form.value.activityItems.push({})
}

function removeDataSpecActivityItemClass(index) {
  step4Form.value.activityItems.splice(index, 1)
}

function resetForms() {
  selectedActivity.value = []
  selectionDetailsCache.value.clear()
  hasExistingDataDomain.value = false
  groupingsChangeForm.value = {
    change_description: '',
  }
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
  return (item.activity_instances || [])
    .map((instance) => escapeHTML(instance.name))
    .join('<br/>')
}

function hasActivityItemValue(item) {
  if (!item) return false
  return (
    (item.ct_terms && item.ct_terms.length > 0) ||
    (item.unit_definition_uids && item.unit_definition_uids.length > 0) ||
    !!item.ct_codelist_uid
  )
}

function recordStep3EmptyItems() {
  step3EmptyItemIndices.value = new Set()
  step3Form.value.activityItems.forEach((item, index) => {
    if (!hasActivityItemValue(item)) {
      step3EmptyItemIndices.value.add(index)
    }
  })
}

function close() {
  emit('close')
  notificationHub.clearErrors()
}

function validateMolecularWeight(value) {
  // Allow empty values (field is optional)
  if (value === null || value === undefined || value === '') {
    return true
  }
  // Convert to string and validate
  const strValue = String(value).trim()
  if (strValue === '' || strValue === '.') {
    return t('ActivityInstanceForm.molecular_weight_hint')
  }
  // Check for invalid patterns
  if (
    strValue === 'NaN' ||
    strValue.toLowerCase() === 'nan' ||
    strValue === 'Infinity' ||
    strValue === '-Infinity'
  ) {
    return t('ActivityInstanceForm.molecular_weight_hint')
  }
  // Check if it's a valid number
  const numValue = Number(strValue)
  if (isNaN(numValue) || !isFinite(numValue)) {
    return t('ActivityInstanceForm.molecular_weight_hint')
  }
  // Check if it matches decimal pattern (allows decimals)
  if (!/^[0-9]*\.?[0-9]+$/.test(strValue)) {
    return t('ActivityInstanceForm.molecular_weight_hint')
  }
  return true
}

function getObserver(step) {
  const stepName = steps.value[step - 1]?.name
  const observersByName = {
    activities: step1FormRef,
    required: step2FormRef,
    optional: step3FormRef,
    dataspec: step4FormRef,
    groupings_change: groupingsChangeFormRef,
  }
  return observersByName[stepName]?.value
}

function extraStepValidation(step) {
  const stepName = steps.value[step - 1]?.name
  if (stepName === 'activities') {
    if (!selectedActivity.value.length) {
      notificationHub.add({
        msg: t('ActivityInstanceForm.activity_not_selected'),
        type: 'error',
      })
      return false
    }
    // Verify all selected rows reference the same activity
    const activityUids = selectedActivity.value.map(
      (val) => parseSelectedActivityUid(val).activityUid
    )
    const uniqueActivityUids = new Set(activityUids)
    if (uniqueActivityUids.size > 1) {
      notificationHub.add({
        msg: t('ActivityInstanceForm.activity_mixed_selection'),
        type: 'error',
      })
      return false
    }
  }
  if (
    stepName === 'required' &&
    isSelectedActivityInstanceClassUnsupported.value
  ) {
    return false
  }
  return true
}

async function prepareActivityItems() {
  const activityItems = [
    ...step2Form.value.activityItems.map((item) => ({
      ...item,
      is_activity_instance_id_specific: true,
    })),
    ...step3Form.value.activityItems.map((item) => ({
      ...item,
      is_activity_instance_id_specific: true,
    })),
    ...step4Form.value.activityItems.map((item) => ({
      ...item,
      is_activity_instance_id_specific: false,
    })),
  ].filter((item) => item && item.activity_item_class_uid)

  function addActivityItem(uid, codelistUid, term_uids) {
    const ct_terms = term_uids.map((term_uid) => {
      return { codelist_uid: codelistUid, term_uid }
    })
    activityItems.push({
      activity_item_class_uid: uid,
      ct_terms,
      odm_item_uids: [],
      unit_definition_uids: [],
      is_adam_param_specific: false,
      is_activity_instance_id_specific: true,
    })
  }

  if (testValue.value) {
    addActivityItem(testCodeAic.value.uid, testCodeCodelistValue.value, [
      testValue.value,
    ])
    addActivityItem(testNameAic.value.uid, testNameCodelistValue.value, [
      testValue.value,
    ])
  }

  const aicName = step2Form.value.activity_instance_class?.name
  const catSubmissionValue =
    activityItemClassesConstants.categoryCodelistSubmissionValues[aicName]
  const subcatSubmissionValue =
    activityItemClassesConstants.subcategoryCodelistSubmissionValues[aicName]

  if (step2Form.value.data_category && catSubmissionValue) {
    const resp = await codelistsApi.getAttributes({
      filters: { submission_value: { v: [catSubmissionValue] } },
    })
    if (resp.data.items.length) {
      const codelistUid = resp.data.items[0].codelist_uid
      addActivityItem(categoryAic.value.uid, codelistUid, [
        step2Form.value.data_category,
      ])
    }
  }

  if (step2Form.value.data_subcategory && subcatSubmissionValue) {
    const resp = await codelistsApi.getAttributes({
      filters: { submission_value: { v: [subcatSubmissionValue] } },
    })
    if (resp.data.items.length) {
      const codelistUid = resp.data.items[0].codelist_uid
      addActivityItem(subcategoryAic.value.uid, codelistUid, [
        step2Form.value.data_subcategory,
      ])
    }
  }
  if (domainAic.value && dataDomainCTTermUid.value) {
    addActivityItem(
      domainAic.value.uid,
      activityItemClassesConstants.sdtmDomainAbbreviationCodelistUid,
      [dataDomainCTTermUid.value]
    )
  }

  if (defaultLinkedActivityItemClasses.value.length) {
    for (const aic of defaultLinkedActivityItemClasses.value) {
      addActivityItem(aic.uid, null, [])
    }
  }

  // Thanks to API inconsistency, we have to do this...
  for (const activityItem of activityItems) {
    // API requires either ct_terms OR ct_codelist_uid, not both
    if (activityItem.ct_codelist_uid) {
      activityItem.ct_terms = []
      continue
    }
    if (!activityItem.ct_terms) {
      continue
    }
    for (const term of activityItem.ct_terms) {
      if (!term.term_uid) {
        term.term_uid = term.uid
      }
    }
  }

  return activityItems
}

async function prepareCreationPayload(forPreview) {
  const activityGroupings = selectedActivity.value.map((selection) => {
    const [activityGroupUid, activitySubgroupUid, activityUid] =
      selection.split('|')
    return {
      activity_group_uid: activityGroupUid,
      activity_subgroup_uid: activitySubgroupUid,
      activity_uid: activityUid,
    }
  })
  const activityItems = await prepareActivityItems()
  const result = {
    library_name: libraryConstants.LIBRARY_SPONSOR,
    nci_concept_name: step3Form.value.nci_concept_name,
    nci_concept_id: step3Form.value.nci_concept_id,
    activity_instance_class_uid: step2Form.value.activity_instance_class.uid,
    activity_items: activityItems,
    is_required_for_activity: step4Form.value.is_required_for_activity,
    is_default_selected_for_activity:
      step4Form.value.is_default_selected_for_activity,
    is_data_sharing: step4Form.value.is_data_sharing,
    is_research_lab: step3Form.value.is_research_lab,
    activity_groupings: activityGroupings,
    strict_mode: true,
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

async function prepareUpdatePayload() {
  const result = {
    library_name: libraryConstants.LIBRARY_SPONSOR,
    nci_concept_name: step3Form.value.nci_concept_name,
    nci_concept_id: step3Form.value.nci_concept_id,
    activity_instance_class_uid: step2Form.value.activity_instance_class.uid,
    is_required_for_activity: step4Form.value.is_required_for_activity,
    is_default_selected_for_activity:
      step4Form.value.is_default_selected_for_activity,
    is_data_sharing: step4Form.value.is_data_sharing,
    is_research_lab: step3Form.value.is_research_lab,
    activity_items: await prepareActivityItems(),
    name: step3Form.value.name,
    name_sentence_case: step3Form.value.name_sentence_case,
    adam_param_code: step3Form.value.adam_param_code,
    topic_code: step3Form.value.topic_code,
    change_description: step4Form.value.change_description || 'Update',
  }
  if (step2Form.value.molecular_weight) {
    result.molecular_weight = step2Form.value.molecular_weight
  }
  return result
}

function prepareGroupingsPayload() {
  const activityGroupings = selectedActivity.value.map((selection) => {
    const [activityGroupUid, activitySubgroupUid, activityUid] =
      selection.split('|')
    return {
      activity_group_uid: activityGroupUid,
      activity_subgroup_uid: activitySubgroupUid,
      activity_uid: activityUid,
    }
  })
  return {
    activity_groupings: activityGroupings,
    change_description:
      groupingsChangeForm.value.change_description || 'Update',
  }
}

async function sendPreviewRequest() {
  loadingPreview.value = true
  const payload = await prepareCreationPayload(true)
  const resp = await activitiesApi.getPreview(payload, 'activity-instances')
  step3Form.value.name = resp.data.name
  step3Form.value.name_sentence_case = resp.data.name_sentence_case
  if (!props.activityInstanceUid) {
    step3Form.value.topic_code = resp.data.topic_code
  }
  step3Form.value.adam_param_code = resp.data.adam_param_code
  loadingPreview.value = false
}

const sendPreviewRequestDebounced = _debounce(sendPreviewRequest, 300)

function onAllowManualEditChange(value) {
  if (!value) {
    sendPreviewRequest()
  }
}

async function updateAIFields(value) {
  if (
    value.ct_terms.length ||
    value.unit_definition_uids.length ||
    value.ct_codelist_uid
  ) {
    await sendPreviewRequestDebounced()
  }
}

async function initStep(step) {
  const stepName = steps.value[step - 1]?.name
  if (stepName === 'optional') {
    // Check if required fields have been selected (param/paramcd)
    const hasRequiredFields =
      // Check test value (test_code/test_name)
      testValue.value ||
      // Check activity items with ct_terms, ct_term_uids, or unit_definition_uids
      step2Form.value.activityItems?.some(
        (item) =>
          item &&
          (item.ct_terms?.length > 0 ||
            item.ct_term_uids?.length > 0 ||
            item.unit_definition_uids?.length > 0 ||
            !!item.ct_codelist_uid)
      )

    // Refresh preview if:
    // 1. Toggle is off (allowManualEdit is false)
    // 2. Required fields have been selected
    // 3. if Wizard stepper for creating an instance Form (activityInstance.value is null)
    if (
      !allowManualEdit.value &&
      hasRequiredFields &&
      !activityInstance.value
    ) {
      await sendPreviewRequest()
    } else if (!step3Form.value.name && !activityInstance.value) {
      // Fallback to original behavior if no required fields selected yet
      await sendPreviewRequest()
    }
  }
}

async function submit() {
  notificationHub.clearErrors()

  try {
    let resp
    if (props.editMode === 'groupings') {
      const payload = prepareGroupingsPayload()
      resp = await activitiesApi.update(
        props.activityInstanceUid,
        payload,
        {},
        'activity-instances',
        'groupings'
      )
      notificationHub.add({
        msg: t('ActivityInstanceForm.update_groupings_success'),
      })
      close()
      return
    } else if (props.editMode === 'attributes') {
      const payload = await prepareUpdatePayload()
      resp = await activitiesApi.update(
        props.activityInstanceUid,
        payload,
        {},
        'activity-instances',
        'attributes'
      )
      notificationHub.add({
        msg: t('ActivityInstanceForm.update_attributes_success'),
      })
    } else if (props.activityInstanceUid) {
      const payload = await prepareUpdatePayload()
      resp = await activitiesApi.update(
        props.activityInstanceUid,
        payload,
        {},
        'activity-instances'
      )
      notificationHub.add({
        msg: t('ActivityInstanceForm.update_success'),
      })
    } else {
      const payload = await prepareCreationPayload()
      resp = await activitiesApi.create(payload, 'activity-instances')
      notificationHub.add({
        msg: t('ActivityInstanceForm.add_success'),
      })
    }
    if (route.name !== 'ActivityInstanceOverview') {
      router.push({
        name: 'ActivityInstanceOverview',
        params: { id: resp.data.uid },
      })
    } else {
      window.location.reload()
    }
  } finally {
    stepper.value.loading = false
  }
}

async function initiateDomainFromActivityItem(activityItem) {
  const firstTermUid = activityItem?.ct_terms?.[0]?.uid
  if (!firstTermUid) {
    return
  }
  const resp = await ctApi.getTermCodelists(firstTermUid)
  for (const codelist of resp.data.codelists) {
    if (
      codelist.codelist_uid ===
      activityItemClassesConstants.sdtmDomainAbbreviationCodelistUid
    ) {
      step2Form.value.data_domain = codelist.submission_value
    }
  }
  dataDomainCTTermUid.value = firstTermUid
}

async function initFromActivityInstance() {
  let resp = await activitiesApi.getObject(
    'activity-instances',
    props.activityInstanceUid
  )
  activityInstance.value = resp.data
  const existingGroupings = activityInstance.value?.activity_groupings || []
  selectedActivity.value = existingGroupings
    .filter((g) => g?.activity_group?.uid && g?.activity_subgroup?.uid)
    .map(
      (g) =>
        `${g.activity_group.uid}|${g.activity_subgroup.uid}|${g.activity?.uid || ''}`
    )

  const activityInstanceClassUid =
    activityInstance.value?.activity_instance_class?.uid
  const supportedActivityInstanceClass = activityInstanceClasses.value.find(
    (item) => item.uid === activityInstanceClassUid
  )
  step2Form.value.activity_instance_class =
    supportedActivityInstanceClass ||
    activityInstance.value?.activity_instance_class
  if (supportedActivityInstanceClass) {
    await fetchActivityItemClasses(supportedActivityInstanceClass)
  }

  if (
    activityInstance.value?.molecular_weight !== undefined &&
    activityInstance.value?.molecular_weight !== null
  ) {
    step2Form.value.molecular_weight = activityInstance.value.molecular_weight
  }

  step3Form.value.name = activityInstance.value?.name || ''
  step3Form.value.name_sentence_case =
    activityInstance.value?.name_sentence_case || ''
  step3Form.value.nci_concept_name = activityInstance.value?.nci_concept_name
  step3Form.value.topic_code = activityInstance.value?.topic_code || ''
  step3Form.value.adam_param_code =
    activityInstance.value?.adam_param_code || ''
  step3Form.value.nci_concept_id = activityInstance.value?.nci_concept_id
  step3Form.value.is_research_lab = activityInstance.value?.is_research_lab

  step4Form.value.is_required_for_activity =
    activityInstance.value?.is_required_for_activity
  step4Form.value.is_data_sharing = activityInstance.value?.is_data_sharing
  step4Form.value.is_default_selected_for_activity =
    activityInstance.value?.is_default_selected_for_activity

  const existingActivityItems = Array.isArray(
    activityInstance.value?.activity_items
  )
    ? activityInstance.value.activity_items
    : []
  hasExistingDataDomain.value = existingActivityItems.some(
    (item) =>
      item?.activity_item_class?.name === 'domain' && !!item?.ct_terms?.[0]?.uid
  )

  for (const activityItem of existingActivityItems) {
    const itemClass = activityItem?.activity_item_class
    const itemClassName = itemClass?.name
    const firstCtTermUid = activityItem?.ct_terms?.[0]?.uid

    // Skip items without a class name — cannot be placed
    if (!itemClassName) {
      continue
    }

    // Step 2 — domain: populates the data_domain dropdown, not a form field
    if (itemClassName === 'domain') {
      await initiateDomainFromActivityItem(activityItem)
      // Re-fetch filtered activity item classes now that domain is known
      // (fetchActivityItemClasses ran before domain was extracted, so
      // filteredActivityItemClasses contains the unfiltered superset)
      if (step2Form.value.data_domain && supportedActivityInstanceClass) {
        const respFiltered =
          await activityInstanceClassesApi.getActivityItemClasses(
            supportedActivityInstanceClass.uid,
            {
              dataset_uid: step2Form.value.data_domain,
              ig_uid: 'SDTMIG',
            }
          )
        filteredActivityItemClasses.value = respFiltered.data
      }
      continue
    }
    // Step 2 — category: mapped to the data_category dropdown
    if (itemClassName === categoryAic.value?.name && firstCtTermUid) {
      step2Form.value.data_category = firstCtTermUid
      continue
    }
    // Step 2 — subcategory: mapped to the data_subcategory dropdown
    if (itemClassName === subcategoryAic.value?.name && firstCtTermUid) {
      step2Form.value.data_subcategory = firstCtTermUid
      continue
    }
    // Step 2 — test code: stored separately, paired with test name
    if (testCodeAic.value && itemClass?.uid === testCodeAic.value.uid) {
      testCodeCodelistValue.value =
        activityItem?.ct_terms?.[0]?.codelist_uid || null
      continue
    }
    // Step 2 — test name: stored separately, paired with test code
    if (
      testNameAic.value &&
      itemClass?.uid === testNameAic.value.uid &&
      firstCtTermUid
    ) {
      testValue.value = firstCtTermUid
      testNameCodelistValue.value =
        activityItem?.ct_terms?.[0]?.codelist_uid || null
      continue
    }

    // Skip default-linked items — they are displayed as read-only cards in step 4
    if (
      defaultLinkedActivityItemClasses.value.some(
        (aic) => aic.uid === itemClass?.uid
      )
    ) {
      continue
    }

    const classMeta =
      filteredActivityItemClasses.value.find(
        (aic) => aic.uid === itemClass?.uid
      ) ||
      availableActivityItemClasses.value.find(
        (aic) => aic.uid === itemClass?.uid
      )

    // Step 2 — mandatory items: already populated by fetchActivityItemClasses, skip duplicates
    const alreadyInStep2 = step2Form.value.activityItems.some(
      (item) => item.activity_item_class_uid === itemClass?.uid
    )
    if (alreadyInStep2) {
      continue
    }

    // When is_activity_instance_id_specific is explicitly set, use it directly:
    // true  → step 3 (instance identity items: single term/unit per item)
    // false → step 4 (data specification items: may link to codelists or multiple values)
    if (activityItem.is_activity_instance_id_specific === true) {
      const step3Item = {
        activity_item_class_uid: itemClass?.uid,
        is_adam_param_specific: !!classMeta?.is_adam_param_specific_enabled,
        unit_definition_uids: [],
        ct_terms: activityItem.ct_terms || [],
      }
      if (
        activityItem.ct_codelist?.uid &&
        (!activityItem.ct_terms || !activityItem.ct_terms.length)
      ) {
        step3Item.ct_codelist_uid = activityItem.ct_codelist.uid
      }
      step3Form.value.activityItems.push(step3Item)
      continue
    }
    if (activityItem.is_activity_instance_id_specific === false) {
      const step4Item = {
        activity_item_class_uid: itemClass?.uid,
        is_adam_param_specific: !!classMeta?.is_adam_param_specific_enabled,
        unit_definition_uids: [],
        ct_terms: activityItem.ct_terms || [],
      }
      if (
        activityItem.ct_codelist?.uid &&
        (!activityItem.ct_terms || !activityItem.ct_terms.length)
      ) {
        step4Item.ct_codelist_uid = activityItem.ct_codelist.uid
      }
      step4Form.value.activityItems.push(step4Item)
      continue
    }

    // Fallback heuristic when is_activity_instance_id_specific is null/undefined
    // (legacy data that predates the flag).
    // Try step 3 first: the item class must be in optionalActivityItemClasses
    // (adam-param-specific, non-mandatory, non-exception).
    let matched = optionalActivityItemClasses.value.find(
      (aic) => aic.uid === itemClass?.uid
    )
    if (matched) {
      // Step 3 items are part of instance identity and can only link to a
      // single CT term or unit. If the item has multiple terms/units or a
      // codelist reference, it belongs in step 4 instead.
      const hasMultipleTermsOrUnits =
        (activityItem.ct_terms?.length || 0) > 1 ||
        (activityItem.unit_definitions?.length || 0) > 1
      const hasCodelist =
        !!activityItem.ct_codelist?.uid &&
        (!activityItem.ct_terms || !activityItem.ct_terms.length)

      if (!hasMultipleTermsOrUnits && !hasCodelist) {
        const step3Item = {
          activity_item_class_uid: matched.uid,
          is_adam_param_specific: matched.is_adam_param_specific_enabled,
          unit_definition_uids: [],
          ct_terms: activityItem.ct_terms || [],
        }
        step3Form.value.activityItems.push(step3Item)
        continue
      }
      // Falls through to step 4 assignment below
    }

    // Step 4 catch-all: any item not claimed by previous steps goes here.
    // This ensures no activity items are lost during edit mode.
    const alreadySelectedInStep4 = step4Form.value.activityItems.some(
      (item) => item.activity_item_class_uid === itemClass?.uid
    )

    if (!alreadySelectedInStep4) {
      const step4Item = {
        activity_item_class_uid: itemClass?.uid,
        is_adam_param_specific: !!classMeta?.is_adam_param_specific_enabled,
        unit_definition_uids: [],
        ct_terms: activityItem.ct_terms || [],
      }
      if (
        activityItem.ct_codelist?.uid &&
        (!activityItem.ct_terms || !activityItem.ct_terms.length)
      ) {
        step4Item.ct_codelist_uid = activityItem.ct_codelist.uid
      }
      step4Form.value.activityItems.push(step4Item)
    }
  }

  recordStep3EmptyItems()
}

resetForms()

const resp = await activityInstanceClassesApi.getAll({
  filters: {
    name: { v: allowedInstanceClasses },
    level: { v: [3] },
  },
  page_size: 0,
})
activityInstanceClasses.value = resp.data.items
await fetchDatasets()

if (props.activityInstanceUid) {
  await initFromActivityInstance()
} else if (props.preselectedGroupings.length > 0) {
  for (const g of props.preselectedGroupings) {
    const compositeUid = `${g.activity_group_uid}|${g.activity_subgroup_uid}|${g.activity_uid}`
    selectedActivity.value.push(compositeUid)
    selectionDetailsCache.value.set(compositeUid, {
      activityName: g.activity_name || '',
      activityGroupName: g.activity_group_name || '',
      activitySubgroupName: g.activity_subgroup_name || '',
    })
  }
}
</script>
