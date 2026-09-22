<template>
  <div class="pa-4 bg-white" style="overflow-x: auto">
    <v-skeleton-loader
      v-if="cellsLoading || armsLoading"
      class="mx-auto"
      max-width="800px"
      type="table-heading, table-thead, table-tbody"
    />
    <template v-else>
      <v-sheet
        :elevation="4"
        :height="200"
        class="pa-5 text-nn-blue"
        border
        rounded="lg"
      >
        <v-row>
          <v-col>
            <div class="text-body-large line-height-125">
              {{ $t('StudyStructureOverview.arms_number') }}
            </div>
            <div class="text-headline-small font-weight-bold mt-1">
              {{ arms.length }}
            </div>
          </v-col>
          <v-col>
            <div class="text-body-large line-height-125">
              {{ $t('StudyStructureOverview.number_branches') }}
            </div>
            <div class="text-headline-small font-weight-bold mt-1">
              {{ branches.length }}
            </div>
          </v-col>
          <v-col>
            <div class="text-body-large line-height-125">
              {{ $t('StudyStructureOverview.number_cohorts') }}
            </div>
            <div class="text-headline-small font-weight-bold mt-1">
              {{ cohorts.length }}
            </div>
          </v-col>
          <v-col>
            <div class="text-body-large line-height-125">
              {{ $t('StudyStructureOverview.planned_subjects') }}
            </div>
            <div class="text-headline-small font-weight-bold mt-1">
              {{ plannedNumberOfSubjects }}
            </div>
          </v-col>
          <v-col>
            <div class="text-body-large line-height-125">
              {{ $t('StudyStructureOverview.number_elements') }}
            </div>
            <div class="text-headline-small font-weight-bold mt-1">
              {{ cells.length }}
            </div>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="4">
            <div class="text-body-large line-height-125">
              {{ $t('StudyStructureOverview.study_design_class') }}
            </div>
            <div class="text-headline-small font-weight-bold mt-1">
              {{ designClass }}
            </div>
          </v-col>
          <v-col v-if="sourceVariable?.source_variable" cols="2">
            <div class="text-body-large line-height-125">
              {{ $t('StudyStructureOverview.source_var') }}
            </div>
            <div class="text-headline-small font-weight-bold mt-1">
              {{ sourceVariable.source_variable }}
            </div>
          </v-col>
          <v-col v-if="sourceVariable?.source_variable">
            <div class="text-body-large line-height-125">
              {{ $t('StudyStructureOverview.source_var_desc') }}
            </div>
            <div class="text-headline-small font-weight-bold mt-1">
              {{ sourceVariable.source_variable_description }}
            </div>
          </v-col>
        </v-row>
      </v-sheet>
      <table
        class="mt-4"
        :aria-label="$t('StudyStructureOverview.table_caption')"
      >
        <thead>
          <tr>
            <th colspan="3" scope="col" style="color: white">
              {{ $t('StudyStructureOverview.study_structure') }}
            </th>
            <th
              v-if="studyEpochs.length > 0"
              :colspan="studyEpochs.length"
              scope="col"
              style="color: white"
            >
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
              {{ $t('StudyStructureOverview.cohorts') }}
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
                  <div class="text-body-large line-height-125">
                    {{ arm.name }}
                  </div>
                  <div class="text-body-medium text-gray">
                    {{ arm.number_of_subjects }}
                    {{ $t('StudyStructureOverview.subjects') }}
                  </div>
                </td>
                <td>
                  <div class="text-body-large line-height-125">
                    {{ branchArm.name }}
                  </div>
                  <div class="text-body-medium text-gray">
                    {{
                      branchArm.number_of_subjects
                        ? branchArm.number_of_subjects
                        : 0
                    }}
                    {{ $t('StudyStructureOverview.subjects') }}
                  </div>
                </td>
                <td>
                  <div class="text-body-large line-height-125">
                    {{ getCohortByBranch(branchArm.branch_arm_uid).name }}
                  </div>
                  <div class="text-body-medium text-gray">
                    {{ getCohortByBranch(branchArm.branch_arm_uid).subjects }}
                  </div>
                </td>
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
                <td>
                  <div class="text-body-large line-height-125">
                    {{ arm.name }}
                  </div>
                  <div class="text-body-medium text-gray">
                    {{ arm.number_of_subjects }}
                    {{ $t('StudyStructureOverview.subjects') }}
                  </div>
                </td>
                <td />
                <td />
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
    </template>
  </div>
</template>

<script setup>
import armsApi from '@/api/arms'
import cohortsApi from '@/api/cohorts'
import visitConstants from '@/constants/visits'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useEpochsStore } from '@/stores/studies-epochs'
import { onMounted, ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const studiesGeneralStore = useStudiesGeneralStore()
const epochsStore = useEpochsStore()

const arms = ref([])
const branches = ref([])
const cells = ref([])
const armsLoading = ref(false)
const cellsLoading = ref(false)
const cohorts = ref([])
const designClass = ref('')
const sourceVariable = ref({})

const studyEpochs = computed(() => {
  return epochsStore.studyEpochs
})
const plannedNumberOfSubjects = computed(() => {
  let result = 0
  for (const arm of arms.value) {
    result += arm.number_of_subjects
  }
  return result
})
const visibleStudyEpochs = computed(() => {
  return studyEpochs.value.filter(
    (studyEpoch) => studyEpoch.epoch_name !== visitConstants.EPOCH_BASIC
  )
})

onMounted(() => {
  try {
    epochsStore.fetchStudyEpochs({
      studyUid: studiesGeneralStore.selectedStudy.uid,
    })
    cellsLoading.value = true
    armsApi
      .getAllStudyCells(studiesGeneralStore.selectedStudy.uid)
      .then((resp) => {
        cells.value = resp.data
        cellsLoading.value = false
      })
    armsLoading.value = true
    const params = {
      page_size: 0,
    }
    armsApi
      .getAllForStudy(studiesGeneralStore.selectedStudy.uid, { params })
      .then((resp) => {
        arms.value = resp.data.items
        arms.value.forEach((arm) => {
          if (arm.arm_connected_branch_arms) {
            branches.value = [
              ...branches.value,
              ...arm.arm_connected_branch_arms,
            ]
          }
        })
        armsLoading.value = false
      })
    armsApi
      .getAllCohorts(studiesGeneralStore.selectedStudy.uid, params)
      .then((resp) => {
        cohorts.value = resp.data.items
      })
    cohortsApi
      .getStudyDesignClass(studiesGeneralStore.selectedStudy.uid)
      .then((resp) => {
        designClass.value = resp.data.value
      })
      .catch((error) => {
        if (error.response.status === 404) {
          console.error(error)
        }
      })
    cohortsApi
      .getSourceVariable(studiesGeneralStore.selectedStudy.uid)
      .then((resp) => {
        if (resp.data) {
          sourceVariable.value = resp.data
        }
      })
  } catch (error) {
    console.error(error)
  }
})

function getDesignCellByBranch(studyEpochUid, branchArmUid) {
  try {
    const result = cells.value.find(
      (cell) =>
        cell.study_epoch_uid === studyEpochUid &&
        cell.study_branch_arm_uid === branchArmUid
    )
    if (result) {
      return result.study_element_name
    }
    return ''
  } catch (error) {
    console.error(error)
  }
}

function getDesignCellByArm(studyEpochUid, armUid) {
  try {
    const result = cells.value.find(
      (cell) =>
        cell.study_epoch_uid === studyEpochUid && cell.study_arm_uid === armUid
    )
    if (result) {
      return result.study_element_name
    }
    return ''
  } catch (error) {
    console.error(error)
  }
}

function getCohortByBranch(branchUid) {
  try {
    for (const cohort of cohorts.value) {
      if (
        cohort.arm_roots?.length > 0 &&
        cohort.branch_arm_roots?.some(
          (branch) => branch.branch_arm_uid === branchUid
        )
      ) {
        return {
          name: cohort.name,
          subjects:
            cohort.number_of_subjects +
            t('StudyStructureOverview.total_subjects'),
        }
      }
    }
    return ''
  } catch (error) {
    console.error(error)
  }
}
</script>

<style scoped lang="scss">
table {
  width: 100%;
  text-align: left;
  border-spacing: 0px;
  border-collapse: separate;
  overflow: hidden;
}
tr {
  padding: 4px;
}
td,
th {
  border: 1px solid gray;
  border-top: none;
  padding-inline: 20px;
  padding-block: 6px;
  color: rgb(var(--v-theme-nnTrueBlue));
}
table {
  border-collapse: separate;
  border: solid gray 1px;
  border-radius: 10px;
}

td:last-child,
th:last-child {
  border-right: none;
}
thead > tr {
  background-color: rgb(var(--v-theme-nnBaseLight));
  color: rgb(var(--v-theme-nnTrueBlue));
  font-weight: 700;
}
thead > tr:first-of-type {
  background-color: rgb(var(--v-theme-nnTrueBlue));
}
.line-height-125 {
  line-height: 1.25;
}
</style>
