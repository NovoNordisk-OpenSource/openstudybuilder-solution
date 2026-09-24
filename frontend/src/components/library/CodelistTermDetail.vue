<template>
  <div>
    <div class="mt-4 mb-6 d-flex align-center">
      <v-spacer />
      <v-menu location="start">
        <template #activator="{ props }">
          <div>
            <v-btn
              data-cy="table-item-action-button"
              icon="mdi-menu"
              color="primary"
              v-bind="props"
              class="pb-3"
            />
          </div>
        </template>
        <v-card elevation="0" color="transparent" class="mt-n1">
          <v-card-item>
            <div class="mb-1">
              <DataTableExportButton type="endpoint" data-url="" />
            </div>
          </v-card-item>
        </v-card>
      </v-menu>
    </div>
    <div class="pa-4 v-label">
      {{ $t('CodelistTermDetail.sponsor_title') }}
    </div>
    <v-table :aria-label="$t('CodelistTermDetail.sponsor_title')">
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
          <td>{{ termNames.sponsor_preferred_name }}</td>
          <td data-cy="names-status" rowspan="2">
            <StatusChip :status="termNames.status" />
          </td>
          <td rowspan="2">
            {{ $filters.date(termNames.start_date) }}
          </td>
          <td data-cy="names-version" rowspan="2">
            {{ termNames.version }}
          </td>
          <td rowspan="2">
            <v-btn
              v-if="
                termNames.possible_actions.find((action) => action === 'edit')
              "
              data-cy="edit-sponsor-values"
              icon="mdi-pencil-outline"
              color="primary"
              :title="$t('CodelistTermDetail.edit_names')"
              variant="text"
              @click="showNamesForm = true"
            />
            <v-btn
              v-if="
                termNames.possible_actions.find(
                  (action) => action === 'approve'
                )
              "
              data-cy="approve-term-sponsor-values"
              color="success"
              icon="mdi-check-decagram"
              :title="$t('CodelistTermDetail.approve_names')"
              variant="text"
              @click="approveTermNames"
            />
            <v-btn
              v-if="
                termNames.possible_actions.find(
                  (action) => action === 'new_version'
                )
              "
              data-cy="create-new-sponsor-values"
              color="primary"
              icon="mdi-plus-circle-outline"
              :title="$t('CodelistTermDetail.new_names_version')"
              variant="text"
              @click="newTermNamesVersion"
            />
            <v-btn
              v-if="
                termNames.possible_actions.find(
                  (action) => action === 'inactivate'
                )
              "
              color="warning"
              icon="mdi-close-octagon-outline"
              :title="$t('CodelistTermDetail.inactivate_names')"
              variant="text"
              @click="inactivateTermNames"
            />
            <v-btn
              v-if="
                termNames.possible_actions.find(
                  (action) => action === 'reactivate'
                )
              "
              color="primary"
              icon="mdi-undo-variant"
              :title="$t('CodelistTermDetail.reactivate_names')"
              variant="text"
              @click="reactivateTermNames"
            />
            <v-btn
              v-if="
                termNames.possible_actions.find((action) => action === 'delete')
              "
              icon="mdi-delete-outline"
              color="error"
              :title="$t('CodelistTermDetail.delete_names')"
              variant="text"
              @click="deleteTermNames()"
            />
            <v-btn
              data-cy="term-sponsor-version-history"
              icon="mdi-history"
              :title="$t('CodeListDetail.history')"
              variant="text"
              @click="openSponsorValuesHistory"
            />
          </td>
        </tr>
        <tr>
          <td>{{ $t('CodelistTermDetail.sentence_case_name') }}</td>
          <td>{{ termNames.sponsor_preferred_name_sentence_case }}</td>
        </tr>
      </tbody>
    </v-table>

    <div class="v-label pa-4 mt-6">
      {{ $t('CodelistTermDetail.attributes_title') }}
    </div>
    <v-table :aria-label="$t('CodelistTermDetail.attributes_title')">
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
          <td>{{ $t('CodelistTermDetail.concept_id') }}</td>
          <td>{{ termAttributes.concept_id }}</td>
          <td data-cy="attributes-status" rowspan="5">
            <StatusChip :status="termAttributes.status" />
          </td>
          <td rowspan="5">
            {{ $filters.date(termAttributes.start_date) }}
          </td>
          <td data-cy="attributes-version" rowspan="5">
            {{ termAttributes.version }}
          </td>
          <td rowspan="5">
            <v-btn
              v-if="
                termAttributes.possible_actions.find(
                  (action) => action === 'edit'
                )
              "
              icon="mdi-pencil-outline"
              color="primary"
              variant="text"
              :title="$t('CodelistTermDetail.edit_attributes')"
              @click="showAttributesForm = true"
            />
            <v-btn
              v-if="
                termAttributes.possible_actions.find(
                  (action) => action === 'approve'
                )
              "
              data-cy="approve-term-attributes-values"
              color="success"
              icon="mdi-check-decagram"
              :title="$t('CodelistTermDetail.approve_attributes')"
              variant="text"
              @click="approveTermAttributes"
            />
            <v-btn
              v-if="
                termAttributes.possible_actions.find(
                  (action) => action === 'new_version'
                )
              "
              color="primary"
              icon="mdi-plus-circle-outline"
              :title="$t('CodelistTermDetail.new_attributes_version')"
              variant="text"
              @click="newTermAttributesVersion"
            />
            <v-btn
              v-if="
                termAttributes.possible_actions.find(
                  (action) => action === 'inactivate'
                )
              "
              color="warning"
              icon="mdi-close-octagon-outline"
              :title="$t('CodelistTermDetail.inactivate_attributes')"
              variant="text"
              @click="inactivateTermAttributes"
            />
            <v-btn
              v-if="
                termAttributes.possible_actions.find(
                  (action) => action === 'reactivate'
                )
              "
              color="primary"
              icon="mdi-undo-variant"
              :title="$t('CodelistTermDetail.reactivate_attributes')"
              variant="text"
              @click="reactivateTermAttributes"
            />
            <v-btn
              v-if="
                termAttributes.possible_actions.find(
                  (action) => action === 'delete'
                )
              "
              icon="mdi-delete-outline"
              color="error"
              :title="$t('CodelistTermDetail.delete_attributes')"
              variant="text"
              @click="deleteTermAttributes()"
            />
            <v-btn
              icon="mdi-history"
              :title="$t('CodeListDetail.history')"
              variant="text"
              @click="openCTValuesHistory"
            />
          </td>
        </tr>
        <tr>
          <td>{{ $t('CodelistTermDetail.nci_pref_name') }}</td>
          <td>{{ termAttributes.nci_preferred_name }}</td>
        </tr>
        <tr>
          <td>{{ $t('_global.definition') }}</td>
          <td>{{ termAttributes.definition }}</td>
        </tr>
      </tbody>
    </v-table>

    <div class="v-label pa-4 mt-6">
      {{ $t('CodelistTermDetail.parents') }}
    </div>
    <v-btn
      class="ml-2"
      size="small"
      variant="outlined"
      color="nnBaseBlue"
      data-cy="add-term-parent-button"
      :title="$t('CodelistTermDetail.add_parent')"
      :disabled="!checkPermission($roles.LIBRARY_WRITE)"
      icon="mdi-plus"
      @click.stop="showAddParentForm = true"
    />
    <v-table :aria-label="$t('CodelistTermDetail.sponsor_title')">
      <thead>
        <tr class="bg-greyBackground">
          <th width="10%">
            {{ $t('CodelistTermDetail.relationship_type') }}
          </th>
          <th width="5%">
            {{ $t('_global.library') }}
          </th>
          <th width="20%">
            {{ $t('CodeListDetail.sponsor_pref_name') }}
          </th>
          <th width="10%">
            {{ $t('CodelistTermDetail.concept_id') }}
          </th>
          <th width="7%">
            {{ $t('CodelistTermDetail.name_status') }}
          </th>
          <th width="8%">
            {{ $t('CodelistTermDetail.name_version') }}
          </th>
          <th width="10%">
            {{ $t('CodelistTermDetail.name_date') }}
          </th>
          <th width="7%">
            {{ $t('CodelistTermDetail.attributes_status') }}
          </th>
          <th width="8%">
            {{ $t('CodelistTermDetail.attributes_version') }}
          </th>
          <th width="10%">
            {{ $t('CodelistTermDetail.attributes_date') }}
          </th>
          <th width="5%">
            {{ $t('_global.actions') }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(parent, index) in termParents.parents"
          :key="`item-${index}`"
        >
          <td>{{ parent.relationship_type }}</td>
          <td>{{ parent.attributes.library_name }}</td>
          <td>
            <router-link
              :to="{
                name: 'CodelistTermDetail',
                params: {
                  term_id: parent.attributes.term_uid,
                },
              }"
            >
              {{ parent.name.sponsor_preferred_name }}
            </router-link>
          </td>
          <td>{{ parent.attributes.concept_id }}</td>
          <td>{{ parent.name.status }}</td>
          <td>{{ parent.name.version }}</td>
          <td>{{ $filters.date(parent.name.start_date) }}</td>
          <td>{{ parent.attributes.status }}</td>
          <td>{{ parent.attributes.version }}</td>
          <td>{{ $filters.date(parent.attributes.start_date) }}</td>
          <td>
            <v-btn
              icon="mdi-delete-outline"
              :title="$t('CodelistTermDetail.remove_parent')"
              variant="text"
              @click="openRemoveParentForm(parent)"
            />
          </td>
        </tr>
      </tbody>
    </v-table>

    <div class="v-label pa-4 mt-6">
      {{ $t('CodelistTermDetail.children') }}
    </div>
    <v-btn
      class="ml-2"
      size="small"
      variant="outlined"
      color="nnBaseBlue"
      data-cy="add-term-parent-button"
      :title="$t('CodelistTermDetail.add_child')"
      :disabled="!checkPermission($roles.LIBRARY_WRITE)"
      icon="mdi-plus"
      @click.stop="showAddChildForm = true"
    />
    <v-table :aria-label="$t('CodelistTermDetail.sponsor_title')">
      <thead>
        <tr class="bg-greyBackground">
          <th width="10%">
            {{ $t('CodelistTermDetail.relationship_type') }}
          </th>
          <th width="5%">
            {{ $t('_global.library') }}
          </th>
          <th width="20%">
            {{ $t('CodeListDetail.sponsor_pref_name') }}
          </th>
          <th width="10%">
            {{ $t('CodelistTermDetail.concept_id') }}
          </th>
          <th width="7%">
            {{ $t('CodelistTermDetail.name_status') }}
          </th>
          <th width="8%">
            {{ $t('CodelistTermDetail.name_version') }}
          </th>
          <th width="10%">
            {{ $t('CodelistTermDetail.name_date') }}
          </th>
          <th width="7%">
            {{ $t('CodelistTermDetail.attributes_status') }}
          </th>
          <th width="8%">
            {{ $t('CodelistTermDetail.attributes_version') }}
          </th>
          <th width="10%">
            {{ $t('CodelistTermDetail.attributes_date') }}
          </th>
          <th width="5%">
            {{ $t('_global.actions') }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(child, index) in termParents.children"
          :key="`item-${index}`"
        >
          <td>{{ child.relationship_type }}</td>
          <td>{{ child.attributes.library_name }}</td>
          <td>
            <router-link
              :to="{
                name: 'CodelistTermDetail',
                params: {
                  term_id: child.attributes.term_uid,
                },
              }"
            >
              {{ child.name.sponsor_preferred_name }}
            </router-link>
          </td>
          <td>{{ child.attributes.concept_id }}</td>
          <td>{{ child.name.status }}</td>
          <td>{{ child.name.version }}</td>
          <td>{{ $filters.date(child.name.start_date) }}</td>
          <td>{{ child.attributes.status }}</td>
          <td>{{ child.attributes.version }}</td>
          <td>{{ $filters.date(child.attributes.start_date) }}</td>
          <td>
            <v-btn
              icon="mdi-delete-outline"
              :title="$t('CodelistTermDetail.remove_child')"
              variant="text"
              @click="openRemoveChildForm(child)"
            />
          </td>
        </tr>
      </tbody>
    </v-table>

    <div class="v-label pa-4 mt-6">
      {{ $t('CodelistTermDetail.code_lists') }}
    </div>
    <v-btn
      class="ml-2"
      size="small"
      variant="outlined"
      color="nnBaseBlue"
      data-cy="add-term-button"
      :title="$t('CodelistTermDetail.add_to_codelists')"
      :disabled="!checkPermission($roles.LIBRARY_WRITE)"
      icon="mdi-plus"
      @click.stop="showAddToCodelistForm = true"
    />
    <v-table :aria-label="$t('CodelistTermDetail.sponsor_title')">
      <thead>
        <tr class="bg-greyBackground">
          <th width="10%">
            {{ $t('_global.library') }}
          </th>
          <th width="15%">
            {{ $t('CodelistTermDetail.code_list_name') }}
          </th>
          <th width="10%">
            {{ $t('CodelistTermDetail.codelist_cid') }}
          </th>
          <th width="20%">
            {{ $t('CodelistTermDetail.codelist_submission_value') }}
          </th>
          <th width="20%">
            {{ $t('CodelistTermDetail.submission_value') }}
          </th>
          <th width="10%">
            {{ $t('CodelistTermDetail.order') }}
          </th>
          <th width="10%">
            {{ $t('_global.modified') }}
          </th>
          <th width="5%">
            {{ $t('_global.actions') }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(cl, index) in termCodelists.codelists"
          :key="`item-${index}`"
        >
          <td>{{ cl.library_name }}</td>
          <td>{{ cl.codelist_name }}</td>
          <td>{{ cl.codelist_concept_id }}</td>
          <td>{{ cl.codelist_submission_value }}</td>
          <td>{{ cl.submission_value }}</td>
          <td>{{ cl.order }}</td>
          <td>{{ $filters.date(cl.start_date) }}</td>
          <td>
            <v-btn
              icon="mdi-pencil-outline"
              :title="$t('CodelistTermDetail.edit_order_submval')"
              variant="text"
              @click="openOrderSubmvalForm(cl)"
            />
          </td>
        </tr>
      </tbody>
    </v-table>

    <v-dialog
      v-model="showNamesForm"
      persistent
      max-width="1024px"
      @keydown.esc="showNamesForm = false"
    >
      <CodelistTermNamesForm
        v-model="termNames"
        @close="showNamesForm = false"
      />
    </v-dialog>
    <v-dialog
      v-model="showAttributesForm"
      persistent
      max-width="1024px"
      @keydown.esc="showAttributesForm = false"
    >
      <CodelistTermAttributesForm
        v-model="termAttributes"
        @close="showAttributesForm = false"
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
    <CodelistTermOrderSubmvalForm
      v-if="showOrderSubmvalForm"
      :open="showOrderSubmvalForm"
      :term-uid="termUid"
      :codelist-uid="selectedCodelist?.codelist_uid"
      :submission-value="selectedCodelist?.submission_value"
      :submission-values="listSubmissionValues()"
      :codelist-name="selectedCodelist?.codelist_name"
      :term-name="termNames.sponsor_preferred_name"
      :order="selectedCodelist?.order"
      @close="closeOrderSubmvalForm"
    />
    <v-dialog
      v-model="showAddToCodelistForm"
      persistent
      max-width="1024px"
      @keydown.esc="showAddToCodelistForm = false"
    >
      <CodelistTermAddToCodelistsForm
        :term-uid="termUid"
        :term-name="termNames.sponsor_preferred_name"
        :submission-values="listSubmissionValues()"
        @close="closeAddToCodelistForm()"
      />
    </v-dialog>
    <v-dialog
      v-model="showAddParentForm"
      persistent
      max-width="1024px"
      @keydown.esc="showAddParentForm = false"
    >
      <AddParentTermForm
        :relationship="'parent'"
        :term-uid="termUid"
        @close="closeAddParentForm()"
      />
    </v-dialog>
    <v-dialog
      v-model="showAddChildForm"
      persistent
      max-width="1024px"
      @keydown.esc="showAddChildForm = false"
    >
      <AddParentTermForm
        :relationship="'child'"
        :term-uid="termUid"
        @close="closeAddChildForm()"
      />
    </v-dialog>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  </div>
</template>

<script>
import controlledTerminology from '@/api/controlledTerminology'
import CodelistTermAttributesForm from '@/components/library/CodelistTermAttributesForm.vue'
import CodelistTermAddToCodelistsForm from '@/components/library/CodelistTermAddToCodelistsForm.vue'
import CodelistTermNamesForm from '@/components/library/CodelistTermNamesForm.vue'
import CodelistTermOrderSubmvalForm from '@/components/library/CodelistTermOrderSubmvalForm.vue'
import DataTableExportButton from '@/components/tools/DataTableExportButton.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import { useAccessGuard } from '@/composables/accessGuard'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import AddParentTermForm from '@/components/library/AddParentTermForm.vue'

export default {
  components: {
    CodelistTermAttributesForm,
    CodelistTermNamesForm,
    CodelistTermOrderSubmvalForm,
    CodelistTermAddToCodelistsForm,
    DataTableExportButton,
    HistoryTable,
    StatusChip,
    ConfirmDialog,
    AddParentTermForm,
  },
  inject: ['notificationHub'],
  props: {
    termUid: {
      type: String,
      default: null,
    },
  },
  setup() {
    const accessGuard = useAccessGuard()
    return {
      ...accessGuard,
    }
  },
  data() {
    return {
      termCodelists: { codelists: [] },
      historyType: '',
      historyItems: [],
      historyHeaders: [],
      showAttributesForm: false,
      showHistory: false,
      showNamesForm: false,
      showOrderSubmvalForm: false,
      showAddToCodelistForm: false,
      showAddChildForm: false,
      showAddParentForm: false,
      term: { term_uid: this.termUid },
      termNames: { possible_actions: [] },
      termAttributes: { possible_actions: [] },
      termParents: { parents: [], children: [] },
      selectedCodelist: null,
    }
  },
  computed: {
    historyTitleLabel() {
      return this.historyType === 'termName'
        ? this.$t('CodelistTermTable.history_label_name', {
            term: this.termUid,
          })
        : this.$t('CodelistTermTable.history_label_attributes', {
            term: this.termUid,
          })
    },
  },
  watch: {
    termUid: {
      handler(val) {
        if (val) {
          this.fetchData()
        }
      },
      immediate: true,
    },
  },
  mounted() {
    this.fetchData()
  },
  methods: {
    fetchData() {
      this.fetchTermNames()
      this.fetchTermAttributes()
      this.fetchTermCodelists()
      this.fetchTermParents()
    },
    fetchTermCodelists() {
      controlledTerminology.getTermCodelists(this.termUid).then((resp) => {
        this.termCodelists = resp.data
      })
    },
    listSubmissionValues() {
      return Array.from(
        new Set(
          this.termCodelists.codelists.map(
            (codelist) => codelist.submission_value
          )
        )
      )
    },
    fetchTermParents() {
      controlledTerminology.getTermParents(this.termUid).then((resp) => {
        this.termParents = resp.data
      })
    },
    fetchTermNames() {
      controlledTerminology.getCodelistTermNames(this.termUid).then((resp) => {
        this.termNames = resp.data
      })
    },
    newTermNamesVersion() {
      controlledTerminology
        .newCodelistTermNamesVersion(this.termNames.term_uid)
        .then((resp) => {
          this.termNames = resp.data
          this.notificationHub.add({
            msg: this.$t('CodelistTermDetail.new_names_version_success'),
          })
        })
    },
    approveTermNames() {
      controlledTerminology
        .approveCodelistTermNames(this.termNames.term_uid)
        .then((resp) => {
          this.termNames = resp.data
          this.notificationHub.add({
            msg: this.$t('CodelistTermDetail.approve_names_success'),
          })
        })
    },
    inactivateTermNames() {
      controlledTerminology
        .inactivateCodelistTermNames(this.termNames.term_uid)
        .then((resp) => {
          this.termNames = resp.data
          this.notificationHub.add({
            msg: this.$t('CodelistTermDetail.inactivate_names_success'),
          })
        })
    },
    reactivateTermNames() {
      controlledTerminology
        .reactivateCodelistTermNames(this.termNames.term_uid)
        .then((resp) => {
          this.termNames = resp.data
          this.notificationHub.add({
            msg: this.$t('CodelistTermDetail.reactivate_names_success'),
          })
        })
    },
    deleteTermNames() {
      controlledTerminology
        .deleteCodelistTermNames(this.termNames.term_uid)
        .then(() => {
          this.fetchTermNames()
          this.notificationHub.add({
            msg: this.$t('CodelistTermDetail.delete_names_success'),
          })
        })
    },
    fetchTermAttributes() {
      controlledTerminology
        .getCodelistTermAttributes(this.termUid)
        .then((resp) => {
          this.termAttributes = resp.data
        })
    },
    newTermAttributesVersion() {
      controlledTerminology
        .newCodelistTermAttributesVersion(this.termAttributes.term_uid)
        .then((resp) => {
          this.termAttributes = resp.data
          this.notificationHub.add({
            msg: this.$t('CodelistTermDetail.new_attributes_version_success'),
          })
        })
    },
    approveTermAttributes() {
      controlledTerminology
        .approveCodelistTermAttributes(this.termAttributes.term_uid)
        .then((resp) => {
          this.termAttributes = resp.data
          this.notificationHub.add({
            msg: this.$t('CodelistTermDetail.approve_attributes_success'),
          })
        })
    },
    inactivateTermAttributes() {
      controlledTerminology
        .inactivateCodelistTermAttributes(this.termAttributes.term_uid)
        .then((resp) => {
          this.termAttributes = resp.data
          this.notificationHub.add({
            msg: this.$t('CodelistTermDetail.inactivate_attributes_success'),
          })
        })
    },
    reactivateTermAttributes() {
      controlledTerminology
        .reactivateCodelistTermAttributes(this.termAttributes.term_uid)
        .then((resp) => {
          this.termAttributes = resp.data
          this.notificationHub.add({
            msg: this.$t('CodelistTermDetail.reactivate_attributes_success'),
          })
        })
    },
    deleteTermAttributes() {
      controlledTerminology
        .deleteCodelistTermAttributes(this.termNames.term_uid)
        .then(() => {
          this.fetchTermAttributes()
          this.notificationHub.add({
            msg: this.$t('CodelistTermDetail.delete_attributes_success'),
          })
        })
    },
    goToTerm(term) {
      this.$router.push({
        name: 'CodelistTermDetail',
        params: { term_id: term.term_uid },
      })
      this.notificationHub.add({
        msg: this.$t('CodelistTermCreationForm.add_success'),
      })
    },
    async openSponsorValuesHistory() {
      this.historyType = 'termName'
      this.historyHeaders = [
        {
          title: this.$t('CodeListDetail.sponsor_pref_name'),
          key: 'sponsor_preferred_name',
        },
        {
          title: this.$t('CodelistTermDetail.sentence_case_name'),
          key: 'sponsor_preferred_name_sentence_case',
        },
        { title: this.$t('CodelistTermDetail.order'), key: 'order' },
        { title: this.$t('_global.status'), key: 'status' },
        { title: this.$t('_global.version'), key: 'version' },
      ]
      const resp = await controlledTerminology.getCodelistTermNamesVersions(
        this.termUid
      )

      this.historyItems = resp.data.map((item) => {
        item.order = null //this.getTermOrderInCodelist(item, this.codelistUid)
        return item
      })
      this.showHistory = true
    },
    async openCTValuesHistory() {
      this.historyType = 'termAttributes'
      this.historyHeaders = [
        { title: this.$t('CodelistTermDetail.concept_id'), key: 'concept_id' },
        {
          title: this.$t('CodeListDetail.nci_pref_name'),
          key: 'nci_preferred_name',
        },
        { title: this.$t('_global.definition'), key: 'definition' },
        { title: this.$t('_global.status'), key: 'status' },
        { title: this.$t('_global.version'), key: 'version' },
      ]
      const resp =
        await controlledTerminology.getCodelistTermAttributesVersions(
          this.termUid
        )
      this.historyItems = resp.data
      this.showHistory = true
    },
    closeHistory() {
      this.showHistory = false
      this.historyType = ''
    },
    async openOrderSubmvalForm(codelist) {
      this.selectedCodelist = codelist
      this.showOrderSubmvalForm = true
    },
    async openRemoveParentForm(parent) {
      const options = {
        type: 'warning',
        cancelLabel: this.$t('_global.cancel'),
        agreeLabel: this.$t('_global.continue'),
      }
      if (
        await this.$refs.confirm.open(
          this.$t('CodelistTermDetail.remove_parent_confirm'),
          options
        )
      ) {
        controlledTerminology
          .deleteTermParent(
            this.termUid,
            parent.attributes.term_uid,
            parent.relationship_type
          )
          .then(() => {
            this.fetchTermParents()
            this.notificationHub.add({
              msg: this.$t('CodelistTermDetail.remove_parent_success'),
            })
          })
      }
    },
    async openRemoveChildForm(child) {
      const options = {
        type: 'warning',
        cancelLabel: this.$t('_global.cancel'),
        agreeLabel: this.$t('_global.continue'),
      }
      if (
        await this.$refs.confirm.open(
          this.$t('CodelistTermDetail.remove_child_confirm'),
          options
        )
      ) {
        controlledTerminology
          .deleteTermParent(
            child.attributes.term_uid,
            this.termUid,
            child.relationship_type
          )
          .then(() => {
            this.fetchTermParents()
            this.notificationHub.add({
              msg: this.$t('CodelistTermDetail.remove_child_success'),
            })
          })
      }
    },
    closeAddParentForm() {
      this.showAddParentForm = false
      this.fetchTermParents()
    },
    closeAddChildForm() {
      this.showAddChildForm = false
      this.fetchTermParents()
    },
    closeAddToCodelistForm() {
      this.showAddToCodelistForm = false
      this.fetchTermCodelists()
    },
    closeOrderSubmvalForm() {
      this.showOrderSubmvalForm = false
      this.fetchTermCodelists()
    },
  },
}
</script>
