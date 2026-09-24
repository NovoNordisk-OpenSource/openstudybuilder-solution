<template>
  <v-card class="bg-nnBaseLight" rounded="lg" border="sm" flat v-bind="$attrs">
    <v-card-text>
      <div class="d-flex">
        <slot name="prepend" />
        <v-select
          v-model="form.activity_item_class"
          :label="$t('ActivityInstanceForm.activity_item_class')"
          :items="compatibleActivityItemClasses"
          bg-color="white"
          item-title="display_name"
          item-value="uid"
          return-object
          :disabled="selectValueOnly || props.disabled"
          :rules="[formRules.required]"
          class="w-50"
          @update:model-value="resetAndUpdate"
        />
        <SelectActivityItemTermField
          v-if="!form.activity_item_class || (!isUnitClass && isCTTerm)"
          ref="termField"
          v-model="form.ct_term_uid"
          v-model:codelist="codelist"
          v-model:search="search"
          :activity-item-class="form.activity_item_class"
          :data-domain="props.dataDomain"
          item-title="sponsor_preferred_name"
          class="ml-4 w-50"
          :multiple="props.multiple"
          :disabled="props.disabled"
          :rules="isAllTermsSelected ? [] : [formRules.required]"
          @update:model-value="update"
          @update:codelist="update"
        />
        <v-select
          v-else-if="isUnitClass"
          ref="unitSelectRef"
          v-model="form.unit_definition_uid"
          :label="$t('ActivityInstanceForm.value')"
          :items="unitDropdownItems"
          item-title="name"
          item-value="uid"
          bg-color="white"
          class="ml-4 w-50"
          :loading="loading"
          :multiple="props.multiple"
          :disabled="props.disabled"
          :rules="[formRules.required, validateUnitSelection]"
          @update:model-value="onUnitSelected"
        />
        <slot name="append" />
        <v-btn
          v-if="props.withAdvancedSearch"
          color="primary"
          variant="outlined"
          class="ml-4"
          icon="mdi-text-box-search-outline"
          size="small"
          @click="openTermsSelectionForm()"
        >
        </v-btn>
      </div>
    </v-card-text>
  </v-card>
  <TermsSelectionForm
    v-model:codelist="codelist"
    v-model:term-selection="form.ct_term_uid"
    :open="showTermsSelectionForm"
    :title="$t('TermsSelectionForm.title')"
    max-width="1200px"
    multiple
    @selected="update"
    @close="closeTermsSelectionForm"
  />
</template>

<script setup>
import { computed, inject, nextTick, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import SelectActivityItemTermField from './SelectActivityItemTermField.vue'
import TermsSelectionForm from '@/components/library/TermsSelectionForm.vue'
import unitsApi from '@/api/units'

const hasInvalidTerms = computed(
  () => termField.value?.hasInvalidTerms ?? false
)

defineExpose({
  hasInvalidTerms,
})

const props = defineProps({
  modelValue: {
    type: Object,
    default: null,
  },
  multiple: {
    type: Boolean,
    default: false,
  },
  compatibleActivityItemClasses: {
    type: Array,
    default: null,
  },
  allActivityItemClasses: {
    type: Array,
    default: null,
  },
  selectValueOnly: {
    type: Boolean,
    default: false,
  },
  unitDimension: {
    type: String,
    default: null,
  },
  adamSpecific: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  dataDomain: {
    type: String,
    default: null,
  },
  preselectedUnitName: {
    type: String,
    default: null,
  },
  withAdvancedSearch: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue'])
const { t } = useI18n()
const formRules = inject('formRules')

const form = ref({})
const codelist = ref(null)
const allowedUnits = ref([])
const loading = ref(false)
const search = ref('')
const showTermsSelectionForm = ref(false)
const termField = ref(null)
const selectedUnitName = ref(null)
const unitSelectRef = ref(null)

const ALL_TERMS_UID = '__ALL_TERMS__'

const isAllTermsSelected = computed(
  () =>
    Array.isArray(form.value.ct_term_uid) &&
    form.value.ct_term_uid.includes(ALL_TERMS_UID)
)

const isUnitClass = computed(() => {
  // There is not yet a separate data type for Unit, so for now we check
  // if the activity item class name ends with '_unit'.
  return !!form.value.activity_item_class?.name?.endsWith('_unit')
})

const isCTTerm = computed(() => {
  if (!form.value.activity_item_class) return true
  const dataType = form.value.activity_item_class.data_type_name?.toLowerCase()
  return dataType === 'ctterm' || dataType === 'ct term'
})

const selectedTerm = computed(() => {
  if (!termField.value) {
    return null
  }
  return termField.value.allowedValues.find(
    (item) => item.term_uid === form.value.ct_term_uid
  )
})

function openTermsSelectionForm() {
  showTermsSelectionForm.value = true
}

function closeTermsSelectionForm() {
  showTermsSelectionForm.value = false
}

const unitDropdownItems = computed(() => {
  if (props.multiple) {
    const selectedUids = form.value.unit_definition_uid || []
    if (allowedUnits.value.length) {
      const missing = selectedUids.filter(
        (uid) => !allowedUnits.value.some((u) => u.uid === uid)
      )
      if (missing.length) {
        return [
          ...missing.map((uid) => ({ uid, name: uid })),
          ...allowedUnits.value,
        ]
      }
      return allowedUnits.value
    }
    if (selectedUids.length) {
      return selectedUids.map((uid) => ({ uid, name: uid }))
    }
    return []
  }
  const currentName =
    selectedUnitName.value ||
    props.preselectedUnitName ||
    form.value.unit_definition_uid
  if (allowedUnits.value.length) {
    // If the pre-selected unit is not in the fetched list, prepend it
    if (
      form.value.unit_definition_uid &&
      !allowedUnits.value.some((u) => u.uid === form.value.unit_definition_uid)
    ) {
      return [
        { uid: form.value.unit_definition_uid, name: currentName },
        ...allowedUnits.value,
      ]
    }
    return allowedUnits.value
  }
  // No dimension selected yet — show placeholder for the pre-selected unit
  if (form.value.unit_definition_uid) {
    return [{ uid: form.value.unit_definition_uid, name: currentName }]
  }
  return []
})

function validateUnitSelection() {
  const selected = form.value.unit_definition_uid
  if (!selected || (Array.isArray(selected) && !selected.length)) return true
  if (!props.unitDimension) {
    return t('ActivityInstanceForm.unit_dimension_not_selected')
  }
  if (loading.value) return true
  const uids = Array.isArray(selected) ? selected : [selected]
  const hasInvalid = uids.some(
    (uid) => !allowedUnits.value.some((u) => u.uid === uid)
  )
  if (hasInvalid) {
    return t('ActivityInstanceForm.unit_not_in_dimension')
  }
  return true
}

function fetchUnits() {
  loading.value = true
  const params = {
    page_size: 0,
  }
  if (props.unitDimension) {
    params.dimension = props.unitDimension
  }
  unitsApi.get({ params }).then((resp) => {
    allowedUnits.value = resp.data.items
    loading.value = false
    nextTick(() => {
      unitSelectRef.value?.validate()
    })
  })
}

function update() {
  const value = {
    is_adam_param_specific: props.adamSpecific,
    ct_terms: [],
    unit_definition_uids: [],
    odm_item_uids: [],
  }
  if (form.value.activity_item_class) {
    value.activity_item_class_uid = form.value.activity_item_class.uid
    if (!isUnitClass.value) {
      if (isAllTermsSelected.value && codelist.value) {
        // "All terms in codelist" selected — send ct_codelist_uid, no ct_terms
        value.ct_codelist_uid = codelist.value
      } else if (!props.multiple) {
        if (selectedTerm.value) {
          value.ct_terms = [
            { term_uid: form.value.ct_term_uid, codelist_uid: codelist.value },
          ]
          value.ct_term_name = selectedTerm.value.sponsor_preferred_name // Only useful to propagate unit dimension name
        }
      } else {
        // We assume there won't be any unit based activity item class in multiple mode
        value.ct_terms = (form.value.ct_term_uid || [])
          .filter((uid) => uid !== ALL_TERMS_UID)
          .map((term_uid) => {
            return { term_uid, codelist_uid: codelist.value }
          })
      }
    } else if (form.value.unit_definition_uid) {
      if (props.multiple) {
        value.unit_definition_uids = form.value.unit_definition_uid
      } else {
        value.unit_definition_uids = [form.value.unit_definition_uid]
      }
    }
  }
  emit('update:modelValue', value)
}

function onUnitSelected(uidOrUids) {
  if (!props.multiple) {
    const unit = allowedUnits.value.find((u) => u.uid === uidOrUids)
    if (unit) {
      selectedUnitName.value = unit.name
    }
  }
  update()
}

function resetAndUpdate() {
  codelist.value = null
  form.value.ct_term_uid = null
  termField.value.allowedValues = []
  update()
}

watch(
  () => props.modelValue,
  (value) => {
    if (value) {
      // FIXME: why this watcher is being called twice whereas there is nochange?
      form.value = {}
      if (value.activity_item_class_uid) {
        form.value.activity_item_class = props.allActivityItemClasses.find(
          (item) => item.uid === value.activity_item_class_uid
        )
      }
      if (value.unit_definition_uids && value.unit_definition_uids.length) {
        if (props.multiple) {
          form.value.unit_definition_uid = [...value.unit_definition_uids]
        } else {
          form.value.unit_definition_uid = value.unit_definition_uids[0]
          if (!selectedUnitName.value) {
            selectedUnitName.value = props.preselectedUnitName || null
          }
        }
      } else if (
        value.ct_codelist_uid &&
        (!value.ct_terms || !value.ct_terms.length)
      ) {
        // "All terms in codelist" — ct_codelist_uid set without specific ct_terms
        codelist.value = value.ct_codelist_uid
        form.value.ct_term_uid = [ALL_TERMS_UID]
      } else if (value.ct_terms && value.ct_terms.length) {
        if (!props.multiple) {
          form.value.ct_term_uid =
            value.ct_terms[0].term_uid || value.ct_terms[0].uid
          codelist.value = value.ct_terms[0].codelist_uid
        } else {
          codelist.value = value.ct_terms[0].codelist_uid
          form.value.ct_term_uid = value.ct_terms.map(
            (ct_term) => ct_term.term_uid || ct_term.uid
          )
        }
      }
    } else {
      form.value = {}
      if (props.multiple) {
        form.value.ct_term_uid = []
        form.value.unit_definition_uid = []
      }
    }
  },
  { immediate: true, deep: true }
)

watch(
  () => props.unitDimension,
  () => {
    if (isUnitClass.value) {
      fetchUnits()
    }
  },
  { immediate: true }
)

watch(
  () => props.dataDomain,
  (newVal, oldVal) => {
    // Only clear the term selection when actively changing from one domain to another,
    // not when setting domain for the first time (from null)
    if (oldVal) {
      form.value.ct_term_uid = null
    }
  }
)
</script>
