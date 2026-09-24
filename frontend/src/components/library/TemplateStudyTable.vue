<template>
  <div>
    <div class="d-flex align-center mb-4">
      <span class="text-subtitle-1 font-weight-medium">
        {{ $t('TemplateStudy.current_template') }}
      </span>
      <v-chip
        v-if="selectedStudy"
        color="success"
        variant="tonal"
        class="ml-2"
        prepend-icon="mdi-check-circle-outline"
      >
        {{ selectedStudy.id }}
      </v-chip>
      <v-chip v-else variant="tonal" class="ml-2">
        {{ $t('_global.none') }}
      </v-chip>
      <v-btn
        color="nnAlertRed"
        variant="flat"
        size="small"
        rounded
        class="ml-2"
        :disabled="!accessGuard.checkPermission($roles.LIBRARY_WRITE)"
        @click="resetTemplate"
      >
        {{ $t('TemplateStudy.reset') }}
      </v-btn>
    </div>
    <NNTable
      ref="table"
      table-id="library-template-studies-table"
      :headers="headers"
      item-value="uid"
      hide-search-field
      disable-filtering
      :modifiable-table="false"
      modify-only-columns
      hide-default-switches
      column-data-resource="studies"
      v-bind="$attrs"
      hide-export-button
      :items-length="total"
      :items="filteredStudies"
      :loading="loading"
      @filter="fetchStudies"
    >
      <template #bottom></template>
      <template #beforeSwitches="">
        <v-text-field
          v-model="searchString"
          clearable
          clear-icon="mdi-close"
          prepend-inner-icon="mdi-magnify"
          :label="$t('_global.search')"
          single-line
          color="nnBaseBlue"
          hide-details
          style="min-width: 240px; max-width: 300px"
          class="searchFieldLabel ml-0"
          data-cy="search-field"
        />
      </template>
      <template #[`item.actions`]="{ item }">
        <v-icon
          v-if="item.uid === selectedTemplateStudy?.study_uid"
          icon="mdi-check-circle-outline"
          color="success"
        />
        <v-btn
          v-else
          icon="mdi-check-circle-outline"
          :loading="item.loading"
          size="small"
          variant="flat"
          :title="$t('_global.select_study')"
          :disabled="!accessGuard.checkPermission($roles.LIBRARY_WRITE)"
          @click="selectStudy(item)"
        />
      </template>
      <template #[`item.version_status`]="{ item }">
        <StatusChip :status="item.version_status" />
      </template>
    </NNTable>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, watch } from 'vue'
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import api from '@/api/study'
import studyTemplateApi from '@/api/studyTemplate'
import { useI18n } from 'vue-i18n'
import { useAccessGuard } from '@/composables/accessGuard'

const { t } = useI18n()
const accessGuard = useAccessGuard()

const studies = ref([])
const filteredStudies = ref([])
const total = ref(0)
const selectedTemplateStudy = ref({})
const loading = ref(false)
const searchString = ref('')

const selectedStudy = computed(() =>
  studies.value.find((s) => s.uid === selectedTemplateStudy?.value?.study_uid)
)

const headers = [
  {
    title: '',
    key: 'actions',
    cellProps: {
      class: 'text-center',
    },
  },
  {
    title: t('StudyTable.clinical_programme'),
    key: 'clinical_programme_name',
  },
  {
    title: t('StudyTable.project_id'),
    key: 'project_number',
  },
  {
    title: t('StudyTable.project_name'),
    key: 'project_name',
  },
  {
    title: t('StudyTable.number'),
    key: 'number',
  },
  {
    title: t('StudyTable.id'),
    key: 'id',
  },
  {
    title: t('StudyTable.study_id'),
    key: 'main_id',
  },
  {
    title: t('StudyTable.acronym'),
    key: 'acronym',
  },
  {
    title: t('StudyTable.title'),
    key: 'title',
  },
  {
    title: t('StudyTable.lts_version'),
    key: 'version_number',
  },
  {
    title: t('_global.status'),
    key: 'version_status',
  },
]

onMounted(() => {
  studyTemplateApi.getStudyTemplate().then((resp) => {
    selectedTemplateStudy.value = resp.data
  })
})

watch(searchString, () => {
  fetchStudies()
})

async function fetchStudies() {
  try {
    if (studies.value.length === 0) {
      const resp = await api.getAllList()
      const filtered = resp.data.filter(
        (s) => s.version_status !== 'DRAFT' && s.subpart_id == null
      )
      studies.value = filtered
      total.value = filtered.length
    }
    filteredStudies.value = studies.value
    handleSearching()
  } catch (error) {
    console.error(error)
  }
}

function handleSearching() {
  if (searchString.value?.length >= 3) {
    filteredStudies.value = filteredStudies.value.filter((obj) =>
      Object.values(obj).some((value) =>
        String(value).toLowerCase().includes(searchString.value.toLowerCase())
      )
    )
    total.value = filteredStudies.value.length
  }
}

function selectStudy(study) {
  study.loading = true
  if (
    selectedTemplateStudy?.value?.study_uid !== null &&
    selectedTemplateStudy?.value?.study_uid !== undefined
  ) {
    studyTemplateApi
      .updateStudyTemplate({
        study_uid: study.uid,
        study_value_version: study.version_number,
        change_description: 'Change the selected template study or version',
      })
      .then(() => {
        selectedTemplateStudy.value.study_uid = study.uid
      })
      .finally(() => {
        study.loading = false
      })
  } else {
    studyTemplateApi
      .setStudyTemplate({
        study_uid: study.uid,
        study_value_version: study.version_number,
      })
      .then(() => {
        selectedTemplateStudy.value = { study_uid: study.uid }
      })
      .finally(() => {
        study.loading = false
      })
  }
}

function resetTemplate() {
  if (selectedTemplateStudy?.value?.study_uid) {
    studyTemplateApi
      .updateStudyTemplate({
        study_uid: '',
        study_value_version: '',
        change_description: 'Reset the selected template study',
      })
      .then(() => {
        selectedTemplateStudy.value.study_uid = ''
      })
  }
}
</script>
