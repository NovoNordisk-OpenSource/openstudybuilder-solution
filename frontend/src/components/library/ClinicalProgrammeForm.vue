<template>
  <SimpleFormDialog
    ref="formRef"
    :title="title"
    :help-text="$t('_help.ClinicalProgrammeForm.general')"
    :help-items="helpItems"
    :open="open"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col cols="12">
            <v-text-field
              id="name"
              v-model="form.name"
              :label="$t('ClinicalProgrammeForm.name')"
              clearable
              data-cy="clinical-programme-name"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useFormStore } from '@/stores/form'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import programmes from '@/api/clinicalProgrammes'

const { t } = useI18n()

const notificationHub = inject('notificationHub')
const formRules = inject('formRules')
const formStore = useFormStore()
const props = defineProps({
  programmeUid: {
    type: String,
    default: null,
  },
  open: Boolean,
})

const emit = defineEmits(['close', 'reload'])

const form = ref({})
const formRef = ref()

const helpItems = ['ClinicalProgrammeForm.name']

const title = computed(() => {
  return props.programmeUid
    ? t('ClinicalProgrammeForm.edit_title')
    : t('ClinicalProgrammeForm.add_title')
})

watch(
  () => props.programmeUid,
  (value) => {
    if (value) {
      programmes.retrieve(value).then((resp) => {
        form.value = resp.data
        formStore.save({ ...form.value })
      })
    }
  },
  { immediate: true }
)

onMounted(() => {
  initForm()
  formStore.save({ ...form.value })
})

async function close() {
  notificationHub.clearErrors()
  if (!formStore.isEqual(form.value)) {
    const options = {
      type: 'warning',
      cancelLabel: t('_global.cancel'),
      agreeLabel: t('_global.continue'),
    }
    if (!(await formRef.value.confirm(t('_global.cancel_changes'), options))) {
      return
    }
  }
  initForm()
  emit('close')
}
function initForm() {
  form.value = {
    name: '',
  }
  formStore.reset()
}
async function addProgramme() {
  notificationHub.clearErrors()

  const data = JSON.parse(JSON.stringify(form.value))
  await programmes.create(data)
  notificationHub.add({
    msg: t('ClinicalProgrammes.add_success'),
  })
}

async function updateProgramme() {
  notificationHub.clearErrors()

  const data = JSON.parse(JSON.stringify(form.value))
  await programmes.patch(props.programmeUid, data)
  notificationHub.add({
    msg: t('ClinicalProgrammes.update_success'),
  })
}

async function submit() {
  try {
    if (!props.programmeUid) {
      await addProgramme()
    } else {
      await updateProgramme()
    }
    emit('reload')
    emit('close')
  } finally {
    formRef.value.working = false
  }
  initForm()
}
</script>
