<template>
  <v-card elevation="0" rounded="xl">
    <v-card-title class="d-flex justify-end">
      <v-skeleton-loader :loading="formLoading" type="text" width="150">
        <v-switch
          v-model="useFormView"
          data-cy="switch-view"
          :label="
            useFormView
              ? t('CRFActivityInstanceManagement.form_view')
              : t('CRFActivityInstanceManagement.table_view')
          "
          base-color="primary"
          hide-details
          class="ml-4"
        />
      </v-skeleton-loader>
    </v-card-title>

    <v-card-text>
      <div v-if="!useFormView">
        <v-autocomplete
          v-model="activityInstance"
          data-cy="select-activity-instance"
          item-title="name"
          item-value="uid"
          :label="t('CRFActivityInstanceManagement.select_activity_instance')"
          :items="availableActivityInstances"
          :loading="formLoading"
          clearable
        />

        <v-data-table
          v-model="selected"
          :headers="itemHeaders"
          :items="activityInstanceItems"
          item-value="item_key"
          return-object
          show-select
          hide-default-footer
          items-per-page="-1"
          :no-data-text="noDataText"
          density="compact"
        >
          <template #[`item.order`]="{ item }">
            <div class="d-block">
              <v-number-input
                v-model="item.order"
                hide-details
                hide
                control-variant="hidden"
                data-cy="item-order"
                min="1"
                :rules="[formRules.required, formRules.numeric]"
                :disabled="disableEdit(item)"
              />
            </div>
          </template>
          <template #[`item.primary`]="{ item }">
            <div class="d-block">
              <v-switch
                v-model="item.primary"
                hide-details
                data-cy="item-primary"
                :disabled="disableEdit(item)"
                @change="removePrimary(item)"
              />
            </div>
          </template>
          <template #[`item.name`]="{ item }">
            <div class="d-block">
              <span v-if="item.ct_terms && item.ct_terms.length > 0">
                {{
                  item.ct_terms.map((term) => term.submission_value).join(', ')
                }}
              </span>
              <span
                v-else-if="
                  item.unit_definitions && item.unit_definitions.length > 0
                "
              >
                {{ item.unit_definitions.map((unit) => unit.name).join(', ') }}
              </span>
              <span v-else-if="item.text_value">
                {{ item.text_value }}
              </span>
              <span v-else>-</span>
            </div>
          </template>
          <template #[`item.item_type`]="{ item }">
            <div class="d-block">
              {{ item.activity_item_class?.data_type_name || '' }}
            </div>
          </template>
          <template #[`item.activity_item_class`]="{ item }">
            <div class="d-block">
              {{ item.activity_item_class?.name || '' }}
            </div>
          </template>
          <template #[`item.name_submission_value`]="{ item }">
            <div class="d-block">
              <span v-if="item.ct_terms && item.ct_terms.length > 0">
                {{ item.ct_terms.map((term) => term.name).join(', ') }}
              </span>
              <span v-else>-</span>
            </div>
          </template>
          <template #[`item.code_submission_value`]="{ item }">
            <div class="d-block">
              <span v-if="item.ct_terms && item.ct_terms.length > 0">
                {{
                  item.ct_terms.map((term) => term.submission_value).join(', ')
                }}
              </span>
              <span v-else>-</span>
            </div>
          </template>
        </v-data-table>
      </div>

      <div v-if="useFormView">
        <v-card
          v-for="(ai, idx) in formInstances"
          :key="idx"
          elevation="1"
          class="mb-8"
          :border="isAlreadyDefined(ai) ? 'error xl' : 'default'"
        >
          <v-card-title class="d-flex">
            <v-skeleton-loader
              :loading="formLoading"
              type="heading"
              width="300"
            >
              {{ t('CRFItems.activity_instance_item') }} {{ idx + 1 }}
            </v-skeleton-loader>

            <v-spacer />
            <span
              v-if="isAlreadyDefined(ai)"
              style="color: #f44336; font-weight: bold"
            >
              {{ t('CRFItems.activity_instance_already_defined') }}
            </span>
            <v-spacer />

            <v-skeleton-loader :loading="formLoading" type="avatar">
              <v-btn
                icon="mdi-delete-outline"
                data-cy="remove-activity-instance"
                size="small"
                variant="outlined"
                color="red"
                :readonly="readOnly"
                @click.stop="removeActivityInstance(idx)"
              />
            </v-skeleton-loader>
          </v-card-title>

          <v-card-text>
            <v-row>
              <v-col>
                <v-skeleton-loader
                  height="54px"
                  :loading="formLoading"
                  type="heading"
                >
                  <v-autocomplete
                    v-model="ai.activity_instance_uid"
                    :label="t('CRFItems.activity_instance')"
                    data-cy="activity-instance"
                    :items="availableActivityInstances"
                    item-title="name"
                    item-value="uid"
                    :clearable="!readOnly"
                    :readonly="readOnly"
                    :rules="[formRules.required]"
                    :class="{
                      shake: isShaking && !ai.activity_instance_uid,
                    }"
                    @update:model-value="onActivityInstanceChange(idx)"
                  />
                </v-skeleton-loader>
              </v-col>
              <v-col @click="() => activateShake(!ai.activity_instance_uid)">
                <v-skeleton-loader
                  height="54px"
                  :loading="formLoading"
                  type="heading"
                >
                  <v-select
                    v-model="ai.activity_item_class_uid"
                    :label="t('CRFItems.activity_item_class')"
                    data-cy="activity-item-class"
                    :items="ai.availableActivityItemClasses"
                    item-title="name"
                    item-value="uid"
                    :clearable="!readOnly"
                    :readonly="readOnly || !ai.activity_instance_uid"
                    :rules="[formRules.required]"
                    :class="{
                      shake:
                        isShaking &&
                        ai.activity_instance_uid &&
                        !ai.activity_item_class_uid,
                    }"
                  />
                </v-skeleton-loader>
              </v-col>
            </v-row>
            <v-row @click="() => activateShake(!ai.activity_item_class_uid)">
              <v-col>
                <v-skeleton-loader
                  height="54px"
                  :loading="formLoading"
                  type="heading"
                >
                  <v-text-field
                    v-model="ai.preset_response_value"
                    :label="t('CRFItems.preset_response_value')"
                    data-cy="preset-response-value"
                    :clearable="!readOnly"
                    :readonly="readOnly || !ai.activity_item_class_uid"
                  />
                </v-skeleton-loader>
              </v-col>
              <v-col>
                <v-skeleton-loader
                  height="54px"
                  :loading="formLoading"
                  type="heading"
                >
                  <v-text-field
                    v-model="ai.value_condition"
                    :label="t('CRFItems.value_condition')"
                    data-cy="value-condition"
                    :clearable="!readOnly"
                    :readonly="readOnly || !ai.activity_item_class_uid"
                  />
                </v-skeleton-loader>
              </v-col>
              <v-col>
                <v-skeleton-loader
                  height="54px"
                  :loading="formLoading"
                  type="heading"
                >
                  <v-text-field
                    v-model="ai.value_dependent_map"
                    :label="t('CRFItems.value_dependent_map')"
                    data-cy="value-dependent-map"
                    :clearable="!readOnly"
                    :readonly="readOnly || !ai.activity_item_class_uid"
                  />
                </v-skeleton-loader>
              </v-col>
              <v-col>
                <v-skeleton-loader
                  height="54px"
                  :loading="formLoading"
                  type="heading"
                >
                  <v-number-input
                    v-model="ai.order"
                    :label="t('_global.order')"
                    data-cy="order"
                    :clearable="!readOnly"
                    :readonly="readOnly || !ai.activity_item_class_uid"
                  />
                </v-skeleton-loader>
              </v-col>
              <v-col>
                <v-skeleton-loader
                  height="20px"
                  :loading="formLoading"
                  type="heading"
                >
                  <v-checkbox
                    v-model="ai.primary"
                    :label="t('CRFItems.primary')"
                    data-cy="primary-checkbox"
                    :readonly="readOnly || !ai.activity_item_class_uid"
                  />
                </v-skeleton-loader>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>

        <v-row v-if="formInstances.length === 0">
          <v-col class="d-flex justify-center align-center mb-4">
            <v-skeleton-loader :loading="formLoading" type="text" width="200">
              {{ t('CRFItems.no_activity_instance_links') }}
            </v-skeleton-loader>
          </v-col>
        </v-row>
        <v-row>
          <v-col class="d-flex justify-center align-center">
            <v-skeleton-loader
              :loading="formLoading"
              type="button"
              height="48"
              width="148"
            >
              <v-btn-group
                color="nnBaseBlue"
                rounded="xl"
                variant="tonal"
                divided
              >
                <v-btn
                  :text="t('_global.reset')"
                  :disabled="readOnly || !hasFormChanged"
                  data-cy="reset-activity-instances"
                  @click.stop="resetActivityInstances"
                />
                <v-btn
                  icon="mdi-plus"
                  data-cy="add-activity-instances"
                  :disabled="
                    readOnly ||
                    (formInstances.length > 0 &&
                      !formInstances[formInstances.length - 1]
                        .activity_item_class_uid)
                  "
                  @click.stop="addActivityInstance"
                />
              </v-btn-group>
            </v-skeleton-loader>
          </v-col>
        </v-row>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { ref, inject, onMounted, watch, computed, nextTick } from 'vue'
import activities from '@/api/activities'
import { useShake } from '@/composables/shake'

const { t } = useI18n()
const formRules = inject('formRules')
const { isShaking, activateShake } = useShake()

const props = defineProps({
  modelValue: {
    type: Array,
    default: undefined,
  },
  readOnly: {
    type: Boolean,
    default: false,
  },
  formView: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['update:modelValue'])

const availableActivityInstances = ref([])
const originalActivityInstances = ref([])
const formLoading = ref(false)

const selected = ref([])
const activityInstance = ref(null)
const activityInstanceItems = ref([])
const isLoadingItems = ref(false)

const useFormView = ref(false)

const formInstances = computed({
  get() {
    return props.modelValue || []
  },
  set(val) {
    emit('update:modelValue', val)
  },
})

const COMPARED_FIELDS = [
  'activity_instance_uid',
  'activity_item_class_uid',
  'order',
  'primary',
  'preset_response_value',
  'value_condition',
  'value_dependent_map',
]

const hasFormChanged = computed(() => {
  const current = formInstances.value
  const original = originalActivityInstances.value
  if (current.length !== original.length) return true
  return current.some((item, idx) =>
    COMPARED_FIELDS.some((field) => item[field] !== original[idx][field])
  )
})

const itemHeaders = computed(() => [
  {
    title: t('activityItemsTable.select_box'),
    key: 'data-table-select',
    width: '5%',
  },
  {
    title: t('_global.order'),
    key: 'order',
    width: '5%',
  },
  {
    title: t('CRFItems.primary'),
    key: 'primary',
    width: '5%',
  },
  {
    title: t('activityItemsTable.headerDataType'),
    key: 'item_type',
    width: '15%',
  },
  {
    title: t('activityItemsTable.headerName'),
    key: 'name',
    width: '25%',
  },
  {
    title: t('activityItemsTable.headerActivityItemClass'),
    key: 'activity_item_class',
    width: '15%',
  },
  {
    title: t('activityItemsTable.headerNameSubmissionValue'),
    key: 'name_submission_value',
    width: '15%',
  },
  {
    title: t('activityItemsTable.headerCodeSubmissionValue'),
    key: 'code_submission_value',
    width: '15%',
  },
])
const noDataText = computed(() => {
  if (!activityInstance.value) {
    return t('CRFActivityInstanceManagement.no_activity_instance_selected')
  }
  return t('CRFActivityInstanceManagement.no_items_available')
})

watch(activityInstance, async () => {
  if (activityInstance.value) {
    isLoadingItems.value = true
    try {
      await getActivityItems()
      selected.value = activityInstanceItems.value.filter((ai) =>
        formInstances.value.some(
          (fi) =>
            fi.activity_instance_uid === activityInstance.value &&
            fi.activity_item_class_uid === ai.activity_item_class.uid
        )
      )

      await nextTick()
    } finally {
      isLoadingItems.value = false
    }
  } else {
    activityInstanceItems.value = []
    selected.value = []
  }
})

watch(selected, () => {
  if (useFormView.value || !activityInstance.value || isLoadingItems.value)
    return
  syncTableViewToModel()
})

watch(
  activityInstanceItems,
  () => {
    if (useFormView.value || !activityInstance.value || isLoadingItems.value)
      return
    syncTableViewToModel()
  },
  { deep: true }
)

watch(useFormView, async (isFormView) => {
  if (isFormView) {
    const updated = formInstances.value.map((ai) => {
      if (ai.availableActivityItemClasses?.length) return ai
      const instance = availableActivityInstances.value.find(
        (inst) => inst.uid === ai.activity_instance_uid
      )
      return {
        ...ai,
        availableActivityItemClasses:
          instance?.activity_items?.map((item) => item.activity_item_class) ||
          [],
      }
    })
    formInstances.value = updated
  } else if (activityInstance.value) {
    isLoadingItems.value = true
    try {
      await getActivityItems()
      selected.value = activityInstanceItems.value.filter((ai) =>
        formInstances.value.some(
          (fi) =>
            fi.activity_instance_uid === activityInstance.value &&
            fi.activity_item_class_uid === ai.activity_item_class.uid
        )
      )
      await nextTick()
    } finally {
      isLoadingItems.value = false
    }
  }
})

function syncTableViewToModel() {
  const selectedKeys = new Set(selected.value.map((s) => s.item_key))
  const otherInstances = formInstances.value.filter(
    (fi) => fi.activity_instance_uid !== activityInstance.value
  )

  const currentInstance = availableActivityInstances.value.find(
    (inst) => inst.uid === activityInstance.value
  )
  const fallbackClasses =
    currentInstance?.activity_items?.map((item) => item.activity_item_class) ||
    []

  const updatedInstances = activityInstanceItems.value
    .filter((item) => selectedKeys.has(item.item_key))
    .map((item) => {
      const existing = formInstances.value.find(
        (fi) =>
          fi.activity_instance_uid === activityInstance.value &&
          fi.activity_item_class_uid === item.activity_item_class.uid
      )
      return {
        activity_instance_uid: activityInstance.value,
        activity_item_class_uid: item.activity_item_class.uid,
        primary: item.primary,
        order: item.order,
        preset_response_value: existing?.preset_response_value || '',
        value_condition: existing?.value_condition || '',
        value_dependent_map: existing?.value_dependent_map || '',
        availableActivityItemClasses: existing?.availableActivityItemClasses
          ?.length
          ? existing.availableActivityItemClasses
          : fallbackClasses,
      }
    })
    .sort((a, b) => a.order - b.order)
  emit('update:modelValue', [...otherInstances, ...updatedInstances])
}

onMounted(async () => {
  useFormView.value = props.formView
  formLoading.value = true

  try {
    const instancesResp = await activities.get(
      { page_size: 0 },
      'activity-instances'
    )
    availableActivityInstances.value = instancesResp.data.items

    const withClasses = (props.modelValue || []).map((ai) => {
      const instance = availableActivityInstances.value.find(
        (inst) => inst.uid === ai.activity_instance_uid
      )
      return {
        ...ai,
        availableActivityItemClasses:
          instance?.activity_items?.map((item) => item.activity_item_class) ||
          ai.availableActivityItemClasses ||
          [],
      }
    })
    emit('update:modelValue', withClasses)
    originalActivityInstances.value = [...withClasses]
  } finally {
    formLoading.value = false
  }
})

function disableEdit(elm) {
  return !selected.value.some(
    (i) => i.activity_item_class.uid === elm.activity_item_class.uid
  )
}

function removePrimary(elm) {
  activityInstanceItems.value.forEach((i) => {
    if (i.item_key !== elm.item_key) {
      i.primary = false
    }
  })
}

async function getActivityItems() {
  const resp = await activities.getActivityInstanceItems(activityInstance.value)
  activityInstanceItems.value = resp.data.map((aii) => {
    const linked = formInstances.value.find(
      (fi) =>
        fi.activity_instance_uid === activityInstance.value &&
        fi.activity_item_class_uid === aii.activity_item_class.uid
    )
    return {
      ...aii,
      item_key: aii.activity_item_class.uid,
      order: linked?.order ?? 1,
      primary: linked?.primary ?? false,
    }
  })
}

function isAlreadyDefined(activityInstance) {
  const key = `${activityInstance.activity_instance_uid}|${activityInstance.activity_item_class_uid}`
  const count = formInstances.value.filter(
    (ai) => `${ai.activity_instance_uid}|${ai.activity_item_class_uid}` === key
  ).length
  return count > 1
}

function addActivityInstance() {
  formInstances.value = [
    ...formInstances.value,
    {
      activity_instance_uid: '',
      activity_item_class_uid: '',
      order: 1,
      preset_response_value: '',
      primary: false,
      value_condition: '',
      value_dependent_map: '',
      availableActivityItemClasses: [],
    },
  ]
}

function removeActivityInstance(idx) {
  const updated = [...formInstances.value]
  updated.splice(idx, 1)
  formInstances.value = updated
}

function resetActivityInstances() {
  formInstances.value = [...originalActivityInstances.value]
}

function onActivityInstanceChange(idx) {
  const updated = [...formInstances.value]
  updated[idx] = {
    ...updated[idx],
    activity_item_class_uid: null,
    availableActivityItemClasses: loadActivityInstanceItemClasses(idx),
  }
  formInstances.value = updated
}

function loadActivityInstanceItemClasses(idx) {
  const ai = availableActivityInstances.value.find(
    (inst) => inst.uid === formInstances.value[idx].activity_instance_uid
  )
  return ai?.activity_items?.map((item) => item.activity_item_class) || []
}
</script>
