<template>
  <v-card bg-color="dfltBackground" data-cy="form-body" rounded="xl">
    <v-card-title class="d-flex align-center">
      <span class="dialog-title">{{ $t('StudyActivityEditForm.title') }}</span>
      <HelpButton :help-text="$t('_help.StudyActivityEditForm.general')" />
    </v-card-title>
    <v-divider />
    <v-card-text class="mt-4">
      <div class="bg-white">
        <v-form ref="observer">
          <v-text-field
            :label="$t('_global.library')"
            :model-value="library"
            disabled
            rounded="lg"
            variant="outlined"
            class="mb-1"
          />
          <v-autocomplete
            v-model="form.study_soa_group"
            :label="$t('StudyActivityForm.flowchart_group')"
            data-cy="flowchart-group"
            :items="flowchartGroups"
            variant="outlined"
            color="nnBaseBlue"
            rounded="lg"
            item-title="name.sponsor_preferred_name"
            return-object
            :rules="[formRules.required]"
            clearable
          />
          <v-autocomplete
            v-model="form.activity_group"
            :label="$t('StudyActivity.activity_group')"
            :items="groups"
            variant="outlined"
            color="nnBaseBlue"
            rounded="lg"
            class="mb-1"
            item-title="activity_group_name"
            return-object
            :disabled="Boolean(groups.length <= 1)"
            :rules="[formRules.required]"
            @update:model-value="form.activity_subgroup = null"
          />
          <v-autocomplete
            v-model="form.activity_subgroup"
            :label="$t('StudyActivity.activity_sub_group')"
            :items="subgroups"
            variant="outlined"
            color="nnBaseBlue"
            rounded="lg"
            class="mb-1"
            item-title="activity_subgroup_name"
            return-object
            :disabled="Boolean(subgroups.length <= 1 && form.activity_subgroup)"
            :rules="[formRules.required]"
            clearable
          />
          <v-text-field
            :label="$t('StudyActivity.activity')"
            :model-value="activity"
            variant="outlined"
            color="nnBaseBlue"
            rounded="lg"
            class="mb-1"
            disabled
          />
          <v-checkbox
            v-model="form.activity.is_data_collected"
            disabled
            :label="$t('StudyActivityForm.is_data_collected')"
          />
        </v-form>
      </div>
    </v-card-text>
    <v-divider />
    <v-card-actions class="pr-6 my-2">
      <v-spacer />
      <v-btn
        class="secondary-btn"
        variant="outlined"
        rounded
        width="120px"
        @click="close"
      >
        {{ $t('_global.cancel') }}
      </v-btn>
      <v-btn
        color="nnBaseBlue"
        rounded
        variant="flat"
        width="120px"
        :loading="working"
        @click="submit"
      >
        {{ $t('_global.save') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import study from '@/api/study'
import terms from '@/api/controlledTerminology/terms'
import HelpButton from '@/components/tools/HelpButton.vue'

const { t } = useI18n()
const eventBusEmit = inject('eventBusEmit')
const formRules = inject('formRules')
const props = defineProps({
  studyActivity: {
    type: Object,
    default: undefined,
  },
})
const emit = defineEmits(['close', 'updated'])

const flowchartGroups = ref([])
const form = ref({})
const working = ref(false)
const observer = ref()

const library = computed(() => {
  return props.studyActivity && props.studyActivity.activity
    ? props.studyActivity.activity.library_name
    : ''
})

const activity = computed(() => {
  return props.studyActivity ? props.studyActivity.activity.name : ''
})

const groups = computed(() => {
  let groups = props.studyActivity.activity.activity_groupings.map(
    (grouping) => ({
      activity_group_name: grouping.activity_group_name,
      activity_group_uid: grouping.activity_group_uid,
    })
  )
  //Removing duplicates
  groups = groups.filter(
    (group1, i, arr) =>
      arr.findIndex(
        (group2) => group2.activity_group_uid === group1.activity_group_uid
      ) === i
  )
  return groups
})

const subgroups = computed(() => {
  const groupings = props.studyActivity.activity.activity_groupings.filter(
    (grouping) =>
      grouping.activity_group_uid ===
      form.value.activity_group.activity_group_uid
  )
  return groupings.map((grouping) => ({
    activity_subgroup_name: grouping.activity_subgroup_name,
    activity_subgroup_uid: grouping.activity_subgroup_uid,
  }))
})

watch(
  () => props.studyActivity,
  (value) => {
    if (value) {
      form.value = { ...props.studyActivity }
      form.value.study_soa_group.name = {
        sponsor_preferred_name: form.value.study_soa_group.soa_group_term_name,
      }
      form.value.activity_group = props.studyActivity.study_activity_group
      form.value.activity_subgroup = props.studyActivity.study_activity_subgroup
    } else {
      form.value = {}
    }
  },
  { immediate: true }
)

onMounted(() => {
  terms.getByCodelist('flowchartGroups').then((resp) => {
    flowchartGroups.value = resp.data.items
  })
})

function close() {
  working.value = false
  form.value = {}
  observer.value.reset()
  emit('close')
}

async function submit() {
  const { valid } = await observer.value.validate()
  if (!valid) {
    return
  }
  working.value = true
  const data = {
    soa_group_term_uid: form.value.study_soa_group.term_uid,
    activity_group_uid: form.value.activity_group.activity_group_uid,
    activity_subgroup_uid: form.value.activity_subgroup.activity_subgroup_uid,
  }
  study
    .updateStudyActivity(
      props.studyActivity.study_uid,
      props.studyActivity.study_activity_uid,
      data
    )
    .then(
      () => {
        eventBusEmit('notification', {
          type: 'success',
          msg: t('StudyActivityEditForm.update_success'),
        })
        emit('updated')
        close()
      },
      () => {
        working.value = false
      }
    )
}
</script>
