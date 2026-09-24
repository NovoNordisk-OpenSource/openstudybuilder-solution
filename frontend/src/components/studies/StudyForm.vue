<template>
  <SimpleFormDialog
    ref="formRef"
    :title="title"
    :help-items="helpItems"
    :open="open"
    :scrollable="false"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col cols="12">
            <v-autocomplete
              v-model="form.project_number"
              :label="$t('StudyForm.project_id')"
              :items="studiesManageStore.projects"
              item-title="project_number"
              return-object
              :rules="[formRules.required]"
              clearable
              data-cy="project-id"
              @update:model-value="updateProject"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              :label="$t('StudyForm.project_name')"
              :model-value="project.name"
              disabled
              hide-details
              data-cy="project-name"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              :label="$t('StudyForm.brand_name')"
              :model-value="project.brand_name"
              disabled
              hide-details
              data-cy="brand-name"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              id="studyNumber"
              v-model="form.study_number"
              :label="$t('StudyForm.number')"
              :rules="[
                formRules.numeric,
                (value) =>
                  formRules.oneOfTwo(
                    value,
                    form.study_acronym,
                    $t('StudyForm.one_of_two_error_message')
                  ),
                (value) => formRules.max(value, appStore.studyNumberLength),
              ]"
              clearable
              data-cy="study-number"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              id="studyAcronym"
              v-model="form.study_acronym"
              :label="$t('StudyForm.acronym')"
              :rules="[
                (value) =>
                  formRules.oneOfTwo(
                    value,
                    form.study_number,
                    $t('StudyForm.one_of_two_error_message')
                  ),
              ]"
              clearable
              data-cy="study-acronym"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="studyId"
              :label="$t('StudyForm.study_id')"
              disabled
              hide-details
              data-cy="study-id"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { computed, onMounted, inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import { useAppStore } from '@/stores/app'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudiesManageStore } from '@/stores/studies-manage'
import studyApi from '@/api/study'
import { useFormStore } from '@/stores/form'

const props = defineProps({
  editedStudy: {
    type: Object,
    default: undefined,
  },
  open: Boolean,
})

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const formRules = inject('formRules')
const emit = defineEmits(['close', 'updated'])
const studiesManageStore = useStudiesManageStore()
const studiesGeneralStore = useStudiesGeneralStore()
const appStore = useAppStore()
const formRef = ref()
const formStore = useFormStore()

const form = ref({})
const project = ref({})
const helpItems = [
  'StudyForm.project_id',
  'StudyForm.project_name',
  'StudyForm.brand_name',
  'StudyForm.study_id',
  { key: 'StudyForm.number', context: getNumberTranslationContext },
  'StudyForm.acronym',
]

const title = computed(() => {
  return props.editedStudy
    ? t('StudyForm.edit_title')
    : t('StudyForm.add_title')
})
const studyId = computed(() => {
  if (project.value.project_number && form.value.study_number) {
    return `${project.value.project_number}-${form.value.study_number}`
  }
  return ''
})

watch(
  () => props.editedStudy,
  (value) => {
    if (value) {
      studyApi.getStudy(value.uid).then((resp) => {
        initForm(resp.data)
      })
    }
  }
)

onMounted(() => {
  if (props.editedStudy) {
    initForm(props.editedStudy)
  }
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
}

function initForm(value) {
  form.value = {
    project_number:
      value.current_metadata.identification_metadata.project_number,
    study_number: value.current_metadata.identification_metadata.study_number,
    study_acronym: value.current_metadata.identification_metadata.study_acronym,
  }
  project.value = studiesManageStore.getProjectByNumber(
    form.value.project_number
  )
  formStore.save(form.value)
}

function updateProject(value) {
  project.value = value
  form.value.project_number = value.project_number
}

async function addStudy() {
  const data = JSON.parse(JSON.stringify(form.value))
  data.project_number = project.value.project_number
  const resp = await studiesManageStore.addStudy(data)
  notificationHub.add({ msg: t('StudyForm.add_success') })
  await studiesGeneralStore.selectStudy(resp.data, true)
}

function updateStudy() {
  if (formStore.isEqual(form.value)) {
    notificationHub.add({ msg: t('_global.no_changes'), type: 'info' })
    return
  }
  const data = JSON.parse(JSON.stringify(form.value))
  data.project_number = form.value.project_number
  return studiesManageStore
    .editStudyIdentification(props.editedStudy.uid, data)
    .then((resp) => {
      if (
        studiesGeneralStore.selectedStudy &&
        props.editedStudy.uid === studiesGeneralStore.selectedStudy.uid
      ) {
        studiesGeneralStore.selectStudy(resp.data)
      }
      emit('updated', resp.data)
      notificationHub.add({ msg: t('StudyForm.update_success') })
    })
}

function getNumberTranslationContext() {
  return { length: appStore.studyNumberLength }
}

async function submit() {
  notificationHub.clearErrors()

  try {
    if (!props.editedStudy) {
      await addStudy()
    } else {
      await updateStudy()
    }
    project.value = {}
    formStore.reset()
    emit('close')
  } finally {
    formRef.value.working = false
  }
}
studiesManageStore.fetchProjects()
</script>
