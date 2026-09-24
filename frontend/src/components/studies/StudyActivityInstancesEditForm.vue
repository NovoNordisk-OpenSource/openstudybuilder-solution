<template>
  <SimpleFormDialog
    ref="form"
    width="95vw"
    max-width="1900px"
    :title="$t('StudyActivityInstances.edit_add_instance')"
    :open="open"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-card elevation="0">
        <v-card-title>
          {{ $t('StudyActivityInstances.activity_selected') }}
        </v-card-title>
        <v-text-field :model-value="getActivityPath" readonly disabled />
        <v-alert
          v-if="selected.length > 1"
          density="compact"
          type="info"
          rounded="lg"
          class="text-white mb-2 ml-1 mr-1"
          :text="$t('StudyActivityInstances.multiple_select_info')"
        />
        <v-data-table
          v-model="selected"
          :headers="headers"
          :items="instances"
          item-value="uid"
          show-select
          @filter="getAvailableInstances()"
        >
          <template #[`item.details`]="{ item }">
            <div v-html="sanitizeHTML(item.details)" />
          </template>
          <template #[`item.state`]="{ item }">
            <div class="px-1">
              {{ getActivityState(item) }}
            </div>
          </template>
          <template #[`item.important`]="{ item }">
            <v-checkbox v-model="importantMap[item.uid]" hide-details>
              <template v-if="importantMap[item.uid]" #label>
                {{ $t('_global.yes') }}
              </template>
            </v-checkbox>
          </template>
          <template #[`item.baseline_visits`]="{ item }">
            <v-select
              v-model="baselineVisitMap[item.uid]"
              :items="availableBaselineVisits"
              :loading="loadingBaselineVisits"
              item-value="uid"
              item-title="visit_name"
              multiple
              class="compact-select"
            />
          </template>
          <template #[`item.data_supplier`]="{ item }">
            <v-select
              v-model="dataSupplierMap[item.uid]"
              :items="studyDataSuppliers"
              item-value="study_data_supplier_uid"
              item-title="name"
              clearable
              class="compact-select"
              :menu-props="{ width: '280px' }"
              @update:model-value="onSupplierChange(item.uid, $event)"
            />
          </template>
          <template #[`item.origin_type`]="{ item }">
            <v-select
              v-model="originTypeMap[item.uid]"
              :items="originTypes"
              item-value="term_uid"
              item-title="sponsor_preferred_name"
              clearable
              class="compact-select"
              :menu-props="{ width: '280px' }"
            />
          </template>
          <template #[`item.origin_source`]="{ item }">
            <v-select
              v-model="originSourceMap[item.uid]"
              :items="originSources"
              item-value="term_uid"
              item-title="sponsor_preferred_name"
              clearable
              class="compact-select"
              :menu-props="{ width: '280px' }"
            />
          </template>
        </v-data-table>
      </v-card>
    </template>
    <template #actions>
      <v-btn
        :disabled="
          selected.length === 0 ||
          editedActivity.state === instancesActions.REMOVE
        "
        variant="outlined"
        rounded
        class="mr-2"
        elevation="0"
        color="success"
        @click="setMultipleActivityInstances(true)"
      >
        {{ $t('StudyActivityInstances.save_reviewed') }}
      </v-btn>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudyActivitiesStore } from '@/stores/studies-activities'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import statuses from '@/constants/statuses'
import activities from '@/api/activities'
import _isEmpty from 'lodash/isEmpty'
import study from '@/api/study'
import terms from '@/api/controlledTerminology/terms'
import dataSuppliers from '@/api/dataSuppliers'
import { escapeHTML, sanitizeHTML } from '@/utils/sanitize'
import instancesActions from '@/constants/instancesActions'

const notificationHub = inject('notificationHub')
const { t } = useI18n()
const props = defineProps({
  open: Boolean,
  editedActivity: {
    type: Object,
    default: null,
  },
})
const emit = defineEmits(['close'])
const studiesGeneralStore = useStudiesGeneralStore()
const activitiesStore = useStudyActivitiesStore()

const selectedStudy = computed(() => studiesGeneralStore.selectedStudy)

const headers = [
  { title: t('StudyActivityInstances.instance'), key: 'name', width: '150px' },
  {
    title: t('StudyActivityInstances.details'),
    key: 'details',
    width: '200px',
  },
  {
    title: t('StudyActivityInstances.library_status'),
    key: 'state',
    width: '100px',
  },
  {
    title: t('StudyActivityInstances.important'),
    key: 'important',
    width: '90px',
  },
  {
    title: t('StudyActivityInstances.baseline_flags'),
    key: 'baseline_visits',
    width: '200px',
  },
  {
    title: t('StudyActivityInstances.data_supplier'),
    key: 'data_supplier',
    width: '220px',
  },
  {
    title: t('StudyActivityInstances.origin_type'),
    key: 'origin_type',
    width: '200px',
  },
  {
    title: t('StudyActivityInstances.origin_source'),
    key: 'origin_source',
    width: '200px',
  },
]

const availableBaselineVisits = ref([])
const instances = ref([])
const selected = ref([])
const selectedHolder = ref([])
const importantMap = ref({})
const baselineVisitMap = ref({})
const dataSupplierMap = ref({})
const originTypeMap = ref({})
const originSourceMap = ref({})
const importantMapHolder = ref({})
const baselineVisitMapHolder = ref({})
const dataSupplierMapHolder = ref({})
const originTypeMapHolder = ref({})
const originSourceMapHolder = ref({})
const form = ref()
const loadingBaselineVisits = ref(false)
const studyDataSuppliers = ref([])
const libraryDataSuppliers = ref([])
const originTypes = ref([])
const originSources = ref([])

const getActivityPath = computed(() => {
  if (!_isEmpty(props.editedActivity)) {
    return `${props.editedActivity.study_activity_group.activity_group_name}/${props.editedActivity.study_activity_subgroup.activity_subgroup_name}/${props.editedActivity.activity.name}`
  }
  return ''
})

watch(
  () => props.editedActivity,
  () => {
    getAvailableInstances()
  }
)

onMounted(() => {
  getAvailableInstances()
  loadDropdownData()
})

async function loadDropdownData() {
  // Load study data suppliers
  study
    .getStudyDataSuppliers(selectedStudy.value.uid, { page_size: 0 })
    .then((resp) => {
      studyDataSuppliers.value = resp.data.items || []
    })

  // Load library data suppliers (for default origin values)
  dataSuppliers.get({ params: { page_size: 1000 } }).then((resp) => {
    libraryDataSuppliers.value = resp.data.items || []
  })

  // Load origin type CT terms
  terms.getTermsByCodelist('originType').then((resp) => {
    originTypes.value = resp.data.items || []
  })

  // Load origin source CT terms
  terms.getTermsByCodelist('originSource').then((resp) => {
    originSources.value = resp.data.items || []
  })
}

function onSupplierChange(instanceUid, supplierUid) {
  if (supplierUid) {
    // Find the selected Study Data Supplier
    const selectedStudySupplier = studyDataSuppliers.value.find(
      (s) => s.study_data_supplier_uid === supplierUid
    )

    if (selectedStudySupplier) {
      // Find the linked Library Data Supplier to get defaults
      const librarySupplier = libraryDataSuppliers.value.find(
        (s) => s.uid === selectedStudySupplier.data_supplier_uid
      )

      if (librarySupplier) {
        // Auto-populate origin type from library supplier defaults
        const originTypeUid =
          librarySupplier.origin_type?.term_uid ||
          librarySupplier.origin_type?.uid
        if (originTypeUid) {
          originTypeMap.value[instanceUid] = originTypeUid
        }

        // Auto-populate origin source from library supplier defaults
        const originSourceUid =
          librarySupplier.origin_source?.term_uid ||
          librarySupplier.origin_source?.uid
        if (originSourceUid) {
          originSourceMap.value[instanceUid] = originSourceUid
        }
      }
    }
  }
}

async function getAvailableInstances() {
  if (!_isEmpty(props.editedActivity)) {
    const params = {
      activity_names: [props.editedActivity.activity.name],
      activity_subgroup_names: [
        props.editedActivity.study_activity_subgroup.activity_subgroup_name,
      ],
      activity_group_names: [
        props.editedActivity.study_activity_group.activity_group_name,
      ],
      filters: {
        status: { v: [statuses.FINAL] },
      },
      page_size: 0,
    }
    await activities.get(params, 'activity-instances').then((resp) => {
      instances.value = transformInstances(resp.data.items)
      // Initialize maps
      importantMap.value = {}
      dataSupplierMap.value = {}
      originTypeMap.value = {}
      originSourceMap.value = {}
      instances.value.forEach((instance) => {
        importantMap.value[instance.uid] = false
        dataSupplierMap.value[instance.uid] = null
        originTypeMap.value[instance.uid] = null
        originSourceMap.value[instance.uid] = null
      })
      // If editing existing activity instance, set its values
      if (props.editedActivity.activity_instance) {
        const selectedInstance = instances.value.find(
          (instance) =>
            instance.uid === props.editedActivity.activity_instance.uid
        )
        if (selectedInstance) {
          selected.value.push(selectedInstance.uid)
          importantMap.value[selectedInstance.uid] =
            props.editedActivity.is_important || false
          if (props.editedActivity.baseline_visits?.length) {
            baselineVisitMap.value[selectedInstance.uid] =
              props.editedActivity.baseline_visits.map((item) => item.uid)
          }
          // Set data supplier and origin values
          dataSupplierMap.value[selectedInstance.uid] =
            props.editedActivity.study_data_supplier_uid || null
          originTypeMap.value[selectedInstance.uid] =
            props.editedActivity.origin_type?.term_uid || null
          originSourceMap.value[selectedInstance.uid] =
            props.editedActivity.origin_source?.term_uid || null
        }
      }
    })
    selectedHolder.value = JSON.parse(JSON.stringify(selected.value))
    importantMapHolder.value = JSON.parse(JSON.stringify(importantMap.value))
    baselineVisitMapHolder.value = JSON.parse(
      JSON.stringify(baselineVisitMap.value)
    )
    dataSupplierMapHolder.value = JSON.parse(
      JSON.stringify(dataSupplierMap.value)
    )
    originTypeMapHolder.value = JSON.parse(JSON.stringify(originTypeMap.value))
    originSourceMapHolder.value = JSON.parse(
      JSON.stringify(originSourceMap.value)
    )
    if (instances.value.length > 1) {
      const par = {
        filters: {
          'activity.uid': { v: [props.editedActivity.activity.uid], op: 'co' },
        },
        page_size: -1,
      }
      study
        .getStudyActivityInstances(selectedStudy.value.uid, par)
        .then((resp) => {
          const uidsToRemove = resp.data.items
            .map((el) => el.activity_instance.uid)
            .filter((el) => el !== selected.value[0])
          instances.value = instances.value.filter(
            (instance) => uidsToRemove.indexOf(instance.uid) === -1
          )
        })
    }
    loadingBaselineVisits.value = true
    try {
      const resp = await study.getBaselineVisitsForStudyActivityInstance(
        props.editedActivity.study_uid,
        props.editedActivity.study_activity_instance_uid
      )
      availableBaselineVisits.value = resp.data
    } finally {
      loadingBaselineVisits.value = false
    }
  }
}
function transformInstances(instances) {
  return instances.map((instance) => {
    const lines = [
      `Class: ${escapeHTML(instance.activity_instance_class.name)}`,
      `Topic code: ${escapeHTML(instance.topic_code)}`,
      `ADaM param: ${escapeHTML(instance.adam_param_code)}`,
    ]

    for (const item of instance.activity_items) {
      const label = escapeHTML(item.activity_item_class.name)
      const values =
        item.ct_terms.length > 0
          ? item.ct_terms.map((term) => escapeHTML(term.name))
          : item.unit_definitions.map((unit) => escapeHTML(unit.name))

      lines.push(`${label}: ${values.join(', ')}`)
    }

    instance.details = lines.join('<br> ')
    return instance
  })
}
function getActivityState(activity) {
  if (activity.is_required_for_activity) {
    return t('StudyActivityInstances.required')
  } else if (activity.is_default_selected_for_activity) {
    return t('StudyActivityInstances.defaulted')
  }
}
function submit() {
  try {
    setMultipleActivityInstances()
  } catch (error) {
    console.error(error)
  }
}
function setMultipleActivityInstances(is_reviewed = false) {
  notificationHub.clearErrors()
  const data = []

  if (_isEmpty(selected.value) && !_isEmpty(selectedHolder.value)) {
    // No selection anymore
    data.push({
      method: 'PATCH',
      content: {
        is_reviewed: false,
        activity_instance_uid: null,
        study_activity_uid: props.editedActivity.study_activity_uid,
        study_activity_instance_uid:
          props.editedActivity.study_activity_instance_uid,
        is_important: false,
        baseline_visit_uids: [],
        study_data_supplier_uid: null,
        origin_type_uid: null,
        origin_source_uid: null,
      },
    })
  } else if (selected.value.includes(selectedHolder.value[0])) {
    // Update existing selection
    data.push({
      method: 'PATCH',
      content: {
        is_reviewed: is_reviewed || props.editedActivity.is_reviewed,
        activity_instance_uid: selectedHolder.value[0],
        study_activity_uid: props.editedActivity.study_activity_uid,
        study_activity_instance_uid:
          props.editedActivity.study_activity_instance_uid,
        is_important: importantMap.value[selectedHolder.value[0]] || false,
        baseline_visit_uids:
          baselineVisitMap.value[selectedHolder.value[0]] || [],
        study_data_supplier_uid:
          dataSupplierMap.value[selectedHolder.value[0]] || null,
        origin_type_uid: originTypeMap.value[selectedHolder.value[0]] || null,
        origin_source_uid:
          originSourceMap.value[selectedHolder.value[0]] || null,
      },
    })
    selected.value.splice(selected.value.indexOf(selectedHolder.value[0]), 1)
    // create new one(s) if needed
    selected.value.forEach((value) => {
      data.push({
        method: 'POST',
        content: {
          is_reviewed: is_reviewed,
          activity_instance_uid: value,
          study_activity_uid: props.editedActivity.study_activity_uid,
          is_important: importantMap.value[value] || false,
          baseline_visit_uids: baselineVisitMap.value[value] || [],
          study_data_supplier_uid: dataSupplierMap.value[value] || null,
          origin_type_uid: originTypeMap.value[value] || null,
          origin_source_uid: originSourceMap.value[value] || null,
        },
      })
    })
  } else {
    // Original selection was replaced
    for (let index = 0; index < selected.value.length; index++) {
      let placeholder = {
        method: index === 0 ? 'PATCH' : 'POST',
        content: {
          is_reviewed: is_reviewed,
          activity_instance_uid: selected.value[index],
          study_activity_uid: props.editedActivity.study_activity_uid,
          is_important: importantMap.value[selected.value[index]] || false,
          baseline_visit_uids:
            baselineVisitMap.value[selected.value[index]] || [],
          study_data_supplier_uid:
            dataSupplierMap.value[selected.value[index]] || null,
          origin_type_uid: originTypeMap.value[selected.value[index]] || null,
          origin_source_uid:
            originSourceMap.value[selected.value[index]] || null,
        },
      }
      if (index === 0) {
        placeholder.content.study_activity_instance_uid =
          props.editedActivity.study_activity_instance_uid
      }
      data.push(placeholder)
    }
  }
  if (_isEmpty(data)) {
    form.value.working = false
    close()
    return
  }
  activitiesStore
    .batchSelectStudyActivityInstances(selectedStudy.value.uid, data)
    .then(
      (resp) => {
        const errors = []
        for (const subResp of resp.data) {
          if (subResp.response_code >= 400) {
            errors.push(subResp.content.message)
            notificationHub.add({
              msg: subResp.content.message,
              type: 'error',
              timeout: 0,
            })
          }
        }
        if (!errors.length) {
          notificationHub.add({
            msg: t('StudyActivityInstances.instance_created'),
            type: 'success',
          })
        }
        close()
      },
      () => {
        form.value.working = false
      }
    )
}
function close() {
  notificationHub.clearErrors()
  instances.value = []
  selected.value = []
  importantMap.value = {}
  importantMapHolder.value = {}
  baselineVisitMap.value = {}
  baselineVisitMapHolder.value = {}
  dataSupplierMap.value = {}
  dataSupplierMapHolder.value = {}
  originTypeMap.value = {}
  originTypeMapHolder.value = {}
  originSourceMap.value = {}
  originSourceMapHolder.value = {}
  availableBaselineVisits.value = []
  emit('close')
}
</script>

<style scoped>
.compact-select :deep(.v-field__input) {
  white-space: normal;
  min-height: 40px;
  height: auto;
}
.compact-select :deep(.v-select__selection-text) {
  white-space: normal;
  overflow: visible;
  text-overflow: unset;
}
</style>
