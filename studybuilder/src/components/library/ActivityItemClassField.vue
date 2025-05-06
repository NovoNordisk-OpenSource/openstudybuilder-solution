<template>
  <v-card class="bg-nnBaseLight" rounded="lg" border="sm" flat>
    <v-card-text>
      <div class="d-flex">
        <slot name="prepend" />
        <v-select
          v-model="form.activity_item_class"
          :label="$t('ActivityInstanceForm.activity_item_class')"
          :items="compatibleActivityItemClasses"
          bg-color="white"
          item-title="name"
          item-value="uid"
          return-object
          :disabled="selectValueOnly || props.disabled"
          variant="outlined"
          density="compact"
          class="w-50"
          hide-details
          @update:model-value="resetAndUpdate"
        />
        <SelectActivityItemTermField
          v-if="
            !form.activity_item_class ||
            form.activity_item_class.name !== 'standard_unit'
          "
          ref="termField"
          v-model="form.ct_term_uid"
          v-model:search="search"
          :activity-item-class="form.activity_item_class"
          :data-domain="props.dataDomain"
          item-title="name"
          class="ml-4 w-50"
          :multiple="props.multiple"
          :disabled="props.disabled"
          :rules="[formRules.required]"
          @update:model-value="update"
        />
        <v-select
          v-else
          v-model="form.unit_definition_uid"
          :label="$t('ActivityInstanceForm.value')"
          :items="allowedUnits"
          item-title="name"
          item-value="uid"
          bg-color="white"
          variant="outlined"
          density="compact"
          class="ml-4 w-50"
          hide-details
          :loading="loading"
          :disabled="props.disabled"
          :rules="[formRules.required]"
          @update:model-value="update"
        />
        <slot name="append" />
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import SelectActivityItemTermField from './SelectActivityItemTermField.vue'
import unitsApi from '@/api/units'

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
})

const emit = defineEmits(['update:modelValue'])
const formRules = inject('formRules')

const form = ref({})
const allowedUnits = ref([])
const loading = ref(false)
const search = ref('')
const termField = ref(null)

const selectedTerm = computed(() => {
  if (!termField.value) {
    return null
  }
  return termField.value.allowedValues.find(
    (item) => item.term_uid === form.value.ct_term_uid
  )
})

function fetchUnits() {
  if (!props.unitDimension) {
    allowedUnits.value = []
    return
  }
  loading.value = true
  unitsApi
    .get({
      params: {
        dimension: props.unitDimension,
        page_size: 0,
      },
    })
    .then((resp) => {
      allowedUnits.value = resp.data.items
      loading.value = false
    })
}

function update() {
  const value = {
    is_adam_param_specific: props.adamSpecific,
    ct_term_uids: [],
    unit_definition_uids: [],
    odm_item_uids: [],
  }
  if (form.value.activity_item_class) {
    value.activity_item_class_uid = form.value.activity_item_class.uid
    if (form.value.activity_item_class.name !== 'standard_unit') {
      if (!props.multiple) {
        if (selectedTerm.value) {
          value.ct_term_uids = [form.value.ct_term_uid]
          value.ct_term_name = selectedTerm.value.name // Only useful to propagate unit dimension name
        }
      } else {
        // We assume there won't be any unit based activity item class in multiple mode
        value.ct_term_uids = form.value.ct_term_uid
      }
    } else if (form.value.unit_definition_uid) {
      value.unit_definition_uids = [form.value.unit_definition_uid]
    }
  }
  emit('update:modelValue', value)
}

function resetAndUpdate() {
  form.value.ct_term_uid = null
  update()
}

watch(
  () => props.modelValue,
  (value) => {
    if (value) {
      form.value = {}
      if (value.activity_item_class_uid) {
        form.value.activity_item_class = props.allActivityItemClasses.find(
          (item) => item.uid === value.activity_item_class_uid
        )
      }
      if (value.unit_definition_uids && value.unit_definition_uids.length) {
        form.value.unit_definition_uid = value.unit_definition_uids[0]
      }
      if (value.ct_term_uids && value.ct_term_uids.length) {
        form.value.ct_term_uid = !props.multiple
          ? value.ct_term_uids[0]
          : value.ct_term_uids
      }
    } else {
      form.value = {}
      if (props.multiple) {
        form.value.ct_term_uid = []
      }
    }
  },
  { immediate: true, deep: true }
)

watch(
  () => props.unitDimension,
  () => {
    if (form.value?.activity_item_class?.name === 'standard_unit') {
      form.value.unit_definition_uid = null
      fetchUnits()
    }
  }
)

watch(
  () => props.dataDomain,
  () => {
    form.value.ct_term_uid = null
  }
)
</script>
