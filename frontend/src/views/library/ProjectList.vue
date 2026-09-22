<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('ProjectsView.title') }}
    </div>
    <NNTable
      ref="table"
      table-id="library-projects-table"
      :headers="headers"
      :items="items"
      :items-length="total"
      hide-default-switches
      column-data-resource="projects"
      item-value="project_number"
      :export-config="{ objectLabel: 'Projects', dataUrl: 'projects' }"
      @filter="fetchProjects"
    >
      <template #actions="">
        <slot name="extraActions" />
        <v-btn
          class="ml-2"
          icon
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          data-cy="add-project"
          @click.stop="showForm"
        >
          <v-icon>mdi-plus</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('ProjectForm.add_title') }}
          </v-tooltip>
        </v-btn>
      </template>
      <template #[`item.actions`]="{ item }">
        <ActionsMenu :actions="actions" :item="item" />
      </template>
    </NNTable>
    <ProjectForm
      :open="showProjectForm"
      :project-uid="selectedProject ? selectedProject.uid : ''"
      @reload="table.filterTable()"
      @close="closeForm"
    />
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  </div>
</template>

<script setup>
import { inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import NNTable from '@/components/tools/NNTable.vue'
import projects from '@/api/projects'
import ProjectForm from '@/components/library/ProjectForm.vue'
import filteringParameters from '@/utils/filteringParameters'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const roles = inject('roles')

const actions = [
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    accessRole: roles.LIBRARY_WRITE,
    click: editProject,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    accessRole: roles.LIBRARY_WRITE,
    click: deleteProject,
  },
]

const headers = [
  { title: '', key: 'actions', width: '1%' },
  { title: t('Projects.name'), key: 'name' },
  { title: t('Projects.project_number'), key: 'project_number' },
  {
    title: t('Projects.clinical_programme'),
    key: 'clinical_programme.name',
  },
  { title: t('Projects.description'), key: 'description' },
]
const items = ref([])
const total = ref(0)
const showProjectForm = ref(false)
const selectedProject = ref(null)
const confirm = ref()
const table = ref()

function fetchProjects(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  projects.get(params).then((resp) => {
    items.value = resp.data.items
    total.value = resp.data.total
  })
}
function showForm() {
  showProjectForm.value = true
}
function closeForm() {
  showProjectForm.value = false
  selectedProject.value = null
}

function editProject(item) {
  selectedProject.value = item
  showProjectForm.value = true
}

async function deleteProject(item) {
  const options = { type: 'warning' }
  const project = item.name
  if (
    await confirm.value.open(t('Projects.confirm_delete', { project }), options)
  ) {
    await projects.delete(item.uid)
    notificationHub.add({
      msg: t('Projects.delete_success'),
      type: 'success',
    })
    table.value.filterTable()
  }
}
</script>
