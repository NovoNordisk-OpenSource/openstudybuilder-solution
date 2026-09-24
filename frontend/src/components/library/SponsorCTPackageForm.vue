<template>
  <SimpleFormDialog
    :title="$t('SponsorCTPackageForm.title')"
    :open="props.open"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-form ref="formRef">
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="selectedCatalogue"
              :label="$t('SponsorCTPackageForm.catalogue_label')"
              :items="catalogues"
              :rules="[formRules.required]"
              item-title="name"
              data-cy="sponsor-ct-catalogue-dropdown"
              return-object
              clearable
              color="nnTrueBlue"
              @update:model-value="fetchPackages"
            />
            <v-autocomplete
              v-model="form.extends_package"
              :label="$t('SponsorCTPackageForm.package_label')"
              :items="packages"
              item-title="name"
              item-value="uid"
              :disabled="selectedCatalogue === null"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import controlledTerminologyApi from '@/api/controlledTerminology'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'

const props = defineProps({
  open: Boolean,
})
const emit = defineEmits(['close', 'created'])
const { t } = useI18n()
const notificationHub = inject('notificationHub')
const formRules = inject('formRules')

const catalogues = ref([])
const form = ref({})
const formRef = ref()
const packages = ref([])
const selectedCatalogue = ref(null)

function close() {
  notificationHub.clearErrors()
  formRef.value.resetValidation()
  form.value = {}
  emit('close')
}

async function submit() {
  const { valid } = await formRef.value.validate()
  if (!valid) {
    return
  }

  notificationHub.clearErrors()

  const today = new Date()
  const data = {
    ...form.value,
    effective_date: today.toISOString().split('T')[0],
  }
  controlledTerminologyApi.createSponsorPackage(data).then(() => {
    notificationHub.add({
      msg: t('SponsorCTPackageForm.creation_success'),
    })
    emit('created')
    close()
  })
}

function fetchPackages(catalogue) {
  form.value.extends_package = null
  controlledTerminologyApi
    .getPackages({ catalogue_name: catalogue.name })
    .then((resp) => {
      packages.value = resp.data
    })
}

controlledTerminologyApi.getCatalogues().then((resp) => {
  catalogues.value = resp.data
})
</script>
