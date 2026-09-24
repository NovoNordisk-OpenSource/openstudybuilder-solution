<template>
  <SimpleFormDialog
    ref="form"
    :title="title"
    max-width="600px"
    no-default-actions
    top-right-cancel
    :open="open"
    @close="close"
  >
    <template #body>
      <v-form ref="observer">
        <div class="label mb-2">
          {{ $t('StudyActivityUpdateForms.activity_group') }}
        </div>
        <v-row>
          <v-col>
            <span
              v-if="
                checkIfDifferent(
                  activity.activity.activity_groupings[0].activity_group_name,
                  activity.latest_activity.activity_groupings[0]
                    .activity_group_name
                )
              "
            >
              <v-chip color="red" class="crossed-out">
                <div class="text-nnTrueBlue">
                  {{
                    activity.activity.activity_groupings[0].activity_group_name
                  }}
                </div>
              </v-chip>
              &#8594;
            </span>
            <v-chip color="green">
              <div class="text-nnTrueBlue">
                {{
                  activity.latest_activity.activity_groupings[0]
                    .activity_group_name
                }}
              </div>
            </v-chip>
          </v-col>
        </v-row>
        <div class="label my-2">
          {{ $t('StudyActivityUpdateForms.activity_subgroup') }}
        </div>
        <v-row>
          <v-col cols="12">
            <span
              v-if="
                checkIfDifferent(
                  activity.activity.activity_groupings[0]
                    .activity_subgroup_name,
                  activity.latest_activity.activity_groupings[0]
                    .activity_subgroup_name
                )
              "
            >
              <v-chip color="red" class="crossed-out">
                <div class="text-nnTrueBlue">
                  {{
                    activity.activity.activity_groupings[0]
                      .activity_subgroup_name
                  }}
                </div>
              </v-chip>
              &#8594;
            </span>
            <v-chip color="green">
              <div class="text-nnTrueBlue">
                {{
                  activity.latest_activity.activity_groupings[0]
                    .activity_subgroup_name
                }}
              </div>
            </v-chip>
          </v-col>
        </v-row>
        <div class="label my-2">
          {{ $t('StudyActivityUpdateForms.activity_name') }}
        </div>
        <v-row>
          <v-col cols="12">
            <span
              v-if="
                checkIfDifferent(
                  activity.activity.name,
                  activity.latest_activity.name
                )
              "
            >
              <v-chip color="red" class="crossed-out">
                <div class="text-nnTrueBlue">
                  {{ activity.activity.name }}
                </div>
              </v-chip>
              &#8594;
            </span>
            <v-chip color="green">
              <div class="text-nnTrueBlue">
                {{ activity.latest_activity.name }}
              </div>
            </v-chip>
          </v-col>
        </v-row>
        <div class="label my-2">
          {{ $t('StudyActivityUpdateForms.accept_change') }}
        </div>
      </v-form>
    </template>
    <template #actions="">
      <v-btn
        v-if="!props.activity.keep_old_version"
        color="nnGoldenSun200"
        variant="flat"
        rounded
        class="mr-2"
        :loading="loading"
        @click="declineAndKeep()"
      >
        <v-icon> mdi-close </v-icon>
        {{ $t('StudyActivityUpdateForms.decline_keep') }}
      </v-btn>
      <v-btn
        color="nnBaseBlue"
        variant="flat"
        rounded
        :loading="loading"
        @click="submit()"
      >
        <v-icon> mdi-check </v-icon>
        {{ $t('StudyActivityUpdateForms.accept') }}
      </v-btn>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useI18n } from 'vue-i18n'
import { computed, inject, ref } from 'vue'
import study from '@/api/study'

const studiesGeneralStore = useStudiesGeneralStore()
const emit = defineEmits(['close'])
const { t } = useI18n()
const notificationHub = inject('notificationHub')

const props = defineProps({
  activity: {
    type: Object,
    default: null,
  },
  open: Boolean,
})

const title = computed(() => {
  return props.activity?.activity?.replaced_by_activity
    ? t('StudyActivityUpdateForms.request_accepted')
    : t('StudyActivityUpdateForms.update_to_request')
})

const loading = ref(false)

function submit() {
  notificationHub.clearErrors()

  loading.value = true
  const data = {
    activity_group_uid:
      props.activity.latest_activity.activity_groupings[0].activity_group_uid,
    activity_subgroup_uid:
      props.activity.latest_activity.activity_groupings[0]
        .activity_subgroup_uid,
  }

  if (props.activity.activity.replaced_by_activity) {
    study
      .updateToApprovedActivity(
        studiesGeneralStore.selectedStudy.uid,
        props.activity.study_activity_uid
      )
      .then(() => {
        loading.value = false
        notificationHub.add({
          type: 'success',
          msg: t('StudyActivityUpdateForms.update_success'),
        })
        close()
      })
  } else {
    study
      .updateToLatestActivityVersion(
        studiesGeneralStore.selectedStudy.uid,
        props.activity.study_activity_uid,
        data
      )
      .then(() => {
        loading.value = false
        notificationHub.add({
          type: 'success',
          msg: t('StudyActivityUpdateForms.update_success'),
        })
        close()
      })
  }
}

function close() {
  emit('close')
  notificationHub.clearErrors()
}

async function declineAndKeep() {
  loading.value = true
  const payload = JSON.parse(JSON.stringify(props.activity))
  payload.keep_old_version = true
  study
    .updateStudyActivity(
      studiesGeneralStore.selectedStudy.uid,
      props.activity.study_activity_uid,
      payload
    )
    .then(() => {
      loading.value = false
      notificationHub.add({
        type: 'success',
        msg: t('StudyActivityUpdateForms.decline_success'),
      })
      close()
    })
}

function checkIfDifferent(valA, valB) {
  return valA !== valB
}
</script>
<style scoped>
.crossed-out {
  text-decoration: line-through;
}
.label {
  font-weight: 700;
  font-size: 18px;
  line-height: 24px;
  letter-spacing: -0.02em;
  color: rgb(var(--v-theme-nnTrueBlue));
  min-height: 24px;
}
</style>
