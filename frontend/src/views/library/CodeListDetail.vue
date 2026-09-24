<template>
  <div class="px-4">
    <div class="mb-6 d-flex align-center">
      <strong>{{ $t('_global.library') }}</strong>
      <span class="ml-2 text-secondary">{{ codelistNames.library_name }}</span>
      <v-spacer />
      <strong>{{ $t('CodeListDetail.concept_id') }}</strong>
      <span class="ml-2 text-secondary">{{ codelistNames.codelist_uid }}</span>
      <v-spacer />
      <v-btn
        size="small"
        :title="$t('CodelistTable.show_terms')"
        icon="mdi-dots-horizontal"
        @click="openCodelistTerms()"
      />
    </div>
    <div class="v-label pa-4">
      {{ $t('CodeListDetail.sponsor_title') }}
    </div>
    <v-table :aria-label="$t('CodeListDetail.sponsor_title')">
      <thead>
        <tr class="bg-greyBackground">
          <th width="25%">
            {{ $t('CodeListDetail.ct_identifiers') }}
          </th>
          <th width="50%">
            {{ $t('CodeListDetail.selected_values') }}
          </th>
          <th width="5%">
            {{ $t('_global.status') }}
          </th>
          <th width="10%">
            {{ $t('_global.modified') }}
          </th>
          <th width="5%">
            {{ $t('_global.version') }}
          </th>
          <th width="5%">
            {{ $t('_global.actions') }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>{{ $t('CodeListDetail.sponsor_pref_name') }}</td>
          <td>{{ codelistNames.name }}</td>
          <td data-cy="names-status" rowspan="4">
            <StatusChip :status="codelistNames.status" />
          </td>
          <td rowspan="4">
            {{ $filters.date(codelistNames.start_date) }}
          </td>
          <td data-cy="names-version" rowspan="4">
            {{ codelistNames.version }}
          </td>
          <td rowspan="4">
            <v-btn
              v-if="
                codelistNames.possible_actions.find(
                  (action) => action === 'edit'
                )
              "
              data-cy="edit-sponsor-values"
              icon="mdi-pencil-outline"
              color="primary"
              :title="$t('CodeListDetail.edit_sponsor_values')"
              variant="text"
              @click="editSponsorValues"
            />
            <v-btn
              v-if="
                codelistNames.possible_actions.find(
                  (action) => action === 'approve'
                )
              "
              data-cy="approve-sponsor-values"
              color="success"
              icon="mdi-check-decagram"
              :title="$t('CodeListDetail.approve_sponsor_values_version')"
              variant="text"
              @click="approveSponsorValues"
            />
            <v-btn
              v-if="
                codelistNames.possible_actions.find(
                  (action) => action === 'new_version'
                )
              "
              data-cy="create-new-sponsor-values"
              color="primary"
              icon="mdi-plus-circle-outline"
              :title="$t('CodeListDetail.new_version')"
              variant="text"
              @click="createNewSponsorValuesVersion"
            />
            <v-btn
              data-cy="sponsor-values-version-history"
              icon="mdi-history"
              :title="$t('CodeListDetail.history')"
              variant="text"
              @click="openNamesHistory"
            />
          </td>
        </tr>
        <tr>
          <td>{{ $t('CodeListDetail.tpl_parameter') }}</td>
          <td>{{ $filters.yesno(codelistNames.template_parameter) }}</td>
        </tr>
        <tr>
          <td>{{ $t('CodeListDetail.type') }}</td>
          <td>{{ codelistNames.codelist_type }}</td>
        </tr>
        <tr>
          <td>{{ $t('CodeListDetail.is_ordinal') }}</td>
          <td>{{ $filters.yesno(codelistNames.is_ordinal) }}</td>
        </tr>
      </tbody>
    </v-table>

    <div class="v-label pa-4 mt-6">
      {{ $t('CodeListDetail.attributes_title') }}
    </div>
    <v-table :aria-label="$t('CodeListDetail.attributes_title')">
      <thead>
        <tr class="bg-greyBackground">
          <th width="25%">
            {{ $t('CodeListDetail.ct_identifiers') }}
          </th>
          <th width="50%">
            {{ $t('CodeListDetail.selected_values') }}
          </th>
          <th width="5%">
            {{ $t('_global.status') }}
          </th>
          <th width="10%">
            {{ $t('_global.modified') }}
          </th>
          <th width="5%">
            {{ $t('_global.version') }}
          </th>
          <th width="5%">
            {{ $t('_global.actions') }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>{{ $t('CodeListDetail.codelist_name') }}</td>
          <td>{{ attributes.name }}</td>
          <td data-cy="attributes-status" rowspan="3">
            <StatusChip :status="attributes.status" />
          </td>
          <td rowspan="3">
            {{ $filters.date(attributes.start_date) }}
          </td>
          <td data-cy="attributes-version" rowspan="3">
            {{ attributes.version }}
          </td>
          <td rowspan="3">
            <v-btn
              v-if="
                attributes.possible_actions.find((action) => action === 'edit')
              "
              icon="mdi-pencil-outline"
              color="primary"
              :title="$t('CodeListDetail.edit_sponsor_values')"
              variant="text"
              @click="editAttributes"
            />
            <v-btn
              v-if="
                attributes.possible_actions.find(
                  (action) => action === 'approve'
                )
              "
              data-cy="approve-attributes-values"
              color="success"
              icon="mdi-check-decagram"
              :title="$t('CodeListDetail.approve_attributes_version')"
              variant="text"
              @click="approveAttributes"
            />
            <v-btn
              v-if="
                attributes.possible_actions.find(
                  (action) => action === 'new_version'
                )
              "
              color="primary"
              icon="mdi-plus-circle-outline"
              :title="$t('CodeListDetail.new_attributes_version')"
              variant="text"
              @click="createNewAttributesVersion"
            />
            <v-btn
              icon="mdi-history"
              :title="$t('CodeListDetail.history')"
              variant="text"
              @click="openAttributesHistory"
            />
          </td>
        </tr>
        <tr>
          <td>{{ $t('CodeListDetail.submission_value') }}</td>
          <td>{{ attributes.submission_value }}</td>
        </tr>
        <tr>
          <td>{{ $t('CodeListDetail.nci_pref_name') }}</td>
          <td>{{ attributes.nci_preferred_name }}</td>
        </tr>
        <tr>
          <td>{{ $t('CodeListDetail.extensible') }}</td>
          <td>{{ $filters.yesno(attributes.extensible) }}</td>
        </tr>
        <tr>
          <td>{{ $t('CodeListDetail.definition') }}</td>
          <td>{{ attributes.definition }}</td>
        </tr>
      </tbody>
    </v-table>

    <div class="v-label pa-4 mt-6">
      {{ $t('CodeListDetail.paired_codelists') }}
    </div>
    <v-btn
      class="ml-2"
      size="small"
      variant="outlined"
      color="nnBaseBlue"
      data-cy="add-paired-codelist-button"
      :title="$t('CodeListDetail.add_paired_codelist')"
      :disabled="!accessGuard.checkPermission($roles.LIBRARY_WRITE)"
      icon="mdi-plus"
      @click.stop="showAddPairedCodelistForm = true"
    />
    <v-table :aria-label="$t('CodeListDetail.paired_codelists')">
      <thead>
        <tr class="bg-greyBackground">
          <th width="10%">
            {{ $t('CodeListDetail.pair_type') }}
          </th>
          <th width="10%">
            {{ $t('_global.library') }}
          </th>
          <th width="15%">
            {{ $t('CodeListDetail.submission_value') }}
          </th>
          <th width="45%">
            {{ $t('CodeListDetail.sponsor_pref_name') }}
          </th>
          <th width="15%">
            {{ $t('CodeListDetail.concept_id') }}
          </th>
          <th width="5%">
            {{ $t('_global.actions') }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(cl, index) in pairedCodelists" :key="`item-${index}`">
          <td>{{ $t('CodeListDetail.pair_type_' + cl.type) }}</td>
          <td>{{ cl.library_name }}</td>
          <td>{{ cl.attributes.submission_value }}</td>
          <td>{{ cl.name.name }}</td>
          <td>{{ cl.attributes.codelist_uid }}</td>
          <td>
            <v-btn
              icon="mdi-delete-outline"
              :title="$t('CodeListDetail.remove_paired_codelist')"
              variant="text"
              @click="openRemovePairedCodelistForm(cl)"
            />
          </td>
        </tr>
      </tbody>
    </v-table>

    <v-dialog
      v-model="showSponsorValuesForm"
      persistent
      max-width="800px"
      @keydown.esc="showSponsorValuesForm = false"
    >
      <CodelistSponsorValuesForm
        v-model="codelistNames"
        @close="showSponsorValuesForm = false"
      />
    </v-dialog>
    <v-dialog
      v-model="showAttributesForm"
      persistent
      max-width="800px"
      @keydown.esc="showAttributesForm = false"
    >
      <CodelistAttributesForm
        v-model="attributes"
        @close="showAttributesForm = false"
      />
    </v-dialog>
    <v-dialog
      v-model="showAddPairedCodelistForm"
      persistent
      max-width="1024px"
      @keydown.esc="showAddPairedCodelistForm = false"
    >
      <CodelistAddPairedForm
        :codelist-uid="route.params.codelist_id"
        @close="closeAddPairedForm"
      />
    </v-dialog>
    <v-dialog
      v-model="showHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeHistory"
    >
      <HistoryTable
        :title="historyTitle"
        :headers="historyHeaders"
        :items="historyItems"
        @close="closeHistory"
      />
    </v-dialog>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  </div>
</template>

<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import controlledTerminology from '@/api/controlledTerminology'
import CodelistAttributesForm from '@/components/library/CodelistAttributesForm.vue'
import CodelistSponsorValuesForm from '@/components/library/CodelistSponsorValuesForm.vue'
import CodelistAddPairedForm from '@/components/library/CodelistAddPairedForm.vue'
import dataFormating from '@/utils/dataFormating'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import { useAppStore } from '@/stores/app'
import { useAccessGuard } from '@/composables/accessGuard'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'

const { t } = useI18n()
const accessGuard = useAccessGuard()
const notificationHub = inject('notificationHub')
const appStore = useAppStore()
const route = useRoute()
const router = useRouter()

const attributes = ref({ possible_actions: [] })
const codelistNames = ref({ possible_actions: [] })
const pairedCodelists = ref([])
const attributesHistoryHeaders = [
  { title: t('CodeListDetail.codelist_name'), key: 'name' },
  {
    title: t('CodeListDetail.submission_value'),
    key: 'submission_value',
  },
  {
    title: t('CodeListDetail.nci_pref_name'),
    key: 'nci_preferred_name',
  },
  { title: t('CodeListDetail.extensible'), key: 'extensible' },
  { title: t('_global.definition'), key: 'definition' },
  { title: t('_global.status'), key: 'status' },
  { title: t('_global.version'), key: 'version' },
]
const historyHeaders = ref([])
const historyItems = ref([])
const historyTitle = ref('')
const confirm = ref()

const namesHistoryHeaders = [
  { title: t('CodeListDetail.sponsor_pref_name'), key: 'name' },
  {
    title: t('CodeListDetail.tpl_parameter'),
    key: 'template_parameter',
  },
  { title: t('CodeListDetail.type'), key: 'codelist_type' },
  { title: t('CodeListDetail.is_ordinal'), key: 'is_ordinal' },
  { title: t('_global.status'), key: 'status' },
  { title: t('_global.version'), key: 'version' },
]
const showAttributesForm = ref(false)
const showHistory = ref(false)
const showSponsorValuesForm = ref(false)
const showAddPairedCodelistForm = ref(false)

const namesHistoryTitle = computed(() => {
  return t('CodeListDetail.names_history_title', {
    codelist: codelistNames.value.codelist_uid,
  })
})
const attributesHistoryTitle = computed(() => {
  return t('CodeListDetail.attributes_history_title', {
    codelist: attributes.value.codelist_uid,
  })
})

onMounted(() => {
  controlledTerminology
    .getCodelistNames(route.params.codelist_id)
    .then((resp) => {
      codelistNames.value = resp.data
      appStore.addBreadcrumbsLevel(
        codelistNames.value.codelist_uid,
        { name: 'CodeListDetail', params: route.params },
        4
      )
    })
  controlledTerminology
    .getCodelistAttributes(route.params.codelist_id)
    .then((resp) => {
      attributes.value = resp.data
    })
  fetchPairedCodelists()
})

function fetchPairedCodelists() {
  controlledTerminology
    .getPairedCodelists(route.params.codelist_id)
    .then((resp) => {
      pairedCodelists.value = []
      if (resp.data.names) {
        resp.data.names.type = 'names'
        pairedCodelists.value.push(resp.data.names)
      }
      if (resp.data.codes) {
        resp.data.codes.type = 'codes'
        pairedCodelists.value.push(resp.data.codes)
      }
    })
}

function editSponsorValues() {
  showSponsorValuesForm.value = true
}
function editAttributes() {
  showAttributesForm.value = true
}
function createNewSponsorValuesVersion() {
  controlledTerminology
    .newCodelistNamesVersion(codelistNames.value.codelist_uid)
    .then((resp) => {
      codelistNames.value = resp.data
      notificationHub.add({
        msg: t('CodeListDetail.new_version_success'),
      })
    })
}
function approveSponsorValues() {
  controlledTerminology
    .approveCodelistNames(codelistNames.value.codelist_uid)
    .then((resp) => {
      codelistNames.value = resp.data
      notificationHub.add({
        msg: t('CodeListDetail.sponsor_values_approve_success'),
      })
    })
}
async function openNamesHistory() {
  historyTitle.value = namesHistoryTitle
  historyHeaders.value = namesHistoryHeaders
  const resp = await controlledTerminology.getCodelistNamesVersions(
    codelistNames.value.codelist_uid
  )
  historyItems.value = transformHistoryItems(resp.data)
  showHistory.value = true
}
function closeHistory() {
  showHistory.value = false
}
function createNewAttributesVersion() {
  controlledTerminology
    .newCodelistAttributesVersion(attributes.value.codelist_uid)
    .then((resp) => {
      attributes.value = resp.data
      notificationHub.add({
        msg: t('CodeListDetail.new_attributes_version_success'),
      })
    })
}
function approveAttributes() {
  controlledTerminology
    .approveCodelistAttributes(attributes.value.codelist_uid)
    .then((resp) => {
      attributes.value = resp.data
      notificationHub.add({
        msg: t('CodeListDetail.attributes_approve_success'),
      })
    })
}
async function openAttributesHistory() {
  historyTitle.value = attributesHistoryTitle
  historyHeaders.value = attributesHistoryHeaders
  const resp = await controlledTerminology.getCodelistAttributesVersions(
    attributes.value.codelist_uid
  )
  historyItems.value = transformHistoryItems(resp.data)
  showHistory.value = true
}
function openCodelistTerms() {
  router.push({
    name: 'CodelistTerms',
    params: { codelist_id: codelistNames.value.codelist_uid },
  })
}
function closeAddPairedForm() {
  showAddPairedCodelistForm.value = false
  fetchPairedCodelists()
}
function transformHistoryItems(items) {
  const result = []
  for (const item of items) {
    const newItem = { ...item }
    if (newItem.template_parameter !== undefined) {
      newItem.template_parameter = dataFormating.yesno(
        newItem.template_parameter
      )
    }
    if (newItem.extensible !== undefined) {
      newItem.extensible = dataFormating.yesno(newItem.extensible)
    }
    if (newItem.is_ordinal !== undefined) {
      newItem.is_ordinal = dataFormating.yesno(newItem.is_ordinal)
    }
    result.push(newItem)
  }
  return result
}
async function openRemovePairedCodelistForm(cl) {
  const options = {
    type: 'warning',
    cancelLabel: t('_global.cancel'),
    agreeLabel: t('_global.continue'),
  }
  if (
    await confirm.value.open(
      t('CodeListDetail.remove_paired_codelist'),
      options
    )
  ) {
    let data
    if (cl.type === 'codes') {
      data = {
        paired_codes_codelist_uid: null,
      }
    } else {
      data = {
        paired_names_codelist_uid: null,
      }
    }
    controlledTerminology
      .updatePairedCodelists(route.params.codelist_id, data)
      .then(() => {
        fetchPairedCodelists()
        notificationHub.add({
          msg: t('CodeListDetail.remove_paired_codelist_success'),
        })
      })
  }
}
</script>
