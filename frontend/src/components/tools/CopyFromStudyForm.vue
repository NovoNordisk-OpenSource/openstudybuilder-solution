<template>
  <v-card elevation="0" rounded="xl">
    <v-card-title>
      <span class="dialog-title">{{ $t('StudyCopyForm.title') }}</span>
    </v-card-title>
    <v-divider />
    <v-card-text>
      <v-form ref="observer">
        <v-row class="mt-4">
          <v-col cols="12">
            <StudySelectorField
              v-model="study_"
              data-cy="study-id"
              :data="selectableStudies"
              :loading="loadingStudies"
            />
          </v-col>
        </v-row>
        <template v-if="study_ && params.length">
          <div class="d-flex align-center mt-4 mb-2">
            <span class="text-subtitle-1 font-weight-medium">
              {{ $t('StudyCopyForm.select_properties') }}
            </span>
            <v-chip
              size="small"
              variant="tonal"
              color="nnBaseBlue"
              class="ml-3"
            >
              {{ selectedProperties.length }} / {{ params.length }}
            </v-chip>
          </div>
          <v-data-table
            v-model="selectedProperties"
            :headers="propertyHeaders"
            :items="params"
            item-value="name"
            show-select
            hide-default-footer
            :items-per-page="-1"
            :loading="loadingPreview"
            :row-props="getRowProps"
            class="copy-table"
            data-cy="copy-properties-table"
          >
            <template #[`item.current_value`]="{ item }">
              <MetadataValueDisplay :param="item" :metadata="metadata" />
            </template>
            <template #[`item.value_to_copy`]="{ item }">
              <MetadataValueDisplay
                v-if="referenceMetadata"
                :param="item"
                :metadata="referenceMetadata"
              />
            </template>
          </v-data-table>
        </template>
      </v-form>
    </v-card-text>
    <v-divider />
    <v-card-actions>
      <v-spacer />
      <v-btn
        variant="outlined"
        rounded
        elevation="0"
        width="120px"
        @click="close"
      >
        {{ $t('_global.cancel') }}
      </v-btn>
      <v-btn
        data-cy="ok-form"
        rounded
        color="secondary"
        variant="flat"
        elevation="0"
        width="120px"
        :loading="loadingPreview || saving"
        :disabled="!selectedProperties.length"
        @click="select"
      >
        {{ $t('_global.apply') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import study from '@/api/study'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import MetadataValueDisplay from '@/components/tools/MetadataValueDisplay.vue'
import StudySelectorField from '@/components/studies/StudySelectorField.vue'
import studyMetadataForms from '@/utils/studyMetadataForms'
import { notificationHub } from '@/plugins/notificationHub'

// Per-component wiring: metadata key, GET reader and PATCH updater on the study API
const COMPONENT_CONFIG = {
  high_level_study_design: {
    key: 'high_level_study_design',
    read: 'getHighLevelStudyDesignMetadata',
    update: 'updateStudyType',
  },
  study_intervention: {
    key: 'study_intervention',
    read: 'getStudyInterventionMetadata',
    update: 'updateStudyIntervention',
  },
  study_population: {
    key: 'study_population',
    read: 'getStudyPopulationMetadata',
    update: 'updateStudyPopulation',
  },
}

const props = defineProps({
  component: {
    type: String,
    default: '',
  },
  params: {
    type: Array,
    default: () => [],
  },
  metadata: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['applied', 'close'])

const { t } = useI18n()
const studiesGeneralStore = useStudiesGeneralStore()
const selectedStudy = computed(() => studiesGeneralStore.selectedStudy)

const study_ = ref(null)
const studies = ref([])
const selectedProperties = ref([])
const referenceMetadata = ref(null)
const loadingStudies = ref(false)
const loadingPreview = ref(false)
const saving = ref(false)

const componentConfig = computed(() => COMPONENT_CONFIG[props.component])
const componentKey = computed(() => componentConfig.value?.key)

const propertyHeaders = computed(() => [
  {
    title: t('StudyCopyForm.property'),
    key: 'label',
    sortable: false,
    width: '34%',
  },
  {
    title: t('StudyCopyForm.value_to_copy'),
    key: 'value_to_copy',
    sortable: false,
  },
  {
    title: t('StudyCopyForm.current_value'),
    key: 'current_value',
    sortable: false,
  },
])

const selectableStudies = computed(() =>
  studies.value.filter((item) => item.uid !== selectedStudy.value?.uid)
)

watch(study_, (value) => {
  selectedProperties.value = []
  if (value) {
    fetchReferenceMetadata()
  } else {
    referenceMetadata.value = null
  }
})

onMounted(() => {
  loadingStudies.value = true
  study
    .getAll()
    .then((resp) => {
      studies.value = resp.data.items
    })
    .finally(() => {
      loadingStudies.value = false
    })
})

function close() {
  emit('close')
}

function getRowProps({ item }) {
  return selectedProperties.value.includes(item.name)
    ? { class: 'copy-row--selected' }
    : {}
}

function fetchReferenceMetadata() {
  if (!study_.value || !componentConfig.value) {
    return
  }
  loadingPreview.value = true
  study[componentConfig.value.read](study_.value.uid)
    .then((resp) => {
      referenceMetadata.value = resp.data.current_metadata[componentKey.value]
    })
    .finally(() => {
      loadingPreview.value = false
    })
}

function getNullValueKey(param) {
  if (param.nullValueName !== undefined) {
    return param.nullValueName
  }
  let nullValueName = param.name
  const suffixes = ['_code', '_codes']
  suffixes.forEach((suffix) => {
    if (nullValueName.endsWith(suffix)) {
      nullValueName = nullValueName.replace(suffix, '')
    }
  })
  return `${nullValueName}_null_value_code`
}

async function select() {
  if (
    !referenceMetadata.value ||
    !selectedProperties.value.length ||
    saving.value
  ) {
    return
  }
  // Build the full component payload: selected properties take the source
  // study's values, the others keep the current study's values.
  const payload = JSON.parse(JSON.stringify(props.metadata))
  props.params.forEach((param) => {
    if (selectedProperties.value.includes(param.name)) {
      payload[param.name] = referenceMetadata.value[param.name]
      const nullValueKey = getNullValueKey(param)
      payload[nullValueKey] =
        referenceMetadata.value[nullValueKey] !== undefined
          ? referenceMetadata.value[nullValueKey]
          : null
    }
  })
  // Normalize CT/dictionary term fields to the PATCH payload shape
  props.params.forEach((param) => {
    if (param.valuesDisplay === 'term') {
      payload[param.name] = studyMetadataForms.getTermPayload(
        payload,
        param.name
      )
    } else if (['terms', 'dictionaryTerms'].includes(param.valuesDisplay)) {
      payload[param.name] = studyMetadataForms.getTermsPayload(
        payload,
        param.name
      )
    }
  })
  const parentUid = selectedStudy.value.study_parent_part
    ? selectedStudy.value.study_parent_part.uid
    : null
  saving.value = true
  try {
    await study[componentConfig.value.update](
      selectedStudy.value.uid,
      payload,
      parentUid
    )
    notificationHub.add({
      msg: t('StudyCopyForm.copy_success'),
    })
    emit('applied')
    close()
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
/* Reduce the header row height */
.copy-table :deep(thead th) {
  padding-top: 5px !important;
  padding-bottom: 5px !important;
}

/* Make the "select all" checkbox readable on the header background */
.copy-table :deep(thead th .v-selection-control .v-icon) {
  color: rgb(var(--v-theme-nnBaseBlue));
}

.copy-table :deep(tr.copy-row--selected > td) {
  background-color: rgba(var(--v-theme-nnBaseBlue), 0.06);
}

.copy-table :deep(td),
.copy-table :deep(th) {
  word-break: break-word;
}
</style>
