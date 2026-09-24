<template>
  <SimpleFormDialog
    ref="dialog"
    :title="title"
    :open="open"
    max-width="600px"
    :action-label="actionLabel"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-form ref="formRef">
        <v-radio-group v-if="!standardVersion" v-model="creationMode">
          <v-radio
            :label="$t('CTStandardVersionsForm.mode_create')"
            value="create"
          />
          <v-radio
            :label="$t('CTStandardVersionsForm.mode_select')"
            value="select"
          />
        </v-radio-group>
        <label class="nn-label">{{
          $t('CTStandardVersionsTable.ct_catalogue')
        }}</label>
        <v-autocomplete
          v-model="selectedCatalogue"
          :items="catalogues"
          :rules="[formRules.required]"
          item-title="name"
          data-cy="sponsor-ct-catalogue-dropdown"
          return-object
          clearable
          color="nnTrueBlue"
          @update:model-value="fetchPackages"
        />
        <label class="nn-label">{{ packageFieldLabel }}</label>
        <v-autocomplete
          v-model="selectedPackage"
          :items="packages"
          :rules="[formRules.required]"
          item-title="name"
          data-cy="sponsor-ct-package-dropdown"
          return-object
          clearable
          :disabled="selectedCatalogue === null"
        />
        <label class="nn-label">{{ $t('_global.description') }}</label>
        <v-textarea
          v-model="form.description"
          data-cy="description-field"
          clearable
          rows="1"
          auto-grow
        />
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import controlledTerminologyApi from '@/api/controlledTerminology'
import studyApi from '@/api/study'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'

const props = defineProps({
  standardVersion: {
    type: Object,
    default: null,
  },
  open: Boolean,
})
const emit = defineEmits(['close', 'save'])

const { t } = useI18n()
const formRules = inject('formRules')
const notificationHub = inject('notificationHub')
const studiesGeneralStore = useStudiesGeneralStore()

const catalogues = ref([])
const creationMode = ref(!props.standardVersion ? 'create' : 'select')
const dialog = ref()
const form = ref({})
const formRef = ref()
const packages = ref([])
const selectedCatalogue = ref(null)
const selectedPackage = ref(null)

const title = computed(() => {
  return props.standardVersion
    ? t('CTStandardVersionsForm.edit_title')
    : t('CTStandardVersionsForm.add_title')
})

const packageFieldLabel = computed(() => {
  return creationMode.value === 'create'
    ? t('CTStandardVersionsTable.cdisc_ct_package')
    : t('CTStandardVersionsTable.sponsor_ct_package')
})

const actionLabel = computed(() => {
  return creationMode.value === 'create'
    ? t('CTStandardVersionsForm.create_package')
    : t('CTStandardVersionsForm.select_package')
})

watch(
  () => props.standardVersion,
  (value) => {
    if (value) {
      selectedCatalogue.value = catalogues.value.find(
        (item) => item.name === value.ct_package.catalogue_name
      )
      fetchPackages(selectedCatalogue)
      selectedPackage.value = value.ct_package
      form.value.description = value.description
      creationMode.value = 'select'
    } else {
      selectedPackage.value = null
      form.value.description = ''
      creationMode.value = 'create'
    }
  },
  { immediate: true }
)

function close() {
  notificationHub.clearErrors()
  form.value = {}
  selectedCatalogue.value = null
  selectedPackage.value = null
  emit('close')
}

function fetchPackages(catalogue) {
  selectedPackage.value = null
  if (creationMode.value === 'create') {
    controlledTerminologyApi
      .getPackages({ catalogue_name: catalogue.name })
      .then((resp) => {
        packages.value = resp.data
      })
  } else {
    controlledTerminologyApi.getSponsorPackages(catalogue.name).then((resp) => {
      packages.value = resp.data
    })
  }
}

async function createSponsorCtPackage() {
  const now = new Date()
  const data = {
    extends_package: selectedPackage.value.name,
    effective_date: now.toISOString().split('T')[0],
    description: form.value.description,
  }
  return await controlledTerminologyApi.createSponsorPackage(data)
}

async function submit() {
  const { valid } = await formRef.value.validate()
  if (!valid) {
    dialog.value.working = false
    return
  }

  notificationHub.clearErrors()

  try {
    if (creationMode.value === 'create') {
      const { data: sponsorPackage } = await createSponsorCtPackage()
      form.value.ct_package_uid = sponsorPackage.uid
    } else {
      form.value.ct_package_uid = selectedPackage.value.uid
    }
    if (!props.standardVersion) {
      await studyApi.createStudyStandardVersions(
        studiesGeneralStore.selectedStudy.uid,
        form.value
      )
      notificationHub.add({
        msg: t('CTStandardVersionsForm.add_success'),
      })
    } else {
      if (
        selectedPackage.value.uid === props.standardVersion.ct_package.uid &&
        props.standardVersion.description === form.value.description
      ) {
        notificationHub.add({
          type: 'info',
          msg: t('_global.no_changes'),
        })
        close()
        return
      }
      await studyApi.updateStudyStandardVersion(
        studiesGeneralStore.selectedStudy.uid,
        props.standardVersion.uid,
        form.value
      )
      notificationHub.add({
        msg: t('CTStandardVersionsForm.update_success'),
      })
    }
    emit('save')
    close()
  } finally {
    dialog.value.working = false
  }
}

controlledTerminologyApi.getCatalogues().then((resp) => {
  catalogues.value = resp.data
})
</script>
