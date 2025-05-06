<template>
  <div>
    <v-row>
      <v-col cols="5">
        <v-select
          v-model="selected"
          :items="items"
          :label="$t('_global.select')"
          item-title="title"
          item-value="value"
          density="compact"
          data-cy="select-specification"
          multiple
          variant="outlined"
          color="nnBaseBlue"
          bg-color="nnWhite"
          hide-details
          single-line
          return-object
          class="mt-4 ml-4 mb-4"
        >
          <template #prepend-item>
            <v-list-item :title="$t('_global.view_all')" @click="toggle">
              <template #prepend>
                <v-checkbox-btn :model-value="selectAll" />
              </template>
            </v-list-item>
          </template>
        </v-select>
      </v-col>
      <v-spacer />
      <v-btn
        rounded="xl"
        size="large"
        class="mt-10 mr-10 text-none"
        color="nnBaseBlue"
        prepend-icon="mdi-download-outline"
        data-cy="export-xml-pharma-cm"
        :loading="downloadLoading"
        @click="getPharmaCmXml"
      >
        {{ $t('StudyDisclosure.download_xml') }}
      </v-btn>
    </v-row>
    <div v-for="i of selected" :key="i.value">
      <div class="page-title ml-4">
        {{ i.title }}
      </div>
      <div v-if="i.value === 'arms'" class="text-h6 font-weight-bold ml-4 mb-1">
        {{ $t('StudyDisclosure.intervention_type') }}:
        {{ data.intervention_type }}
      </div>
      <v-data-table
        :headers="dataArray[i.index].headers"
        :items="dataArray[i.index].data"
        :loading="loading"
        data-cy="data-table"
        class="table mb-4 ml-4 mr-4"
      >
        <template #bottom />
      </v-data-table>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import study from '@/api/study'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import exportLoader from '@/utils/exportLoader'

const studiesGeneralStore = useStudiesGeneralStore()

const { t } = useI18n()
const items = ref([
  { title: t('StudyDisclosure.table_1'), value: 'identification', index: 0 },
  { title: t('StudyDisclosure.table_2'), value: 'secondary_ids', index: 1 },
  { title: t('StudyDisclosure.table_8'), value: 'conditions', index: 6 },
  { title: t('StudyDisclosure.table_4'), value: 'design', index: 2 },
  { title: t('StudyDisclosure.table_5'), value: 'arms', index: 3 },
  { title: t('StudyDisclosure.table_6'), value: 'measures', index: 4 },
])
const selected = ref([])
const data = ref({})
const dataArray = ref([])
const loading = ref(false)
const downloadLoading = ref(false)
const defaultHeaders = [
  { title: t('StudyDisclosure.sb_term'), key: 'sbLabel' },
  { title: t('StudyDisclosure.pharma_term'), key: 'pharmaLabel' },
  { title: t('_global.values'), key: 'value' },
]
const idsHeaders = [
  { title: t('StudyDisclosure.secondary_id'), key: 'secondary_id' },
  { title: t('StudyDisclosure.secondary_id_type'), key: 'id_type' },
  { title: t('StudyDisclosure.registry_id'), key: 'description' },
]
const armsHeaders = [
  { title: t('StudyDisclosure.arm_title'), key: 'arm_title' },
  { title: t('_global.type'), key: 'arm_type' },
  { title: t('_global.description'), key: 'arm_description' },
]
const measuresHeaders = [
  { title: t('StudyDisclosure.outcome_measure'), key: 'title' },
  { title: t('StudyDisclosure.timeframe'), key: 'timeframe' },
  { title: t('_global.description'), key: 'description' },
]
const eligibilityHeaders = [
  { title: t('_global.title'), key: 'title' },
  { title: t('_global.values'), key: 'value' },
]

const identificationParams = ref([
  {
    sbLabel: t('StudyDisclosure.study_id'),
    pharmaLabel: t('StudyDisclosure.unique_id'),
    value: 'unique_protocol_identification_number',
  },
  {
    sbLabel: t('StudyDisclosure.short_title'),
    pharmaLabel: t('StudyDisclosure.brief_title'),
    value: 'brief_title',
  },
  {
    sbLabel: t('StudyDisclosure.study_acronym'),
    pharmaLabel: t('StudyDisclosure.acronym'),
    value: 'acronym',
  },
  {
    sbLabel: t('StudyDisclosure.study_title'),
    pharmaLabel: t('StudyDisclosure.official_title'),
    value: 'official_title',
  },
])

const conditionsParams = ref([
  {
    sbLabel: t('StudyDisclosure.indication_dict'),
    pharmaLabel: t('StudyDisclosure.studied_trial'),
    value: 'unique_protocol_identification_number',
  },
])

const designParams = ref([
  {
    sbLabel: t('StudyDisclosure.study_type'),
    pharmaLabel: t('StudyDisclosure.study_type'),
    value: 'study_type',
  },
  {
    sbLabel: t('StudyDisclosure.intent_type'),
    pharmaLabel: t('StudyDisclosure.primary_purpose'),
    value: 'primary_purpose',
  },
  {
    sbLabel: t('StudyDisclosure.study_phase_class'),
    pharmaLabel: t('StudyDisclosure.study_phase'),
    value: 'study_phase',
  },
  {
    sbLabel: t('StudyDisclosure.intervention_model'),
    pharmaLabel: t('StudyDisclosure.intervention_study_model'),
    value: 'interventional_study_model',
  },
  {
    sbLabel: t('StudyDisclosure.arms_num'),
    pharmaLabel: t('StudyDisclosure.arms_num'),
    value: 'number_of_arms',
  },
  {
    sbLabel: t('StudyDisclosure.study_randomised'),
    pharmaLabel: t('StudyDisclosure.allocation'),
    value: 'allocation',
  },
])

const eligibilityParams = ref([
  {
    title: t('StudyDisclosure.min_age'),
    value: 'minimum_age',
  },
  {
    title: t('StudyDisclosure.max_age'),
    value: 'maximum_age',
  },
  {
    title: t('StudyDisclosure.healthy_volunteers'),
    value: 'accepts_healthy_volunteers',
  },
  {
    title: t('StudyDisclosure.inc_criteria'),
    value: 'inclusion_criteria',
  },
  {
    title: t('StudyDisclosure.exc_criteria'),
    value: 'exclusion_criteria',
  },
])

const selectAll = computed(() => {
  return selected.value.length === items.value.length
})

onMounted(() => {
  selected.value = items.value
  getPharmaCm()
})

function toggle() {
  if (selectAll.value) {
    selected.value = []
  } else {
    selected.value = items.value.slice()
  }
}

function getPharmaCm() {
  loading.value = true
  study.getPharmaCm(studiesGeneralStore.selectedStudy.uid).then((resp) => {
    data.value = resp.data
    setTableData()
  })
}

function getPharmaCmXml() {
  downloadLoading.value = true
  study.getPharmaCmXml(studiesGeneralStore.selectedStudy.uid).then((resp) => {
    exportLoader.downloadFile(
      resp.data,
      'text/xml',
      t('StudyDisclosure.study_disclosure') +
        ' ' +
        studiesGeneralStore.selectedStudy.current_metadata
          .identification_metadata.study_id
    )
    downloadLoading.value = false
  })
}

function setTableData() {
  setParams(identificationParams.value)
  setParams(designParams.value)
  setParams(eligibilityParams.value)
  conditionsParams.value[0].value =
    data.value.primary_disease_or_condition_being_studied.join(', ')

  dataArray.value[0] = {
    data: identificationParams.value,
    headers: defaultHeaders,
  }
  dataArray.value[1] = { data: data.value.secondary_ids, headers: idsHeaders }
  dataArray.value[2] = { data: designParams.value, headers: defaultHeaders }
  dataArray.value[3] = { data: data.value.study_arms, headers: armsHeaders }
  dataArray.value[4] = {
    data: data.value.outcome_measures,
    headers: measuresHeaders,
  }
  dataArray.value[5] = {
    data: eligibilityParams.value,
    headers: eligibilityHeaders,
  }
  dataArray.value[6] = { data: conditionsParams.value, headers: defaultHeaders }

  loading.value = false
}

function setParams(params) {
  params.forEach((param, index) => {
    if (
      data.value[param.value] &&
      typeof data.value[param.value] === 'object'
    ) {
      params[index].value = data.value[param.value].join(', ')
    } else {
      params[index].value = data.value[param.value]
    }
  })
}
</script>
<style>
.table {
  width: auto !important;
}
</style>
