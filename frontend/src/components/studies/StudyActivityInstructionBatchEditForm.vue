<template>
  <SimpleFormDialog
    ref="form"
    :title="$t('StudyActivityInstructionBatchEditForm.title')"
    :help-items="helpItems"
    :open="open"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-autocomplete
        v-model="form.activity_instruction_template"
        :label="$t('StudyActivityInstructionBatchEditForm.select_template')"
        :items="templates"
        item-title="name_plain"
        return-object
        @change="loadParameters"
      />
      <v-form v-if="form.activityInstructionTemplate" ref="observer">
        <v-progress-circular
          v-if="loadingParameters"
          indeterminate
          color="secondary"
        />
        <ParameterValueSelector
          :model-value="parameters"
          :template="form.activityInstructionTemplate.name"
          color="white"
        />
      </v-form>
      <hr class="my-4 text-dfltBackground" />
      <StudyActivitySelectionTable
        :selection="selection"
        :title="$t('StudyActivityInstructionBatchForm.batch_table_title')"
      />
      <hr class="my-4 text-dfltBackground" />
      <v-checkbox
        v-model="deleteSelection"
        :color="deleteSelection ? 'error' : ''"
      >
        <template #label>
          <span :class="{ 'text-error': deleteSelection }">
            {{ $t('StudyActivityInstructionBatchEditForm.delete_selection') }}
          </span>
        </template>
      </v-checkbox>
    </template>
  </SimpleFormDialog>
</template>

<script>
import { computed } from 'vue'
import activityInstructionTemplates from '@/api/activityInstructionTemplates'
import instances from '@/utils/instances'
import ParameterValueSelector from '@/components/tools/ParameterValueSelector.vue'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import study from '@/api/study'
import StudyActivitySelectionTable from './StudyActivitySelectionTable.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    ParameterValueSelector,
    SimpleFormDialog,
    StudyActivitySelectionTable,
  },
  inject: ['notificationHub'],
  props: {
    selection: {
      type: Array,
      default: () => [],
    },
    instructionsPerStudyActivity: {
      type: Object,
      default: undefined,
    },
    open: Boolean,
  },
  emits: ['close', 'deleted', 'remove', 'updated'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
    }
  },
  data() {
    return {
      deleteSelection: false,
      form: {},
      helpItems: [],
      loadingParameters: false,
      parameters: [],
      templates: [],
    }
  },
  mounted() {
    const activityGroupUids = []
    const activitySubGroupUids = []
    for (const studyActivity of this.selection) {
      if (studyActivity.study_activity_group.activity_group_uid) {
        activityGroupUids.push(
          studyActivity.study_activity_group.activity_group_uid
        )
      }
      if (studyActivity.study_activity_subgroup.activity_subgroup_uid) {
        activitySubGroupUids.push(
          studyActivity.study_activity_subgroup.activity_subgroup_uid
        )
      }
    }
    const params = {
      filters: {
        'activity_groups.uid': { v: activityGroupUids },
        'activity_subgroups.uid': { v: activitySubGroupUids },
      },
      operator: 'or',
    }
    activityInstructionTemplates.get(params).then((resp) => {
      this.templates = resp.data.items
    })
  },
  methods: {
    close() {
      this.$emit('close')
      this.notificationHub.clearErrors()
      this.form = {}
    },
    async loadParameters(template) {
      if (template) {
        this.loadingParameters = true
        const resp =
          await activityInstructionTemplates.getObjectTemplateParameters(
            template.uid
          )
        this.parameters = resp.data
        this.loadingParameters = false
      } else {
        this.parameters = []
      }
    },
    async submit() {
      const operations = []
      let msg
      let notifType = 'success'
      let event

      if (this.$refs.observer) {
        const { valid } = await this.$refs.observer.validate()
        if (!valid) {
          this.$refs.form.working = false
          return
        }

        this.notificationHub.clearErrors()

        for (const item of this.selection) {
          operations.push({
            method: 'DELETE',
            content: {
              study_activity_instruction_uid:
                this.instructionsPerStudyActivity[item.study_activity_uid]
                  .study_activity_instruction_uid,
            },
          })
          operations.push({
            method: 'POST',
            content: {
              activity_instruction_data: {
                activity_instruction_template_uid:
                  this.form.activity_instruction_template.uid,
                parameter_terms: await instances.formatParameterValues(
                  this.parameters
                ),
                library_name:
                  this.form.activity_instruction_template.library.name,
              },
              study_activity_uid: item.study_activity_uid,
            },
          })
        }
        msg = this.$t('StudyActivityInstructionBatchEditForm.update_success')
        event = 'updated'
      } else if (this.deleteSelection) {
        for (const item of this.selection) {
          operations.push({
            method: 'DELETE',
            content: {
              study_activity_instruction_uid:
                this.instructionsPerStudyActivity[item.study_activity_uid]
                  .study_activity_instruction_uid,
            },
          })
        }
        msg = this.$t('StudyActivityInstructionBatchEditForm.delete_success')
        event = 'deleted'
      }

      if (operations.length) {
        await study.studyActivityInstructionBatchOperations(
          this.selectedStudy.uid,
          operations
        )
        this.$emit(event)
      } else {
        notifType = 'info'
        msg = this.$t('_global.no_changes')
      }
      this.notificationHub.add({ msg, type: notifType })
      this.$refs.form.working = false
      this.close()
    },
    unselectItem(item) {
      this.$emit('remove', item)
    },
  },
}
</script>
