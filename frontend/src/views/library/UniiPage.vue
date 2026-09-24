<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('DictionaryTermTable.unii_title') }}
      <HelpButton :help-text="$t('_help.UniiTable.general')" />
    </div>

    <NNTable
      table-id="library-unii-terms-table"
      :headers="headers"
      item-value="term_uid"
      :items-length="total"
      :items="formattedTableItems"
      :column-data-resource="columnDataResource"
      :export-config="{
        objectLabel: dictionaryName,
        dataUrl: columnDataResource,
      }"
      @filter="fetchTerms"
    >
      <template #actions="">
        <v-btn
          class="ml-2"
          icon
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          :disabled="!accessGuard.checkPermission($roles.LIBRARY_WRITE)"
          @click="openCreateTermForm()"
        >
          <v-icon>mdi-plus</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('DictionaryTermTable.add_title') }}
          </v-tooltip>
        </v-btn>
      </template>
      <template #[`item.status`]="{ item }">
        <StatusChip :status="item.status" />
      </template>
      <template #[`item.start_date`]="{ item }">
        {{ $filters.date(item.start_date) }}
      </template>
      <template #[`item.actions`]="{ item }">
        <ActionsMenu :actions="actions" :item="item" />
      </template>
    </NNTable>

    <slot
      name="termForm"
      :close-form="closeForm"
      :open="showTermForm"
      :edited-term="editedTerm"
    >
      <SimpleFormDialog
        ref="formRef"
        :title="$t('DictionaryTermForm.title', { dictionaryName })"
        :help-items="helpItems"
        :open="showTermForm"
        @close="cancel"
        @submit="submit"
      >
        <template #body>
          <v-form ref="observer">
            <v-row>
              <v-col cols="12">
                <v-text-field
                  v-model="form.dictionary_id"
                  :label="`${dictionaryName}`"
                  clearable
                  :rules="[formRules.required]"
                />
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="12">
                <v-text-field
                  v-model="form.name"
                  :label="$t('_global.name')"
                  clearable
                  :rules="[formRules.required]"
                  @blur="setLowerCase"
                />
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="12">
                <v-text-field
                  v-model="form.name_sentence_case"
                  :label="$t('DictionaryTermForm.lower_case_name')"
                  clearable
                  :rules="[formRules.required]"
                />
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="12">
                <v-text-field
                  v-model="form.abbreviation"
                  :label="$t('DictionaryTermForm.abbreviation')"
                  clearable
                />
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="12">
                <v-textarea
                  v-model="form.definition"
                  :label="$t('DictionaryTermForm.definition')"
                  clearable
                  rows="1"
                  auto-grow
                />
              </v-col>
            </v-row>
            <v-row v-if="editedTerm">
              <v-col cols="12">
                <v-textarea
                  v-model="form.change_description"
                  :label="$t('_global.change_description')"
                  clearable
                  rows="1"
                  auto-grow
                  :rules="[formRules.required]"
                />
              </v-col>
            </v-row>

            <v-row>
              <v-col>
                <v-autocomplete
                  v-model="form.pclass.term_uid"
                  :label="$t('DictionaryTermTable.pclass')"
                  :items="pclassTerms"
                  :custom-filter="customFilterPclass"
                  item-title="name"
                  item-value="term_uid"
                  clearable
                >
                  <template #item="{ props, internalItem: item }">
                    <v-list-item
                      v-bind="props"
                      :title="`${item.raw.name} (${item.raw.dictionary_id})`"
                    >
                    </v-list-item>
                  </template>
                </v-autocomplete>
              </v-col>
            </v-row>
          </v-form>
        </template>
      </SimpleFormDialog>
    </slot>
  </div>
</template>

<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import dictionaries from '@/api/dictionaries'
import HelpButton from '@/components/tools/HelpButton.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import filteringParameters from '@/utils/filteringParameters'
import { useAccessGuard } from '@/composables/accessGuard'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import _isEmpty from 'lodash/isEmpty'

const formRules = inject('formRules')
const notificationHub = inject('notificationHub')
const roles = inject('roles')

const { t } = useI18n()
const accessGuard = useAccessGuard()

const total = ref(0)
const items = ref([])
const showTermForm = ref(false)
const editedTerm = ref({ pclass: { term_uid: null } })
const pclassTerms = ref([])
const form = ref({})
const formRef = ref()

let pclassCodelistUid = null
const pclassCodelistName = 'MED-RT'
const dictionaryName = 'UNII'
let codelistUid = null
const columnDataResource = 'dictionaries/substances'
const actions = [
  {
    label: t('_global.approve'),
    icon: 'mdi-check-decagram',
    iconColor: 'success',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'approve'),
    accessRole: roles.LIBRARY_WRITE,
    click: approveTerm,
  },
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'edit'),
    accessRole: roles.LIBRARY_WRITE,
    click: openEditTermForm,
  },
  {
    label: t('_global.new_version'),
    icon: 'mdi-plus-circle-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'new_version'),
    accessRole: roles.LIBRARY_WRITE,
    click: newTermVersion,
  },
  {
    label: t('_global.inactivate'),
    icon: 'mdi-close-octagon-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'inactivate'),
    accessRole: roles.LIBRARY_WRITE,
    click: inactivateTerm,
  },
  {
    label: t('_global.reactivate'),
    icon: 'mdi-undo-variant',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'reactivate'),
    accessRole: roles.LIBRARY_WRITE,
    click: reactivateTerm,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'delete'),
    accessRole: roles.LIBRARY_WRITE,
    click: deleteTerm,
  },
]

const headers = [
  { title: '', key: 'actions', width: '1%' },
  { title: t('DictionaryTermTable.unii_id'), key: 'dictionary_id' },
  { title: t('DictionaryTermTable.substance_name'), key: 'name' },
  {
    title: t('DictionaryTermTable.substance_name_lower_case'),
    key: 'name_sentence_case',
  },
  {
    title: t('DictionaryTermTable.abbreviation'),
    key: 'abbreviation',
  },
  {
    title: t('DictionaryTermTable.definition'),
    key: 'definition',
  },
  {
    title: t('DictionaryTermTable.pclass'),
    key: 'pclass_formatted',
    sortKey: 'pclass.name',
    columnDataKey: 'pclass.name',
  },
  { title: t('_global.status'), key: 'status' },
  { title: t('_global.version'), key: 'version' },
  { title: t('_global.modified'), key: 'start_date' },
]

const helpItems = [
  'DictionaryTermForm.dictionary_id',
  'DictionaryTermForm.name',
  'DictionaryTermForm.lower_case_name',
  'DictionaryTermForm.abbreviation',
  'DictionaryTermForm.definition',
]

const formattedTableItems = computed(() => {
  return formatItems(items.value)
})

onMounted(() => {
  dictionaries.getCodelists(dictionaryName).then((resp) => {
    codelistUid = resp.data.items[0].codelist_uid
  })
  dictionaries.getCodelists(pclassCodelistName).then((resp) => {
    pclassCodelistUid = resp.data.items[0].codelist_uid
    dictionaries
      .getTerms({
        codelist_uid: pclassCodelistUid,
        page: 1,
        page_size: 0,
      })
      .then((resp) => {
        pclassTerms.value = resp.data.items
      })
  })
})

function fetchTerms(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  dictionaries.getSubstances(params).then((resp) => {
    items.value = resp.data.items
    total.value = resp.data.total
  })
}
function inactivateTerm(item) {
  dictionaries.inactivate(item.term_uid).then(() => {
    fetchTerms()
  })
}
function reactivateTerm(item) {
  dictionaries.reactivate(item.term_uid).then(() => {
    fetchTerms()
  })
}
function deleteTerm(item) {
  dictionaries.delete(item.term_uid).then(() => {
    fetchTerms()
  })
}
function approveTerm(item) {
  dictionaries.approve(item.term_uid).then(() => {
    fetchTerms()
  })
}
function newTermVersion(item) {
  dictionaries.newVersion(item.term_uid).then(() => {
    fetchTerms()
  })
}
function openEditTermForm(item) {
  if (!_isEmpty(item)) {
    dictionaries.getSubstance(item.term_uid).then((resp) => {
      editedTerm.value = structuredClone(resp.data)
      form.value = structuredClone(resp.data)
      form.value.change_description = t('_global.draft_change')

      if (resp.data.pclass == null) {
        form.value.pclass = { term_uid: null }
        editedTerm.value.pclass = { term_uid: null }
      }
    })
  }
  showTermForm.value = true
}
function openCreateTermForm() {
  form.value = { pclass: { term_uid: null } }
  form.value.change_description = t('_global.draft_change')
  editedTerm.value = { pclass: { term_uid: null } }
  showTermForm.value = true
}
function closeForm() {
  editedTerm.value = { pclass: { term_uid: null } }
  showTermForm.value = false
}
function formatItems(items) {
  const result = []
  for (const item of items) {
    const newItem = { ...item }
    newItem.pclass_formatted = item.pclass
      ? `${item.pclass.name} (${item.pclass.dictionary_id})`
      : '-'
    result.push(newItem)
  }
  return result
}
function customFilterPclass(itemText, queryText, item) {
  if (!queryText) return true

  const searchText = queryText.toLowerCase()
  const name = (item.raw.name || '').toLowerCase()
  const dictionaryId = (item.raw.dictionary_id || '').toLowerCase()

  return name.includes(searchText) || dictionaryId.includes(searchText)
}
async function cancel() {
  if (JSON.stringify(editedTerm.value) === JSON.stringify(form.value)) {
    closeForm()
  } else {
    const options = {
      type: 'warning',
      cancelLabel: t('_global.cancel'),
      agreeLabel: t('_global.continue'),
    }
    if (await formRef.value.confirm(t('_global.cancel_changes'), options)) {
      closeForm()
    }
  }
}
function submit() {
  if (editedTerm.value && editedTerm.value.term_uid) {
    edit()
  } else {
    create()
  }
}
function edit() {
  let data = { ...form.value }
  data.pclass_uid = form.value.pclass?.term_uid || null

  dictionaries.editSubstance(data.term_uid, data).then(
    () => {
      notificationHub.add({
        msg: t('DictionaryTermForm.update_success'),
      })
      fetchTerms()
      closeForm()
    },
    () => {
      formRef.value.working = false
    }
  )
}
async function create() {
  let data = { ...form.value }
  data.pclass_uid = form.value.pclass?.term_uid || null
  data.codelist_uid = codelistUid
  data.library_name = dictionaryName

  try {
    await dictionaries.createSubstance(data)
    notificationHub.add({
      msg: t('DictionaryTermForm.create_success'),
    })
    closeForm()
  } finally {
    formRef.value.working = false
  }
}
function setLowerCase() {
  if (form.value.name) {
    form.value.name_sentence_case = form.value.name.toLowerCase()
  }
}
</script>
