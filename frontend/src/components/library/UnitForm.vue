<template>
  <SimpleFormDialog
    ref="formRef"
    :title="title"
    :help-items="helpItems"
    :help-text="$t('HelpMessages.units')"
    :open="open"
    max-width="1000px"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-alert
          v-if="!editing && form.master_unit"
          type="info"
          variant="tonal"
          class="mb-4"
        >
          {{ $t('UnitForm.created_as_master_unit') }}
        </v-alert>
        <v-row>
          <v-col cols="12" md="8">
            <v-text-field
              v-model="form.name"
              :label="$t('_global.name')"
              data-cy="unit-name"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
          <v-col cols="12" md="4">
            <v-autocomplete
              v-model="form.unit_dimension"
              :label="$t('UnitForm.dimension')"
              data-cy="unit-dimension"
              :items="unitDimensions"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              clearable
              :disabled="dimensionLocked"
              :hint="dimensionLocked ? $t('UnitForm.dimension_locked') : ''"
              :persistent-hint="dimensionLocked"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12" md="4">
            <v-autocomplete
              v-model="form.ct_units"
              :label="$t('UnitForm.ct_term')"
              data-cy="unit-codelist-term"
              :items="unitTerms"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              single-line
              multiple
              chips
              closable-chips
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
          <v-col cols="12" md="4">
            <v-select
              v-model="form.unit_subsets"
              label="Unit Subset"
              data-cy="unit-subset"
              :items="unitSubsets"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              single-line
              multiple
              chips
              closable-chips
              clearable
            />
          </v-col>
          <v-col cols="12" md="4">
            <StudybuilderUCUMField v-model="form.ucum" />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12" md="4">
            <v-checkbox
              v-model="form.convertible_unit"
              :label="$t('UnitForm.convertible_unit')"
              data-cy="convertible-unit"
            />
            <v-checkbox
              v-model="form.use_molecular_weight"
              :label="$t('UnitForm.molecular_weight')"
            />
          </v-col>
          <v-col cols="12" md="4">
            <v-number-input
              v-model="form.conversion_factor_to_master"
              :label="$t('UnitForm.conversion_factor')"
              data-cy="unit-conversion-factor"
              :disabled="
                (!form.convertible_unit && !form.master_unit) ||
                forcedMasterFactor
              "
              clearable
              :precision="5"
            />
          </v-col>
          <v-col cols="12" md="4">
            <v-text-field
              :model-value="masterUnit?.name"
              :label="$t('UnitForm.master_unit')"
              data-cy="master-unit"
              disabled
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12" class="d-flex flex-column flex-md-row ga-md-6">
            <v-checkbox
              v-model="form.display_unit"
              :label="$t('UnitForm.display_unit')"
              data-cy="display-unit"
              class="flex-grow-0"
            />
            <v-checkbox
              v-model="form.us_conventional_unit"
              :label="$t('UnitForm.us_unit')"
              data-cy="us-unit"
              class="flex-grow-0"
            />
            <v-checkbox
              v-model="form.use_complex_unit_conversion"
              :label="$t('UnitForm.complex_conversion')"
              class="flex-grow-0"
            />
          </v-col>
        </v-row>
        <v-row v-if="editing">
          <v-col>
            <label class="v-label">{{
              $t('UnitForm.reason_for_change')
            }}</label>
            <v-textarea
              v-model="form.change_description"
              clearable
              auto-grow
              rows="1"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import terms from '@/api/controlledTerminology/terms'
import units from '@/api/units'
import _isEmpty from 'lodash/isEmpty'
import _isEqual from 'lodash/isEqual'
import libConstants from '@/constants/libraries'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import StudybuilderUCUMField from '@/components/tools/StudybuilderUCUMField.vue'
import { useUnitsStore } from '@/stores/units'
import { useI18n } from 'vue-i18n'

const notificationHub = inject('notificationHub')
const formRules = inject('formRules')
const { t } = useI18n()
const formRef = ref()

const props = defineProps({
  unit: {
    type: Object,
    default: null,
  },
  open: Boolean,
})

const emit = defineEmits(['close'])
const unitsStore = useUnitsStore()

const form = ref(getInitialForm())
const helpItems = [
  'UnitForm.ct_term',
  'UnitForm.convertible_unit',
  'UnitForm.display_unit',
  'UnitForm.master_unit',
  'UnitForm.us_unit',
  'UnitForm.dimension',
  'UnitForm.add_success',
  'UnitForm.molecular_weight',
  'UnitForm.conversion_factor',
]
const unitTerms = ref([])
const unitDimensions = ref([])
const unitSubsets = ref([])
const masterUnit = ref(null)

const title = computed(() => {
  return props.unit.uid ? t('UnitForm.edit_title') : t('UnitForm.add_title')
})

const editing = computed(() => {
  return !_isEmpty(props.unit)
})

// Only a draft that has never been approved (version 0.x) may change dimension
const dimensionLocked = computed(() => {
  return (
    editing.value &&
    !(props.unit.status === 'Draft' && parseFloat(props.unit.version) < 1)
  )
})

// A new master unit converts to itself, so its factor is always 1
const forcedMasterFactor = computed(() => {
  return !editing.value && form.value.master_unit
})

watch(
  () => form.value.convertible_unit,
  (value) => {
    if (!value && !forcedMasterFactor.value) {
      form.value.conversion_factor_to_master = null
    }
  }
)

watch(forcedMasterFactor, (value) => {
  form.value.conversion_factor_to_master = value ? 1.0 : null
})

// A dimension can only have one master unit: a new unit becomes the master
// unless its dimension already has one. The API enforces this across every
// library, but its list endpoint leaves out the Archived library unless asked
// for it explicitly, so that library is queried separately.
watch(
  () => form.value.unit_dimension,
  async (dimensionUid) => {
    masterUnit.value = null
    if (!editing.value) {
      form.value.master_unit = false
    }
    if (!dimensionUid) {
      return
    }
    const params = {
      filters: JSON.stringify({
        'unit_dimension.uid': { v: [dimensionUid] },
        master_unit: { v: [true] },
      }),
      page_size: 1,
    }
    const responses = await Promise.all([
      units.get({ params }),
      units.get({
        params: { ...params, library_name: libConstants.LIBRARY_ARCHIVED },
      }),
    ])
    // Ignore the response if the dimension changed while it was in flight
    if (form.value.unit_dimension !== dimensionUid) {
      return
    }
    masterUnit.value = responses.flatMap((resp) => resp.data.items)[0] || null
    if (!editing.value) {
      form.value.master_unit = !masterUnit.value
    }
  }
)

watch(
  () => props.unit,
  (value) => {
    if (Object.keys(value).length !== 0) {
      units.getObject(value.uid).then((resp) => {
        form.value = JSON.parse(JSON.stringify(resp.data))
        form.value.ct_units = value.ct_units.map((el) => el.term_uid)
        form.value.unit_subsets = value.unit_subsets.map((el) => el.term_uid)
        value.ucum
          ? (form.value.ucum = value.ucum.term_uid)
          : (form.value.ucum = '')
        form.value.unit_dimension = value.unit_dimension.term_uid
      })
    }
  }
)

onMounted(() => {
  terms.getTermsByCodelist('units', { all: true }).then((resp) => {
    unitTerms.value = resp.data.items
  })
  terms.getTermsByCodelist('unitDimensions').then((resp) => {
    unitDimensions.value = resp.data.items
  })
  terms.getTermsByCodelist('unitSubsets').then((resp) => {
    unitSubsets.value = resp.data.items
  })
  if (Object.keys(props.unit).length !== 0) {
    form.value = JSON.parse(JSON.stringify(props.unit))
    form.value.ct_units = props.unit.ct_units.map((el) => el.term_uid)
    form.value.unit_subsets = props.unit.unit_subsets.map((el) => el.term_uid)
    props.unit.ucum
      ? (form.value.ucum = props.unit.ucum.term_uid)
      : (form.value.ucum = '')
    form.value.unit_dimension = props.unit.unit_dimension.term_uid
  }
})

function getInitialForm() {
  return {
    library_name: libConstants.LIBRARY_SPONSOR,
    convertible_unit: false,
    display_unit: true,
    master_unit: false,
    conversion_factor_to_master: null,
    us_conventional_unit: false,
    use_molecular_weight: false,
    use_complex_unit_conversion: false,
  }
}

async function cancel() {
  if (!editing.value && _isEqual(form.value, getInitialForm())) {
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
  emit('close')
  notificationHub.clearErrors()
  form.value = getInitialForm()
}

async function confirmMolecularWeight() {
  if (form.value.use_molecular_weight) {
    return true
  }
  if (!/\bmol\w*/i.test(form.value.name || '')) {
    return true
  }
  const options = {
    type: 'warning',
    cancelLabel: t('_global.cancel'),
    agreeLabel: t('_global.continue'),
  }
  return await formRef.value.confirmHtml(
    t('UnitForm.molecular_weight_confirm'),
    options
  )
}

async function submit() {
  notificationHub.clearErrors()

  if (!(await confirmMolecularWeight())) {
    formRef.value.working = false
    return
  }

  if (form.value.ucum && form.value.ucum.term_uid) {
    form.value.ucum = form.value.ucum.term_uid
  }
  if (form.value.unit_dimension && form.value.unit_dimension.term_uid) {
    form.value.unit_dimension = form.value.unit_dimension.term_uid
  }
  if (Object.keys(props.unit).length !== 0) {
    try {
      const data = {
        uid: props.unit.uid,
        data: form.value,
      }
      await unitsStore.updateUnit(data)
      notificationHub.add({ msg: t('UnitForm.update_success') })
      close()
    } finally {
      formRef.value.working = false
    }
  } else {
    try {
      await unitsStore.addUnit(form.value)
      notificationHub.add({ msg: t('UnitForm.add_success') })
      close()
    } finally {
      formRef.value.working = false
    }
  }
}
</script>
