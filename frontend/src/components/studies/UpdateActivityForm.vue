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
              activity.activity.name,
              activity.latest_activity.name
            )
          "
        >
          <div class="label my-2">
            {{ $t('StudyActivityUpdateForms.activity_name') }}
          </div>
          <v-row>
            <v-col cols="12">
              <span>
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
        </div>
        <div
          v-if="
            !groups.some(
              (group) =>
                group &&
                group.activity_group_name ===
                  activity.study_activity_group.activity_group_name
            )
          "
        >
          <div class="label mb-2">
            {{ $t('StudyActivityUpdateForms.activity_group') }}
          </div>
          <div style="display: flex">
            <v-chip color="red" class="crossed-out">
              <div class="text-nnTrueBlue">
                {{ activity.study_activity_group.activity_group_name }}
              </div>
            </v-chip>
            <div class="ml-2 mr-8 mt-1">&#8594;</div>
            <v-autocomplete
              v-model="selectedGroupings.activity_group_uid"
              :label="$t('StudyActivityUpdateForms.activity_group')"
              :items="groups"
              item-title="activity_group_name"
              item-value="activity_group_uid"
              class="mt-n1 ml-n4"
              color="nnBaseBlue"
              clearable
              :rules="[formRules.required]"
              @update:model-value="
                selectedGroupings.activity_subgroup_uid = null
              "
            />
          </div>
        </div>
        <div
          v-if="
            !subgroups.some(
              (subgroup) =>
                subgroup.activity_subgroup_name ===
                activity.study_activity_subgroup.activity_subgroup_name
            )
          "
        >
          <div class="label my-2">
            {{ $t('StudyActivityUpdateForms.activity_subgroup') }}
          </div>
          <div style="display: flex">
            <v-chip color="red" class="crossed-out">
              <div class="text-nnTrueBlue">
                {{ activity.study_activity_subgroup.activity_subgroup_name }}
              </div>
            </v-chip>
            <div class="ml-2 mr-8 mt-1">&#8594;</div>
            <v-autocomplete
              v-model="selectedGroupings.activity_subgroup_uid"
              :label="$t('StudyActivityUpdateForms.activity_subgroup')"
              :items="subgroups"
              item-title="activity_subgroup_name"
              item-value="activity_subgroup_uid"
              class="mt-n1 ml-n4"
              width="300px"
              color="nnBaseBlue"
              clearable
              :rules="[formRules.required]"
              :disabled="Boolean(subgroups.length < 1)"
            />
          </div>
        </div>
        <div
          v-if="
            checkIfDifferent(
              activity.activity.status,
              activity.latest_activity.status
            ) && activity.latest_activity.status === statuses.RETIRED
          "
        >
          <div class="label my-2">{{ $t('_global.status') }}</div>
          <v-row>
            <v-col cols="12">
              <span>
                <v-chip color="red" class="crossed-out">
                  <div class="text-nnTrueBlue">
                    {{ activity.activity.status }}
                  </div>
                </v-chip>
                &#8594;
              </span>
              <v-chip color="warning">
                <div class="text-nnTrueBlue">
                  {{ activity.latest_activity.status }}
                </div>
              </v-chip>
            </v-col>
          </v-row>
        </div>
        <div
          v-if="activity.latest_activity.status !== statuses.RETIRED"
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
        v-if="activity.latest_activity.status !== statuses.RETIRED"
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
import { computed, inject, ref, watch } from 'vue'
import study from '@/api/study'
import statuses from '@/constants/statuses.js'

const studiesGeneralStore = useStudiesGeneralStore()
const emit = defineEmits(['close'])
const { t } = useI18n()
const formRules = inject('formRules')
const notificationHub = inject('notificationHub')

const props = defineProps({
  activity: {
    type: Object,
    default: null,
  },
  open: Boolean,
})

const selectedGroupings = ref({})
const observer = ref()
const loading = ref(false)

watch(
  () => props.activity,
  (value) => {
    if (value) {
      selectedGroupings.value.activity_group_uid = null
      selectedGroupings.value.activity_subgroup_uid = null
      if (value.latest_activity.activity_groupings.length === 1) {
        selectedGroupings.value.activity_group_uid =
          value.latest_activity.activity_groupings[0].activity_group_uid
        selectedGroupings.value.activity_subgroup_uid =
          value.latest_activity.activity_groupings[0].activity_subgroup_uid
      }
    }
  },
  { immediate: true }
)

const groups = computed(() => {
  return props.activity.latest_activity.activity_groupings
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
})

const subgroups = computed(() => {
  if (selectedGroupings.value.activity_group_uid) {
    const groupings = props.activity.latest_activity.activity_groupings.filter(
      (grouping) =>
        grouping.activity_group_uid ===
        selectedGroupings.value.activity_group_uid
    )
    return groupings.map((grouping) => ({
      activity_subgroup_name: grouping.activity_subgroup_name,
      activity_subgroup_uid: grouping.activity_subgroup_uid,
    }))
  } else if (
    groups.value.some(
      (group) =>
        group &&
        group.activity_group_name ===
          props.activity.study_activity_group.activity_group_name
    )
  ) {
    const groupings = props.activity.latest_activity.activity_groupings.filter(
      (grouping) =>
        grouping.activity_group_uid ===
        props.activity.study_activity_group.activity_group_uid
    )
    return groupings.map((grouping) => ({
      activity_subgroup_name: grouping.activity_subgroup_name,
      activity_subgroup_uid: grouping.activity_subgroup_uid,
    }))
  }
  return props.activity.latest_activity.activity_groupings.map((grouping) => ({
    activity_subgroup_name: grouping.activity_subgroup_name,
    activity_subgroup_uid: grouping.activity_subgroup_uid,
  }))
})

async function submit() {
  const { valid } = await observer.value.validate()
  if (!valid) {
    return
  }

  notificationHub.clearErrors()

  loading.value = true
  try {
    selectedGroupings.value.activity_group_uid = selectedGroupings.value
      ?.activity_group_uid
      ? selectedGroupings.value?.activity_group_uid
      : props.activity.study_activity_group.activity_group_uid
    selectedGroupings.value.activity_subgroup_uid = selectedGroupings.value
      ?.activity_subgroup_uid
      ? selectedGroupings.value?.activity_subgroup_uid
      : props.activity.study_activity_subgroup.activity_subgroup_uid
    study
      .updateToLatestActivityVersion(
        studiesGeneralStore.selectedStudy.uid,
        props.activity.study_activity_uid,
        selectedGroupings.value
      )
      .then(() => {
        loading.value = false
        notificationHub.add({
          type: 'success',
          msg: t('StudyActivityUpdateForms.update_success'),
        })
        close()
      })
      .finally(() => {
        loading.value = false
      })
  } catch (error) {
    loading.value = false
    console.error(error)
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
