<template>
  <HorizontalStepperForm
    ref="stepper"
    :title="title"
    :help-items="helpItems"
    :steps="steps"
    :form-observer-getter="getObserver"
    :form-url="formUrl"
    :editable="isEdit()"
    :save-from-any-step="isEdit()"
    :read-only="isReadOnly"
    @close="close"
    @save="submit"
  >
    <template #[`step.form`]="{ step }">
      <v-form :ref="`observer${step}`">
        <v-card elevation="1" class="mx-auto pa-4">
          <div class="text-headline-medium mb-4">
            {{ $t('CRFForms.definition') }}
          </div>
          <v-row v-if="showLibraryDropdown">
            <v-col>
              <v-select
                v-model="selectedLibraryName"
                :label="$t('CRFForms.library')"
                data-cy="crf-form-library"
                :items="editableLibraries"
                item-title="name"
                item-value="name"
                :disabled="isEdit() || !!props.libraryName"
                :rules="[formRules.required]"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="5">
              <v-text-field
                v-model="form.name"
                :label="$t('CRFForms.name') + '*'"
                data-cy="form-oid-name"
                :clearable="!isReadOnly"
                :readonly="isReadOnly"
                :rules="[formRules.required]"
              />
            </v-col>
            <v-col cols="5">
              <v-text-field
                v-model="form.oid"
                :label="$t('CRFForms.oid')"
                data-cy="form-oid"
                :clearable="!isReadOnly"
                :readonly="isReadOnly"
              />
            </v-col>
            <v-col cols="2">
              <v-radio-group
                v-model="form.repeating"
                :label="$t('CRFForms.repeating')"
                :readonly="isReadOnly"
                inline
              >
                <v-radio :label="$t('_global.yes')" value="Yes" />
                <v-radio :label="$t('_global.no')" value="No" />
              </v-radio-group>
            </v-col>
          </v-row>
        </v-card>
      </v-form>
    </template>
    <template #[`step.translated_texts`]="{ step }">
      <v-form :ref="`observer${step}`">
        <CrfTranslatedTextSelection
          v-model="form.translated_texts"
          :read-only="isReadOnly"
        />
      </v-form>
    </template>
    <template #[`step.extensions`]>
      <CrfExtensionsManagementTable
        type="FormDef"
        :read-only="isReadOnly"
        :edit-extensions="selectedExtensions"
        @set-extensions="setExtensions"
      />
    </template>
    <template #[`step.alias`]="{ step }">
      <v-form :ref="`observer${step}`">
        <CrfAliasSelection v-model="form.aliases" :read-only="isReadOnly" />
      </v-form>
    </template>
    <template #[`step.change_description`]="{ step }">
      <v-form :ref="`observer${step}`">
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.change_description"
              :label="$t('CRFForms.change_desc')"
              data-cy="form-change-description"
              :clearable="!isReadOnly"
              :readonly="isReadOnly"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #actions>
      <ActionsMenu
        v-if="selectedForm && checkPermission($roles.LIBRARY_WRITE)"
        :actions="actions"
        :item="form"
      />
    </template>
  </HorizontalStepperForm>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  <CrfApprovalSummaryConfirmDialog ref="confirmApproval" />
  <CrfNewVersionSummaryConfirmDialog ref="confirmNewVersion" />
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import crfs from '@/api/crfs'
import CrfAliasSelection from '@/components/library/crfs/CrfAliasSelection.vue'
import CrfTranslatedTextSelection from '@/components/library/crfs/CrfTranslatedTextSelection.vue'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import '@vueup/vue-quill/dist/vue-quill.snow.css'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import actionTypes from '@/constants/actions'
import libConstants from '@/constants/libraries'
import CrfExtensionsManagementTable from '@/components/library/crfs/CrfExtensionsManagementTable.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import CrfApprovalSummaryConfirmDialog from '@/components/library/crfs/CrfApprovalSummaryConfirmDialog.vue'
import CrfNewVersionSummaryConfirmDialog from '@/components/library/crfs/CrfNewVersionSummaryConfirmDialog.vue'
import { useAccessGuard } from '@/composables/accessGuard'
import { useEditableLibraries } from '@/composables/editableLibraries'

const notificationHub = inject('notificationHub')
const formRules = inject('formRules')
const roles = inject('roles')

const props = defineProps({
  selectedForm: {
    type: Object,
    default: null,
  },
  readOnlyProp: {
    type: Boolean,
    default: false,
  },
  libraryName: {
    type: String,
    default: null,
  },
})

const { libraries: editableLibraries, showDropdown: showLibraryDropdown } =
  useEditableLibraries()
const selectedLibraryName = ref(libConstants.LIBRARY_SPONSOR)

const emit = defineEmits(['updateForm', 'close', 'linkForm'])

const { t } = useI18n()
const { checkPermission } = useAccessGuard()

const stepper = ref(null)
const observer1 = ref(null)
const observer2 = ref(null)
const observer3 = ref(null)
const observer4 = ref(null)
const confirm = ref(null)
const confirmApproval = ref(null)
const confirmNewVersion = ref(null)

function getObserver(step) {
  const observers = {
    1: observer1,
    2: observer2,
    3: observer3,
    4: observer4,
  }
  return observers[step]?.value
}

const helpItems = [
  'CRFForms.name',
  'CRFForms.oid',
  'CRFForms.repeating',
  'CRFForms.vendor_extensions',
  'CRFForms.aliases',
  'CRFForms.context',
]

function createEmptyForm() {
  return {
    oid: 'F.',
    repeating: 'No',
    aliases: [],
    translated_texts: [],
    vendor_elements: [],
    vendor_element_attributes: [],
    vendor_attributes: [],
  }
}

const form = ref(createEmptyForm())
const readOnly = ref(props.readOnlyProp)
const selectedExtensions = ref([])

watch(
  () => props.readOnlyProp,
  (value) => {
    readOnly.value = value
  }
)

watch(
  () => props.libraryName,
  (value) => {
    if (value) selectedLibraryName.value = value
  },
  { immediate: true }
)

watch(
  () => props.selectedForm,
  (value) => {
    if (isEdit() && value) {
      initForm(value)
    }
  },
  { immediate: true }
)

const isReadOnly = computed(() => {
  return readOnly.value || !checkPermission(roles.LIBRARY_WRITE)
})

const title = computed(() => {
  const name = form.value?.name || ''
  if (isEdit()) {
    if (readOnly.value) {
      return `${t('CRFForms.crf_form')} - ${name}`
    }
    return `${t('CRFForms.edit_form')} - ${name}`
  }
  return t('CRFForms.add_form')
})

const formUrl = computed(() => {
  if (!isEdit()) {
    return null
  }
  return `${window.location.href.replace('crf-tree', 'forms')}/form/${props.selectedForm.uid}`
})

const createSteps = computed(() => [
  { name: 'form', title: t('CRFForms.form_details') },
  {
    name: 'translated_texts',
    title: t('CRFForms.translated_text_details'),
  },
  {
    name: 'extensions',
    title: t('CRFForms.vendor_extensions'),
  },
  { name: 'alias', title: t('CRFForms.alias_details') },
])

const editSteps = computed(() => [
  { name: 'form', title: t('CRFForms.form_details') },
  {
    name: 'translated_texts',
    title: t('CRFForms.translated_text_details'),
  },
  {
    name: 'extensions',
    title: t('CRFForms.vendor_extensions'),
  },
  { name: 'alias', title: t('CRFForms.alias_details') },
  { name: 'change_description', title: t('CRFForms.change_desc') },
])

const steps = computed(() => {
  return isEdit() ? editSteps.value : createSteps.value
})

const actions = computed(() => [
  {
    label: t('_global.approve'),
    icon: 'mdi-check-decagram',
    iconColor: 'success',
    condition: () => !readOnly.value,
    click: approve,
  },
  {
    label: t('_global.new_version'),
    icon: 'mdi-plus-circle-outline',
    iconColor: 'primary',
    condition: () => readOnly.value,
    click: newVersion,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: (item) =>
      item.possible_actions
        ? item.possible_actions.find((action) => action === actionTypes.DELETE)
        : false,
    click: deleteForm,
  },
])

function isEdit() {
  if (props.selectedForm) {
    return Object.keys(props.selectedForm).length !== 0
  }
  return false
}

function getForm() {
  crfs.getForm(props.selectedForm.uid).then((resp) => {
    initForm(resp.data)
  })
}

async function newVersion() {
  if (
    await confirmNewVersion.value.open({
      agreeLabel: t('CRFForms.create_new_version'),
      form: props.selectedForm,
    })
  ) {
    crfs.newVersion('forms', props.selectedForm.uid).then((resp) => {
      emit('updateForm', resp.data)
      readOnly.value = false
      getForm()

      notificationHub.add({
        msg: t('_global.new_version_success'),
      })
    })
  }
}

async function approve() {
  if (
    await confirmApproval.value.open({
      agreeLabel: t('CRFForms.approve_form'),
      form: props.selectedForm,
    })
  ) {
    crfs.approve('forms', props.selectedForm.uid).then((resp) => {
      emit('updateForm', resp.data)
      readOnly.value = true
      close()
      getForm()

      notificationHub.add({
        msg: t('CRFForms.approved'),
      })
    })
  }
}

async function deleteForm() {
  let relationships = 0
  await crfs.getRelationships(props.selectedForm.uid, 'forms').then((resp) => {
    if (resp.data.OdmStudyEvent && resp.data.OdmStudyEvent.length > 0) {
      relationships = resp.data.OdmStudyEvent.length
    }
  })

  const options = {
    type: 'warning',
    cancelLabel: t('_global.cancel'),
    agreeLabel: t('_global.continue'),
  }

  if (
    relationships > 0 &&
    (await confirm.value.open(
      `${t('CRFForms.delete_warning', { count: relationships })}`,
      options
    ))
  ) {
    crfs.delete('forms', props.selectedForm.uid).then(() => {
      emit('close')
    })
  } else if (relationships === 0) {
    crfs.delete('forms', props.selectedForm.uid).then(() => {
      emit('close')
    })
  }
}

function close() {
  notificationHub.clearErrors()
  form.value = createEmptyForm()
  selectedExtensions.value = []
  stepper.value?.reset()
  emit('close')
}

async function submit() {
  if (isReadOnly.value) {
    close()
    return
  }

  notificationHub.clearErrors()

  form.value.library_name = props.libraryName || selectedLibraryName.value
  if (form.value.oid === 'F.') {
    form.value.oid = null
  }

  const elements = []
  const attributes = []
  let elementAttributes = []

  selectedExtensions.value.forEach((ex) => {
    if (ex.type) {
      attributes.push(ex)
    } else {
      elements.push(ex)
      if (ex.vendor_attributes) {
        elementAttributes = [...elementAttributes, ...ex.vendor_attributes]
      }
    }
  })

  form.value.vendor_elements = elements
  form.value.vendor_element_attributes = elementAttributes
  form.value.vendor_attributes = attributes

  try {
    if (isEdit()) {
      await crfs
        .updateForm(form.value, props.selectedForm.uid)
        .then(async (resp) => {
          notificationHub.add({
            msg: t('CRFForms.form_updated'),
          })
          emit('updateForm', resp.data)
          close()
        })
    } else {
      await crfs.createForm(form.value).then(async (resp) => {
        notificationHub.add({
          msg: t('CRFForms.form_created'),
        })
        emit('linkForm', resp)
        close()
      })
    }
  } finally {
    if (stepper.value) {
      stepper.value.loading = false
    }
  }
}

function setExtensions(extensions) {
  selectedExtensions.value = extensions
}

function initForm(item) {
  form.value = item
  form.value.aliases = item.aliases
  form.value.translated_texts = item.translated_texts
  form.value.change_description = t('_global.draft_change')
  selectedLibraryName.value = item.library_name || libConstants.LIBRARY_SPONSOR

  item.vendor_attributes.forEach((attr) => (attr.type = 'attr'))
  item.vendor_elements.forEach((element) => {
    element.vendor_attributes = item.vendor_element_attributes.filter(
      (attribute) => attribute.vendor_element_uid === element.uid
    )
  })
  selectedExtensions.value = [
    ...item.vendor_attributes,
    ...item.vendor_elements,
  ]
}
</script>
