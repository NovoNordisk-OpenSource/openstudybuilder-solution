<template>
  <div class="trial-parameter-details">
    <div class="d-flex align-center mb-4">
      <h2
        data-cy="page-title"
        class="text-headline-small font-weight-bold text-nnTrueBlue"
      >
        {{ t('TrialSummaryParameters.trial_phase') }}
      </h2>
      <v-spacer />
      <v-btn
        data-cy="close-overview-button"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        @click="router.go(-1)"
      >
        <v-icon>mdi-close</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ t('_global.close') }}
        </v-tooltip>
      </v-btn>
    </div>

    <v-card
      data-cy="header-card"
      variant="flat"
      class="pa-4 mb-4 rounded-lg"
      border
    >
      <v-row>
        <v-col data-cy="term-library" cols="6" md="3">
          <div class="text-caption text-medium-emphasis">
            {{ t('_global.library') }}
          </div>
          <div class="font-weight-bold">{{ currentName.library_name }}</div>
        </v-col>
        <v-col data-cy="term-concept-id" cols="6" md="3">
          <div class="text-caption text-medium-emphasis">
            {{ t('TrialSummaryParameters.concept_id') }}
          </div>
          <div class="font-weight-bold">{{ props.termUid }}</div>
        </v-col>
      </v-row>
    </v-card>

    <div class="d-flex justify-end mb-2">
      <v-btn
        v-if="hasNameAction('edit')"
        data-cy="edit-sponsor-values"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        class="mr-2"
        @click="openEditForm('sponsor')"
      >
        <v-icon>mdi-pencil-outline</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ t('_global.edit') }}
        </v-tooltip>
      </v-btn>
      <v-btn
        v-if="hasNameAction('approve')"
        data-cy="approve-term-sponsor-values"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        class="mr-2"
        @click="approveTermNamesVersion()"
      >
        <v-icon>mdi-check-decagram</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ t('_global.approve') }}
        </v-tooltip>
      </v-btn>
      <v-btn
        v-if="hasNameAction('new_version')"
        data-cy="create-new-sponsor-values"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        class="mr-2"
        @click="newTermNamesVersion()"
      >
        <v-icon>mdi-plus-circle-outline</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ t('_global.new_version') }}
        </v-tooltip>
      </v-btn>
      <v-btn
        v-if="hasNameAction('inactivate')"
        data-cy="inactivate-sponsor-values"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        class="mr-2"
        @click="inactivateTermNamesVersion()"
      >
        <v-icon>mdi-close-octagon-outline</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ t('_global.inactivate') }}
        </v-tooltip>
      </v-btn>
      <v-btn
        v-if="hasNameAction('reactivate')"
        data-cy="reactivate-sponsor-values"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        class="mr-2"
        @click="reactivateTermNamesVersion()"
      >
        <v-icon>mdi-undo-variant</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ t('_global.reactivate') }}
        </v-tooltip>
      </v-btn>
      <v-btn
        data-cy="term-sponsor-version-history"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        @click="openSponsorValuesHistory"
      >
        <v-icon>mdi-history</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ t('_global.history') }}
        </v-tooltip>
      </v-btn>
    </div>

    <v-card
      data-cy="term-sponsor-values-card"
      variant="flat"
      class="pa-4 mb-4 rounded-lg"
      border
    >
      <div
        data-cy="term-sponsor-values-title"
        class="text-headline-small font-weight-bold text-nnTrueBlue mb-3"
      >
        {{ t('TrialSummaryParameters.term_sponsor_values') }}
      </div>
      <table data-cy="term-sponsor-values-table" class="details-table">
        <tbody>
          <tr class="details-table__labels">
            <td>{{ t('TrialSummaryParameters.sponsor_name') }}</td>
            <td>
              {{ t('TrialSummaryParameters.sponsor_sentence_case_name') }}
            </td>
            <td>{{ t('TrialSummaryParameters.semantic_data_type') }}</td>
            <td>{{ t('TrialSummaryParameters.osb_field_name') }}</td>
            <td>{{ t('TrialSummaryParameters.osb_page_reference') }}</td>
          </tr>
          <tr class="details-table__values">
            <td data-cy="sponsor-preferred-name">
              {{ currentName.sponsor_preferred_name }}
            </td>
            <td data-cy="sponsor-preferred-name-sentence-case">
              {{ currentName.sponsor_preferred_name_sentence_case }}
            </td>
            <td data-cy="semantic-data-type">
              {{
                currentName.semantic_data_type?.sponsor_preferred_name || '-'
              }}
            </td>
            <td data-cy="osb-field-name">
              {{ currentName.osb_field_name || '-' }}
            </td>
            <td data-cy="osb-page-reference">
              {{ currentName.osb_page_reference || '-' }}
            </td>
          </tr>

          <tr class="details-table__labels">
            <td>{{ t('TrialSummaryParameters.response_code_list') }}</td>
            <td>{{ t('TrialSummaryParameters.required_level') }}</td>
            <td>{{ t('TrialSummaryParameters.cardinality') }}</td>
            <td>{{ t('TrialSummaryParameters.valid_null_flavor') }}</td>
            <td>{{ t('TrialSummaryParameters.notes') }}</td>
          </tr>
          <tr class="details-table__values">
            <td data-cy="response-codelist">
              {{ currentName.response_codelist?.sponsor_preferred_name || '-' }}
            </td>
            <td data-cy="required-level">
              {{ currentName.required_level || '-' }}
            </td>
            <td data-cy="cardinality">{{ currentName.cardinality || '-' }}</td>
            <td data-cy="valid-null-flavor">
              {{
                currentName.valid_null_flavor_terms?.[0]
                  ?.sponsor_preferred_name || '-'
              }}
            </td>
            <td data-cy="notes">{{ currentName.notes || '-' }}</td>
          </tr>

          <tr class="details-table__labels">
            <td>{{ t('_global.status') }}</td>
            <td>{{ t('_global.version') }}</td>
            <td>{{ t('_global.modified_by') }}</td>
            <td>{{ t('_global.modified') }}</td>
            <td></td>
          </tr>
          <tr class="details-table__values">
            <td data-cy="names-status">
              <StatusChip :status="currentName.status || '-'" />
            </td>
            <td data-cy="names-version">
              <v-select
                v-model="selectedNameVersion"
                :items="nameVersions"
                density="compact"
                variant="outlined"
                hide-details
                data-cy="select-name-version"
                style="max-width: 120px"
              />
            </td>
            <td data-cy="names-modified-by">
              {{ currentName.author_username || '-' }}
            </td>
            <td data-cy="names-modified-date">
              {{ $filters.date(currentName.start_date) || '-' }}
            </td>
            <td></td>
          </tr>
        </tbody>
      </table>
    </v-card>

    <div class="d-flex justify-end mb-2">
      <v-btn
        v-if="hasAttributeAction('edit')"
        data-cy="edit-attributes-values"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        class="mr-2"
        @click="openEditForm('attributes')"
      >
        <v-icon>mdi-pencil-outline</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ t('_global.edit') }}
        </v-tooltip>
      </v-btn>
      <v-btn
        v-if="hasAttributeAction('approve')"
        data-cy="approve-term-attributes-values"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        class="mr-2"
        @click="approveTermAttributesVersion()"
      >
        <v-icon>mdi-check-decagram</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ t('_global.approve') }}
        </v-tooltip>
      </v-btn>
      <v-btn
        v-if="hasAttributeAction('new_version')"
        data-cy="create-new-attributes-values"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        class="mr-2"
        @click="newTermAttributesVersion()"
      >
        <v-icon>mdi-plus-circle-outline</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ t('_global.new_version') }}
        </v-tooltip>
      </v-btn>
      <v-btn
        v-if="hasAttributeAction('inactivate')"
        data-cy="inactivate-attributes-values"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        class="mr-2"
        @click="inactivateTermAttributesVersion()"
      >
        <v-icon>mdi-close-octagon-outline</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ t('_global.inactivate') }}
        </v-tooltip>
      </v-btn>
      <v-btn
        v-if="hasAttributeAction('reactivate')"
        data-cy="reactivate-attributes-values"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        class="mr-2"
        @click="reactivateTermAttributesVersion()"
      >
        <v-icon>mdi-undo-variant</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ t('_global.reactivate') }}
        </v-tooltip>
      </v-btn>
      <v-btn
        data-cy="term-attributes-version-history"
        icon
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        @click="openCTValuesHistory"
      >
        <v-icon>mdi-history</v-icon>
        <v-tooltip activator="parent" location="top">
          {{ t('_global.history') }}
        </v-tooltip>
      </v-btn>
    </div>

    <v-card
      data-cy="term-attributes-values-card"
      variant="flat"
      class="pa-4 mb-4 rounded-lg"
      border
    >
      <div
        data-cy="term-attributes-values-title"
        class="text-headline-small font-weight-bold text-nnTrueBlue mb-3"
      >
        {{ t('TrialSummaryParameters.term_attributes_values') }}
      </div>
      <table data-cy="term-attributes-values-table" class="details-table">
        <tbody>
          <tr class="details-table__labels">
            <td>{{ t('TrialSummaryParameters.concept_id') }}</td>
            <td>{{ t('TrialSummaryParameters.nci_preferred_name') }}</td>
            <td colspan="2">{{ t('TrialSummaryParameters.definition') }}</td>
          </tr>
          <tr class="details-table__values">
            <td data-cy="concept-id">
              {{ currentAttribute.concept_id || '-' }}
            </td>
            <td data-cy="nci-preferred-name">
              {{ currentAttribute.nci_preferred_name || '-' }}
            </td>
            <td data-cy="definition" colspan="2">
              {{ currentAttribute.definition || '-' }}
            </td>
          </tr>

          <tr class="details-table__labels">
            <td>{{ t('_global.status') }}</td>
            <td>{{ t('_global.version') }}</td>
            <td>{{ t('_global.modified_by') }}</td>
            <td>{{ t('_global.modified') }}</td>
          </tr>
          <tr class="details-table__values">
            <td data-cy="attributes-status">
              <StatusChip :status="currentAttribute.status || '-'" />
            </td>
            <td data-cy="attributes-version">
              <v-select
                v-model="selectedAttributeVersion"
                :items="attributeVersions"
                density="compact"
                variant="outlined"
                hide-details
                data-cy="select-attribute-version"
                style="max-width: 120px"
              />
            </td>
            <td data-cy="attributes-modified-by">
              {{ currentAttribute.author_username || '-' }}
            </td>
            <td data-cy="attributes-modified-date">
              {{ $filters.date(currentAttribute.start_date) || '-' }}
            </td>
          </tr>
        </tbody>
      </table>
    </v-card>

    <v-card
      data-cy="codelists-context-card"
      variant="flat"
      class="table-card pa-4 mb-4 rounded-lg"
      border
    >
      <div
        data-cy="codelists-context-title"
        class="text-headline-small font-weight-bold text-nnTrueBlue mb-3"
      >
        {{ t('TrialSummaryParameters.ct_term_codelists_context') }}
      </div>
      <v-data-table
        data-cy="codelists-context-table"
        :headers="codelistHeaders"
        :items="codelistItems"
        item-value="codelist_uid"
        :items-per-page="-1"
        hide-default-footer
        density="compact"
      >
        <template #[`item.actions`]="{ item }">
          <ActionsMenu :actions="actions" :item="item" />
        </template>
        <template #[`item.start_date`]="{ item }">
          {{ $filters.date(item.start_date) || '-' }}
        </template>
      </v-data-table>
    </v-card>
  </div>
  <CodelistTermOrderSubmvalForm
    v-if="showOrderSubmvalForm"
    :open="showOrderSubmvalForm"
    :term-uid="termUid"
    :codelist-uid="selectedCodelist?.codelist_uid"
    :submission-value="selectedCodelist?.submission_value"
    :submission-values="listSubmissionValues()"
    :codelist-name="selectedCodelist?.codelist_name"
    :term-name="latestName?.sponsor_preferred_name || ''"
    :order="selectedCodelist?.order"
    @close="closeOrderSubmvalForm"
  />
  <v-dialog
    v-model="showForm"
    fullscreen
    persistent
    content-class="fullscreen-dialog"
  >
    <TrialSummaryParameterEditForm
      :section="editSection"
      :edit-data="prepareEditData()"
      @close="closeEditForm()"
    />
  </v-dialog>
  <v-dialog
    v-model="showHistory"
    persistent
    :fullscreen="$globals.historyDialogFullscreen"
    @keydown.esc="closeHistory"
  >
    <HistoryTable
      :title="historyTitleLabel"
      :headers="historyHeaders"
      :items="historyItems"
      @close="closeHistory"
    />
  </v-dialog>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { useI18n } from 'vue-i18n'
import controlledTerminology from '@/api/controlledTerminology'
import StatusChip from '@/components/tools/StatusChip.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import CodelistTermOrderSubmvalForm from '@/components/library/CodelistTermOrderSubmvalForm.vue'
import TrialSummaryParameterEditForm from './TrialSummaryParameterEditForm.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import { useRouter } from 'vue-router'

const roles = inject('roles')
const { t } = useI18n()
const router = useRouter()

const props = defineProps({
  termUid: {
    type: String,
    default: '',
  },
})

const codelistHeaders = [
  { title: '', key: 'actions', width: '1%', sortable: false },
  { title: t('_global.library'), key: 'library_name' },
  { title: t('TrialSummaryParameters.codelist_name'), key: 'codelist_name' },
  {
    title: t('TrialSummaryParameters.codelist_concept_id'),
    key: 'codelist_concept_id',
  },
  {
    title: t('TrialSummaryParameters.codelist_submission_value'),
    key: 'codelist_submission_value',
  },
  {
    title: t('TrialSummaryParameters.submission_value'),
    key: 'submission_value',
  },
  { title: t('_global.order'), key: 'order' },
  { title: t('_global.modified'), key: 'start_date' },
]

const actions = [
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    accessRole: roles.LIBRARY_WRITE,
    click: editCodelist,
  },
]

const showForm = ref(false)
const editSection = ref('')
const selectedCodelist = ref(null)
const showOrderSubmvalForm = ref(false)

const codelistItems = ref([])

const termNames = ref([])
const selectedNameVersion = ref(null)
const latestName = computed(() => termNames.value[0] || null)
const namePossibleActions = computed(
  () => latestName.value?.possible_actions || []
)
const nameVersions = computed(() => [
  ...new Set(termNames.value.map((i) => i.version)),
])
const currentName = computed(
  () =>
    termNames.value.find((i) => i.version === selectedNameVersion.value) || {}
)

const termAttributes = ref([])
const selectedAttributeVersion = ref(null)
const latestAttribute = computed(() => termAttributes.value[0] || null)
const attributePossibleActions = computed(
  () => latestAttribute.value?.possible_actions || []
)
const attributeVersions = computed(() => [
  ...new Set(termAttributes.value.map((i) => i.version)),
])
const currentAttribute = computed(
  () =>
    termAttributes.value.find(
      (i) => i.version === selectedAttributeVersion.value
    ) || {}
)

onMounted(() => {
  fetchData()
})

function fetchData() {
  fetchTermNames()
  fetchTermAttributes()
  fetchTermCodelists()
}

function fetchTermNames() {
  const params = { include_ts_parameters: true }
  controlledTerminology
    .getCodelistTermNamesVersions(props.termUid, params)
    .then((resp) => {
      termNames.value = resp.data
      selectedNameVersion.value = resp.data[0]?.version ?? null
    })
}

function fetchTermAttributes() {
  const params = { include_ts_parameters: true }
  controlledTerminology
    .getCodelistTermAttributesVersions(props.termUid, params)
    .then((resp) => {
      termAttributes.value = resp.data
      selectedAttributeVersion.value = resp.data[0]?.version ?? null
    })
}

function fetchTermCodelists() {
  controlledTerminology.getTermCodelists(props.termUid).then((resp) => {
    codelistItems.value = resp.data.codelists
  })
}

function hasNameAction(action) {
  return namePossibleActions.value.includes(action)
}

function hasAttributeAction(action) {
  return attributePossibleActions.value.includes(action)
}

function prepareEditData() {
  const name = latestName.value || {}
  const attribute = latestAttribute.value || {}

  return {
    term_uid: props.termUid,
    response_codelist: name.response_codelist,
    required_level: name.required_level,
    valid_null_flavor_terms: name.valid_null_flavor_terms,
    cardinality: name.cardinality,
    osb_page_reference: name.osb_page_reference,
    osb_field_name: name.osb_field_name,
    semantic_data_type: name.semantic_data_type,
    notes: name.notes,
    library_name: attribute.library_name,
    concept_id: attribute.concept_id,
    nci_preferred_name: attribute.nci_preferred_name,
    definition: attribute.definition,
  }
}

function openEditForm(section) {
  editSection.value = section
  showForm.value = true
}
function closeEditForm() {
  editSection.value = ''
  showForm.value = false
  fetchTermNames()
  fetchTermAttributes()
}

function editCodelist(item) {
  selectedCodelist.value = item
  showOrderSubmvalForm.value = true
}

function closeOrderSubmvalForm() {
  showOrderSubmvalForm.value = false
  selectedCodelist.value = null
  fetchTermCodelists()
}

function listSubmissionValues() {
  return Array.from(
    new Set(codelistItems.value.map((codelist) => codelist.submission_value))
  )
}

function newTermNamesVersion() {
  if (!latestName.value?.term_uid) {
    return
  }

  controlledTerminology
    .newCodelistTermNamesVersion(latestName.value.term_uid)
    .then(() => {
      fetchTermNames()
    })
}

function approveTermNamesVersion() {
  if (!latestName.value?.term_uid) {
    return
  }

  controlledTerminology
    .approveCodelistTermNames(latestName.value.term_uid)
    .then(() => {
      fetchTermNames()
    })
}

function inactivateTermNamesVersion() {
  if (!latestName.value?.term_uid) {
    return
  }

  controlledTerminology
    .inactivateCodelistTermNames(latestName.value.term_uid)
    .then(() => {
      fetchTermNames()
    })
}

function reactivateTermNamesVersion() {
  if (!latestName.value?.term_uid) {
    return
  }

  controlledTerminology
    .reactivateCodelistTermNames(latestName.value.term_uid)
    .then(() => {
      fetchTermNames()
    })
}

function newTermAttributesVersion() {
  if (!latestAttribute.value?.term_uid) {
    return
  }

  controlledTerminology
    .newCodelistTermAttributesVersion(latestAttribute.value.term_uid)
    .then(() => {
      fetchTermAttributes()
    })
}

function approveTermAttributesVersion() {
  if (!latestAttribute.value?.term_uid) {
    return
  }

  controlledTerminology
    .approveCodelistTermAttributes(latestAttribute.value.term_uid)
    .then(() => {
      fetchTermAttributes()
    })
}

function inactivateTermAttributesVersion() {
  if (!latestAttribute.value?.term_uid) {
    return
  }

  controlledTerminology
    .inactivateCodelistTermAttributes(latestAttribute.value.term_uid)
    .then(() => {
      fetchTermAttributes()
    })
}

function reactivateTermAttributesVersion() {
  if (!latestAttribute.value?.term_uid) {
    return
  }

  controlledTerminology
    .reactivateCodelistTermAttributes(latestAttribute.value.term_uid)
    .then(() => {
      fetchTermAttributes()
    })
}

const historyHeaders = ref([])
const historyItems = ref([])
const historyType = ref('')
const showHistory = ref(false)

const historyTitleLabel = computed(() => {
  return historyType.value === 'termName'
    ? t('TrialSummaryParameters.history_label_name', {
        term: props.termUid,
      })
    : t('TrialSummaryParameters.history_label_attributes', {
        term: props.termUid,
      })
})

async function openSponsorValuesHistory() {
  historyType.value = 'termName'
  historyHeaders.value = [
    {
      title: t('TrialSummaryParameters.sponsor_name'),
      key: 'sponsor_preferred_name',
    },
    {
      title: t('CodelistTermDetail.sentence_case_name'),
      key: 'sponsor_preferred_name_sentence_case',
    },
    { title: t('_global.status'), key: 'status' },
    { title: t('_global.version'), key: 'version' },
  ]
  const resp = await controlledTerminology.getCodelistTermNamesVersions(
    props.termUid
  )
  historyItems.value = resp.data
  showHistory.value = true
}

async function openCTValuesHistory() {
  historyType.value = 'termAttributes'
  historyHeaders.value = [
    { title: t('CodelistTermDetail.concept_id'), key: 'concept_id' },
    {
      title: t('CodeListDetail.nci_pref_name'),
      key: 'nci_preferred_name',
    },
    { title: t('_global.definition'), key: 'definition' },
    { title: t('_global.status'), key: 'status' },
    { title: t('_global.version'), key: 'version' },
  ]
  const resp = await controlledTerminology.getCodelistTermAttributesVersions(
    props.termUid
  )
  historyItems.value = resp.data
  showHistory.value = true
}

function closeHistory() {
  showHistory.value = false
  historyType.value = ''
}
</script>

<style scoped>
.trial-parameter-details {
  padding: 16px;
}

.details-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  color: rgb(var(--v-theme-nnTrueBlue));
}

.details-table td {
  padding: 0 12px 0 0;
  vertical-align: top;
  word-break: break-word;
}

.details-table__labels td {
  font-size: 0.85rem;
  color: rgb(var(--v-theme-nnTrueBlue));
  padding-bottom: 0;
}

.details-table__values td {
  font-size: 1.1rem;
  font-weight: 700;
  padding-top: 0;
  padding-bottom: 8px;
}

.details-table__labels:not(:first-child) td {
  padding-top: 16px;
}
</style>
