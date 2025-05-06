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
          item-title="name.sponsor_preferred_name"
          return-object
          clearable
          class="mt-4"
          variant="outlined"
          color="nnBaseBlue"
          rounded="lg"
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

<script>
import { computed } from 'vue'
import study from '@/api/study'
import StudyActivitySelectionBaseForm from './StudyActivitySelectionBaseForm.vue'
import studyEpochs from '@/api/studyEpochs'
import terms from '@/api/controlledTerminology/terms'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    StudyActivitySelectionBaseForm,
  },
  inject: ['eventBusEmit', 'formRules'],
  props: {
    selection: {
      type: Array,
      default: () => [],
    },
    currentSelectionMatrix: {
      type: Object,
      default: undefined,
    },
    open: Boolean,
  },
  emits: ['close', 'updated', 'remove'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
    }
  },
  data() {
    return {
      helpItems: [],
      selectedVisitsGrouped: [],
      studyVisitsGrouped: {},
      flowchartGroups: [],
      selectedFlowchartGroup: null,
    }
  },
  mounted() {
    terms.getByCodelist('flowchartGroups').then((resp) => {
      this.flowchartGroups = resp.data.items
    })
    // Filter out non-visit and unscheduled-visits as these shouldn't
    // be able to be assigned to any schedules
    const params = {
      page_size: 0,
      filters: {
        visit_class: { v: ['NON_VISIT', 'UNSCHEDULED_VISIT'], op: 'ne' },
      },
    }
    studyEpochs.getStudyVisits(this.selectedStudy.uid, params).then((resp) => {
      // a mapping to arrays of visits with the same consecutive_visit_group if set, else a single visit with the visit uid as key
      this.studyVisitsGrouped = resp.data.items.reduce((acc, item) => {
        const key = item.consecutive_visit_group ?? item.uid
        if (!acc[key]) {
          acc[key] = []
        }
        acc[key].push(item)
        return acc
      }, {})
    })
  },
  methods: {
    close() {
      this.$emit('close')
      this.selectedVisitsGrouped = []
    },
    unselectItem(item) {
      this.$emit('remove', item)
    },
    async submit() {
      const { valid } = await this.$refs.observer.validate()
      if (!valid) {
        return
      }
      this.$refs.baseForm.loading = true
      const data = []
      for (const item of this.selection) {
        // First: delete any existing study activity schedule for the given selection
        for (const cell of Object.values(
          this.currentSelectionMatrix[item.study_activity_uid]
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
        for (const visits of this.selectedVisitsGrouped) {
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
              soa_group_term_uid: this.selectedFlowchartGroup?.term_uid,
            },
          },
        })
      }
      study
        .studyActivitySoaEditsBatchOperations(this.selectedStudy.uid, data)
        .then(
          () => {
            this.eventBusEmit('notification', {
              type: 'success',
              msg: this.$t('DetailedFlowchart.batch_update_success', {
                number: this.selection.length,
              }),
            })
            this.$emit('updated')
            this.close()
            this.$refs.baseForm.loading = false
          },
          () => {
            this.$refs.baseForm.loading = false
          }
        )
    },
  },
}
</script>

<style scoped lang="scss">
.text-white {
  color: white !important;
}
</style>
