<template>
  <HorizontalStepperForm
    ref="stepper"
    :title="$t('StudyActivityUpdateForms.batch_activities_title')"
    :steps="updateSteps"
    :reset-loading="resetLoading"
    :form-observer-getter="() => reviewForm"
    @close="close"
    @save="submit"
  >
    <template #[`step.review`]>
      <v-form ref="reviewForm">
        <v-alert
          density="compact"
          type="info"
          rounded="lg"
          class="text-white mb-2 ml-1 mr-1"
          :text="$t('StudyActivityUpdateForms.no_requested_in_batch_info')"
        />
        <v-data-table
          class="elevation-0 table"
          :items="studyActivities"
          :headers="updateHeaders"
          :loading="loading"
        >
          <template #[`item.name`]="{ item }">
            <span v-if="item.activity.name !== item.latest_activity.name">
              <v-chip
                color="red"
                class="crossed-out"
                density="compact"
                size="small"
              >
                <div class="text-nnTrueBlue">
                  {{ item.activity.name }}
                </div>
              </v-chip>
              &#8594;
            </span>
            <v-chip color="green" density="compact" size="small">
              <div class="text-nnTrueBlue">
                {{ item.latest_activity.name }}
              </div>
            </v-chip>
            <v-tooltip top>
              <template #activator="{ props }">
                <v-icon
                  v-if="item.show_activity_in_protocol_flowchart"
                  v-bind="props"
                  class="ml-2"
                >
                  mdi-eye-outline
                </v-icon>
              </template>
              <span>{{ $t('StudyActivityUpdateForms.visible_in_soa') }}</span>
            </v-tooltip>
          </template>
          <template #[`item.group`]="{ item }">
            <div
              v-if="
                item.latest_activity.status === statuses.RETIRED ||
                checkIfCurrentGroupingExist(item) ||
                getGroups(item).some(
                  (group) =>
                    group.activity_group_name ===
                    item.study_activity_group.activity_group_name
                )
              "
            >
              -
            </div>
            <div v-else-if="getGroups(item).length === 0">
              <v-chip
                color="red"
                class="crossed-out"
                density="compact"
                size="small"
              >
                <div class="text-nnTrueBlue">
                  {{ item.study_activity_group.activity_group_name }}
                </div>
                <v-tooltip top>
                  <template #activator="{ props }">
                    <v-icon
                      v-if="item.show_activity_group_in_protocol_flowchart"
                      v-bind="props"
                      class="ml-2"
                    >
                      mdi-eye-outline
                    </v-icon>
                  </template>
                  <span>{{
                    $t('StudyActivityUpdateForms.visible_in_soa')
                  }}</span>
                </v-tooltip>
              </v-chip>
              <div class="ml-2 mr-8 mt-1">&#8594;</div>
              <v-chip color="red" density="compact" size="small">
                <div class="text-nnTrueBlue">{{ statuses.RETIRED }}</div>
              </v-chip>
            </div>
            <div v-else-if="getGroups(item).length === 1" class="flow-row">
              <v-chip
                color="red"
                class="crossed-out"
                density="compact"
                size="small"
              >
                <div class="text-nnTrueBlue">
                  {{ item.study_activity_group.activity_group_name }}
                </div>
              </v-chip>

              <v-tooltip top>
                <template #activator="{ props }">
                  <div
                    v-if="item.show_activity_group_in_protocol_flowchart"
                    v-bind="props"
                  >
                    <v-icon>mdi-eye-outline</v-icon>
                  </div>
                </template>
                <span>{{ $t('StudyActivityUpdateForms.visible_in_soa') }}</span>
              </v-tooltip>

              <div>→</div>

              <v-chip color="green" density="compact" size="small">
                <div class="text-nnTrueBlue">
                  {{
                    item.latest_activity.activity_groupings[0]
                      .activity_group_name
                  }}
                </div>
              </v-chip>
            </div>
            <div v-else>
              <v-chip
                color="red"
                class="crossed-out"
                density="compact"
                size="small"
              >
                <div class="text-nnTrueBlue">
                  {{ item.study_activity_group.activity_group_name }}
                </div>
              </v-chip>
              <v-tooltip top>
                <template #activator="{ props }">
                  <v-icon
                    v-if="item.show_activity_group_in_protocol_flowchart"
                    v-bind="props"
                    class="ml-2"
                  >
                    mdi-eye-outline
                  </v-icon>
                </template>
                <span>{{ $t('StudyActivityUpdateForms.visible_in_soa') }}</span>
              </v-tooltip>
              &#8594;
              <v-autocomplete
                v-model="item.activity_group_uid"
                :label="$t('StudyActivityUpdateForms.activity_group')"
                :items="getGroups(item)"
                item-title="activity_group_name"
                item-value="activity_group_uid"
                class="mt-2 mb-n2"
                color="nnBaseBlue"
                clearable
                @update:model-value="
                  ((item.activity_subgroup_uid = null),
                  removeFromPayload(item),
                  (item.accept = false),
                  (item.decline = false))
                "
              />
            </div>
          </template>
          <template #[`item.subgroup`]="{ item }">
            <div
              v-if="
                item.latest_activity.status === statuses.RETIRED ||
                checkIfCurrentGroupingExist(item) ||
                (getSubroups(item).length === 1 &&
                  item.study_activity_subgroup.activity_subgroup_name ===
                    getSubroups(item)[0].activity_subgroup_name)
              "
            >
              -
            </div>
            <div v-else-if="getSubroups(item).length === 0">
              <v-chip
                color="red"
                class="crossed-out"
                density="compact"
                size="small"
              >
                <div class="text-nnTrueBlue">
                  {{ item.study_activity_subgroup.activity_subgroup_name }}
                </div>
              </v-chip>
              <v-tooltip top>
                <template #activator="{ props }">
                  <v-icon
                    v-if="item.show_activity_subgroup_in_protocol_flowchart"
                    v-bind="props"
                    class="ml-2"
                  >
                    mdi-eye-outline
                  </v-icon>
                </template>
                <span>{{ $t('StudyActivityUpdateForms.visible_in_soa') }}</span>
              </v-tooltip>
              <div class="ml-2 mr-8 mt-1">&#8594;</div>
              <v-chip color="red" density="compact" size="small">
                <div class="text-nnTrueBlue">{{ statuses.RETIRED }}</div>
              </v-chip>
            </div>
            <div v-else-if="getSubroups(item).length === 1" class="flow-row">
              <v-chip
                color="red"
                class="crossed-out"
                density="compact"
                size="small"
              >
                <div class="text-nnTrueBlue">
                  {{ item.study_activity_subgroup.activity_subgroup_name }}
                </div>
              </v-chip>

              <v-tooltip top>
                <template #activator="{ props }">
                  <div
                    v-if="item.show_activity_subgroup_in_protocol_flowchart"
                    v-bind="props"
                  >
                    <v-icon>mdi-eye-outline</v-icon>
                  </div>
                </template>
                <span>{{ $t('StudyActivityUpdateForms.visible_in_soa') }}</span>
              </v-tooltip>

              <div>→</div>

              <v-chip color="green" density="compact" size="small">
                <div class="text-nnTrueBlue">
                  {{ getSubroups(item)[0].activity_subgroup_name }}
                </div>
              </v-chip>
            </div>
            <div v-else>
              <v-chip
                color="red"
                class="crossed-out"
                density="compact"
                size="small"
              >
                <div class="text-nnTrueBlue">
                  {{ item.study_activity_subgroup.activity_subgroup_name }}
                </div>
              </v-chip>
              <v-tooltip top>
                <template #activator="{ props }">
                  <v-icon
                    v-if="item.show_activity_subgroup_in_protocol_flowchart"
                    v-bind="props"
                    class="ml-2"
                  >
                    mdi-eye-outline
                  </v-icon>
                </template>
                <span>{{ $t('StudyActivityUpdateForms.visible_in_soa') }}</span>
              </v-tooltip>
              &#8594;
              <v-autocomplete
                v-model="item.activity_subgroup_uid"
                :label="$t('StudyActivityUpdateForms.activity_subgroup')"
                :items="getSubroups(item)"
                item-title="activity_subgroup_name"
                item-value="activity_subgroup_uid"
                class="mt-2 mb-n2"
                width="300px"
                color="nnBaseBlue"
                clearable
                :disabled="
                  !item.activity_group_uid && getGroups(item).length !== 1
                "
                @update:model-value="
                  (removeFromPayload(item),
                  (item.accept = false),
                  (item.decline = false))
                "
              />
            </div>
          </template>
          <template #[`item.status`]="{ item }">
            <span v-if="item.latest_activity.status === statuses.RETIRED">
              <v-chip
                color="green"
                class="crossed-out"
                density="compact"
                size="small"
              >
                <div class="text-nnTrueBlue">
                  {{ item.activity.status }}
                </div>
              </v-chip>
              &#8594;
              <v-chip color="red" density="compact" size="small">
                <div class="text-nnTrueBlue">
                  {{ item.latest_activity.status }}
                </div>
              </v-chip>
            </span>
            <div v-else>-</div>
          </template>
          <template #[`item.actions`]="{ item }">
            <v-btn
              v-if="item.latest_activity.status !== statuses.RETIRED"
              variant="outlined"
              size="x-small"
              rounded
              class="mr-2"
              :disabled="
                !item.latest_activity.activity_groupings.some(
                  (group) =>
                    group.activity_group_name ===
                    item.study_activity_group.activity_group_name
                ) &&
                item.latest_activity.activity_groupings.length > 1 &&
                !item.activity_group_uid &&
                !item.activity_subgroup_uid
              "
              :active="item.accept"
              active-color="nnBaseBlue"
              @click="
                (item.accept
                  ? removeFromPayload(item)
                  : preparePayload(item, true),
                (item.accept = item.accept ? false : true),
                (item.decline = false))
              "
            >
              <v-icon v-if="item.accept"> mdi-check </v-icon>
              {{ $t('StudyActivityUpdateForms.accept') }}
            </v-btn>
            <v-btn
              variant="outlined"
              size="x-small"
              rounded
              :active="item.decline"
              active-color="error"
              @click="
                (item.decline
                  ? removeFromPayload(item)
                  : preparePayload(item, false),
                (item.decline = item.decline ? false : true),
                (item.accept = false))
              "
            >
              <v-icon v-if="item.decline"> mdi-close </v-icon>
              {{ $t('StudyActivityUpdateForms.decline') }}
            </v-btn>
          </template>
        </v-data-table>
      </v-form>
    </template>
  </HorizontalStepperForm>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
</template>

<script setup>
import { inject, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import filteringParameters from '@/utils/filteringParameters'
import { useStudyActivitiesStore } from '@/stores/studies-activities'
import study from '@/api/study'
import statuses from '@/constants/statuses'
import libraries from '@/constants/libraries'

const notificationHub = inject('notificationHub')
const { t } = useI18n()
const emit = defineEmits(['close', 'added'])
const studiesGeneralStore = useStudiesGeneralStore()
const activitiesStore = useStudyActivitiesStore()

const reviewForm = ref()
const studyActivities = ref([])
const resetLoading = ref(0)
const confirm = ref()
const stepper = ref()
const loading = ref(false)
const payloadActivities = ref([])

const updateSteps = [
  { name: 'review', title: t('StudyActivityUpdateForms.review_changes') },
]
const updateHeaders = [
  { title: t('StudyActivityUpdateForms.activity_name'), key: 'name' },
  { title: t('StudyActivityUpdateForms.activity_group'), key: 'group' },
  { title: t('StudyActivityUpdateForms.activity_subgroup'), key: 'subgroup' },
  { title: t('StudyActivityUpdateForms.activity_status'), key: 'status' },
  { title: '', key: 'actions' },
]

onMounted(() => {
  getStudyActivitiesForUpdate()
})

function close() {
  emit('close')
  stepper.value.reset()
}

function getGroups(activity) {
  try {
    return activity.latest_activity.activity_groupings
      .map((grouping) => ({
        activity_group_name: grouping.activity_group_name,
        activity_group_uid: grouping.activity_group_uid,
      }))
      .filter(
        (group1, i, arr) =>
          arr.findIndex(
            (group2) => group2.activity_group_uid === group1.activity_group_uid
          ) === i
      )
  } catch (error) {
    console.error(error)
  }
}

function getSubroups(activity) {
  if (
    getGroups(activity).some(
      (group) =>
        group.activity_group_name ===
        activity.study_activity_group.activity_group_name
    )
  ) {
    activity.activity_group_uid =
      activity.study_activity_group.activity_group_uid
  }
  let groupings = JSON.parse(
    JSON.stringify(activity.latest_activity.activity_groupings)
  )

  if (activity.activity_group_uid) {
    groupings = groupings.filter(
      (item) => item.activity_group_uid === activity.activity_group_uid
    )
  }

  try {
    return groupings
      .map((grouping) => ({
        activity_subgroup_name: grouping.activity_subgroup_name,
        activity_subgroup_uid: grouping.activity_subgroup_uid,
      }))
      .filter(
        (group1, i, arr) =>
          arr.findIndex(
            (group2) =>
              group2.activity_subgroup_uid === group1.activity_subgroup_uid
          ) === i
      )
  } catch (error) {
    console.error(error)
  }
}

async function getStudyActivitiesForUpdate(filters, options, filtersUpdated) {
  loading.value = true
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  params.filters = {
    is_activity_updated: { v: [true] },
    keep_old_version: { v: [false] },
    'latest_activity.is_request_rejected': { v: [false] },
    'latest_activity.library_name': {
      v: [libraries.LIBRARY_REQUESTED],
      op: 'ne',
    },
  }

  params.filter_out_retired_groupings = true
  params.studyUid = studiesGeneralStore.selectedStudy.uid
  const resp = await activitiesStore.fetchStudyActivities(params)
  studyActivities.value = resp.data.items
  loading.value = false
}

function preparePayload(item, accept) {
  try {
    payloadActivities.value = payloadActivities.value.filter(
      (el) => el.uid !== item.study_activity_uid
    )

    const newItem = {
      action: accept ? statuses.ACCEPT : statuses.DECLINE,
      uid: item.study_activity_uid,
      content: accept
        ? getGroupingsForPayload(item)
        : { keep_old_version: true },
    }

    payloadActivities.value.push(newItem)
  } catch (error) {
    console.error(error)
  }
}

function removeFromPayload(item) {
  payloadActivities.value = payloadActivities.value.filter(
    (el) => el.uid !== item.study_activity_uid
  )
}

function getGroupingsForPayload(activity) {
  if (activity?.activity_group_uid && activity?.activity_subgroup_uid) {
    return {
      activity_group_uid: activity.activity_group_uid,
      activity_subgroup_uid: activity.activity_subgroup_uid,
    }
  }

  if (activity?.activity_group_uid && !activity?.activity_subgroup_uid) {
    return {
      activity_group_uid: activity.activity_group_uid,
      activity_subgroup_uid: getSubroups(activity)[0].activity_subgroup_uid,
    }
  }

  const groupings = activity?.latest_activity?.activity_groupings ?? []

  if (!activity?.activity_group_uid && activity?.activity_subgroup_uid) {
    return {
      activity_group_uid: groupings[0].activity_group_uid,
      activity_subgroup_uid: activity.activity_subgroup_uid,
    }
  }

  if (groupings.length > 0 && groupings[0]) {
    return {
      activity_group_uid: groupings[0].activity_group_uid,
      activity_subgroup_uid: groupings[0].activity_subgroup_uid,
    }
  }

  return {
    activity_group_uid: null,
    activity_subgroup_uid: null,
  }
}

function checkIfCurrentGroupingExist(activity) {
  return activity.latest_activity.activity_groupings.some(
    (obj) =>
      obj.activity_group_name ===
        activity.study_activity_group.activity_group_name &&
      obj.activity_subgroup_name ===
        activity.study_activity_subgroup.activity_subgroup_name
  )
}

async function submit() {
  const options = {
    type: 'warning',
    cancelLabel: t('_global.cancel'),
    agreeLabel: t('_global.continue'),
  }
  if (await confirm.value.open(t('_global.save_question'), options)) {
    study
      .batchUpdateStudyActivities(
        studiesGeneralStore.selectedStudy.uid,
        payloadActivities.value
      )
      .then((resp) => {
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
            msg: t('StudyActivityUpdateForms.update_confirm_activities', {
              number: payloadActivities.value.length,
            }),
            type: 'success',
          })
        }
        resetLoading.value += 1
        close()
      })
  } else {
    resetLoading.value += 1
  }
}
</script>

<style scoped lang="scss">
.crossed-out {
  text-decoration: line-through;
}
.table {
  border: solid gray 1px;
  border-radius: 10px;
  font-size: 14px;
}
.flow-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
</style>
