<template>
  <v-card color="dfltBackground">
    <v-card-title class="d-flex align-center">
      <span class="dialog-title">{{ $t('CodelistTermNamesForm.title') }}</span>
      <HelpButtonWithPanels :title="$t('_global.help')" :items="helpItems" />
    </v-card-title>
    <v-card-text class="mt-4">
      <div class="bg-white pa-4">
        <v-form ref="observer">
          <v-text-field
            v-model="form.concept_id"
            :label="$t('CodelistTermCreationForm.concept_id')"
            clearable
          />
          <v-text-field
            v-model="form.nci_preferred_name"
            :label="$t('CodelistTermCreationForm.nci_pref_name')"
            clearable
          />
          <v-textarea
            v-model="form.definition"
            :label="$t('CodelistTermCreationForm.definition')"
            :rules="[formRules.required]"
            clearable
            rows="1"
            auto-grow
          />
          <v-textarea
            v-model="form.change_description"
            :label="$t('HistoryTable.change_description')"
            :rules="[formRules.required]"
            :rows="1"
            class="white py-2"
            auto-grow
          />
        </v-form>
      </div>
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn class="secondary-btn" color="white" @click="cancel">
        {{ $t('_global.cancel') }}
      </v-btn>
      <v-btn color="secondary" :loading="working" @click="submit">
        {{ $t('_global.save') }}
      </v-btn>
    </v-card-actions>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  </v-card>
</template>

<script setup>
import { inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import controlledTerminology from '@/api/controlledTerminology'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import { useFormStore } from '@/stores/form'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const formRules = inject('formRules')
const props = defineProps({
  modelValue: {
    type: Object,
    default: null,
  },
})
const emit = defineEmits(['close', 'update:modelValue'])
const formStore = useFormStore()

const form = ref({})
const working = ref(false)
const confirm = ref()
const observer = ref()

const helpItems = [
  'CodelistTermCreationForm.nci_pref_name',
  'CodelistTermCreationForm.definition',
]

watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      controlledTerminology
        .getCodelistTermAttributes(val.term_uid)
        .then((resp) => {
          form.value = {
            concept_id: resp.data.concept_id,
            nci_preferred_name: resp.data.nci_preferred_name,
            definition: resp.data.definition,
          }
          formStore.save(form.value)
        })
    }
  },
  { immediate: true }
)

async function cancel() {
  if (formStore.isEmpty || formStore.isEqual(form.value)) {
    close()
  } else {
    const options = {
      type: 'warning',
      cancelLabel: t('_global.cancel'),
      agreeLabel: t('_global.continue'),
    }
    if (await confirm.value.open(t('_global.cancel_changes'), options)) {
      close()
    }
  }
}

function close() {
  emit('close')
  notificationHub.clearErrors()
  formStore.reset()
  form.value.change_description = ''
}

async function submit() {
  const { valid } = await observer.value.validate()

  notificationHub.clearErrors()

  if (!valid) return
  working.value = true
  try {
    const resp = await controlledTerminology.updateCodelistTermAttributes(
      props.modelValue.term_uid,
      form.value
    )
    emit('update:modelValue', resp.data)
    notificationHub.add({
      msg: t('CodelistTermNamesForm.update_success'),
    })
    close()
  } finally {
    working.value = false
  }
}
</script>
