<template>
  <SimpleFormDialog
    :title="$t('StandardsImport.cdisc_api_key_title')"
    :action-label="$t('StandardsImport.cdisc_api_key_action')"
    :open="open"
    max-width="600px"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer" @submit.prevent="submit">
        <p class="mb-4">
          {{ $t('StandardsImport.cdisc_api_key_description') }}
        </p>
        <v-text-field
          v-model="apiKey"
          :label="$t('StandardsImport.cdisc_api_key_label')"
          :rules="[formRules.required]"
          type="password"
          autocomplete="off"
          clearable
          autofocus
          data-cy="cdisc-api-key-field"
        />
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { inject, ref, watch } from 'vue'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'

const props = defineProps({
  open: Boolean,
})
const emit = defineEmits(['close', 'submit'])

const formRules = inject('formRules')
const observer = ref(null)
const apiKey = ref('')

// The key is never kept past the dialog: it is cleared whenever the dialog closes.
watch(
  () => props.open,
  (isOpen) => {
    if (!isOpen) {
      apiKey.value = ''
    }
  }
)

function close() {
  apiKey.value = ''
  emit('close')
}

function submit() {
  const key = (apiKey.value || '').trim()
  if (!key) {
    return
  }
  emit('submit', key)
}
</script>
