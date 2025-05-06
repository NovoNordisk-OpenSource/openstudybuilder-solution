<template>
  <div>
    <NNTable
      ref="table"
      :headers="headers"
      item-value="uid"
      export-object-label="Studies"
      :export-data-url="exportDataUrl"
      column-data-resource="studies"
      v-bind="$attrs"
    >
      <template #actions="">
        <v-btn
          v-if="!readOnly"
          data-cy="add-study"
          class="ml-2"
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          :title="$t('StudyForm.add_title')"
          :disabled="!accessGuard.checkPermission($roles.STUDY_WRITE)"
          icon="mdi-plus"
          @click.stop="showCreationForm = true"
        />
      </template>
      <template #[`item.brand_name`]="{ item }">
        {{ getBrandName(item) }}
      </template>
      <template
        #[`item.current_metadata.identification_metadata.study_number`]="{
          item,
        }"
      >
        {{ item.current_metadata.identification_metadata.study_number }}
      </template>
      <template
        #[`item.current_metadata.identification_metadata.study_id`]="{ item }"
      >
        <template v-if="!item.study_parent_part">
          {{ item.current_metadata.identification_metadata.study_id }}
        </template>
        <template v-else>
          {{ item.study_parent_part.study_id }}
        </template>
      </template>
      <template #[`item.sub_study_id`]="{ item }">
        <template v-if="item.study_parent_part">
          {{ item.current_metadata.identification_metadata.study_id }}
        </template>
      </template>
      <template
        #[`item.current_metadata.study_description.study_title`]="{ item }"
      >
        {{
          item.study_parent_part
            ? item.study_parent_part.study_title
            : item.current_metadata.study_description.study_title
        }}
      </template>
      <template
        #[`item.current_metadata.version_metadata.version_timestamp`]="{ item }"
      >
        {{
          $filters.date(
            item.current_metadata.version_metadata.version_timestamp
          )
        }}
      </template>
    </NNTable>
    <StudyForm
      :open="showForm"
      :edited-study="activeStudy"
      @close="closeForm"
    />
    <v-dialog
      v-model="showCreationForm"
      persistent
      fullscreen
      content-class="fullscreen-dialog"
    >
      <StudyCreationForm @close="showCreationForm = false" />
    </v-dialog>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import NNTable from '@/components/tools/NNTable.vue'
import StudyForm from '@/components/studies/StudyForm.vue'
import StudyCreationForm from '@/components/studies/StudyCreationForm.vue'
import { useI18n } from 'vue-i18n'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesManageStore } from '@/stores/studies-manage'

const props = defineProps({
  readOnly: {
    type: Boolean,
    default: false,
  },
})
const emit = defineEmits(['refreshStudies'])

const { t } = useI18n()
const accessGuard = useAccessGuard()
const studiesManageStore = useStudiesManageStore()

const headers = [
  {
    title: t('StudyTable.clinical_programme'),
    key: 'current_metadata.identification_metadata.clinical_programme_name',
  },
  {
    title: t('StudyTable.project_id'),
    key: 'current_metadata.identification_metadata.project_number',
  },
  {
    title: t('StudyTable.project_name'),
    key: 'current_metadata.identification_metadata.project_name',
  },
  { title: t('StudyTable.brand_name'), key: 'brand_name' },
  {
    title: t('StudyTable.number'),
    key: 'current_metadata.identification_metadata.study_number',
  },
  {
    title: t('StudyTable.id'),
    key: 'current_metadata.identification_metadata.study_id',
  },
  {
    title: t('StudyTable.subpart_id'),
    key: 'current_metadata.identification_metadata.subpart_id',
  },
  {
    title: t('StudyTable.sub_study_id'),
    key: 'sub_study_id',
    filteringName: 'current_metadata.identification_metadata.study_id',
  },
  {
    title: t('StudyTable.acronym'),
    key: 'current_metadata.identification_metadata.study_acronym',
  },
  {
    title: t('StudyTable.subpart_acronym'),
    key: 'current_metadata.identification_metadata.study_subpart_acronym',
  },
  {
    title: t('StudyTable.title'),
    key: 'current_metadata.study_description.study_title',
  },
  {
    title: t('_global.status'),
    key: 'current_metadata.version_metadata.study_status',
  },
  {
    title: t('_global.modified'),
    key: 'current_metadata.version_metadata.version_timestamp',
  },
  {
    title: t('_global.modified_by'),
    key: 'current_metadata.version_metadata.version_author',
  },
]

const showCreationForm = ref(false)
const showForm = ref(false)
const activeStudy = ref(null)
const table = ref()

const exportDataUrl = computed(() => {
  let result = '/studies'
  if (props.readOnly) {
    result += '?deleted=true'
  }
  return result
})

function closeForm() {
  showForm.value = false
  activeStudy.value = null
  table.value.filterTable()
  emit('refreshStudies')
}
function getBrandName(study) {
  const project = studiesManageStore.getProjectByNumber(
    study.current_metadata.identification_metadata.project_number
  )
  return project !== undefined ? project.brand_name : ''
}
</script>
