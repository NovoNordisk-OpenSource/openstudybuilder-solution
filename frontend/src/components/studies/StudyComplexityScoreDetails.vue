<template>
  <v-card class="px-4 pb-12">
    <v-card-text v-if="showStudySelect" class="mb-0">
      <v-autocomplete
        v-model="selectedStudy"
        :items="studies"
        :item-title="(value) => getStudyLabel(value)"
        item-value="uid"
        :label="t('_global.select_study')"
        class="mx-0 mt-4 mb-0"
        return-object
      />
    </v-card-text>

    <v-card-title class="d-flex align-center">
      {{ $t('ComplexityScore.complexity_score') }}: {{ complexityScore }}
      <v-spacer />
      <v-btn v-if="showClose" icon variant="text" @click="$emit('close')">
        <v-icon>mdi-close</v-icon>
      </v-btn>
    </v-card-title>

    <v-card-text>
      <v-progress-linear v-if="loading" indeterminate color="primary" />
      <div v-else-if="details" style="width: 100%">
        <v-alert
          color="nnLightBlue200"
          density="compact"
          class="text-nnTrueBlue pl-6 mx-0 mb-6 text-body-2"
        >
          {{ $t('ComplexityScore.complexity_score_intro') }}
        </v-alert>
        <h4 class="mb-2">{{ $t('ComplexityScore.visits') }}</h4>
        <v-data-table
          :headers="visitHeaders"
          :items="visitItems"
          :items-per-page="-1"
          class="mb-8 complexity-table"
          density="compact"
          hide-default-footer
        />
        <h4 class="mb-2">{{ $t('ComplexityScore.activities') }}</h4>
        <v-data-table
          :headers="assessmentHeaders"
          :items="assessmentItems"
          :items-per-page="-1"
          class="complexity-table"
          density="compact"
          hide-default-footer
        />
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import studyApi from '@/api/study'

const props = defineProps({
  studyUid: {
    type: String,
    default: null,
  },
  showClose: {
    type: Boolean,
    default: false,
  },
  showStudySelect: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['close'])

const { t } = useI18n()
const loading = ref(false)
const details = ref(null)
const complexityScore = ref(null)
const studies = ref([])
const selectedStudy = ref(null)

const activeStudyUid = computed(() => {
  if (props.showStudySelect) {
    return selectedStudy.value?.uid || null
  }
  return props.studyUid
})

const toFixed2 = (value) => Number(value).toFixed(2)

const visitItems = computed(() =>
  (details.value?.visits || []).map((item) => ({
    ...item,
    type: t(`ComplexityScore.visit_type_${item.type}`),
    count_times_burden: parseFloat((item.count * item.burden).toFixed(2)),
  }))
)

const assessmentItems = computed(() =>
  (details.value?.assessments || []).map((item) => ({
    ...item,
    count_times_burden: parseFloat((item.count * item.burden).toFixed(2)),
  }))
)

const visitHeaders = [
  { key: 'type', title: t('_global.type') },
  { key: 'count', title: t('_global.count'), align: 'end', width: '100px' },
  {
    key: 'burden',
    title: t('ComplexityScore.burden'),
    align: 'end',
    width: '100px',
    value: (item) => toFixed2(item.burden),
  },
  {
    key: 'count_times_burden',
    title: t('ComplexityScore.count_times_burden'),
    align: 'end',
    width: '160px',
    value: (item) => toFixed2(item.count_times_burden),
  },
]

const assessmentHeaders = [
  { key: 'type', title: t('ComplexityScore.activity_subgroup') },
  { key: 'count', title: t('_global.count'), align: 'end', width: '100px' },
  {
    key: 'burden',
    title: t('ComplexityScore.burden'),
    align: 'end',
    width: '100px',
    value: (item) => toFixed2(item.burden),
  },
  {
    key: 'count_times_burden',
    title: t('ComplexityScore.count_times_burden'),
    align: 'end',
    width: '160px',
    value: (item) => toFixed2(item.count_times_burden),
  },
]

loadDetails()

if (props.showStudySelect) {
  studyApi.getAllList().then((resp) => {
    studies.value = resp.data
    selectedStudy.value = studies.value[0] || null
  })
}

watch(activeStudyUid, (uid) => {
  if (uid) {
    loadDetails()
  } else {
    details.value = null
    complexityScore.value = null
  }
})

function getStudyLabel(study) {
  const id =
    study?.id || study?.current_metadata?.identification_metadata?.study_id
  const acronym =
    study?.acronym ||
    study?.current_metadata?.identification_metadata?.study_acronym
  if (id && acronym) {
    return `${id} (${acronym})`
  } else if (id) {
    return id
  } else if (acronym) {
    return acronym
  }
}

function loadDetails() {
  const uid = activeStudyUid.value
  if (!uid) return
  loading.value = true
  studyApi.getComplexityScoreDetails(uid).then((resp) => {
    details.value = resp.data
    loading.value = false
  })
  studyApi.getComplexityScore(uid).then((resp) => {
    complexityScore.value = toFixed2(resp.data)
  })
}
</script>

<style lang="scss" scoped>
.complexity-table :deep(thead th) {
  padding-top: 2px !important;
  padding-bottom: 2px !important;
  height: 40px !important;
}
</style>
