<template>
  <div class="pa-4 bg-white">
    <div class="d-flex align-center mb-4">
      <v-radio-group
        v-model="expandAllRows"
        row
        hide-details
        @change="toggleAllRowState"
      >
        <v-radio :label="$t('DetailedFlowchart.expand_all')" :value="true" />
        <v-radio :label="$t('DetailedFlowchart.collapse_all')" :value="false" />
      </v-radio-group>
      <v-spacer />
      <v-btn
        size="small"
        color="primary"
        :title="$t('StudyActivityInstructionTable.open_batch_form')"
        :disabled="
          !checkPermission($roles.STUDY_WRITE) || selectedStudyVersion !== null
        "
        icon="mdi-plus-box-multiple-outline"
        @click="openBatchForm()"
      />
    </div>
    <table :aria-label="$t('StudyActivityInstructionTable.table_caption')">
      <thead>
        <tr>
          <th width="5%" />
          <th width="25%">
            {{ $t('StudyActivityInstructionTable.activities') }}
          </th>
          <th width="15%">
            {{ $t('StudyActivityInstructionTable.visits') }}
          </th>
          <th width="50%">
            {{ $t('StudyActivityInstructionTable.instructions') }}
          </th>
          <th width="5%" />
        </tr>
      </thead>
      <tbody>
        <template
          v-for="(
            groups, flowchartGroup, flGroupIndex
          ) in activitiesStore.sortedStudyActivities"
          :key="flowchartGroup"
        >
          <tr class="flowchart text-uppercase">
            <td>
              <v-btn
                :icon="getDisplayButtonIcon(`flgroup-${flGroupIndex}`)"
                variant="text"
                @click="toggleRowState(`flgroup-${flGroupIndex}`)"
              />
            </td>
            <td colspan="4" class="text-strong">
              {{ flowchartGroup }}
            </td>
          </tr>
          <template v-for="(subgroups, group, groupIndex) in groups">
            <template v-if="rowsDisplayState[`flgroup-${flGroupIndex}`]">
              <tr :key="`${flowchartGroup}-${group}`" class="group">
                <td>
                  <v-btn
                    :icon="
                      getDisplayButtonIcon(
                        `group-${flGroupIndex}-${groupIndex}`
                      )
                    "
                    variant="text"
                    @click="
                      toggleRowState(`group-${flGroupIndex}-${groupIndex}`)
                    "
                  />
                </td>
                <td colspan="4" class="text-strong">
                  {{ group }}
                </td>
              </tr>
              <template
                v-for="(studyActivities, subgroup, subgroupIndex) in subgroups"
              >
                <template
                  v-if="rowsDisplayState[`group-${flGroupIndex}-${groupIndex}`]"
                >
                  <tr :key="`${flowchartGroup}-${group}-${subgroup}`">
                    <td>
                      <v-btn
                        :icon="
                          getDisplayButtonIcon(
                            `subgroup-${flGroupIndex}-${groupIndex}-${subgroupIndex}`
                          )
                        "
                        variant="text"
                        @click="
                          toggleRowState(
                            `subgroup-${flGroupIndex}-${groupIndex}-${subgroupIndex}`
                          )
                        "
                      />
                    </td>
                    <td colspan="4" class="subgroup">
                      <div class="d-flex align-center">
                        <v-checkbox
                          on-icon="mdi-checkbox-multiple-marked-outline"
                          off-icon="mdi-checkbox-multiple-blank-outline"
                          hide-details
                          :disabled="
                            !checkPermission($roles.STUDY_WRITE) ||
                            selectedStudyVersion !== null
                          "
                          class="flex-grow-0"
                          color="primary"
                          @change="
                            (event) =>
                              toggleSubgroupActivitiesSelection(
                                flowchartGroup,
                                group,
                                subgroup,
                                event
                              )
                          "
                        />
                        {{ subgroup }}
                      </div>
                    </td>
                  </tr>
                  <template
                    v-if="
                      rowsDisplayState[
                        `subgroup-${flGroupIndex}-${groupIndex}-${subgroupIndex}`
                      ]
                    "
                  >
                    <tr
                      v-for="studyActivity in studyActivities"
                      :key="studyActivity.study_activity_uid"
                    >
                      <td />
                      <td class="activity">
                        <div class="d-flex align-center">
                          <v-checkbox
                            hide-details
                            :model-value="
                              currentSelection.findIndex(
                                (item) =>
                                  item.study_activity_uid ===
                                  studyActivity.study_activity_uid
                              ) !== -1
                            "
                            :disabled="
                              !checkPermission($roles.STUDY_WRITE) ||
                              selectedStudyVersion !== null
                            "
                            class="flex-grow-0"
                            color="primary"
                            @change="
                              (event) =>
                                toggleActivitySelection(studyActivity, event)
                            "
                          />
                          {{ studyActivity.activity.name }}
                        </div>
                      </td>
                      <td>
                        {{
                          getStudyActivityVisits(
                            studyActivity.study_activity_uid
                          )
                        }}
                      </td>
                      <td>
                        <NNParameterHighlighter
                          :name="
                            getStudyActivityInstruction(
                              studyActivity.study_activity_uid
                            )
                          "
                          :show-prefix-and-postfix="false"
                        />
                      </td>
                      <td>
                        <ActionsMenu
                          v-if="
                            getStudyActivityInstruction(
                              studyActivity.study_activity_uid
                            )
                          "
                          :actions="actions"
                          :item="studyActivity"
                        />
                      </td>
                    </tr>
                  </template>
                </template>
              </template>
            </template>
          </template>
        </template>
      </tbody>
    </table>
    <v-dialog
      v-model="showBatchForm"
      persistent
      fullscreen
      content-class="fullscreen-dialog"
    >
      <StudyActivityInstructionBatchForm
        :study-activities="currentSelection"
        :current-study-activity-instructions="studyActivityInstructions"
        class="fullscreen-dialog"
        @close="closeBatchForm"
        @added="getInstructionsPerActivity"
      />
    </v-dialog>
    <v-dialog
      v-model="showBatchEditForm"
      persistent
      content-class="top-dialog"
      max-width="800px"
    >
      <StudyActivityInstructionBatchEditForm
        :selection="currentSelection"
        :instructions-per-study-activity="instructionsPerStudyActivity"
        :open="showBatchEditForm"
        @close="closeBatchEditForm"
        @deleted="onInstructionsDeleted"
        @updated="getInstructionsPerActivity"
      />
    </v-dialog>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  </div>
</template>

<script>
import { computed } from 'vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter.vue'
import study from '@/api/study'
import StudyActivityInstructionBatchForm from './StudyActivityInstructionBatchForm.vue'
import StudyActivityInstructionBatchEditForm from './StudyActivityInstructionBatchEditForm.vue'
import studyEpochs from '@/api/studyEpochs'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudyActivitiesStore } from '@/stores/studies-activities'

export default {
  components: {
    ActionsMenu,
    ConfirmDialog,
    NNParameterHighlighter,
    StudyActivityInstructionBatchEditForm,
    StudyActivityInstructionBatchForm,
  },
  inject: ['eventBusEmit'],
  setup() {
    const accessGuard = useAccessGuard()
    const studiesGeneralStore = useStudiesGeneralStore()
    const activitiesStore = useStudyActivitiesStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
      selectedStudyVersion: computed(
        () => studiesGeneralStore.selectedStudyVersion
      ),
      activitiesStore,
      ...accessGuard,
    }
  },
  data() {
    return {
      actions: [
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil-outline',
          iconColor: 'primary',
          accessRole: this.$roles.STUDY_WRITE,
          click: this.editActivityInstruction,
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete-outline',
          iconColor: 'error',
          accessRole: this.$roles.STUDY_WRITE,
          click: this.deleteActivityInstruction,
        },
      ],
      currentSelection: [],
      expandAllRows: false,
      instructionsPerStudyActivity: {},
      rowsDisplayState: {},
      showBatchForm: false,
      showBatchEditForm: false,
      studyActivityInstructions: [],
      visitsPerStudyActivity: {},
    }
  },
  async mounted() {
    await this.activitiesStore.fetchStudyActivities({
      studyUid: this.selectedStudy.uid,
    })
    this.getVisitsPerActivity()
    this.getInstructionsPerActivity()
  },
  methods: {
    getCurrentDisplayValue(rowKey) {
      const currentValue = this.rowsDisplayState[rowKey]
      if (currentValue === undefined) {
        return false
      }
      return currentValue
    },
    getDisplayButtonIcon(rowKey) {
      return this.getCurrentDisplayValue(rowKey)
        ? 'mdi-chevron-down'
        : 'mdi-chevron-right'
    },
    async getInstructionsPerActivity() {
      this.instructionsPerStudyActivity = {}
      const resp = await study.getStudyActivityInstructions(
        this.selectedStudy.uid
      )
      for (const instruction of resp.data) {
        this.instructionsPerStudyActivity[instruction.study_activity_uid] =
          instruction
      }
      this.studyActivityInstructions = resp.data
    },
    getStudyActivityInstruction(studyActivityUid) {
      if (this.instructionsPerStudyActivity[studyActivityUid] !== undefined) {
        return this.instructionsPerStudyActivity[studyActivityUid]
          .activity_instruction_name
      }
      return ''
    },
    async getVisitsPerActivity() {
      const resp = await studyEpochs.getStudyVisits(this.selectedStudy.uid, {
        page_size: 0,
      })
      const schedules = await study.getStudyActivitySchedules(
        this.selectedStudy.uid
      )
      const visitNamePerUid = {}

      for (const visit of resp.data.items) {
        visitNamePerUid[visit.uid] = visit.visit_short_name
        for (const schedule of schedules.data) {
          if (schedule.study_visit_uid === visit.uid) {
            if (
              this.visitsPerStudyActivity[schedule.study_activity_uid] ===
              undefined
            ) {
              this.visitsPerStudyActivity[schedule.study_activity_uid] = []
            }
            this.visitsPerStudyActivity[schedule.study_activity_uid].push(
              visitNamePerUid[schedule.study_visit_uid]
            )
          }
        }
      }
    },
    getStudyActivityVisits(studyActivityUid) {
      if (this.visitsPerStudyActivity[studyActivityUid] === undefined) {
        return ''
      }
      return this.visitsPerStudyActivity[studyActivityUid].join(', ')
    },
    editActivityInstruction(studyActivityInstruction) {
      this.currentSelection = [studyActivityInstruction]
      this.showBatchEditForm = true
    },
    async deleteActivityInstruction(studyActivity) {
      const options = { type: 'warning' }
      const instruction =
        this.instructionsPerStudyActivity[studyActivity.study_activity_uid]
      const uid = instruction.study_activity_instruction_uid
      const msg = this.$t('StudyActivityInstructionTable.confirm_delete', {
        instruction: instruction.activity_instruction_name,
      }).replace(/<\/?[^>]+(>|$)/g, '')
      if (await this.$refs.confirm.open(msg, options)) {
        study
          .deleteStudyActivityInstruction(this.selectedStudy.uid, uid)
          .then(() => {
            delete this.instructionsPerStudyActivity[
              studyActivity.study_activity_uid
            ]
            this.eventBusEmit('notification', {
              type: 'success',
              msg: this.$t('StudyActivityInstructionTable.delete_success'),
            })
          })
      }
    },
    /*
     ** Event handler to update display after some instructions were batch deleted
     */
    onInstructionsDeleted() {
      for (const item of this.currentSelection) {
        delete this.instructionsPerStudyActivity[item.study_activity_uid]
      }
    },
    openBatchForm() {
      if (!this.currentSelection.length) {
        this.eventBusEmit('notification', {
          type: 'warning',
          msg: this.$t('StudyActivityInstructionTable.batch_no_selection'),
        })
        return
      }
      let itemWithNoInstruction = false
      for (const item of this.currentSelection) {
        if (
          this.instructionsPerStudyActivity[item.study_activity_uid] ===
          undefined
        ) {
          itemWithNoInstruction = true
          break
        }
      }
      if (itemWithNoInstruction) {
        this.showBatchForm = true
      } else {
        this.showBatchEditForm = true
      }
    },
    closeBatchForm() {
      this.showBatchForm = false
    },
    closeBatchEditForm() {
      this.showBatchEditForm = false
      this.currentSelection = []
    },
    toggleRowState(rowKey) {
      const currentValue = this.getCurrentDisplayValue(rowKey)
      this.rowsDisplayState[rowKey] = !currentValue
    },
    toggleAllRowState(value) {
      let flgroupIndex = 0
      for (const flgroup in this.activitiesStore.sortedStudyActivities) {
        let groupIndex = 0
        this.rowsDisplayState[`flgroup-${flgroupIndex}`] = value
        for (const group in this.activitiesStore.sortedStudyActivities[
          flgroup
        ]) {
          let subgroupIndex = 0
          this.rowsDisplayState[`group-${flgroupIndex}-${groupIndex}`] = value
          // prettier-ignore
          for (const subgroup in this.activitiesStore.sortedStudyActivities[ // eslint-disable-line no-unused-vars
              flgroup
          ][group]) {
            this.rowsDisplayState[
              `subgroup-${flgroupIndex}-${groupIndex}-${subgroupIndex}`
            ] = value
            subgroupIndex += 1
          }
          groupIndex += 1
        }
        flgroupIndex += 1
      }
    },
    toggleActivitySelection(studyActivity, event) {
      if (event.target.checked) {
        this.currentSelection.push(studyActivity)
      } else {
        for (let i = 0; i < this.currentSelection.length; i++) {
          if (
            this.currentSelection[i].study_activity_uid ===
            studyActivity.study_activity_uid
          ) {
            this.currentSelection.splice(i, 1)
            break
          }
        }
      }
    },
    toggleSubgroupActivitiesSelection(flgroup, group, subgroup, event) {
      if (event.target.checked) {
        this.currentSelection = this.currentSelection.concat(
          this.activitiesStore.sortedStudyActivities[flgroup][group][subgroup]
        )
      } else {
        for (const studyActivity of this.activitiesStore.sortedStudyActivities[
          flgroup
        ][group][subgroup]) {
          const index = this.currentSelection.findIndex(
            (item) =>
              item.study_activity_uid === studyActivity.study_activity_uid
          )
          this.currentSelection.splice(index, 1)
        }
      }
    },
  },
}
</script>

<style scoped lang="scss">
table {
  width: 100%;
  text-align: left;
  border-spacing: 0px;
  border-collapse: collapse;
}
thead {
  background-color: rgb(var(--v-theme-greyBackground));
  font-weight: 600;
}
tr {
  padding: 4px;
  &.section {
    background-color: rgb(var(--v-theme-greyBackground));
    font-weight: 600;
  }
}
tbody tr {
  border-bottom: 1px solid rgb(var(--v-theme-greyBackground));
}
th {
  vertical-align: middle;
  padding-top: 16px !important;
  padding-bottom: 16px !important;
}
th,
td {
  padding: 6px;
  font-size: 14px !important;
}
.flowchart {
  background-color: rgb(var(--v-theme-dfltBackgroundLight1));
}
.group {
  background-color: rgb(var(--v-theme-dfltBackgroundLight2));
}
.subgroup {
  font-weight: 600;
  padding-left: 20px;
}
.activity {
  padding-left: 20px;
}
.text-vertical {
  text-orientation: mixed;
}
.text-strong {
  font-weight: 600;
}
</style>
