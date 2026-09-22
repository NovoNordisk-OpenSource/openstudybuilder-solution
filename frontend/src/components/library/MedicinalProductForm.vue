<template>
  <SimpleFormDialog
    ref="formRef"
    :title="title"
    :help-items="helpItems"
    :open="open"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.name"
              :label="$t('_global.name')"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="form.compound_uid"
              :label="$t('MedicinalProduct.compound')"
              :items="compounds"
              item-title="name"
              item-value="uid"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="form.pharmaceutical_product_uid"
              :label="$t('MedicinalProduct.pharmaceutical_product')"
              :items="pharmaceuticalProducts"
              :item-title="
                (item) => item.derived_name + ' / ' + displayDosageForms(item)
              "
              item-value="uid"
              variant="outlined"
              :rules="[formRules.required]"
              :filter-keys="['raw.searchable_text']"
            >
              <template #item="{ props, internalItem: item }">
                <v-list-item v-bind="props" :title="item.raw.derived_name">
                  <v-list-item-subtitle class="pa-2">
                    {{ displayDosageForms(item.raw) }}
                    {{ displayRoutesOfAdministration(item.raw) }}
                  </v-list-item-subtitle>
                </v-list-item>
              </template>
            </v-autocomplete>
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="form.dose_frequency_uids"
              :label="$t('MedicinalProduct.frequency')"
              :items="frequencies"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              multiple
              chips
              closable-chips
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="form.delivery_device_uid"
              :label="$t('MedicinalProduct.delivery_device')"
              :items="devices"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="form.dispenser_uid"
              :label="$t('MedicinalProduct.dispenser')"
              :items="dispensers"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <div class="text-headline-small my-2">
              {{ $t('MedicinalProductForm.dose_values') }}
              <v-btn
                color="primary"
                size="x-small"
                icon="mdi-plus"
                variant="outlined"
                @click="addDoseValue"
              />
            </div>
            <v-card
              v-for="(dose_value, index) in form.dose_values"
              :key="`dosevalue-${index}`"
              style="position: relative"
            >
              <v-card-text style="position: relative">
                <NumericValueWithUnitField
                  v-model="form.dose_values[index]"
                  :label="$t('MedicinalProduct.dose')"
                  subset="Dose Unit"
                />
              </v-card-text>
              <v-btn
                color="error"
                position="absolute"
                location="top right"
                size="x-small"
                icon="mdi-delete-outline"
                variant="outlined"
                @click="removeDoseValue(index)"
              />
            </v-card>
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useNumericValues } from '@/composables/numericValues'
import { usePharmaceuticalProducts } from '@/composables/pharmaceuticalProducts'
import compoundsApi from '@/api/concepts/compounds'
import pharmaceuticalProductsApi from '@/api/concepts/pharmaceuticalProducts'
import termsApi from '@/api/controlledTerminology/terms'
import api from '@/api/concepts/medicinalProducts'
import libConstants from '@/constants/libraries'
import statuses from '@/constants/statuses'
import NumericValueWithUnitField from '@/components/tools/NumericValueWithUnitField.vue'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'

const notificationHub = inject('notificationHub')
const formRules = inject('formRules')
const { t } = useI18n()
const { createNumericValues } = useNumericValues()
const { displayDosageForms, displayRoutesOfAdministration } =
  usePharmaceuticalProducts()
const props = defineProps({
  medicinalProductUid: {
    type: String,
    default: undefined,
  },
  open: Boolean,
})
const emit = defineEmits(['close', 'created', 'updated'])

const compounds = ref([])
const devices = ref([])
const dispensers = ref([])
const frequencies = ref([])
const form = ref(getInitialForm())
const formRef = ref()
const pharmaceuticalProducts = ref([])

const title = computed(() => {
  return props.medicinalProductUid
    ? t('MedicinalProductForm.edit_title')
    : t('MedicinalProductForm.add_title')
})

const helpItems = [
  'MedicinalProduct.compound',
  'MedicinalProduct.pharmaceutical_product',
  'MedicinalProduct.frequency',
  'MedicinalProduct.delivery_device',
  'MedicinalProduct.dispenser',
  'MedicinalProductForm.dose_values',
]

watch(
  () => props.medicinalProductUid,
  (value) => {
    if (value) {
      loadMedicinalProduct(value)
    } else {
      form.value = getInitialForm()
    }
  },
  { immediate: true }
)

function getInitialForm() {
  return {
    dose_values: [],
    dose_frequency_uids: [],
  }
}

function loadMedicinalProduct(uid) {
  api.getObject(uid).then((resp) => {
    form.value = {
      name: resp.data.name,
      compound_uid: resp.data.compound.uid,
      dose_values: resp.data.dose_values,
      dose_frequency_uids: (resp.data.dose_frequencies || []).map(
        (frequency) => frequency.term_uid
      ),
    }
    if (
      resp.data.pharmaceutical_products &&
      resp.data.pharmaceutical_products.length
    ) {
      form.value.pharmaceutical_product_uid =
        resp.data.pharmaceutical_products[0].uid
    }
    if (resp.data.delivery_device) {
      form.value.delivery_device_uid = resp.data.delivery_device.term_uid
    }
    if (resp.data.dispenser) {
      form.value.dispenser_uid = resp.data.dispenser.term_uid
    }
  })
}

function close() {
  emit('close')
  notificationHub.clearErrors()
  form.value = getInitialForm()
}

async function addProduct(data) {
  notificationHub.clearErrors()

  data.library_name = libConstants.LIBRARY_SPONSOR
  await api.create(data)
  emit('created')
  notificationHub.add({
    msg: t('MedicinalProductForm.add_success'),
    type: 'success',
  })
}

async function updateProduct(data) {
  notificationHub.clearErrors()

  data.change_description = t('_global.work_in_progress')
  await api.update(props.medicinalProductUid, data)
  emit('updated')
  notificationHub.add({
    msg: t('MedicinalProductForm.update_success'),
    type: 'success',
  })
}

async function submit() {
  const data = {
    name: form.value.name,
    compound_uid: form.value.compound_uid,
    dose_frequency_uids: form.value.dose_frequency_uids || [],
    delivery_device_uid: form.value.delivery_device_uid,
    dispenser_uid: form.value.dispenser_uid,
  }
  if (form.value.pharmaceutical_product_uid) {
    data.pharmaceutical_product_uids = [form.value.pharmaceutical_product_uid]
  }
  data.dose_value_uids = await createNumericValues(form.value.dose_values)
  try {
    if (!props.medicinalProductUid) {
      await addProduct(data)
    } else {
      await updateProduct(data)
    }
    close()
  } finally {
    formRef.value.working = false
  }
}

function addDoseValue() {
  form.value.dose_values.push({})
}

function removeDoseValue(index) {
  form.value.dose_values.splice(index, 1)
}

compoundsApi
  .getFiltered({
    page_size: 0,
    filters: { status: { v: [statuses.FINAL] } },
    sort_by: { name: true },
  })
  .then((resp) => {
    compounds.value = resp.data.items
  })
pharmaceuticalProductsApi
  .getFiltered({ page_size: 0, filters: { status: { v: [statuses.FINAL] } } })
  .then((resp) => {
    pharmaceuticalProducts.value = resp.data.items.map((item) => {
      item.searchable_text = displayDosageForms(item) + ' ' + item.derived_name
      return item
    })
  })
termsApi.getTermsByCodelist('frequency', { all: true }).then((resp) => {
  frequencies.value = resp.data.items
})
termsApi.getTermsByCodelist('deliveryDevice', { all: true }).then((resp) => {
  devices.value = resp.data.items
})
termsApi.getTermsByCodelist('dispensedIn', { all: true }).then((resp) => {
  dispensers.value = resp.data.items
})
</script>
