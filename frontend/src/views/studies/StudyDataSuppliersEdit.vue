<template>
  <div class="px-4">
    <div class="d-flex align-center mb-2">
      <div class="page-title">{{ $t('StudyDataSuppliers.page_title') }}</div>
      <HelpButtonWithPanels
        :help-text="$t('_help.StudyDataSuppliersEdit.general')"
        :items="helpItems"
      />
    </div>

    <!-- Info alert -->
    <v-alert
      type="info"
      density="compact"
      class="mb-4"
      :text="$t('StudyDataSuppliers.info_message')"
    />

    <v-card elevation="1" class="mt-4 pa-6">
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

          <!-- Existing suppliers -->
          <div
            v-for="(supplier, index) in suppliers"
            :key="supplier.study_data_supplier_uid || supplier._tempId || index"
            class="d-flex align-center mb-3"
          >
            <div class="text-body-medium mr-4" style="min-width: 120px">
              {{ $t('StudyDataSuppliers.data_supplier_label') }}
            </div>
            <v-select
              v-model="supplier.data_supplier_uid"
              :items="getFilteredSuppliers(typeName)"
              :item-title="(item) => item?.name || item.title"
              item-value="uid"
              class="flex-grow-1 mr-4"
              hide-details
            />
            <v-select
              v-model="supplier.blinded"
              :items="blindedOptions"
              :label="$t('StudyDataSuppliers.blinded_field')"
              hide-details
              class="flex-shrink-0 mr-4"
              style="max-width: 150px"
            />
            <v-btn
              color="error"
              variant="elevated"
              @click="removeSupplier(typeName, index)"
            >
              {{ $t('StudyDataSuppliers.remove_button') }}
            </v-btn>
          </div>

          <!-- Empty state or add more -->
          <div v-if="suppliers.length === 0" class="mb-3">
            <div class="text-body-large mb-3">
              {{ $t('StudyDataSuppliers.empty_state') }}
            </div>
          </div>

          <!-- Add buttons -->
          <div class="d-flex align-center gap-6">
            <v-btn
              variant="outlined"
              color="nnBaseBlue"
              rounded
              @click="addSupplier(typeName)"
            >
              <v-icon>mdi-plus</v-icon>
            </v-btn>

            <div
              v-if="
                canCreateFromStudy &&
                suppliers.length > 0 &&
                suppliers.some((s) => !s.data_supplier_uid)
              "
              class="d-flex align-center ml-auto"
            >
              <span class="text-body-medium text-medium-emphasis mr-6">{{
                $t('StudyDataSuppliers.not_present_prompt')
              }}</span>
              <v-btn
                variant="outlined"
                color="nnBaseBlue"
                prepend-icon="mdi-plus"
                rounded
                @click="addUserDefinedSupplier(typeName)"
              >
                {{ $t('StudyDataSuppliers.add_user_defined') }}
              </v-btn>
            </div>
          </div>
        </div>
      </div>
    </v-card>

    <!-- Bottom navigation -->
    <div class="d-flex justify-space-between mt-6 mb-6">
      <v-btn
        variant="outlined"
        color="nnBaseBlue"
        size="large"
        rounded
        :disabled="saving"
        @click="handleCancel"
      >
        {{ $t('StudyDataSuppliers.cancel_button') }}
      </v-btn>
      <v-btn
        variant="elevated"
        color="nnBaseBlue"
        size="large"
        rounded
        :loading="saving"
        :disabled="saving"
        @click="handleContinue"
      >
        {{ $t('StudyDataSuppliers.save_button') }}
      </v-btn>
    </div>

    <!-- Data Supplier Form Dialog -->
    <DataSupplierForm
      :open="supplierDialogOpen"
      :selected-data-supplier="null"
      :default-supplier-type-uid="defaultSupplierTypeUid"
      @close="handleSupplierDialogClose"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudyDataSuppliersStore } from '@/stores/studies-data-suppliers'
import { useFeatureFlagsStore } from '@/stores/feature-flags'
import terms from '@/api/controlledTerminology/terms'
import dataSuppliers from '@/api/dataSuppliers'
import DataSupplierForm from '@/components/library/DataSupplierForm.vue'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'

const notificationHub = inject('notificationHub')

const router = useRouter()
const { t } = useI18n()
const studiesGeneralStore = useStudiesGeneralStore()
const dataSupplierStore = useStudyDataSuppliersStore()
const featureFlagsStore = useFeatureFlagsStore()

const blindedOptions = [
  { title: t('_global.tbd'), value: null },
  { title: t('_global.yes'), value: true },
  { title: t('_global.no'), value: false },
]

const canCreateFromStudy = computed(() => {
  return (
    featureFlagsStore.getFeatureFlag(
      'study_data_suppliers_create_from_study'
    ) !== false
  )
})

const studyDataSuppliers = ref([])
const dataSupplierTypes = ref([])
const availableSuppliers = ref([])
const saving = ref(false)
const saveError = ref(null)
const supplierDialogOpen = ref(false)
const defaultSupplierTypeUid = ref(null)
const pendingSupplierTypeName = ref(null)
const helpItems = ref([
  'StudyDataSuppliers.page_title',
  'StudyDataSuppliers.supplier_data_type',
])

// Get grouped suppliers with dedicated suppliers first, then other suppliers
const getFilteredSuppliers = (typeName) => {
  const typeData = dataSupplierTypes.value.find(
    (t) => (t.sponsor_preferred_name || t.term_name) === typeName
  )
  const typeUid = typeData?.term_uid

  // Split suppliers into dedicated (matching type) and other
  const dedicatedSuppliers = availableSuppliers.value.filter(
    (s) => s.supplier_type?.uid === typeUid
  )
  const otherSuppliers = availableSuppliers.value.filter(
    (s) => s.supplier_type?.uid !== typeUid
  )

  // Build grouped array with subheaders and dividers
  const grouped = []

  if (dedicatedSuppliers.length > 0) {
    grouped.push(
      {
        type: 'subheader',
        title: t('StudyDataSuppliers.dedicated_suppliers_header'),
      },
      ...dedicatedSuppliers
    )
  }

  if (otherSuppliers.length > 0) {
    if (dedicatedSuppliers.length > 0) {
      grouped.push({ type: 'divider' })
    }
    grouped.push(
      {
        type: 'subheader',
        title: t('StudyDataSuppliers.other_suppliers_header'),
      },
      ...otherSuppliers
    )
  }

  return grouped
}

// Group suppliers by type
const groupedSuppliers = computed(() => {
  const groups = {}

  // Initialize groups for ALL types from the codelist
  dataSupplierTypes.value.forEach((type) => {
    const typeName = type.sponsor_preferred_name || type.term_name
    groups[typeName] = []
  })

  // Add existing suppliers to their groups
  studyDataSuppliers.value.forEach((supplier) => {
    const typeName = supplier.study_data_supplier_type?.term_name
    if (typeName && groups[typeName]) {
      groups[typeName].push(supplier)
    }
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

const fetchStudyDataSuppliers = async () => {
  try {
    const response = await dataSupplierStore.fetchStudyDataSuppliers({
      studyUid: studiesGeneralStore.studyUid,
      page_size: 1000,
      sort_by: JSON.stringify({ study_data_supplier_order: true }),
      total_count: true,
    })
    studyDataSuppliers.value = response.data.items || []
  } catch (error) {
    console.error('Error fetching study data suppliers:', error)
  }
}

const fetchAvailableSuppliers = async () => {
  try {
    const response = await dataSuppliers.get({ params: { page_size: 1000 } })
    availableSuppliers.value = response.data.items || []
  } catch (error) {
    console.error('Error fetching available suppliers:', error)
  }
}

// Counter for generating unique temp IDs for new suppliers
let tempIdCounter = 0

const addSupplier = (typeName) => {
  const typeData = dataSupplierTypes.value.find(
    (t) => (t.sponsor_preferred_name || t.term_name) === typeName
  )

  studyDataSuppliers.value.push({
    _tempId: `temp_${++tempIdCounter}`, // Unique temp ID for removal tracking
    data_supplier_uid: null,
    study_data_supplier_type: {
      term_name: typeName,
      term_uid: typeData?.term_uid,
    },
    name: '',
    description: '',
    blinded: null,
  })
}

const removeSupplier = (typeName, index) => {
  const suppliers = groupedSuppliers.value[typeName]
  const supplierToRemove = suppliers[index]

  // Use filter to create a new array - ensures Vue reactivity triggers properly
  studyDataSuppliers.value = studyDataSuppliers.value.filter((s) => {
    // Keep all suppliers EXCEPT the one to remove
    // Match by study_data_supplier_uid if it exists (existing supplier from DB)
    if (supplierToRemove.study_data_supplier_uid) {
      return (
        s.study_data_supplier_uid !== supplierToRemove.study_data_supplier_uid
      )
    }
    // For new suppliers, match by temp ID
    if (supplierToRemove._tempId) {
      return s._tempId !== supplierToRemove._tempId
    }
    // Fallback to object reference
    return s !== supplierToRemove
  })
}

const addUserDefinedSupplier = (typeName) => {
  // Store which type section triggered this
  pendingSupplierTypeName.value = typeName

  // Find the term_uid for this type
  const typeData = dataSupplierTypes.value.find(
    (t) => (t.sponsor_preferred_name || t.term_name) === typeName
  )

  // Set the default supplier type for the form
  defaultSupplierTypeUid.value = typeData?.term_uid

  // Open the dialog
  supplierDialogOpen.value = true
}

const handleSupplierDialogClose = async () => {
  // Store old supplier UIDs as a Set
  const oldSupplierUids = new Set(availableSuppliers.value.map((s) => s.uid))

  // Close dialog
  supplierDialogOpen.value = false
  defaultSupplierTypeUid.value = null

  // Re-fetch available suppliers to get the newly created one
  await fetchAvailableSuppliers()

  // Find the newly created supplier
  const newSupplier = availableSuppliers.value.find(
    (s) => !oldSupplierUids.has(s.uid)
  )

  // If a new supplier was created, auto-add it to the section
  if (newSupplier && pendingSupplierTypeName.value) {
    const typeData = dataSupplierTypes.value.find(
      (t) =>
        (t.sponsor_preferred_name || t.term_name) ===
        pendingSupplierTypeName.value
    )

    studyDataSuppliers.value.push({
      _tempId: `temp_${++tempIdCounter}`,
      data_supplier_uid: newSupplier.uid,
      study_data_supplier_type: {
        term_name: pendingSupplierTypeName.value,
        term_uid: typeData?.term_uid,
      },
      name: newSupplier.name,
      description: newSupplier.description,
      blinded: null,
    })
  }

  // Clear pending type
  pendingSupplierTypeName.value = null
}

const handleCancel = () => {
  router.push({
    name: 'StudyDataSuppliers',
    params: { study_id: studiesGeneralStore.studyUid },
  })
}

const handleContinue = async () => {
  saving.value = true
  saveError.value = null

  try {
    // Build the list of suppliers to sync
    // Only include items with a data_supplier_uid selected
    const suppliers = studyDataSuppliers.value
      .filter((s) => s.data_supplier_uid)
      .map((s) => ({
        data_supplier_uid: s.data_supplier_uid,
        study_data_supplier_type_uid:
          s.study_data_supplier_type?.term_uid || null,
        blinded: s.blinded ?? null,
      }))

    // Single API call - validates all inputs first, then syncs
    // If duplicates found, rejects entire request with error
    await dataSupplierStore.syncStudyDataSuppliers(
      studiesGeneralStore.studyUid,
      suppliers
    )

    notificationHub.add({ msg: t('StudyDataSuppliers.update_success') })

    // Navigate back to overview
    router.push({
      name: 'StudyDataSuppliers',
      params: { study_id: studiesGeneralStore.studyUid },
    })
  } catch (error) {
    console.error('Error saving study data suppliers:', error)
    saveError.value = error.message || 'Failed to save changes'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await Promise.all([
    fetchDataSupplierTypes(),
    fetchStudyDataSuppliers(),
    fetchAvailableSuppliers(),
  ])
})
</script>

<style scoped>
.page-title {
  font-size: 24px;
  font-weight: 500;
  margin-bottom: 16px;
}

.supplier-type-section {
  background-color: white;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}
</style>
