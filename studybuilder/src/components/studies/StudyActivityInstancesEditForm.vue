<template>
  <SimpleFormDialog
    ref="form"
    max-width="1000px"
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
        <v-text-field
          :model-value="getActivityPath"
          density="compact"
          readonly
          disabled
        />
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
            <div v-html="item.details" />
          </template>
          <template #[`item.state`]="{ item }">
            <div :class="'px-1 ' + getActivityStateBackground(item)">
              {{ getActivityState(item) }}
            </div>
          </template>
        </v-data-table>
      </v-card>
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

const eventBusEmit = inject('eventBusEmit')
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
  { title: t('StudyActivityInstances.instance'), key: 'name' },
  { title: t('StudyActivityInstances.details'), key: 'details' },
  { title: t('StudyActivityInstances.state'), key: 'state' },
]

const instances = ref([])
const selected = ref([])
const form = ref()

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
})

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
      if (props.editedActivity.activity_instance) {
        selected.value.push(
          instances.value.find(
            (instance) =>
              instance.uid === props.editedActivity.activity_instance.uid
          ).uid
        )
      }
    })
    if (instances.value.length > 1) {
      const par = {
        filters: {
          'activity.uid': { v: [props.editedActivity.activity.uid], op: 'co' },
        },
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
  }
}
function transformInstances(instances) {
  for (let instance of instances) {
    instance.details = `Class: ${instance.activity_instance_class.name} <br> Topic code: ${instance.topic_code} <br> ADaM param: ${instance.adam_param_code}`
    for (let item of instance.activity_items) {
      if (item.ct_terms.length > 0) {
        instance.details += `<br> ${item.activity_item_class.name}: ${item.ct_terms.map((term) => term.name)}`
      } else {
        instance.details += `<br> ${item.activity_item_class.name}: ${item.unit_definitions.map((unit) => unit.name)}`
      }
    }
  }
  return instances
}
function getActivityStateBackground(activity) {
  if (activity.is_required_for_activity) {
    return 'mandatory'
  } else if (activity.is_default_selected_for_activity) {
    return 'defaulted'
  }
  if (instances.value.length === 1) {
    return 'suggestion'
  }
}
function getActivityState(activity) {
  if (activity.is_required_for_activity) {
    return t('StudyActivityInstances.mandatory')
  } else if (activity.is_default_selected_for_activity) {
    return t('StudyActivityInstances.defaulted')
  }
  if (instances.value.length === 1) {
    return t('StudyActivityInstances.suggestion')
  }
}
function submit() {
  if (selected.value.length === 1) {
    setSingleActivityInstance()
  } else {
    setMultipleActivityInstances()
  }
}
function setSingleActivityInstance() {
  const data = {
    activity_instance_uid: selected.value[0],
    study_activity_uid: props.editedActivity.study_activity_uid,
    show_activity_instance_in_protocol_flowchart:
      props.editedActivity.show_activity_instance_in_protocol_flowchart,
  }
  activitiesStore
    .updateStudyActivityInstance(
      selectedStudy.value.uid,
      props.editedActivity.study_activity_instance_uid,
      data
    )
    .then(
      () => {
        eventBusEmit('notification', {
          msg: t('StudyActivityInstances.instance_updated'),
          type: 'success',
        })
        close()
      },
      () => {
        form.value.working = false
      }
    )
}
function setMultipleActivityInstances() {
  const data = {
    activity_instance_uids: selected.value,
    study_activity_uid: props.editedActivity.study_activity_uid,
  }
  activitiesStore
    .batchSelectStudyActivityInstances(selectedStudy.value.uid, data)
    .then(
      () => {
        eventBusEmit('notification', {
          msg: t('StudyActivityInstances.instance_created'),
          type: 'success',
        })
        close()
      },
      () => {
        form.value.working = false
      }
    )
}
function close() {
  instances.value = []
  selected.value = []
  emit('close')
}
</script>

<style scoped>
.defaulted {
  background-color: darkseagreen;
  border-radius: 5px;
}
.mandatory {
  background-color: rgb(202, 124, 124);
  border-radius: 5px;
}
.suggestion {
  background-color: rgb(217, 201, 106);
  border-radius: 5px;
}
</style>
