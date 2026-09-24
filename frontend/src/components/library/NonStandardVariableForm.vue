<template>
  <SimpleFormDialog
    ref="formRef"
    :title="dialogTitle"
    :open="open"
    max-width="1400px"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row align="center">
          <v-col cols="3">
            <v-select
              v-model="aicSelectValue"
              :label="
                $t('NonStandardVariableForm.activity_instance_class') + '*'
              "
              :items="activityInstanceClasses"
              item-title="name"
              item-value="uid"
              :multiple="form.non_standard_variable.is_multiple"
              :chips="form.non_standard_variable.is_multiple"
              closable-chips
              :rules="[formRules.required]"
              clearable
              class="mt-3"
              data-cy="nsv-activity-instance-class"
            />
          </v-col>
          <v-col cols="3">
            <v-switch
              v-model="form.non_standard_variable.is_multiple"
              :label="$t('NonStandardVariableForm.is_multiple')"
              :true-value="true"
              :false-value="false"
              color="primary"
              hide-details
              density="compact"
              data-cy="nsv-is-multiple"
            />
          </v-col>
          <v-col cols="3">
            <v-switch
              v-model="form.non_standard_variable.is_cdisc_defined"
              :label="$t('NonStandardVariableForm.is_cdisc_defined') + '*'"
              :true-value="true"
              :false-value="false"
              color="primary"
              hide-details
              density="compact"
              data-cy="nsv-is-cdisc-defined"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="3">
            <v-text-field
              v-model="form.non_standard_variable.code"
              :label="$t('NonStandardVariableForm.nsv_code') + '*'"
              :rules="[
                formRules.required,
                (v) => formRules.max(v, nsvCodeMaxLength),
              ]"
              :maxlength="nsvCodeMaxLength"
              :counter="nsvCodeMaxLength"
              clearable
              class="mt-3"
              data-cy="nsv-code"
              @update:model-value="
                (v) =>
                  (form.non_standard_variable.code = v ? v.toUpperCase() : v)
              "
            />
          </v-col>
          <v-col cols="3">
            <v-text-field
              v-model="form.display_name"
              :label="$t('NonStandardVariableForm.nsv_label') + '*'"
              :rules="[formRules.required, (v) => formRules.max(v, 40)]"
              maxlength="40"
              counter="40"
              clearable
              class="mt-3"
              data-cy="nsv-label"
              @update:model-value="onLabelChange"
            />
          </v-col>
          <v-col cols="3">
            <v-text-field
              v-model="form.name"
              :label="$t('NonStandardVariableForm.name') + '*'"
              :rules="[formRules.required]"
              clearable
              class="mt-3"
              data-cy="nsv-name"
            />
          </v-col>
          <v-col cols="3">
            <v-select
              v-model="form.role_uid"
              :label="$t('NonStandardVariableForm.role') + '*'"
              :items="roles"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              :rules="[formRules.required]"
              clearable
              class="mt-3"
              data-cy="nsv-role"
            />
          </v-col>
        </v-row>
        <v-row align="start">
          <v-col cols="3" class="d-flex align-start">
            <v-select
              v-model="form.data_type_uid"
              :label="$t('NonStandardVariableForm.data_type') + '*'"
              :items="dataTypes"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              :rules="[formRules.required]"
              clearable
              data-cy="nsv-data-type"
            >
              <template #prepend-item>
                <v-list-item>
                  <v-list-item-title
                    class="d-flex align-center justify-space-between ga-4 text-caption text-medium-emphasis"
                  >
                    <span>{{
                      $t('NonStandardVariableForm.data_type_column')
                    }}</span>
                    <span class="text-disabled">|</span>
                    <span>{{
                      $t('NonStandardVariableForm.nsv_xml_dt_column')
                    }}</span>
                  </v-list-item-title>
                </v-list-item>
                <v-divider />
              </template>
              <template #item="{ props: itemProps, internalItem: item }">
                <v-list-item v-bind="itemProps" :title="undefined">
                  <v-list-item-title
                    class="d-flex align-center justify-space-between ga-4"
                  >
                    <span>{{ item.raw.sponsor_preferred_name }}</span>
                    <span
                      v-if="getNsvXmlDtHint(item.raw)"
                      class="text-warning font-weight-medium text-caption"
                    >
                      {{ getNsvXmlDtHint(item.raw) }}
                    </span>
                  </v-list-item-title>
                </v-list-item>
              </template>
            </v-select>
          </v-col>
          <v-col cols="3">
            <v-number-input
              v-model="form.non_standard_variable.length"
              :label="$t('NonStandardVariableForm.length') + '*'"
              :rules="[
                formRules.required,
                (v) => formRules.min_value(v, 1),
                (v) => formRules.max_value(v, 200),
              ]"
              :min="1"
              :max="200"
              data-cy="nsv-length"
            />
          </v-col>
          <v-col cols="3" class="d-flex align-start">
            <v-text-field
              :model-value="
                form.valid_codelist?.submission_value ||
                form.valid_codelist?.attributes?.submission_value ||
                ''
              "
              :label="$t('NonStandardVariableForm.codelist_codes')"
              readonly
              clearable
              data-cy="nsv-codelist-code"
              @click:clear="form.valid_codelist = null"
            />
            <v-btn
              color="primary"
              variant="outlined"
              icon="mdi-text-box-search-outline"
              size="small"
              class="ml-2 mt-3"
              :disabled="!isCtTermDataType"
              data-cy="nsv-codelist-search"
              :aria-label="$t('NonStandardVariableForm.select_codelists')"
              @click="showCodelistSelectionForm = true"
            />
            <v-tooltip location="top">
              <template #activator="{ props: tipProps }">
                <v-icon
                  v-bind="tipProps"
                  class="ml-1 mt-4"
                  size="small"
                  data-cy="nsv-codelist-info"
                >
                  mdi-information-outline
                </v-icon>
              </template>
              {{ $t('NonStandardVariableForm.codelist_ct_term_help') }}
            </v-tooltip>
          </v-col>
          <v-col cols="3">
            <v-textarea
              v-model="form.non_standard_variable.algorithm"
              :label="$t('NonStandardVariableForm.algorithm')"
              rows="3"
              auto-grow
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="3">
            <v-select
              v-model="form.non_standard_variable.origin_type_uid"
              :label="$t('NonStandardVariableForm.origin_type')"
              :items="originTypes"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              clearable
            />
          </v-col>
          <v-col cols="3">
            <v-select
              v-model="form.non_standard_variable.origin_source_uid"
              :label="$t('NonStandardVariableForm.origin_source')"
              :items="originSources"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              clearable
            />
          </v-col>
          <v-col cols="3">
            <v-textarea
              v-model="form.definition"
              :label="$t('NonStandardVariableForm.definition_optional')"
              :rules="[(v) => formRules.max(v, 200)]"
              maxlength="200"
              counter="200"
              rows="3"
              auto-grow
              clearable
            />
          </v-col>
          <v-col cols="3">
            <v-textarea
              v-model="form.non_standard_variable.derivation_rule"
              :label="$t('NonStandardVariableForm.derivation_rule')"
              :rules="[(v) => formRules.max(v, 200)]"
              maxlength="200"
              counter="200"
              rows="3"
              auto-grow
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="3">
            <v-text-field
              v-model="form.nci_concept_id"
              :label="$t('NonStandardVariableForm.nci_concept_id')"
              clearable
            />
          </v-col>
          <v-col cols="3">
            <v-text-field
              v-model="form.nci_concept_name"
              :label="$t('NonStandardVariableForm.nci_concept_name')"
              clearable
            />
          </v-col>
        </v-row>
        <v-row v-if="isEdit">
          <v-col cols="12">
            <v-textarea
              v-model="form.change_description"
              :label="$t('NonStandardVariableForm.change_description') + '*'"
              :rules="[formRules.required]"
              rows="1"
              auto-grow
              clearable
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
  <CodelistSelectionForm
    v-model:codelist="form.valid_codelist"
    :open="showCodelistSelectionForm"
    :title="$t('NonStandardVariableForm.select_codelists')"
    max-width="1200px"
    @close="showCodelistSelectionForm = false"
  />
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import CodelistSelectionForm from '@/components/library/CodelistSelectionForm.vue'
import api from '@/api/activityItemClasses'
import instanceClassesApi from '@/api/activityInstanceClasses'
import terms from '@/api/controlledTerminology/terms'
import libConstants from '@/constants/libraries'

const ORIGIN_TYPE_CODELIST_UID = 'C170449'
const ORIGIN_SOURCE_CODELIST_UID = 'C170450'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const formRules = inject('formRules')

const props = defineProps({
  open: Boolean,
  editedItem: {
    type: Object,
    default: null,
  },
})
const emit = defineEmits(['close', 'created', 'updated'])

const isEdit = computed(() => !!props.editedItem)
const dialogTitle = computed(() =>
  isEdit.value
    ? t('NonStandardVariableForm.edit_title')
    : t('NonStandardVariableForm.add_title')
)
function isCtTermLabel(value) {
  if (value == null) return false
  if (typeof value === 'object') {
    return isCtTermLabel(
      value.sponsor_preferred_name || value.name || value.submission_value
    )
  }
  const normalized = String(value).replace(/\s+/g, ' ').trim().toLowerCase()
  const compact = normalized.replace(/\s+/g, '')
  // Fresh sponsor import uses "CT Term"; older DBs / NCI preferred name use "CTTerm".
  return (
    normalized === 'ct term' ||
    normalized.startsWith('ct term ') ||
    compact === 'ctterm'
  )
}

const isCtTermDataType = computed(() => {
  const selected = dataTypes.value.find(
    (dt) => dt.term_uid === form.value.data_type_uid
  )
  if (!selected) return false
  // submission_value is the stable identifier for the DATATYPE codelist's
  // "CT Term" entry (TERM_SUBMVAL "ctTerm"); fall back to label matching for
  // data that predates that field or the demo mock.
  if (selected.submission_value) {
    return String(selected.submission_value).trim().toLowerCase() === 'ctterm'
  }
  return (
    isCtTermLabel(selected.sponsor_preferred_name) ||
    isCtTermLabel(selected.name) ||
    isCtTermLabel(selected.nci_preferred_name)
  )
})
// Fixed mapping from SEMTCDT (Semantic Data Type) terms to their NSVXMLDT
// (NSV XML Data Type) equivalent. Derived by hand from the specialization
// chain in import_sponsor_data/datafiles/sponsor_library/datatype.csv -
// update this table if that chain changes, this is not computed from the API.
const SEMTCDT_TO_NSV_XML_DT_HINT = {
  text: 'text',
  integer: 'integer',
  float: 'float',
  datetime: 'datetime',
  boolean: 'text',
  durationDatetime: 'durationDatetime',
  uri: 'text',
  code: 'text',
  ctTerm: 'text',
  unii: 'text',
  snomed: 'text',
  medrt: 'text',
}

function getNsvXmlDtHint(dataType) {
  return dataType ? SEMTCDT_TO_NSV_XML_DT_HINT[dataType.submission_value] : null
}

const nsvCodeMaxLength = computed(() =>
  form.value.non_standard_variable.is_multiple ? 7 : 8
)

const DEFAULT_INSTANCE_CLASS_NAME = 'SubjectObservation'
const DEFAULT_ROLE_NAME = 'Record Qualifier'

const formRef = ref()
const observer = ref()
const showCodelistSelectionForm = ref(false)
const originTypes = ref([])
const originSources = ref([])
const dataTypes = ref([])
const roles = ref([])
const activityInstanceClasses = ref([])

function getDefaultInstanceClassUid() {
  return (
    activityInstanceClasses.value.find(
      (cls) => cls.name === DEFAULT_INSTANCE_CLASS_NAME
    )?.uid ?? null
  )
}

function getDefaultRoleUid() {
  return (
    roles.value.find((r) => r.sponsor_preferred_name === DEFAULT_ROLE_NAME)
      ?.term_uid ?? null
  )
}

function emptyForm() {
  return {
    name: null,
    display_name: null,
    definition: null,
    change_description: null,
    nci_concept_id: null,
    nci_concept_name: null,
    activity_instance_class_uids: (() => {
      const uid = getDefaultInstanceClassUid()
      return uid ? [uid] : []
    })(),
    data_type_uid: null,
    role_uid: getDefaultRoleUid(),
    valid_codelist: null,
    non_standard_variable: {
      code: null,
      is_multiple: false,
      is_cdisc_defined: false,
      length: null,
      origin_type_uid: null,
      origin_source_uid: null,
      algorithm: null,
      derivation_rule: null,
    },
  }
}

const form = ref(emptyForm())

const aicSelectValue = computed({
  get() {
    const uids = form.value.activity_instance_class_uids || []
    if (form.value.non_standard_variable.is_multiple) {
      return uids
    }
    return uids[0] ?? null
  },
  set(value) {
    if (form.value.non_standard_variable.is_multiple) {
      form.value.activity_instance_class_uids = Array.isArray(value)
        ? value.filter(Boolean)
        : value
          ? [value]
          : []
    } else {
      form.value.activity_instance_class_uids = value ? [value] : []
    }
  },
})

watch(
  () => form.value.non_standard_variable.is_multiple,
  (isMultiple) => {
    const uids = form.value.activity_instance_class_uids || []
    if (!isMultiple && uids.length > 1) {
      form.value.activity_instance_class_uids = [uids[0]]
    }
  }
)

function populateForm(item) {
  const nsv = item.non_standard_variable || {}
  form.value = {
    name: item.name ?? null,
    display_name: item.display_name ?? null,
    definition: item.definition ?? null,
    change_description: null,
    nci_concept_id: item.nci_concept_id ?? null,
    nci_concept_name: item.nci_concept_name ?? null,
    activity_instance_class_uids: (() => {
      const uids = (item.activity_instance_classes || [])
        .map((cls) => cls.uid)
        .filter(Boolean)
      if (nsv.is_multiple) return uids
      return uids.slice(0, 1)
    })(),
    data_type_uid: item.data_type?.uid ?? item.data_type?.term_uid ?? null,
    role_uid: item.role?.uid ?? item.role?.term_uid ?? null,
    valid_codelist: item.valid_codelists?.[0] ?? null,
    non_standard_variable: {
      code: nsv.code ?? null,
      is_multiple: nsv.is_multiple ?? false,
      is_cdisc_defined: nsv.is_cdisc_defined ?? false,
      length: nsv.length ?? null,
      origin_type_uid:
        nsv.origin_type?.uid ?? nsv.origin_type?.term_uid ?? null,
      origin_source_uid:
        nsv.origin_source?.uid ?? nsv.origin_source?.term_uid ?? null,
      algorithm: nsv.algorithm ?? null,
      derivation_rule: nsv.derivation_rule ?? null,
    },
  }
}

watch(
  () => props.editedItem,
  (item) => {
    if (item) {
      populateForm(item)
    } else {
      form.value = emptyForm()
    }
  },
  { immediate: true }
)

onMounted(() => {
  terms.getTermsByCodelist('originType').then((resp) => {
    originTypes.value = resp.data.items
  })
  terms.getTermsByCodelist('originSource').then((resp) => {
    originSources.value = resp.data.items
  })
  terms.getTermsByCodelist('semanticDataType', { all: true }).then((resp) => {
    dataTypes.value = resp.data.items
  })
  terms.getTermsByCodelist('role').then((resp) => {
    roles.value = resp.data.items
    if (!isEdit.value && !form.value.role_uid) {
      form.value.role_uid = getDefaultRoleUid()
    }
  })
  instanceClassesApi.getAll({ page_size: 0 }).then((resp) => {
    activityInstanceClasses.value = resp.data.items
    if (
      !isEdit.value &&
      !(form.value.activity_instance_class_uids || []).length
    ) {
      const uid = getDefaultInstanceClassUid()
      form.value.activity_instance_class_uids = uid ? [uid] : []
    }
  })
})

function onLabelChange(value) {
  form.value.name = value ? value.toLowerCase().replace(/\s+/g, '_') : value
}

function isDefined(value) {
  return value !== null && value !== undefined && value !== ''
}

function pickDefined(obj) {
  return Object.fromEntries(Object.entries(obj).filter(([, v]) => isDefined(v)))
}

function buildPayload() {
  const nsv = form.value.non_standard_variable
  const nsvPayload = {
    ...pickDefined({
      code: nsv.code,
      length: nsv.length,
      algorithm: nsv.algorithm,
      derivation_rule: nsv.derivation_rule,
      origin_type: isDefined(nsv.origin_type_uid)
        ? {
            term_uid: nsv.origin_type_uid,
            codelist_uid: ORIGIN_TYPE_CODELIST_UID,
          }
        : null,
      origin_source: isDefined(nsv.origin_source_uid)
        ? {
            term_uid: nsv.origin_source_uid,
            codelist_uid: ORIGIN_SOURCE_CODELIST_UID,
          }
        : null,
    }),
    is_multiple: Boolean(nsv.is_multiple),
    is_cdisc_defined: Boolean(nsv.is_cdisc_defined),
  }

  const aicUids = form.value.activity_instance_class_uids || []

  return pickDefined({
    name: form.value.name,
    display_name: form.value.display_name,
    definition: form.value.definition,
    nci_concept_id: form.value.nci_concept_id,
    nci_concept_name: form.value.nci_concept_name,
    change_description: isEdit.value ? form.value.change_description : null,
    order: 1,
    library_name: libConstants.LIBRARY_SPONSOR,
    data_type_uid: form.value.data_type_uid,
    role_uid: form.value.role_uid,
    valid_codelist_uids: (() => {
      const uid =
        form.value.valid_codelist?.uid ||
        form.value.valid_codelist?.codelist_uid
      return uid ? [uid] : []
    })(),
    activity_instance_classes: aicUids.length
      ? aicUids.map((uid) => ({
          uid,
          is_adam_param_specific_enabled: false,
          is_additional_optional: false,
          is_default_linked: false,
          mandatory: false,
        }))
      : null,
    non_standard_variable: nsvPayload,
  })
}

async function submit() {
  const { valid } = await observer.value.validate()
  if (!valid) {
    formRef.value.working = false
    return
  }
  notificationHub.clearErrors()

  const payload = buildPayload()
  const request = isEdit.value
    ? api.update(props.editedItem.uid, payload)
    : api.create(payload)

  request.then(
    () => {
      notificationHub.add({
        msg: isEdit.value
          ? t('NonStandardVariableForm.updated')
          : t('NonStandardVariableForm.created'),
        type: 'success',
      })
      emit(isEdit.value ? 'updated' : 'created')
      close()
    },
    () => {
      formRef.value.working = false
    }
  )
}

function cancel() {
  close()
}

function close() {
  notificationHub.clearErrors()
  form.value = emptyForm()
  observer.value?.reset()
  emit('close')
}
</script>
