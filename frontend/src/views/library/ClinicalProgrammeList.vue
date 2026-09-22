<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('ClinicalProgrammesView.title') }}
    </div>
    <NNTable
      ref="table"
      table-id="library-clinical-programmes-table"
      :headers="headers"
      :items="items"
      :items-length="total"
      column-data-resource="clinical-programmes"
      hide-default-switches
      item-value="name"
      :export-config="{
        objectLabel: 'ClinicalProgrammes',
        dataUrl: 'clinical-programmes',
      }"
      @filter="fetchProgrammes"
    >
      <template #actions="">
        <slot name="extraActions" />
        <v-btn
          class="ml-2"
          icon
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          data-cy="add-clinical-programme"
          @click.stop="showForm"
        >
          <v-icon>mdi-plus</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('ClinicalProgrammeForm.add_title') }}
          </v-tooltip>
        </v-btn>
      </template>
      <template #[`item.actions`]="{ item }">
        <ActionsMenu :actions="actions" :item="item" />
      </template>
    </NNTable>
    <ClinicalProgrammeForm
      :open="showClinicalProgrammeForm"
      :programme-uid="selectedProgramme ? selectedProgramme.uid : ''"
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
import programmes from '@/api/clinicalProgrammes'
import ClinicalProgrammeForm from '@/components/library/ClinicalProgrammeForm.vue'
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
    click: editProgramme,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    accessRole: roles.LIBRARY_WRITE,
    click: deleteProgramme,
  },
]

const headers = [
  { title: '', key: 'actions', width: '1%' },
  { title: t('ClinicalProgrammes.name'), key: 'name' },
]

const items = ref([])
const total = ref(0)
const showClinicalProgrammeForm = ref(false)
const selectedProgramme = ref(null)
const confirm = ref()
const table = ref()

function fetchProgrammes(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  programmes.get(params).then((resp) => {
    items.value = resp.data.items
    total.value = resp.data.total
  })
}

function showForm() {
  showClinicalProgrammeForm.value = true
}

function closeForm() {
  showClinicalProgrammeForm.value = false
  selectedProgramme.value = null
}

function editProgramme(item) {
  selectedProgramme.value = item
  showClinicalProgrammeForm.value = true
}

async function deleteProgramme(item) {
  const options = { type: 'warning' }
  const programme = item.name
  if (
    await confirm.value.open(
      t('ClinicalProgrammes.confirm_delete', { programme }),
      options
    )
  ) {
    await programmes.delete(item.uid)
    notificationHub.add({
      msg: t('ClinicalProgrammes.delete_success'),
      type: 'success',
    })
    table.value.filterTable()
  }
}
</script>
