<template>
  <div>
    <NNTable
      ref="table"
      table-id="studies-list-table"
      :headers="headers"
      item-value="uid"
      hide-search-field
      disable-filtering
      :modifiable-table="false"
      modify-only-columns
      column-data-resource="studies"
      v-bind="$attrs"
      :export-config="{ objectLabel: 'Studies', dataUrl: exportDataUrl }"
      @custom-sort="sort"
    >
      <template #beforeSearch>
        <slot name="customSearch" />
      </template>
      <template #customFiltering>
        <slot name="customFiltering" />
      </template>
      <template #actions="">
        <v-btn
          v-if="!readOnly"
          data-cy="add-study"
          class="ml-2"
          icon
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          :disabled="!accessGuard.checkPermission($roles.STUDY_WRITE)"
          @click.stop="showCreationForm = true"
        >
          <v-icon>mdi-plus</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('StudyForm.add_title') }}
          </v-tooltip>
        </v-btn>
        <v-btn
          class="ml-2"
          icon
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          @click="emit('enableFiltering')"
        >
          <v-icon>mdi-filter-outline</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('NNTableTooltips.filters') }}
          </v-tooltip>
        </v-btn>
      </template>
      <template #[`item.actions`]="{ item }">
        <v-icon
          v-if="item.uid === selectedStudyUid"
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
          @click="selectStudy(item, true)"
        />
      </template>
      <template #[`item.version_start_date`]="{ item }">
        <v-tooltip location="top">
          <template #activator="{ props }">
            <span v-bind="props">{{
              $filters.dateRelative(item.version_start_date)
            }}</span>
          </template>
          {{ $filters.date(item.version_start_date) }}
        </v-tooltip>
      </template>
      <template #[`item.latest_locked_version`]="{ item }">
        <div class="d-flex">
          <div class="version-chip">
            {{
              item.latest_locked_version?.substring(
                0,
                item.latest_locked_version.indexOf(' ')
              )
            }}
          </div>
          <v-tooltip
            v-if="item.latest_locked_version?.length > 60"
            location="top"
          >
            <template #activator="{ props }">
              <span v-bind="props">{{
                item.latest_locked_version.substring(
                  item.latest_locked_version.indexOf(' '),
                  60
                ) + '...'
              }}</span>
            </template>
            <span>{{ item.latest_locked_version }}</span>
          </v-tooltip>
          <div v-else>
            {{
              item.latest_locked_version?.substring(
                item.latest_locked_version.indexOf(' ')
              )
            }}
          </div>
        </div>
      </template>
      <template #[`item.latest_released_version`]="{ item }">
        <div class="d-flex">
          <div class="version-chip">
            {{
              item.latest_released_version?.substring(
                0,
                item.latest_released_version.indexOf(' ')
              )
            }}
          </div>
          <v-tooltip
            v-if="item.latest_released_version?.length > 60"
            location="top"
          >
            <template #activator="{ props }">
              <span v-bind="props">{{
                item.latest_released_version?.substring(
                  item.latest_released_version.indexOf(' '),
                  60
                ) + '...'
              }}</span>
            </template>
            <span>{{ item.latest_released_version }}</span>
          </v-tooltip>
          <div v-else>
            {{
              item.latest_released_version?.substring(
                item.latest_released_version.indexOf(' ')
              )
            }}
          </div>
        </div>
      </template>
      <template #[`item.data_completeness_tags`]="{ item }">
        <div class="d-flex">
          <div
            v-for="tag in item.data_completeness_tags"
            :key="tag"
            class="version-chip"
            style="white-space: nowrap"
          >
            {{ tag }}
          </div>
        </div>
      </template>
      <template #[`item.version_status`]="{ item }">
        <StatusChip :status="item.version_status" />
      </template>
    </NNTable>
    <StudyForm
      :open="showForm"
      :edited-study="activeStudy"
      @close="closeForms"
    />
    <v-dialog
      v-model="showCreationForm"
      persistent
      fullscreen
      content-class="fullscreen-dialog"
    >
      <StudyCreationForm @close="closeForms" />
    </v-dialog>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import NNTable from '@/components/tools/NNTable.vue'
import StudyForm from '@/components/studies/StudyForm.vue'
import StudyCreationForm from '@/components/studies/StudyCreationForm.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import api from '@/api/study'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useI18n } from 'vue-i18n'
import { useAccessGuard } from '@/composables/accessGuard'

const props = defineProps({
  readOnly: {
    type: Boolean,
    default: false,
  },
})
const emit = defineEmits(['refreshStudies', 'enableFiltering', 'sort'])

const { t } = useI18n()
const accessGuard = useAccessGuard()
const studiesGeneralStore = useStudiesGeneralStore()

const selectedStudyUid = computed(() => studiesGeneralStore.selectedStudyUid)

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
    title: t('StudyTable.main_id'),
    key: 'main_id',
  },
  {
    title: t('StudyTable.subpart_id'),
    key: 'subpart_id',
  },
  {
    title: t('StudyTable.acronym'),
    key: 'acronym',
  },
  {
    title: t('StudyTable.subpart_acronym'),
    key: 'subpart_acronym',
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
    title: t('StudyTable.lts_locked_ver'),
    key: 'latest_locked_version',
  },
  {
    title: t('StudyTable.lts_released_ver'),
    key: 'latest_released_version',
  },
  {
    title: t('StudyTable.data_completeness'),
    key: 'data_completeness_tags',
  },
  {
    title: t('_global.status'),
    key: 'version_status',
  },
  {
    title: t('_global.modified'),
    key: 'version_start_date',
  },
  {
    title: t('_global.modified_by'),
    key: 'version_author',
  },
]

const showCreationForm = ref(false)
const showForm = ref(false)
const activeStudy = ref(null)
const table = ref()

const exportDataUrl = computed(() => {
  let result = '/studies/list?minimal_response=false'
  if (props.readOnly) {
    result += '&deleted=true'
  }
  return result
})

async function selectStudy(study) {
  study.loading = true
  let resp
  resp = await api.getStudy(study.uid, true)
  await studiesGeneralStore.selectStudy(resp.data, true)
  study.loading = false
}

function sort(data) {
  emit('sort', data)
}

function closeForms() {
  showForm.value = false
  showCreationForm.value = false
  activeStudy.value = null
  table.value.filterTable()
  emit('refreshStudies')
}

function filter() {
  table.value.filterTable()
}

defineExpose({ filter })
</script>
<style lang="css" scoped>
.version-chip {
  background-color: aliceblue;
  width: fit-content;
  height: fit-content;
  padding-inline: 10px;
  border-radius: 8px;
  margin-right: 5px;
}
</style>
