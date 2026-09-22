<template>
  <SimpleFormDialog
    ref="formRef"
    :title="title"
    :help-items="helpItems"
    :open="open"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col>
            <v-text-field
              v-model="dataSupplier.name"
              :label="t('DataSupplierView.DataSupplierForm.name') + '*'"
              data-cy="data-supplier-name"
              clearable
              class="mt-3"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-select
              v-model="dataSupplier.supplier_type_uid"
              data-cy="data-supplier-type-uid"
              :label="
                t('DataSupplierView.DataSupplierForm.supplier_type') + '*'
              "
              :items="dataSupplierTypes"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              persistent-hint
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="dataSupplier.description"
              :label="t('DataSupplierView.DataSupplierForm.description')"
              data-cy="data-supplier-description"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-number-input
              v-model="dataSupplier.order"
              :label="t('DataSupplierView.DataSupplierForm.order')"
              :placeholder="
                t('DataSupplierView.DataSupplierForm.order_placeholder')
              "
              :hint="t('_help.DataSupplierView.DataSupplierForm.order_hint')"
              persistent-hint
              data-cy="data-supplier-order"
              :min="1"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="dataSupplier.api_base_url"
              :label="t('DataSupplierView.DataSupplierForm.api_base_url')"
              data-cy="data-supplier-description"
              clearable
            />
          </v-col>
          <v-col>
            <v-text-field
              v-model="dataSupplier.ui_base_url"
              :label="t('DataSupplierView.DataSupplierForm.ui_base_url')"
              data-cy="data-supplier-description"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-select
              v-model="dataSupplier.origin_source_uid"
              data-cy="data-supplier-origin-source-uid"
              :label="t('DataSupplierView.DataSupplierForm.origin_source')"
              :items="dataSupplierOriginSources"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              clearable
              persistent-hint
            />
          </v-col>
          <v-col>
            <v-select
              v-model="dataSupplier.origin_type_uid"
              data-cy="data-supplier-origin-type-uid"
              :label="t('DataSupplierView.DataSupplierForm.origin_type')"
              :items="dataSupplierOriginTypes"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              clearable
              persistent-hint
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { ref, computed, inject, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useFormStore } from '@/stores/form'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import dataSuppliersApi from '@/api/dataSuppliers'
import _isEqual from 'lodash/isEqual'
import terms from '@/api/controlledTerminology/terms'

const { t } = useI18n()
const formStore = useFormStore()
const notificationHub = inject('notificationHub')
const formRules = inject('formRules')
const emit = defineEmits(['close'])

const props = defineProps({
  selectedDataSupplier: {
    type: Object,
    default: null,
  },
  open: Boolean,
  defaultSupplierTypeUid: {
    type: String,
    default: null,
  },
})

const observer = ref()
const formRef = ref()

const dataSupplier = ref({
  description: null,
  api_base_url: null,
  ui_base_url: null,
  origin_source_uid: null,
  origin_type_uid: null,
})
const helpItems = [
  'DataSupplierView.DataSupplierForm.name',
  'DataSupplierView.DataSupplierForm.supplier_type',
  'DataSupplierView.DataSupplierForm.description',
  'DataSupplierView.DataSupplierForm.order',
  'DataSupplierView.DataSupplierForm.api_base_url',
  'DataSupplierView.DataSupplierForm.ui_base_url',
  'DataSupplierView.DataSupplierForm.origin_source',
  'DataSupplierView.DataSupplierForm.origin_type',
]
const dataSupplierTypes = ref([])
const dataSupplierOriginSources = ref([])
const dataSupplierOriginTypes = ref([])

const title = computed(() => {
  return isEdit()
    ? t('DataSupplierView.DataSupplierForm.edit_data_supplier') +
        ' - ' +
        dataSupplier.value.name
    : t('DataSupplierView.DataSupplierForm.add_data_supplier')
})

watch(
  () => props.selectedDataSupplier,
  (value) => {
    if (value) {
      dataSupplier.value = { ...value }
      dataSupplier.value.supplier_type_uid = value.supplier_type.uid
      dataSupplier.value.origin_source_uid = value.origin_source?.uid || null
      dataSupplier.value.origin_type_uid = value.origin_type?.uid || null
      formStore.save(dataSupplier.value)
    }
  }
)

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen && !props.selectedDataSupplier && props.defaultSupplierTypeUid) {
      // Pre-populate supplier type for create mode
      dataSupplier.value.supplier_type_uid = props.defaultSupplierTypeUid
    }
  }
)

onMounted(() => {
  terms.getTermsByCodelist('dataSupplierType').then((resp) => {
    dataSupplierTypes.value = resp.data.items
  })
  terms.getTermsByCodelist('originSource').then((resp) => {
    dataSupplierOriginSources.value = resp.data.items
  })
  terms.getTermsByCodelist('originType').then((resp) => {
    dataSupplierOriginTypes.value = resp.data.items
  })
})

async function submit() {
  const { valid } = await observer.value.validate()
  if (!valid) return

  notificationHub.clearErrors()

  if (isEdit()) {
    dataSuppliersApi
      .update(dataSupplier.value, props.selectedDataSupplier.uid)
      .then(
        () => {
          notificationHub.add({
            msg: t('DataSupplierView.DataSupplierForm.data_supplier_updated'),
          })
          close()
        },
        () => {
          formRef.value.working = false
        }
      )
  } else {
    dataSuppliersApi.create(dataSupplier.value).then(
      () => {
        notificationHub.add({
          msg: t('DataSupplierView.DataSupplierForm.data_supplier_created'),
        })
        close()
      },
      () => {
        formRef.value.working = false
      }
    )
  }
}
async function cancel() {
  if (
    props.selectedDataSupplier === null ||
    _isEqual(props.selectedDataSupplier, JSON.stringify(dataSupplier.value))
  ) {
    close()
  } else {
    const options = {
      type: 'warning',
      cancelLabel: t('_global.cancel'),
      agreeLabel: t('_global.continue'),
    }
    if (await formRef.value.confirm(t('_global.cancel_changes'), options)) {
      close()
    }
  }
}
function close() {
  notificationHub.clearErrors()
  dataSupplier.value = {
    description: null,
    api_base_url: null,
    ui_base_url: null,
    origin_source_uid: null,
    origin_type_uid: null,
  }
  observer.value.reset()
  emit('close')
}
function isEdit() {
  if (props.selectedDataSupplier) {
    return Object.keys(props.selectedDataSupplier).length !== 0
  }
  return false
}
</script>
