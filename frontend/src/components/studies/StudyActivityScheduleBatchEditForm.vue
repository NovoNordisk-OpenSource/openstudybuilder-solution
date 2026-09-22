<template>
  <StudyActivitySelectionBaseForm
    ref="baseForm"
    :help-items="helpItems"
    :selection="selection"
    :open="open"
    max-width="600px"
    @close="close"
    @submit="submit"
    @remove="unselectItem"
  >
    <template #body>
      <v-form ref="observer">
        <v-autocomplete
          v-model="selectedFlowchartGroup"
          :label="$t('StudyActivityForm.flowchart_group')"
          :items="flowchartGroups"
          item-title="sponsor_preferred_name"
          return-object
          clearable
          class="mt-4"
          color="nnBaseBlue"
        />
        <v-autocomplete
          v-model="selectedVisitsGrouped"
          :items="Object.values(studyVisitsGrouped)"
          :label="$t('StudyActivityScheduleBatchEditForm.studyVisits')"
          :item-title="
            (visits) =>
              visits[0].consecutive_visit_group ?? visits[0].visit_short_name
          "
          return-object
          multiple
          clearable
          :rules="[formRules.required]"
          class="mt-1"
          variant="outlined"
          color="nnBaseBlue"
          rounded="lg"
        />
        <v-alert
          density="compact"
          type="warning"
          class="text-white"
          :text="$t('DetailedFlowchart.batch_edit_warning')"
        />
      </v-form>
    </template>
  </StudyActivitySelectionBaseForm>
</template>

<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useI18n } from 'vue-i18n'
import StudyActivitySelectionBaseForm from './StudyActivitySelectionBaseForm.vue'
import study from '@/api/study'
import terms from '@/api/controlledTerminology/terms'
import visitConstants from '@/constants/visits'

const notificationHub = inject('notificationHub')
const formRules = inject('formRules')

const props = defineProps({
  selection: {
    type: Array,
    default: () => [],
  },
  currentSelectionMatrix: {
    type: Object,
    default: undefined,
  },
  studyVisits: {
    type: Array,
    default: null,
  },
  open: Boolean,
})

const emit = defineEmits(['close', 'updated', 'remove'])
const { t } = useI18n()
const studiesGeneralStore = useStudiesGeneralStore()

const selectedStudy = computed(() => studiesGeneralStore.selectedStudy)

const helpItems = []
const selectedVisitsGrouped = ref([])
const studyVisitsGrouped = ref({})
const flowchartGroups = ref([])
const selectedFlowchartGroup = ref(null)
const baseForm = ref()
const observer = ref()

onMounted(() => {
  terms.getTermsByCodelist('flowchartGroups').then((resp) => {
    flowchartGroups.value = resp.data.items
  })
  studyVisitsGrouped.value = props.studyVisits
    .filter(
      // Filter out non-visit and unscheduled-visits as these shouldn't
      // be able to be assigned to any schedules
      (item) =>
        item.visit_class !== visitConstants.CLASS_NON_VISIT &&
        item.visit_class !== visitConstants.CLASS_UNSCHEDULED_VISIT
    )
    .reduce((acc, item) => {
      // a mapping to arrays of visits with the same consecutive_visit_group if set, else a single visit with the visit uid as key
      const key = item.consecutive_visit_group ?? item.uid
      if (!acc[key]) {
        acc[key] = []
      }
      acc[key].push(item)
      return acc
    }, {})
})

function close() {
  emit('close')
  notificationHub.clearErrors()
  selectedVisitsGrouped.value = []
}
function unselectItem(item) {
  emit('remove', item)
}
async function submit() {
  const { valid } = await observer.value.validate()
  if (!valid) {
    return
  }

  notificationHub.clearErrors()

  baseForm.value.loading = true
  const data = []
  for (const item of props.selection) {
    // First: delete any existing study activity schedule for the given selection
    for (const cell of Object.values(
      props.currentSelectionMatrix[item.study_activity_uid]
    )) {
      if (cell.uid) {
        cell.value = false
        const uids = Array.isArray(cell.uid) ? cell.uid : [cell.uid]
        for (const uid of uids) {
          data.push({
            method: 'DELETE',
            object: 'StudyActivitySchedule',
            content: { uid },
          })
        }
      }
    }
    // Second: create new activity schedules
    for (const visits of selectedVisitsGrouped.value) {
      for (const visit of visits) {
        data.push({
          method: 'POST',
          object: 'StudyActivitySchedule',
          content: {
            study_activity_uid: item.study_activity_uid,
            study_visit_uid: visit.uid,
          },
        })
      }
    }
    data.push({
      method: 'PATCH',
      object: 'StudyActivity',
      content: {
        study_activity_uid: item.study_activity_uid,
        content: {
          soa_group_term_uid: selectedFlowchartGroup.value?.term_uid,
        },
      },
    })
  }
  try {
    const resp = await study.studyActivitySoaEditsBatchOperations(
      selectedStudy.value.uid,
      data
    )
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
        type: 'success',
        msg: t('DetailedFlowchart.batch_update_success', {
          number: props.selection.length,
        }),
      })
    }
    emit('updated')
    close()
  } finally {
    baseForm.value.loading = false
  }
}
</script>

<style scoped lang="scss">
.text-white {
  color: white !important;
}
</style>
