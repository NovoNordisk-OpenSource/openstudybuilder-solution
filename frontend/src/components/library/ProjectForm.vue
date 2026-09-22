<template>
  <SimpleFormDialog
    ref="formRef"
    :title="title"
    :help-items="helpItems"
    :help-text="$t('_help.ClinicalProgrammeForm.general')"
    :open="open"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col cols="11">
            <v-autocomplete
              v-model="form.clinical_programme_uid"
              :label="$t('ProjectForm.clinical_programme')"
              data-cy="template-activity-group"
              :items="programmes"
              item-title="name"
              item-value="uid"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              id="name"
              v-model="form.name"
              :label="$t('ProjectForm.name')"
              clearable
              data-cy="project-name"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row v-if="!projectUid">
          <v-col cols="12">
            <v-text-field
              id="project-number"
              v-model="form.project_number"
              :label="$t('ProjectForm.project_number')"
              clearable
              data-cy="project-number"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              id="description"
              v-model="form.description"
              :label="$t('ProjectForm.description')"
              clearable
              data-cy="project-description"
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
import programmesApi from '@/api/clinicalProgrammes'
import projects from '@/api/projects'

const { t } = useI18n()
const formStore = useFormStore()
const formRules = inject('formRules')
const notificationHub = inject('notificationHub')

const props = defineProps({
  projectUid: {
    type: String,
    default: null,
  },
  open: Boolean,
})

const emit = defineEmits(['reload', 'close'])

const form = ref({})
const formRef = ref()
const programmes = ref([])

const helpItems = [
  'ProjectForm.clinical_programme',
  'ProjectForm.name',
  'ProjectForm.project_number',
  'ProjectForm.description',
]

const title = computed(() => {
  return props.projectUid
    ? t('ProjectForm.edit_title')
    : t('ProjectForm.add_title')
})

watch(
  () => props.projectUid,
  (value) => {
    if (value) {
      projects.retrieve(value).then((resp) => {
        form.value = resp.data
        form.value.clinical_programme_uid = form.value.clinical_programme.uid
        formStore.save({ ...form.value })
      })
    }
  },
  { immediate: true }
)

onMounted(() => {
  fetchProgrammes()
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
  emit('close')
  initForm()
}

function initForm() {
  form.value = {}
  formStore.reset()
}

async function addProject() {
  const data = JSON.parse(JSON.stringify(form.value))
  await projects.create(data)
  notificationHub.add({
    msg: t('Projects.add_success'),
  })
}

async function updateProject() {
  const data = JSON.parse(JSON.stringify(form.value))
  await projects.patch(props.projectUid, data)
  notificationHub.add({
    msg: t('Projects.update_success'),
  })
}

async function submit() {
  notificationHub.clearErrors()

  try {
    if (!props.projectUid) {
      await addProject()
    } else {
      await updateProject()
    }
    emit('close')
    emit('reload')
  } finally {
    formRef.value.working = false
  }
  initForm()
}

function fetchProgrammes() {
  programmesApi.get({ page_size: 0 }).then((resp) => {
    programmes.value = resp.data.items
  })
}
</script>
