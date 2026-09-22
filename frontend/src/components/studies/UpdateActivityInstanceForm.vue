<template>
  <SimpleFormDialog
    :title="$t('StudyActivityUpdateForms.update_to_activity')"
    max-width="600px"
    no-default-actions
    top-right-cancel
    :open="open"
    @close="close"
  >
    <template #body>
      <v-form ref="observer">
        <div
          v-if="
            checkIfDifferent(
              activity.activity_instance.name,
              activity.latest_activity_instance.name
            )
          "
        >
          <div class="label mb-2">
            {{ $t('StudyActivityUpdateForms.instance_name') }}
          </div>
          <v-row>
            <v-col cols="12">
              <span>
                <v-chip color="red" class="crossed-out">
                  <div class="text-nnTrueBlue">
                    {{ activity.activity_instance.name }}
                  </div>
                </v-chip>
                &#8594;
              </span>
              <v-chip color="green">
                <div class="text-nnTrueBlue">
                  {{ activity.latest_activity_instance.name }}
                </div>
              </v-chip>
            </v-col>
          </v-row>
        </div>
        <div
          v-if="
            checkIfDifferent(
              activity.activity_instance.activity_instance_class.uid,
              activity.latest_activity_instance.activity_instance_class.uid
            )
          "
        >
          <div class="label my-2">
            {{ $t('StudyActivityUpdateForms.instance_class') }}
          </div>
          <v-row>
            <v-col cols="12">
              <span>
                <v-chip color="red" class="crossed-out">
                  <div class="text-nnTrueBlue">
                    {{
                      activity.activity_instance.activity_instance_class.name
                    }}
                  </div>
                </v-chip>
                &#8594;
              </span>
              <v-chip color="green">
                <div class="text-nnTrueBlue">
                  {{
                    activity.latest_activity_instance.activity_instance_class
                      .name
                  }}
                </div>
              </v-chip>
            </v-col>
          </v-row>
        </div>
        <div
          v-if="
            checkIfDifferent(
              activity.activity_instance.topic_code,
              activity.latest_activity_instance.topic_code
            )
          "
        >
          <div class="label my-2">
            {{ $t('StudyActivityUpdateForms.topic_code') }}
          </div>
          <v-row>
            <v-col cols="12">
              <span>
                <v-chip color="red" class="crossed-out">
                  <div class="text-nnTrueBlue">
                    {{ activity.activity_instance.topic_code }}
                  </div>
                </v-chip>
                &#8594;
              </span>
              <v-chip color="green">
                <div class="text-nnTrueBlue">
                  {{ activity.latest_activity_instance.topic_code }}
                </div>
              </v-chip>
            </v-col>
          </v-row>
        </div>
        <div
          v-if="
            checkIfDifferent(
              activity.activity_instance.status,
              activity.latest_activity_instance.status
            ) && activity.latest_activity_instance.status === statuses.RETIRED
          "
        >
          <div class="label my-2">{{ $t('_global.status') }}</div>
          <v-row>
            <v-col cols="12">
              <span>
                <v-chip color="red" class="crossed-out">
                  <div class="text-nnTrueBlue">
                    {{ activity.activity_instance.status }}
                  </div>
                </v-chip>
                &#8594;
              </span>
              <v-chip color="warning">
                <div class="text-nnTrueBlue">
                  {{ activity.latest_activity_instance.status }}
                </div>
              </v-chip>
            </v-col>
          </v-row>
        </div>
        <div
          v-if="activity.latest_activity_instance.status !== statuses.RETIRED"
          class="label my-2"
        >
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
        v-if="activity.latest_activity_instance.status !== statuses.RETIRED"
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
import { useI18n } from 'vue-i18n'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { inject, ref } from 'vue'
import study from '@/api/study'
import statuses from '@/constants/statuses.js'

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

const observer = ref()
const loading = ref(false)

async function submit() {
  notificationHub.clearErrors()

  loading.value = true
  study
    .updateStudyActivityInstanceToLatest(
      studiesGeneralStore.selectedStudy.uid,
      props.activity.study_activity_instance_uid
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

function close() {
  emit('close')
  notificationHub.clearErrors()
}

async function declineAndKeep() {
  loading.value = true
  const payload = JSON.parse(JSON.stringify(props.activity))
  payload.keep_old_version = true
  payload.is_reviewed = true
  study
    .updateStudyActivityInstance(
      studiesGeneralStore.selectedStudy.uid,
      props.activity.study_activity_instance_uid,
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
