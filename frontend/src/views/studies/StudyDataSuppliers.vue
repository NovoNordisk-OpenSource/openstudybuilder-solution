<template>
  <div class="px-4">
    <div class="page-title d-flex align-center justify-space-between">
      <div class="d-flex align-center">
        <span>{{
          $t('StudyDataSuppliers.page_title_overview', { studyId: studyId })
        }}</span>
        <HelpButtonWithPanels
          :help-text="$t('_help.StudyDataSuppliers.general')"
          :items="helpItems"
        />
      </div>
      <div class="d-flex">
        <v-btn
          icon
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          class="mr-4"
          :title="$t('NNTableTooltips.edit')"
          @click="goToEditMode"
        >
          <v-icon>mdi-pencil-outline</v-icon>
        </v-btn>
        <v-btn
          icon
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          class="mr-4"
          :title="$t('NNTableTooltips.download')"
          @click="handleDownload"
        >
          <v-icon>mdi-download-outline</v-icon>
        </v-btn>
        <v-btn
          icon
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          :title="$t('NNTableTooltips.history')"
          @click="openHistory"
        >
          <v-icon>mdi-history</v-icon>
        </v-btn>
      </div>
    </div>

    <v-card elevation="1">
      <v-tabs v-model="tab" bg-color="white">
        <v-tab value="overview">{{
          $t('StudyDataSuppliers.overview_tab')
        }}</v-tab>
        <v-tab value="list">{{ $t('StudyDataSuppliers.list_tab') }}</v-tab>
      </v-tabs>

      <v-window v-model="tab">
        <!-- Overview Tab -->
        <v-window-item value="overview">
          <div v-if="loading" class="text-center pa-4">
            <v-progress-circular indeterminate color="primary" />
          </div>
          <div v-else class="pa-6">
            <!-- Info alert -->
            <v-alert
              type="info"
              density="compact"
              class="mb-4"
              :text="$t('StudyDataSuppliers.info_message')"
            />
            <!-- Group suppliers by type -->
            <div
              v-for="(suppliers, typeName) in groupedSuppliers"
              :key="typeName"
              class="mb-6"
            >
              <div class="supplier-type-section pa-4">
                <div class="text-headline-small mb-4">
                  {{ $t('StudyDataSuppliers.supplier_data_type') }}
                  <strong>{{ typeName }}</strong>
                </div>
                <div
                  v-if="suppliers.length === 0"
                  class="pa-4 bg-grey-lighten-3 rounded"
                >
                  <div class="text-body-large">
                    {{ $t('StudyDataSuppliers.empty_state') }}
                  </div>
                </div>
                <div v-else>
                  <div
                    v-for="supplier in suppliers"
                    :key="supplier.study_data_supplier_uid"
                    class="mb-3 pa-4 bg-grey-lighten-3 rounded"
                  >
                    <div class="text-body-large">
                      {{ $t('StudyDataSuppliers.data_supplier_label') }}
                      <strong>{{ supplier.name }}</strong>
                    </div>
                    <div
                      v-if="supplier.blinded !== null"
                      class="text-body-medium mt-1"
                    >
                      {{ $t('StudyDataSuppliers.blinded_field') }}:
                      <strong>
                        {{
                          supplier.blinded
                            ? $t('_global.yes')
                            : $t('_global.no')
                        }}
                      </strong>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </v-window-item>

        <!-- List Tab -->
        <v-window-item value="list">
          <div class="pa-4">
            <NNTable
              ref="tableRef"
              table-id="studies-data-suppliers-table"
              :headers="headers"
              :items="dataSuppliers"
              :items-length="total"
              item-value="study_data_supplier_uid"
              :show-filter-bar-by-default="true"
              :initial-sort-by="[
                { key: 'study_data_supplier_order', order: 'asc' },
              ]"
              :loading="loading"
              hide-default-switches
              @filter="fetchDataSuppliers"
            >
              <template #afterSwitches>
                <div class="ml-4">
                  <v-switch
                    v-model="showReorderMode"
                    :label="$t('StudyDataSuppliers.reorder_content')"
                    class="mr-6"
                    hide-details
                  />
                </div>
              </template>
              <template #[`item.study_data_supplier_type`]="{ item }">
                {{ item.study_data_supplier_type?.term_name || '-' }}
              </template>
              <template #[`item.description`]="{ item }">
                {{ item.description || '-' }}
              </template>
              <template #[`item.library`]="{ item }">
                {{ item.library_name || '-' }}
              </template>
              <template #[`item.origin_type`]="{ item }">
                {{ item.origin_type?.term_name || '-' }}
              </template>
              <template #[`item.origin_source`]="{ item }">
                {{ item.origin_source?.name || '-' }}
              </template>
              <template #[`item.ui_base_url`]="{ item }">
                {{ item.ui_base_url || '-' }}
              </template>
              <template #[`item.api_base_url`]="{ item }">
                {{ item.api_base_url || '-' }}
              </template>
              <template #[`item.start_date`]="{ item }">
                {{ formatDate(item.start_date) }}
              </template>
              <template #[`item.author_username`]="{ item }">
                {{ item.author_username || '-' }}
              </template>
              <template #[`item.blinded`]="{ item }">
                {{
                  item.blinded === null
                    ? $t('_global.tbd')
                    : item.blinded
                      ? $t('_global.yes')
                      : $t('_global.no')
                }}
              </template>
              <template #[`item.actions`]="{ item }">
                <div class="pr-0 mr-0">
                  <v-menu>
                    <template #activator="{ props }">
                      <v-btn
                        icon="mdi-dots-vertical"
                        variant="text"
                        size="small"
                        v-bind="props"
                      />
                    </template>
                    <v-list>
                      <v-list-item @click="openEditDialog(item)">
                        <template #prepend>
                          <v-icon>mdi-pencil</v-icon>
                        </template>
                        <v-list-item-title>{{
                          $t('StudyDataSuppliers.edit_action')
                        }}</v-list-item-title>
                      </v-list-item>
                      <v-list-item @click="handleDelete(item)">
                        <template #prepend>
                          <v-icon>mdi-delete</v-icon>
                        </template>
                        <v-list-item-title>{{
                          $t('StudyDataSuppliers.delete_action')
                        }}</v-list-item-title>
                      </v-list-item>
                      <v-list-item @click="openAuditTrail(item)">
                        <template #prepend>
                          <v-icon>mdi-history</v-icon>
                        </template>
                        <v-list-item-title>{{
                          $t('StudyDataSuppliers.audit_trail_action')
                        }}</v-list-item-title>
                      </v-list-item>
                    </v-list>
                  </v-menu>
                </div>
              </template>
            </NNTable>
          </div>
        </v-window-item>
      </v-window>
    </v-card>

    <!-- Edit Dialog -->
    <v-dialog v-model="dialog" max-width="800px" persistent>
      <v-card>
        <v-card-title>
          <span class="text-headline-medium">{{
            $t('StudyDataSuppliers.edit_dialog_title')
          }}</span>
        </v-card-title>
        <v-card-text>
          <v-form ref="form" v-model="valid">
            <v-row>
              <v-col cols="10">
                <SelectDataSupplier
                  v-model="formData.data_supplier_uid"
                  :label="$t('StudyDataSuppliers.data_supplier_field')"
                  :required="true"
                />
              </v-col>
              <v-col cols="2">
                <v-select
                  v-model="formData.blinded"
                  :items="blindedOptions"
                  :label="$t('StudyDataSuppliers.blinded_field')"
                  hide-details
                />
              </v-col>
              <v-col cols="10">
                <SelectDataSupplierType
                  v-model="formData.study_data_supplier_type_uid"
                  :label="
                    $t('StudyDataSuppliers.study_data_supplier_type_field')
                  "
                  :required="false"
                />
              </v-col>
              <v-col cols="2">
                <v-text-field
                  v-model="formData.study_data_supplier_order"
                  :label="$t('_global.order')"
                  type="number"
                  :rules="[(v) => !!v || 'Order is required']"
                />
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn color="grey" variant="text" @click="closeDialog">
            {{ $t('StudyDataSuppliers.cancel_button') }}
          </v-btn>
          <v-btn
            color="primary"
            variant="elevated"
            :disabled="!valid"
            @click="handleSave"
          >
            {{ $t('StudyDataSuppliers.save_button') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Audit Trail Dialog -->
    <v-dialog v-model="auditDialog" max-width="1200px">
      <v-card>
        <v-card-title>
          <span class="text-headline-medium">{{
            $t('StudyDataSuppliers.audit_trail_title')
          }}</span>
        </v-card-title>
        <v-card-text>
          <div v-if="auditTrailLoading" class="text-center pa-4">
            <v-progress-circular indeterminate color="primary" />
          </div>
          <v-table v-else>
            <thead>
              <tr>
                <th>{{ $t('HistoryTable.date') }}</th>
                <th>{{ $t('_global.user') }}</th>
                <th>{{ $t('HistoryTable.change_type') }}</th>
                <th>{{ $t('_global.name') }}</th>
                <th>{{ $t('_global.order') }}</th>
                <th>{{ $t('StudyDataSuppliers.blinded_field') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(entry, index) in auditTrail" :key="index">
                <td>{{ formatDate(entry.start_date) }}</td>
                <td>{{ entry.author_username }}</td>
                <td>{{ entry.change_type }}</td>
                <td>{{ entry.name }}</td>
                <td>{{ entry.order }}</td>
                <td>
                  {{
                    entry.blinded === null
                      ? $t('_global.tbd')
                      : entry.blinded
                        ? $t('_global.yes')
                        : $t('_global.no')
                  }}
                </td>
              </tr>
            </tbody>
          </v-table>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn color="primary" variant="text" @click="auditDialog = false">
            {{ $t('_global.close') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- History Dialog -->
    <v-dialog
      v-model="showHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeHistory"
    >
      <HistoryTable
        :title="$t('StudyDataSuppliers.history_title')"
        :headers="historyHeaders"
        :items="historyItems"
        @close="closeHistory"
      />
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudyDataSuppliersStore } from '@/stores/studies-data-suppliers'
import SelectDataSupplier from '@/components/ui/SelectDataSupplier.vue'
import SelectDataSupplierType from '@/components/ui/SelectDataSupplierType.vue'
import NNTable from '@/components/tools/NNTable.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import terms from '@/api/controlledTerminology/terms'
import study from '@/api/study'
import filteringParameters from '@/utils/filteringParameters'

const router = useRouter()
const { t } = useI18n()
const notificationHub = inject('notificationHub')
const studiesGeneralStore = useStudiesGeneralStore()
const dataSupplierStore = useStudyDataSuppliersStore()

const studyId = computed(() => studiesGeneralStore.studyId)
const tab = ref('overview')
const loading = ref(false)
const dataSuppliers = ref([])
const dataSupplierTypes = ref([])
const total = ref(0)
const tableRef = ref(null)
const showReorderMode = ref(false)
const dialog = ref(false)
const valid = ref(false)
const form = ref(null)
const auditDialog = ref(false)
const auditTrailLoading = ref(false)
const auditTrail = ref([])
const showHistory = ref(false)
const historyItems = ref([])
const helpItems = ref([
  {
    key: 'StudyDataSuppliers.page_title_overview',
    context: () => ({ studyId: studyId.value }),
  },
  'StudyDataSuppliers.overview_tab',
  'StudyDataSuppliers.list_tab',
])

const blindedOptions = [
  { title: t('_global.tbd'), value: null },
  { title: t('_global.yes'), value: true },
  { title: t('_global.no'), value: false },
]

const formData = ref({
  study_data_supplier_uid: null,
  data_supplier_uid: null,
  study_data_supplier_type_uid: null,
  study_data_supplier_order: 1,
  blinded: null,
})

const headers = [
  { title: '', key: 'actions', sortable: false, width: '80px' },
  {
    title: '#',
    key: 'study_data_supplier_order',
    sortable: true,
    width: '80px',
  },
  {
    title: t('StudyDataSuppliers.study_data_supplier_type_field'),
    key: 'study_data_supplier_type',
    sortable: true,
  },
  { title: t('StudyDataSuppliers.history_name'), key: 'name', sortable: true },
  {
    title: t('StudyDataSuppliers.blinded_field'),
    key: 'blinded',
    sortable: true,
  },
  { title: t('_global.description'), key: 'description', sortable: true },
  { title: t('_global.library'), key: 'library', sortable: false },
  {
    title: t('DataSupplierView.DataSupplierTable.origin_type'),
    key: 'origin_type',
    sortable: false,
  },
  {
    title: t('DataSupplierView.DataSupplierTable.origin_source'),
    key: 'origin_source',
    sortable: false,
  },
  {
    title: t('DataSupplierView.DataSupplierTable.ui_base_url'),
    key: 'ui_base_url',
    sortable: false,
  },
  {
    title: t('DataSupplierView.DataSupplierTable.api_base_url'),
    key: 'api_base_url',
    sortable: false,
  },
  { title: t('_global.modified'), key: 'start_date', sortable: true },
  { title: t('_global.modified_by'), key: 'author_username', sortable: true },
]

const historyHeaders = [
  { title: t('StudyDataSuppliers.history_change_type'), key: 'change_type' },
  {
    title: t('StudyDataSuppliers.history_order'),
    key: 'study_data_supplier_order',
  },
  {
    title: t('StudyDataSuppliers.history_type'),
    key: 'study_data_supplier_type.name',
  },
  { title: t('StudyDataSuppliers.history_name'), key: 'name' },
  { title: t('StudyDataSuppliers.history_description'), key: 'description' },
  { title: t('StudyDataSuppliers.history_modified'), key: 'start_date' },
  {
    title: t('StudyDataSuppliers.history_modified_by'),
    key: 'author_username',
  },
]

// Group suppliers by their data_supplier_type.term_name
// Show all types from the codelist, including types with no suppliers
const groupedSuppliers = computed(() => {
  const groups = {}

  // Initialize groups for ALL types from the codelist
  dataSupplierTypes.value.forEach((type) => {
    const typeName = type.sponsor_preferred_name || type.term_name
    groups[typeName] = []
  })

  // Add suppliers to their respective groups
  dataSuppliers.value.forEach((supplier) => {
    const typeName = supplier.study_data_supplier_type?.term_name || 'Unknown'
    if (!groups[typeName]) {
      groups[typeName] = []
    }
    groups[typeName].push(supplier)
  })

  // Sort each group by study_data_supplier_order
  Object.keys(groups).forEach((typeName) => {
    groups[typeName].sort(
      (a, b) => a.study_data_supplier_order - b.study_data_supplier_order
    )
  })

  return groups
})

const fetchDataSupplierTypes = async () => {
  try {
    const response = await terms.getTermsByCodelist('dataSupplierType', {
      all: true,
    })
    dataSupplierTypes.value = response.data.items || []
  } catch (error) {
    console.error('Error fetching data supplier types:', error)
  }
}

const fetchDataSuppliers = async (filters, options, filtersUpdated) => {
  loading.value = true
  try {
    const params = filteringParameters.prepareParameters(
      options,
      filters,
      filtersUpdated
    )
    params.studyUid = studiesGeneralStore.studyUid

    const response = await dataSupplierStore.fetchStudyDataSuppliers(params)
    dataSuppliers.value = response.data.items || []
    total.value = response.data.total || 0
  } catch (error) {
    console.error('Error fetching study data suppliers:', error)
  } finally {
    loading.value = false
  }
}

const openEditDialog = async (item) => {
  try {
    // Fetch fresh data for the specific supplier
    const response = await dataSupplierStore.getStudyDataSupplier(
      studiesGeneralStore.studyUid,
      item.study_data_supplier_uid
    )
    const supplier = response.data
    formData.value = {
      study_data_supplier_uid: supplier.study_data_supplier_uid,
      data_supplier_uid: supplier.data_supplier_uid,
      study_data_supplier_type_uid:
        supplier.study_data_supplier_type?.term_uid || null,
      study_data_supplier_order: supplier.study_data_supplier_order,
      blinded: supplier.blinded ?? null,
    }
  } catch (error) {
    // Fallback to item data if fetch fails
    console.error('Error fetching supplier details:', error)
    formData.value = {
      study_data_supplier_uid: item.study_data_supplier_uid,
      data_supplier_uid: item.data_supplier_uid,
      study_data_supplier_type_uid:
        item.study_data_supplier_type?.term_uid || null,
      study_data_supplier_order: item.study_data_supplier_order,
      blinded: item.blinded ?? null,
    }
  }
  dialog.value = true
}

const closeDialog = () => {
  dialog.value = false
  formData.value = {
    study_data_supplier_uid: null,
    data_supplier_uid: null,
    study_data_supplier_type_uid: null,
    study_data_supplier_order: 1,
    blinded: null,
  }
}

const handleSave = async () => {
  if (!form.value.validate()) return

  try {
    const payload = {
      data_supplier_uid: formData.value.data_supplier_uid,
      study_data_supplier_type_uid: formData.value.study_data_supplier_type_uid,
      study_data_supplier_order: parseInt(
        formData.value.study_data_supplier_order
      ),
      blinded: formData.value.blinded,
    }

    await dataSupplierStore.updateStudyDataSupplier(
      studiesGeneralStore.studyUid,
      formData.value.study_data_supplier_uid,
      payload
    )

    notificationHub.add({ msg: t('StudyDataSuppliers.update_success') })
    closeDialog()
    await fetchDataSuppliers()
  } catch (error) {
    // Backend validation errors (including duplicates) are shown via notification hub
    console.error('Error saving study data supplier:', error)
  }
}

const handleDelete = async (item) => {
  if (!confirm(t('StudyDataSuppliers.confirm_delete', { name: item.name }))) {
    return
  }

  try {
    await dataSupplierStore.deleteStudyDataSupplier(
      studiesGeneralStore.studyUid,
      item.study_data_supplier_uid
    )
    await fetchDataSuppliers()
  } catch (error) {
    console.error('Error deleting study data supplier:', error)
  }
}

const openAuditTrail = async (item) => {
  auditDialog.value = true
  auditTrailLoading.value = true
  try {
    const response = await dataSupplierStore.fetchStudyDataSupplierAuditTrail(
      studiesGeneralStore.studyUid,
      item.study_data_supplier_uid
    )
    auditTrail.value = response.data || []
  } catch (error) {
    console.error('Error fetching audit trail:', error)
  } finally {
    auditTrailLoading.value = false
  }
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

const goToEditMode = () => {
  router.push({
    name: 'StudyDataSuppliersEdit',
    params: { study_id: studiesGeneralStore.studyUid },
  })
}

const handleDownload = () => {
  // TODO: Implement download functionality
  console.log('Download data suppliers')
}

const openHistory = async () => {
  try {
    const response = await study.getStudyDataSuppliersAuditTrail(
      studiesGeneralStore.studyUid
    )
    historyItems.value = response.data || []
    showHistory.value = true
  } catch (error) {
    console.error('Error fetching history:', error)
  }
}

const closeHistory = () => {
  showHistory.value = false
  historyItems.value = []
}

onMounted(async () => {
  await fetchDataSupplierTypes()
  // Initial load with sorting and pagination for Overview tab
  await fetchDataSuppliers(null, {
    page: 1,
    itemsPerPage: 25,
    sortBy: [{ key: 'study_data_supplier_order', order: 'asc' }],
  })
})
</script>

<style scoped>
.page-title {
  font-size: 24px;
  font-weight: 500;
  margin-bottom: 16px;
}

.bg-grey-lighten-3 {
  background-color: rgb(238, 238, 238);
}

/* Supplier type section styling - white box with border */
.supplier-type-section {
  background-color: white;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

/* Add rounded corners to NNTable */
:deep(.v-table) {
  border-radius: 12px;
  overflow: hidden;
}

:deep(.v-table__wrapper) {
  border-radius: 12px;
}
</style>
