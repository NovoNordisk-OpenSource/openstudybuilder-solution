<template>
  <SimpleFormDialog
    ref="formRef"
    :title="$t('StudySubparts.edit_subpart')"
    :help-items="helpItems"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col>
            <v-text-field
              :label="$t('StudySubparts.derived_subpart_id')"
              :model-value="form.study_number"
              disabled
              hide-details
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.study_acronym"
              :label="$t('StudySubparts.study_acronym')"
              hide-details
              disabled
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              :model-value="form.study_subpart_acronym"
              :label="$t('StudySubparts.study_subpart_acronym')"
              :rules="[
                formRules.required,
                formRules.uppercaseAlphanumeric,
                (v) => formRules.max(v, 10),
              ]"
              @update:model-value="
                form.study_subpart_acronym = $event?.toUpperCase().trim()
              "
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-textarea
              v-model="form.description"
              :label="$t('_global.description')"
              clearable
              auto-grow
              rows="3"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import _isEmpty from 'lodash/isEmpty'
import studies from '@/api/study'
import { watch, ref, inject } from 'vue'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  editedSubpart: {
    type: Object,
    default: null,
  },
})

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const formRules = inject('formRules')
const emit = defineEmits(['close'])
const studiesGeneralStore = useStudiesGeneralStore()

const form = ref({})
const formRef = ref()
const observer = ref()

let payload = {}
const helpItems = []

watch(
  () => props.editedSubpart,
  (value) => {
    if (!_isEmpty(value)) {
      studies.getStudy(value.uid).then((resp) => {
        initForm(resp.data)
      })
    }
  }
)

function initForm(subpart) {
  form.value.study_number =
    subpart.current_metadata.identification_metadata.study_number
  form.value.study_acronym =
    subpart.current_metadata.identification_metadata.study_acronym
  form.value.study_subpart_acronym =
    subpart.current_metadata.identification_metadata.study_subpart_acronym
  form.value.description =
    subpart.current_metadata.identification_metadata.description
  payload = subpart
}

function submit() {
  notificationHub.clearErrors()

  payload.study_parent_part_uid = studiesGeneralStore.selectedStudy.uid
  payload.current_metadata.identification_metadata.description =
    form.value.description
  payload.current_metadata.identification_metadata.study_acronym =
    form.value.study_acronym
  payload.current_metadata.identification_metadata.study_subpart_acronym =
    form.value.study_subpart_acronym
  delete payload.current_metadata.study_description
  delete payload.study_parent_part
  delete payload.current_metadata.identification_metadata.registry_identifiers
  studies.updateStudy(payload.uid, payload).then(
    () => {
      notificationHub.add({ msg: t('StudySubparts.subpart_edited') })
      formRef.value.working = false
      cancel()
    },
    () => {
      formRef.value.working = false
    }
  )
}

function cancel() {
  emit('close')
  notificationHub.clearErrors()
}
</script>
