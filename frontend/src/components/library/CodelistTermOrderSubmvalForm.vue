<template>
  <SimpleFormDialog
    ref="formRef"
    :title="$t('CodelistTermOrderSubmvalForm.order_and_submval_edit')"
    :help-items="helpItems"
    :open="open"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-text-field
          data-cy="term-name"
          :model-value="termName"
          :label="$t('CodelistTermOrderSubmvalForm.term')"
          disabled
        />
        <v-text-field
          data-cy="codelist-name"
          :model-value="codelistName"
          :label="$t('CodelistTermOrderSubmvalForm.codelist')"
          disabled
        />
        <v-combobox
          v-model="form.submissionValue"
          :items="submissionValues"
          data-cy="term-submission-value"
          :label="$t('CodelistTermDetail.submission_value')"
          :rules="[formRules.required]"
          clearable
        />
        <v-text-field
          v-model.number="form.order"
          data-cy="term-order"
          type="number"
          :label="$t('CodelistTermCreationForm.order')"
          :rules="[formRules.required]"
          clearable
        />
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import controlledTerminology from '@/api/controlledTerminology'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'

const formRules = inject('formRules')
const notificationHub = inject('notificationHub')

const props = defineProps({
  open: Boolean,
  termUid: {
    type: String,
    default: null,
  },
  codelistUid: {
    type: String,
    default: null,
  },
  submissionValue: {
    type: String,
    default: null,
  },
  order: {
    type: Number,
    default: null,
  },
  codelistName: {
    type: String,
    default: null,
  },
  termName: {
    type: String,
    default: null,
  },
  submissionValues: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['close', 'update:modelValue'])
const { t } = useI18n()

const form = ref({})
const observer = ref()
const working = ref(false)

const helpItems = [
  'CodelistTermCreationForm.submission_value',
  'CodelistTermCreationForm.order',
]

watch(
  () => props.termUid,
  (val) => {
    if (val) {
      form.value = {
        submissionValue: props.submissionValue,
        order: props.order,
      }
    }
  },
  { immediate: true }
)

function close() {
  emit('close')
  notificationHub.clearErrors()
}

async function submit() {
  const { valid } = await observer.value.validate()
  if (!valid) return

  notificationHub.clearErrors()

  working.value = true
  try {
    const orderData = {
      codelist_uid: props.codelistUid,
      order: form.value.order,
      submission_value: form.value.submissionValue,
    }
    await controlledTerminology.updateCodelistTermOrderSubmval(
      props.termUid,
      orderData
    )
    notificationHub.add({
      msg: t('CodelistTermOrderSubmvalForm.update_success'),
    })
    close()
  } finally {
    working.value = false
  }
}
</script>
