<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('StudyManageView.title') }}
      <HelpButton :help-text="$t('_help.SelectOrAddStudyTable.general')" />
    </div>
    <NavigationTabs :tabs="tabs" :breadcrumbs-level="2">
      <template #default="{ tabKeys }">
        <v-window-item :key="`active-${tabKeys.active}`" value="active">
          <StudyTable
            key="activeStudiesTable"
            :items="activeStudies"
            :items-length="totalActiveStudies"
            @filter="fetchActiveStudies"
            @refresh-studies="activeStudiesTable.filterTable()"
          />
        </v-window-item>
        <v-window-item :key="`deleted-${tabKeys.deleted}`" value="deleted">
          <StudyTable
            key="deletedStudies"
            :items="deletedStudies"
            :items-length="totalDeletedStudies"
            read-only
            @filter="fetchDeletedStudies"
          />
        </v-window-item>
      </template>
    </NavigationTabs>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import api from '@/api/study'
import _isEmpty from 'lodash/isEmpty'
import filteringParameters from '@/utils/filteringParameters'
import StudyTable from '@/components/studies/StudyTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'
import NavigationTabs from '@/components/tools/NavigationTabs.vue'
import { useStudiesManageStore } from '@/stores/studies-manage'
import { useI18n } from 'vue-i18n'

const studiesManageStore = useStudiesManageStore()
const { t } = useI18n()

const activeStudies = ref([])
const activeOptions = ref({})
const deletedStudies = ref([])
const deletedOptions = ref({})
const totalActiveStudies = ref(0)
const totalDeletedStudies = ref(0)
const savedFilters = ref('')

const activeStudiesTable = ref()

const tabs = [
  { tab: 'active', name: t('SelectOrAddStudyTable.tab1_title') },
  { tab: 'deleted', name: t('SelectOrAddStudyTable.tab2_title') },
]

watch(activeOptions, () => {
  fetchActiveStudies()
})
watch(deletedOptions, () => {
  fetchDeletedStudies()
})

function fetchActiveStudies(filters, options, filtersUpdated) {
  if (filters) {
    savedFilters.value = filters
  }
  const params = filteringParameters.prepareParameters(
    options,
    savedFilters.value,
    filtersUpdated
  )
  if (options.sortBy && _isEmpty(options.sortBy)) {
    params.sort_by = JSON.stringify({
      'current_metadata.identification_metadata.study_id': true,
    })
  }
  api.get(params).then((resp) => {
    activeStudies.value = resp.data.items
    totalActiveStudies.value = resp.data.total
  })
}

function fetchDeletedStudies(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  params.deleted = true
  api.get(params).then((resp) => {
    deletedStudies.value = resp.data.items
    totalDeletedStudies.value = resp.data.total
  })
}
function initialSortByDate() {
  activeOptions.value.sortBy = [
    'current_metadata.version_metadata.version_timestamp',
  ]
  activeOptions.value.sortDesc = [true]
}

studiesManageStore.fetchProjects()
initialSortByDate()
</script>
