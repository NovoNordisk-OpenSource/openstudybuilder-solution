<template>
  <div class="pa-4 bg-white" style="overflow-x: auto">
    <v-skeleton-loader
      v-if="cellsLoading || armsLoading || metadataLoading"
      class="mx-auto"
      max-width="800px"
      type="table-heading, table-thead, table-tbody"
    />
    <template v-else>
      <table
        class="mt-4"
        :aria-label="$t('StudyStructureOverview.table_caption')"
      >
        <thead>
          <tr>
            <th colspan="3" scope="col" />
            <th :colspan="studyEpochs.length" scope="col">
              {{ $t('StudyStructureOverview.epochs') }}
            </th>
          </tr>
          <tr>
            <th scope="col">
              {{ $t('StudyStructureOverview.arms') }}
            </th>
            <th scope="col">
              {{ $t('StudyStructureOverview.branch_arms') }}
            </th>
            <th scope="col">
              {{ $t('StudyStructureOverview.number_of_subjects') }}
            </th>
            <td v-for="studyEpoch in visibleStudyEpochs" :key="studyEpoch.uid">
              {{ studyEpoch.epoch_name }}
            </td>
          </tr>
        </thead>
        <tbody>
          <template v-for="arm in arms">
            <template v-if="arm.arm_connected_branch_arms">
              <tr
                v-for="(branchArm, index) in arm.arm_connected_branch_arms"
                :key="branchArm.branch_arm_uid"
              >
                <td
                  v-if="index === 0"
                  :rowspan="arm.arm_connected_branch_arms.length"
                >
                  {{ arm.name }}
                </td>
                <td>
                  {{ branchArm.name }}
                </td>
                <td>{{ branchArm.number_of_subjects }}</td>
                <td
                  v-for="studyEpoch in visibleStudyEpochs"
                  :key="`${studyEpoch.uid}-${branchArm.branch_arm_uid}`"
                >
                  {{
                    getDesignCellByBranch(
                      studyEpoch.uid,
                      branchArm.branch_arm_uid
                    )
                  }}
                </td>
              </tr>
            </template>
            <template v-else>
              <tr :key="arm.arm_uid">
                <td>{{ arm.name }}</td>
                <td />
                <td>{{ arm.number_of_subjects }}</td>
                <td
                  v-for="studyEpoch in visibleStudyEpochs"
                  :key="`${studyEpoch.uid}-${arm.arm_uid}`"
                >
                  {{ getDesignCellByArm(studyEpoch.uid, arm.arm_uid) }}
                </td>
              </tr>
            </template>
          </template>
        </tbody>
      </table>
      <v-row class="mt-6">
        <v-col cols="2">
          {{ $t('StudyStructureOverview.arms_number') }}
        </v-col>
        <v-col cols="10">
          {{ arms.length }}
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="2">
          {{ $t('StudyStructureOverview.planned_subjects') }}
        </v-col>
        <v-col cols="10">
          {{ plannedNumberOfSubjects }}
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="2">
          {{ $t('StudyStructureOverview.study_design_class') }}
        </v-col>
        <v-col cols="10">
          <span v-if="metadata.trial_blinding_schema_code">{{
            metadata.trial_blinding_schema_code.name
          }}</span>
          &nbsp;<span v-if="metadata.intervention_model_code">{{
            metadata.intervention_model_code.name
          }}</span>
        </v-col>
      </v-row>
    </template>
  </div>
</template>

<script>
import arms from '@/api/arms'
import study from '@/api/study'
import visitConstants from '@/constants/visits'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useEpochsStore } from '@/stores/studies-epochs'
import { computed } from 'vue'

export default {
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    const epochsStore = useEpochsStore()

    return {
      selectedStudy: studiesGeneralStore.selectedStudy,
      studyEpochs: computed(() => epochsStore.studyEpochs),
      fetchStudyEpochs: epochsStore.fetchStudyEpochs,
    }
  },
  data() {
    return {
      arms: [],
      cells: [],
      armsLoading: false,
      cellsLoading: false,
      metadataLoading: false,
      metadata: [],
    }
  },
  computed: {
    plannedNumberOfSubjects() {
      let result = 0
      for (const arm of this.arms) {
        result += arm.number_of_subjects
      }
      return result
    },
    visibleStudyEpochs() {
      return this.studyEpochs.filter(
        (studyEpoch) => studyEpoch.epoch_name !== visitConstants.EPOCH_BASIC
      )
    },
  },
  mounted() {
    this.fetchStudyEpochs({ studyUid: this.selectedStudy.uid })
    this.cellsLoading = true
    arms.getAllStudyCells(this.selectedStudy.uid).then((resp) => {
      this.cells = resp.data
      this.cellsLoading = false
    })
    this.armsLoading = true
    const params = {
      page_size: 0,
    }
    arms.getAllForStudy(this.selectedStudy.uid, { params }).then((resp) => {
      this.arms = resp.data.items
      this.armsLoading = false
    })
    this.metadataLoading = true
    study.getStudyInterventionMetadata(this.selectedStudy.uid).then((resp) => {
      this.metadata = resp.data.current_metadata.study_intervention
      this.metadataLoading = false
    })
  },
  methods: {
    getDesignCellByBranch(studyEpochUid, branchArmUid) {
      const result = this.cells.find(
        (cell) =>
          cell.study_epoch_uid === studyEpochUid &&
          cell.study_branch_arm_uid === branchArmUid
      )
      if (result) {
        return result.study_element_name
      }
      return ''
    },
    getDesignCellByArm(studyEpochUid, armUid) {
      const result = this.cells.find(
        (cell) =>
          cell.study_epoch_uid === studyEpochUid &&
          cell.study_arm_uid === armUid
      )
      if (result) {
        return result.study_element_name
      }
      return ''
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
tr {
  padding: 4px;
}
td,
th {
  border: 1px solid black;
  padding: 4px;
}
</style>
