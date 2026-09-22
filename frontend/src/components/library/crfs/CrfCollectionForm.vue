<template>
  <SimpleFormDialog
    ref="formDialog"
    :title="title"
    :help-items="helpItems"
    :open="true"
    :form-url="formUrl"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row v-if="showLibraryDropdown">
          <v-col>
            <v-select
              v-model="form.library_name"
              :label="$t('CRFCollections.library')"
              data-cy="crf-collection-library"
              :items="editableLibraries"
              item-title="name"
              item-value="name"
              :disabled="isEdit || isDisabled"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.name"
              :label="$t('CRFCollections.name') + '*'"
              data-cy="crf-collection-name"
              clearable
              class="mt-3"
              :disabled="isDisabled"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.oid"
              :label="$t('CRFCollections.oid')"
              data-cy="crf-collection-oid"
              clearable
              :disabled="isDisabled"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6">
            <v-menu
              v-model="effectiveDateMenu"
              :close-on-content-click="false"
              offset-y
              max-width="290px"
              min-width="290px"
            >
              <template #activator="{ props }">
                <v-text-field
                  :label="$t('CRFCollections.effective_date')"
                  data-cy="crf-collection-effective-date"
                  readonly
                  :model-value="effectiveDateDisp"
                  v-bind="props"
                />
              </template>
              <v-date-picker
                v-model="form.effective_date"
                locale="en-in"
                no-title
                data-cy="crf-collection-effective-date-picker"
                :disabled="isDisabled"
                @input="effectiveDateMenu = false"
              />
            </v-menu>
          </v-col>
          <v-col cols="6">
            <v-menu
              v-model="retiredDateMenu"
              :close-on-content-click="false"
              offset-y
              max-width="290px"
              min-width="290px"
            >
              <template #activator="{ props }">
                <v-text-field
                  :label="$t('CRFCollections.retired_date')"
                  data-cy="crf-collection-retired-date"
                  readonly
                  :model-value="retiredDateDisp"
                  v-bind="props"
                />
              </template>
              <v-date-picker
                v-model="form.retired_date"
                locale="en-in"
                no-title
                data-cy="crf-collection-retired-date-picker"
                :disabled="isDisabled"
                @input="retiredDateMenu = false"
              />
            </v-menu>
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template v-if="accessGuard.checkPermission($roles.LIBRARY_WRITE)" #actions>
      <v-btn v-if="readOnly" class="primary mr-2" @click="newVersion">
        {{ $t('_global.new_version') }}
      </v-btn>
      <v-btn
        v-else-if="
          selectedCollection && selectedCollection.status === statuses.DRAFT
        "
        class="primary mr-2"
        @click="approve"
      >
        {{ $t('_global.approve') }}
      </v-btn>
    </template>
  </SimpleFormDialog>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  <CrfApprovalSummaryConfirmDialog ref="confirmApproval" />
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import CrfApprovalSummaryConfirmDialog from '@/components/library/crfs/CrfApprovalSummaryConfirmDialog.vue'
import crfs from '@/api/crfs'
import { useEditableLibraries } from '@/composables/editableLibraries'
import libConstants from '@/constants/libraries'
import statusesConst from '@/constants/statuses'
import { useFormStore } from '@/stores/form'
import { useAccessGuard } from '@/composables/accessGuard'

const props = defineProps({
  selectedCollection: {
    type: Object,
    default: null,
  },
  readOnlyProp: Boolean,
})

const emit = defineEmits(['updateCollection', 'close'])

const { t } = useI18n()

const notificationHub = inject('notificationHub')
const roles = inject('roles')
const accessGuard = useAccessGuard()

const formRules = inject('formRules')

const formStore = useFormStore()

const formDialog = ref(null)
const observer = ref(null)
const confirmApproval = ref(null)

const form = ref({ library_name: libConstants.LIBRARY_SPONSOR })
const { libraries: editableLibraries, showDropdown: showLibraryDropdown } =
  useEditableLibraries()
const helpItems = ref([
  'CRFCollections.name',
  'CRFCollections.oid',
  'CRFCollections.effective_date',
  'CRFCollections.retired_date',
])
const effectiveDateMenu = ref(false)
const retiredDateMenu = ref(false)
const readOnly = ref(props.readOnlyProp)

const statuses = statusesConst

const isEdit = computed(() => {
  if (props.selectedCollection) {
    return Object.keys(props.selectedCollection).length !== 0
  }
  return false
})

const isDisabled = computed(
  () => readOnly.value || !accessGuard.checkPermission(roles?.LIBRARY_WRITE)
)

const title = computed(() => {
  return isEdit.value
    ? t('CRFCollections.edit_collection') + ' - ' + form.value.name
    : t('CRFCollections.add_collection')
})

const effectiveDateDisp = computed(() => {
  if (form.value.effective_date) {
    return formatDate(form.value.effective_date)
  }
  return ''
})

const retiredDateDisp = computed(() => {
  if (form.value.retired_date) {
    return formatDate(form.value.retired_date)
  }
  return ''
})

const formUrl = computed(() => {
  if (!isEdit.value) {
    return null
  }
  const href = globalThis.window?.location?.href
  if (!href) {
    return null
  }
  return `${href.replace('crf-tree', 'collections')}/collection/${props.selectedCollection.uid}`
})

watch(
  () => props.selectedCollection,
  (value) => {
    if (value) {
      form.value = { ...value }
      form.value.effective_date = form.value.effective_date
        ? new Date(form.value.effective_date)
        : null
      form.value.retired_date = form.value.retired_date
        ? new Date(form.value.retired_date)
        : null
      formStore.save(form.value)
    }
  }
)

watch(
  () => props.readOnlyProp,
  (value) => {
    readOnly.value = value
  }
)

onMounted(() => {
  if (isEdit.value) {
    form.value = { ...props.selectedCollection }
    form.value.effective_date = new Date(form.value.effective_date)
    form.value.retired_date = new Date(form.value.retired_date)
    formStore.save(form.value)
  }
})

function formatDate(value) {
  if (typeof value === 'string' && value.length <= 10) {
    return value
  }
  let month = 1 + value.getMonth()
  if (month < 10) {
    month = `0${month}`
  }
  let day = value.getDate()
  if (day < 10) {
    day = `0${day}`
  }
  const date = `${value.getFullYear()}-${month}-${day}`
  if (date === '1970-01-01') {
    return null
  }
  return `${value.getFullYear()}-${month}-${day}`
}

function newVersion() {
  crfs.newVersion('study-events', props.selectedCollection.uid).then((resp) => {
    emit('updateCollection', resp.data)
    readOnly.value = false

    notificationHub?.add({
      msg: t('_global.new_version_success'),
    })
  })
}

async function approve() {
  const ok = await confirmApproval.value?.open({
    agreeLabel: t('CRFCollections.approve_collection'),
    collection: props.selectedCollection,
  })
  if (ok) {
    crfs.approve('study-events', props.selectedCollection.uid).then((resp) => {
      emit('updateCollection', resp.data)
      readOnly.value = true
      close()

      notificationHub?.add({
        msg: t('CRFCollections.approved'),
      })
    })
  }
}

async function submit() {
  if (isDisabled.value) {
    close()
    return
  }

  const { valid } = (await observer.value?.validate?.()) || { valid: false }
  if (!valid) return

  notificationHub?.clearErrors?.()

  if (form.value.effective_date) {
    form.value.effective_date = formatDate(form.value.effective_date)
  }
  if (form.value.retired_date) {
    form.value.retired_date = formatDate(form.value.retired_date)
  }

  if (isEdit.value) {
    crfs.updateCollection(form.value, props.selectedCollection.uid).then(
      () => {
        notificationHub?.add({
          msg: t('CRFCollections.updated'),
        })
        close()
      },
      () => {
        if (formDialog.value) {
          formDialog.value.working = false
        }
      }
    )
  } else {
    crfs.createCollection(form.value).then(
      () => {
        notificationHub?.add({
          msg: t('CRFCollections.created'),
        })
        close()
      },
      () => {
        if (formDialog.value) {
          formDialog.value.working = false
        }
      }
    )
  }
}

async function cancel() {
  const options = {
    type: 'warning',
    cancelLabel: t('_global.cancel'),
    agreeLabel: t('_global.continue'),
  }
  const ok = await formDialog.value?.confirm?.(
    t('_global.cancel_changes'),
    options
  )
  if (ok) {
    close()
  }
}

function close() {
  notificationHub?.clearErrors?.()
  form.value = { library_name: libConstants.LIBRARY_SPONSOR }
  observer.value?.reset?.()
  emit('close')
}
</script>
