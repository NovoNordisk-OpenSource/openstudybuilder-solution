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
                :label="$t('CRFItemGroups.library')"
                data-cy="crf-item-group-library"
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
                :label="$t('CRFItemGroups.name') + '*'"
                data-cy="item-group-name"
                :clearable="!isReadOnly"
                :readonly="isReadOnly"
                :rules="[formRules.required]"
              />
            </v-col>
            <v-col cols="5">
              <v-text-field
                v-model="form.oid"
                :label="$t('CRFItemGroups.oid')"
                data-cy="item-group-oid"
                :clearable="!isReadOnly"
                :readonly="isReadOnly"
              />
            </v-col>
            <v-col cols="2">
              <v-radio-group
                v-model="form.repeating"
                class="mt-2"
                :label="$t('CRFItemGroups.repeating')"
                :readonly="isReadOnly"
                inline
              >
                <v-radio :label="$t('_global.yes')" value="Yes" />
                <v-radio :label="$t('_global.no')" value="No" />
              </v-radio-group>
            </v-col>
          </v-row>
        </v-card>
        <v-card elevation="1" class="mx-auto mt-3 pa-4">
          <div class="text-headline-medium mb-4">
            {{ $t('CRFForms.annotations') }}
          </div>
          <v-row>
            <v-col cols="6">
              <v-select
                v-model="form.sdtm_domains"
                :label="$t('CRFItemGroups.domain')"
                data-cy="item-group-domain"
                :items="domains"
                :item-props="sdtmDataDomainProps"
                single-line
                :clearable="!isReadOnly"
                return-object
                multiple
                :readonly="isReadOnly"
              >
                <template #menu-header>
                  <div class="border-b w-100 pa-2" @keydown.stop>
                    <v-text-field
                      v-model="domainSearch"
                      :placeholder="$t('_global.search')"
                      prepend-inner-icon="mdi-magnify"
                      hide-details
                      clearable
                    />
                  </div>
                </template>

                <template #item="{ props }">
                  <v-list-item
                    v-bind="props"
                    @click="
                      () => {
                        props.onClick()
                        domainSearch = ''
                      }
                    "
                  >
                    <template #prepend="{ isActive }">
                      <v-list-item-action start>
                        <v-checkbox-btn :model-value="isActive" />
                      </v-list-item-action>
                    </template>
                    <template #title>
                      {{ props.title }}
                    </template>
                  </v-list-item>
                </template>

                <template #selection="{ index }">
                  <div v-if="index === 0">
                    <span>{{
                      form.sdtm_domains[0].sponsor_preferred_name ||
                      form.sdtm_domains[0].term_name
                    }}</span>
                  </div>
                  <span
                    v-if="index === 1"
                    class="grey--text text-body-small mr-1"
                  >
                    (+{{ form.sdtm_domains.length - 1 }})
                  </span>
                </template>
              </v-select>
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model="form.sas_dataset_name"
                :label="$t('CRFItemGroups.sas_dataset')"
                data-cy="item-group-sas-dataset-name"
                :clearable="!isReadOnly"
                :readonly="isReadOnly"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="2">
              <v-radio-group
                v-model="form.is_reference_data"
                class="mt-2"
                :label="$t('CRFItemGroups.is_referential')"
                :readonly="isReadOnly"
              >
                <v-radio :label="$t('_global.yes')" value="Yes" />
                <v-radio :label="$t('_global.no')" value="No" />
              </v-radio-group>
            </v-col>
            <v-col cols="4">
              <v-select
                v-model="form.origin"
                :label="$t('CRFItemGroups.origin')"
                data-cy="item-group-origin"
                :items="origins"
                item-title="nci_preferred_name"
                item-value="nci_preferred_name"
                :clearable="!isReadOnly"
                :readonly="isReadOnly"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="6">
              <v-text-field
                v-model="form.purpose"
                :label="$t('CRFItemGroups.purpose')"
                data-cy="item-group-purpose"
                :clearable="!isReadOnly"
                :readonly="isReadOnly"
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model="form.comment"
                :label="$t('CRFItemGroups.comment')"
                data-cy="item-group-comment"
                :clearable="!isReadOnly"
                :readonly="isReadOnly"
              />
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
        type="ItemGroupDef"
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
              data-cy="item-group-change-description"
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
        v-if="selectedGroup && checkPermission($roles.LIBRARY_WRITE)"
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
import { computed, inject, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import crfs from '@/api/crfs'
import terms from '@/api/controlledTerminology/terms'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import CrfAliasSelection from '@/components/library/crfs/CrfAliasSelection.vue'
import CrfTranslatedTextSelection from '@/components/library/crfs/CrfTranslatedTextSelection.vue'
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

defineOptions({ name: 'CrfItemGroupForm' })

const notificationHub = inject('notificationHub')
const formRules = inject('formRules')
const roles = inject('roles')

const props = defineProps({
  selectedGroup: {
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

const emit = defineEmits(['updateItemGroup', 'close', 'linkGroup'])

const { t } = useI18n()
const { checkPermission } = useAccessGuard()

const stepper = ref(null)
const confirm = ref(null)
const confirmApproval = ref(null)
const confirmNewVersion = ref(null)

const observer1 = ref(null)
const observer2 = ref(null)
const observer3 = ref(null)
const observer4 = ref(null)
const observer5 = ref(null)

function getObserver(step) {
  const observers = {
    1: observer1,
    2: observer2,
    3: observer3,
    4: observer4,
    5: observer5,
  }
  return observers[step]?.value
}

const helpItems = [
  'CRFItemGroups.name',
  'CRFItemGroups.oid',
  'CRFItemGroups.repeating',
  'CRFItemGroups.aliases',
  'CRFItemGroups.context',
]

function createEmptyForm() {
  return {
    oid: 'G.',
    repeating: 'No',
    isReferenceData: 'No',
    aliases: [],
    translated_texts: [],
    sdtm_domains: [],
    vendor_elements: [],
    vendor_element_attributes: [],
    vendor_attributes: [],
  }
}

const form = ref(createEmptyForm())
const steps = ref([])
const selectedExtensions = ref([])
const origins = ref([])
const domains = ref([])
const readOnly = ref(props.readOnlyProp)
const domainSearch = ref('')

function buildCreateSteps() {
  return [
    { name: 'form', title: t('CRFItemGroups.group_details') },
    {
      name: 'translated_texts',
      title: t('CRFItemGroups.translated_text_details'),
    },
    {
      name: 'extensions',
      title: t('CRFForms.vendor_extensions'),
    },
    { name: 'alias', title: t('CRFItemGroups.alias_details') },
  ]
}

function buildEditSteps() {
  return [
    { name: 'form', title: t('CRFItemGroups.group_details') },
    {
      name: 'translated_texts',
      title: t('CRFItemGroups.translated_text_details'),
    },
    {
      name: 'extensions',
      title: t('CRFForms.vendor_extensions'),
    },
    { name: 'alias', title: t('CRFItemGroups.alias_details') },
    { name: 'change_description', title: t('CRFForms.change_desc') },
  ]
}

function isEdit() {
  if (props.selectedGroup) {
    return Object.keys(props.selectedGroup).length !== 0
  }
  return false
}

const isReadOnly = computed(() => {
  return readOnly.value || !checkPermission(roles.LIBRARY_WRITE)
})

const title = computed(() => {
  if (!isEdit()) {
    return t('CRFItemGroups.add_group')
  }

  const prefix = readOnly.value
    ? t('CRFItemGroups.item_group')
    : t('CRFItemGroups.edit_group')
  return `${prefix} - ${form.value.name}`
})

const formUrl = computed(() => {
  if (!isEdit()) {
    return null
  }
  return `${globalThis.location.href.replace('crf-tree', 'item-groups')}/item-group/${props.selectedGroup.uid}`
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
    click: deleteGroup,
  },
])

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

watch(domainSearch, () => {
  filterSdtmDomains()
})

watch(
  () => props.selectedGroup,
  (value) => {
    if (isEdit()) {
      steps.value = buildEditSteps()
      initForm(value)
    } else {
      steps.value = buildCreateSteps()
    }
  },
  { immediate: true }
)

const sdtmDataDomainProps = (item) => {
  return {
    title: `${item.sponsor_preferred_name || item.term_name} (${item.submission_value})`,
    value: item.term_uid,
  }
}

const domainSearchTimeout = ref(undefined)

async function filterSdtmDomains() {
  clearTimeout(domainSearchTimeout.value)

  const baseParams = {
    page_size: 10,
    sort_by: JSON.stringify({ submission_value: true }),
  }

  if (domainSearch.value && domainSearch.value.trim().length > 0) {
    const params = {
      ...baseParams,
      filters: JSON.stringify({
        sponsor_preferred_name: { v: [domainSearch.value], op: 'co' },
        submission_value: { v: [domainSearch.value], op: 'co' },
      }),
      operator: 'or',
    }

    domainSearchTimeout.value = setTimeout(async () => {
      const resp = await terms.getTermsByCodelist(
        'sdtmDomainAbbreviation',
        params
      )
      domains.value = [
        ...form.value.sdtm_domains,
        ...resp.data.items.filter(
          (item) =>
            !form.value.sdtm_domains.some(
              (domain) => domain.term_uid === item.term_uid
            )
        ),
      ]
    }, 400)
    return
  }

  const resp = await terms.getTermsByCodelist(
    'sdtmDomainAbbreviation',
    baseParams
  )
  domains.value = [
    ...form.value.sdtm_domains,
    ...resp.data.items.filter(
      (item) =>
        !form.value.sdtm_domains.some(
          (domain) => domain.term_uid === item.term_uid
        )
    ),
  ]
}

function getGroup() {
  crfs.getItemGroup(props.selectedGroup.uid).then((resp) => {
    initForm(resp.data)
  })
}

async function newVersion() {
  if (
    await confirmNewVersion.value?.open({
      agreeLabel: t('CRFItemGroups.create_new_version'),
      itemGroup: props.selectedGroup,
    })
  ) {
    crfs.newVersion('item-groups', props.selectedGroup.uid).then((resp) => {
      emit('updateItemGroup', resp.data)
      readOnly.value = false
      getGroup()

      notificationHub.add({
        msg: t('_global.new_version_success'),
      })
    })
  }
}

async function approve() {
  if (
    await confirmApproval.value?.open({
      agreeLabel: t('CRFItemGroups.approve_group'),
      itemGroup: props.selectedGroup,
    })
  ) {
    crfs.approve('item-groups', props.selectedGroup.uid).then((resp) => {
      emit('updateItemGroup', resp.data)
      readOnly.value = true
      close()
      getGroup()

      notificationHub.add({
        msg: t('CRFItemGroups.approved'),
      })
    })
  }
}

async function deleteGroup() {
  let relationships = 0

  await crfs
    .getRelationships(props.selectedGroup.uid, 'item-groups')
    .then((resp) => {
      if (resp.data.OdmForm && resp.data.OdmForm.length > 0) {
        relationships = resp.data.OdmForm.length
      }
    })

  const options = {
    type: 'warning',
    cancelLabel: t('_global.cancel'),
    agreeLabel: t('_global.continue'),
  }

  if (
    relationships > 0 &&
    (await confirm.value?.open(
      `${t('CRFItemGroups.delete_warning', { count: relationships })}`,
      options
    ))
  ) {
    crfs.delete('item-groups', props.selectedGroup.uid).then(() => {
      emit('close')
    })
  } else if (relationships === 0) {
    crfs.delete('item-groups', props.selectedGroup.uid).then(() => {
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
  if (form.value.oid === 'G.') {
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
    form.value.sdtm_domain_uids = form.value.sdtm_domains.map(
      (el) => el.term_uid
    )

    if (isEdit()) {
      await crfs
        .updateItemGroup(form.value, props.selectedGroup.uid)
        .then(async (resp) => {
          notificationHub.add({
            msg: t('CRFItemGroups.group_updated'),
          })
          emit('updateItemGroup', resp.data)
          close()
        })
    } else {
      await crfs.createItemGroup(form.value).then(async (resp) => {
        notificationHub.add({
          msg: t('CRFItemGroups.group_created'),
        })
        emit('linkGroup', resp)
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

async function initForm(item) {
  form.value = item
  form.value.aliases = item.aliases
  form.value.translated_texts = item.translated_texts
  form.value.sdtm_domains = item.sdtm_domains
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

onMounted(() => {
  terms.getTermsByCodelist('originType').then((resp) => {
    origins.value = resp.data.items
  })

  filterSdtmDomains()
  steps.value = isEdit() ? buildEditSteps() : buildCreateSteps()
})

onBeforeUnmount(() => {
  clearTimeout(domainSearchTimeout.value)
})
</script>
