<template>
  <HorizontalStepperForm
    ref="stepper"
    :title="$t('StudyActivityUpdateForms.batch_instances_title')"
    :steps="updateSteps"
    :reset-loading="resetLoading"
    :form-observer-getter="() => reviewForm"
    @close="close"
    @save="submit"
  >
    <template #[`step.review`]>
      <v-form ref="reviewForm">
        <v-data-table
          class="elevation-0"
          :items="studyActivities"
          :headers="updateHeaders"
          :loading="loading"
        >
          <template #[`item.name`]="{ item }">
            <span
              v-if="
                checkIfDifferent(
                  item.activity_instance.name,
                  item.latest_activity_instance.name
                )
              "
            >
              <v-chip
                color="red"
                class="crossed-out"
                density="compact"
                size="small"
              >
                <div class="text-nnTrueBlue">
                  {{ item.activity_instance.name }}
                </div>
              </v-chip>
              &#8594;
            </span>
            <v-chip color="green" density="compact" size="small">
              <div class="text-nnTrueBlue">
                {{ item.latest_activity_instance.name }}
              </div>
            </v-chip>
          </template>
          <template #[`item.class`]="{ item }">
            <span
              v-if="
                checkIfDifferent(
                  item.activity_instance.activity_instance_class.name,
                  item.latest_activity_instance.activity_instance_class.name
                )
              "
            >
              <v-chip
                color="red"
                class="crossed-out"
                density="compact"
                size="small"
              >
                <div class="text-nnTrueBlue">
                  {{ item.activity_instance.activity_instance_class.name }}
                </div>
              </v-chip>
              &#8594;
              <v-chip color="green" density="compact" size="small">
                <div class="text-nnTrueBlue">
                  {{
                    item.latest_activity_instance.activity_instance_class.name
                  }}
                </div>
              </v-chip>
            </span>
            <div v-else>-</div>
          </template>
          <template #[`item.code`]="{ item }">
            <span
              v-if="
                checkIfDifferent(
                  item.activity_instance.topic_code,
                  item.latest_activity_instance.topic_code
                )
              "
            >
              <v-chip
                color="red"
                class="crossed-out"
                density="compact"
                size="small"
              >
                <div class="text-nnTrueBlue">
                  {{ item.activity_instance.topic_code }}
                </div>
              </v-chip>
              &#8594;
              <v-chip color="green" density="compact" size="small">
                <div class="text-nnTrueBlue">
                  {{ item.latest_activity_instance.topic_code }}
                </div>
              </v-chip>
            </span>
            <div v-else>-</div>
          </template>
          <template #[`item.status`]="{ item }">
            <span
              v-if="item.latest_activity_instance.status === statuses.RETIRED"
            >
              <v-chip
                color="red"
                class="crossed-out"
                density="compact"
                size="small"
              >
                <div class="text-nnTrueBlue">
                  {{ item.activity_instance.status }}
                </div>
              </v-chip>
              &#8594;
              <v-chip color="green" density="compact" size="small">
                <div class="text-nnTrueBlue">
                  {{ item.latest_activity_instance.status }}
                </div>
              </v-chip>
            </span>
            <div v-else>-</div>
          </template>
          <template #[`item.actions`]="{ item }">
            <v-btn
              v-if="item.latest_activity_instance.status !== statuses.RETIRED"
              variant="outlined"
              size="x-small"
              rounded
              class="mr-2"
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
  { title: t('StudyActivityUpdateForms.instance_name'), key: 'name' },
  { title: t('StudyActivityUpdateForms.instance_class'), key: 'class' },
  { title: t('StudyActivityUpdateForms.topic_code'), key: 'code' },
  { title: t('_global.status'), key: 'status' },
  { title: '', key: 'actions' },
]

onMounted(() => {
  getStudyActivitiesForUpdate()
})

function close() {
  emit('close')
  stepper.value.reset()
}

async function getStudyActivitiesForUpdate(filters, options, filtersUpdated) {
  loading.value = true
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  params.filters = {
    is_activity_instance_updated: { v: [true] },
    keep_old_version: { v: [false] },
  }

  params.studyUid = studiesGeneralStore.selectedStudy.uid
  const resp = await activitiesStore.fetchStudyActivityInstances(params)
  studyActivities.value = resp.data.items
  loading.value = false
}

function checkIfDifferent(valA, valB) {
  return valA !== valB
}

function removeFromPayload(item) {
  payloadActivities.value = payloadActivities.value.filter(
    (el) => el.uid !== item.study_activity_instance_uid
  )
}

function preparePayload(item, accept) {
  try {
    payloadActivities.value = payloadActivities.value.filter(
      (el) => el.uid !== item.study_activity_instance_uid
    )

    const newItem = {
      action: accept ? statuses.ACCEPT : statuses.DECLINE,
      uid: item.study_activity_instance_uid,
      content: accept ? null : { keep_old_version: true },
    }

    payloadActivities.value.push(newItem)
  } catch (error) {
    console.error(error)
  }
}

async function submit() {
  const options = {
    type: 'warning',
    cancelLabel: t('_global.cancel'),
    agreeLabel: t('_global.continue'),
  }
  if (await confirm.value.open(t('_global.save_question'), options)) {
    study
      .batchUpdateStudyActivityInstances(
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
            msg: t('StudyActivityUpdateForms.update_confirm_instances', {
              number: payloadActivities.value.length,
            }),
            type: 'success',
          })
        }
        close()
      })
  }

  resetLoading.value += 1
}
</script>

<style scoped lang="scss">
.crossed-out {
  text-decoration: line-through;
}
</style>
