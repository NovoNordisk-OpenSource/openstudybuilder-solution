<template>
  <div>
    <p class="text-grey text-body-large font-weight-bold ml-3">
      {{ $t('DesignMatrix.matrix_guide') }}
    </p>
    <v-skeleton-loader
      v-if="!tableReady"
      class="mx-4"
      type="table-heading, table-thead, table-tbody"
    />
    <NNTable
      v-else
      table-id="studies-design-matrix-table"
      :headers="headers"
      item-value="id"
      :items-length="total"
      :export-config="{
        objectLabel: 'DesignMatrixStructure',
        dataUrl: exportDataUrl,
      }"
      disable-filtering
      :items="paginatedMatrix"
      :loading="loading"
      :history-config="{
        externalHeaders: historyHeaders,
        dataFetcher: fetchDesignCellsHistory,
        title: $t('DesignMatrix.history_title'),
      }"
      @filter="fetchStudyArms"
    >
      <template #afterSwitches>
        <v-switch
          v-model="transitionRulesMode"
          :label="$t('DesignMatrix.transition_rules')"
          class="mr-6"
          hide-details
          :title="$t('DesignMatrix.transition_rules_help')"
        />
      </template>
      <template #actions>
        <v-btn
          v-if="!editMode"
          class="ml-2"
          icon
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          :disabled="
            !accessGuard.checkPermission($roles.STUDY_WRITE) ||
            selectedStudyVersion !== null
          "
          @click.stop="edit"
        >
          <v-icon>mdi-pencil-outline</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('_global.edit') }}
          </v-tooltip>
        </v-btn>
        <v-btn
          v-if="editMode"
          color="primary"
          variant="flat"
          height="40px"
          rounded
          :title="$t('_global.save')"
          :loading="editLoading"
          @click.stop="save"
        >
          {{ $t('_global.save') }}
        </v-btn>
        <v-btn
          v-if="editMode"
          class="secondary-btn ml-2"
          color="white"
          height="40px"
          variant="outlined"
          rounded
          :title="$t('_global.cancel')"
          @click.stop="cancel"
        >
          {{ $t('_global.cancel') }}
        </v-btn>
      </template>
      <template
        v-for="header in headers"
        :key="header.key"
        #[`item.${header.key}`]="item"
      >
        <div v-if="header.key === 'arms'">
          <v-chip
            v-if="item.item.armColor"
            size="small"
            variant="flat"
            :color="item.item.armColor"
          >
          </v-chip>
          <router-link
            v-if="item.item.uid"
            :to="{
              name: 'StudyArmOverview',
              params: { study_id: selectedStudy.uid, id: item.item.uid },
            }"
          >
            {{ item.value }}
          </router-link>
          <div v-else>
            {{ item.value }}
          </div>
        </div>
        <div v-else-if="header.key === 'branches'">
          <v-chip
            v-if="item.item.branchColor"
            size="small"
            variant="flat"
            :color="item.item.branchColor"
            class="mr-1"
            density="compact"
          />
          <router-link
            v-if="item.item.id"
            :to="{
              name: 'StudyBranchArmOverview',
              params: { study_id: selectedStudy.uid, id: item.item.id },
            }"
          >
            {{ item.value }}
          </router-link>
          <div v-else>
            {{ item.value }}
          </div>
        </div>
        <ElementsDropdownList
          v-else
          :key="header.key"
          :save-object="saveObject"
          :edit-mode="editMode"
          :transition-rules-mode="transitionRulesMode"
          :cells="cells"
          :study-elements="elements"
          :epoch="header.key"
          :arm="item.item.id ? null : item.item.uid"
          :arm-branch="item.item.id"
          @add-to-object="prepareUpdateObject"
        />
      </template>
    </NNTable>
  </div>
</template>

<script setup>
import { computed, inject, ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import armsApi from '@/api/arms'
import ElementsDropdownList from '@/components/tools/ElementsDropdownList.vue'
import NNTable from '@/components/tools/NNTable.vue'
import visitConstants from '@/constants/visits'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useEpochsStore } from '@/stores/studies-epochs'
import filteringParameters from '@/utils/filteringParameters'

const notificationHub = inject('notificationHub')

const { t } = useI18n()
const studiesGeneralStore = useStudiesGeneralStore()
const epochsStore = useEpochsStore()
const accessGuard = useAccessGuard()

const studyEpochs = computed(() => epochsStore.studyEpochs)
const selectedStudy = computed(() => studiesGeneralStore.selectedStudy)
const selectedStudyVersion = computed(
  () => studiesGeneralStore.selectedStudyVersion
)

const exportDataUrl = computed(() => {
  return `studies/${studiesGeneralStore.selectedStudy.uid}/study-design-matrix-structure`
})

const fetchStudyEpochs = epochsStore.fetchStudyEpochs

const historyHeaders = [
  { title: t('_global.uid'), key: 'study_design_cell_uid' },
  { title: '#', key: 'order' },
  { title: t('DesignMatrix.epoch'), key: 'study_epoch_name' },
  { title: t('DesignMatrix.study_arm'), key: 'study_arm_name' },
  { title: t('DesignMatrix.branch'), key: 'study_branch_arm_name' },
  { title: t('DesignMatrix.element'), key: 'study_element_name' },
  { title: t('DesignMatrix.transition_rule'), key: 'transition_rule' },
]

const total = ref(0)
const arms = ref([])
const branchArms = ref({})
const elements = ref([])
const cells = ref({})
const matrix = ref([])
const paginatedMatrix = ref([])
const editMode = ref(false)
const loading = ref(true)
const updateObject = ref([])
const saveObject = ref(false)
const editLoading = ref(false)
const transitionRulesMode = ref(false)

const filteredStudyEpochs = computed(() => {
  return studyEpochs.value.filter(
    (item) => item.epoch_name !== visitConstants.EPOCH_BASIC
  )
})

const tableReady = ref(false)

const headers = computed(() => [
  { title: t('DesignMatrix.study_arm'), key: 'arms' },
  { title: t('DesignMatrix.branches'), key: 'branches' },
  ...filteredStudyEpochs.value.map((el) => ({
    title: el.epoch_name,
    key: el.uid,
    color: el.color_hash,
  })),
])

onMounted(async () => {
  try {
    await fetchStudyEpochs({ studyUid: selectedStudy.value.uid })
    await fetchStudyElements()
    cells.value = await armsApi.getAllStudyCells(selectedStudy.value.uid)
  } catch (error) {
    console.error(error)
    notificationHub.add({
      msg: t('DesignMatrix.load_error'),
      type: 'error',
      timeout: 0,
    })
  } finally {
    tableReady.value = true
  }
})

async function matrixPushCalls(matrixPushStack, params) {
  // this method is created to be sure that this.matrix is being pushed in the correct order, so the ElementsDropdownList won't have "Uncaught Promises"
  // we define the method as async
  // await for the sort to then await for each push in the correct order
  matrix.value = []
  // await for the sort
  await matrixPushStack.sort((a, b) => {
    return a.order - b.order
  })
  // await for each push in the correct order
  for (const iMatrix of matrixPushStack) {
    matrix.value.push(iMatrix)
  }
  total.value = matrix.value.length
  setPaginatedMatrix(params)
}
function setPaginatedMatrix(params) {
  paginatedMatrix.value = matrix.value.slice(
    (params.page_number - 1) *
      (params.page_size < 0 ? 99999999 : params.page_size),
    params.page_number * (params.page_size < 0 ? 99999999 : params.page_size)
  )
}
async function fetchStudyArms(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  if (matrix.value.length === 0) {
    await armsApi
      .getAllForStudy(selectedStudy.value.uid, { params })
      .then(async (resp) => {
        arms.value = resp.data.items
        matrix.value = []
        branchArms.value = {}
        for (const el of arms.value) {
          await armsApi
            .getAllBranchesForArm(selectedStudy.value.uid, el.arm_uid)
            .then((resp) => {
              branchArms.value[el.arm_uid] = resp.data
            })
        }
      })
    buildMatrix(params)
    loading.value = false
  } else {
    setPaginatedMatrix(params)
  }
}
async function buildMatrix(params) {
  const matrixPushStack = []
  for (const el of arms.value) {
    if (branchArms.value[el.arm_uid].length === 0) {
      // making a stack of what has to be pushed in this.matrix
      matrixPushStack.push({
        uid: el.arm_uid,
        arms: el.name,
        armColor: el.arm_colour,
        order: el.order,
      })
    } else {
      branchArms.value[el.arm_uid].forEach((value) => {
        // making a stack of what has to be pushed in this.matrix
        matrixPushStack.push({
          id: value.branch_arm_uid,
          uid: el.arm_uid,
          arms: el.name,
          armColor: value.arm_root.arm_colour,
          branches: value.name,
          branchColor: value.colour_code,
          order: el.order,
        })
      })
    }
  }
  // making this.matrix.push() in the right order
  matrixPushCalls(matrixPushStack, params)
}
async function fetchStudyElements() {
  const params = {
    page_size: 0,
  }
  return armsApi
    .getStudyElements(selectedStudy.value.uid, params)
    .then((resp) => {
      elements.value = resp.data.items
    })
}
function edit() {
  editMode.value = true
}
function save() {
  editLoading.value = true
  saveObject.value = true
  setTimeout(() => {
    updateObject.value = updateObject.value.filter(
      (el) => Object.keys(el).length !== 0
    )
    armsApi
      .cellsBatchUpdate(selectedStudy.value.uid, updateObject.value)
      .then((batchResponse) => {
        editLoading.value = false
        editMode.value = false
        let hasError = false
        for (const subResponse of batchResponse.data) {
          if (subResponse.response_code >= 400) {
            notificationHub.add({
              msg: subResponse.content.message,
              type: 'error',
              timeout: 0,
            })
            hasError = true
          }
        }
        armsApi.getAllStudyCells(selectedStudy.value.uid).then((resp) => {
          cells.value = resp
          if (!hasError) {
            notificationHub.add({
              msg: t('DesignMatrix.matrix_updated'),
            })
          }
          editLoading.value = false
          editMode.value = false
          updateObject.value = []
          saveObject.value = false
        })
      })
  }, 1000)
}
function prepareUpdateObject(cell) {
  updateObject.value.push(cell)
}
function cancel() {
  editMode.value = false
  buildMatrix()
}

async function fetchDesignCellsHistory() {
  const resp = await armsApi.getStudyCellsHistory(selectedStudy.value.uid)
  return resp.data.map((item) => {
    return {
      ...item,
      start_date: item.modified,
    }
  })
}
</script>
