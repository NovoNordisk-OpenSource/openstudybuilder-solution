<template>
  <SimpleFormDialog
    ref="form"
    :title="title"
    :open="open"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="formData.group_id"
              :label="$t('StudyDesignPopulationForm.group_id')"
              data-cy="sdp-group-id"
              :rules="[atLeastOneFieldRule]"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="formData.name"
              :label="$t('StudyDesignPopulationForm.name')"
              data-cy="sdp-name"
              :rules="[atLeastOneFieldRule]"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-textarea
              v-model="formData.definition"
              :label="$t('StudyDesignPopulationForm.definition')"
              data-cy="sdp-definition"
              rows="3"
              :rules="[atLeastOneFieldRule]"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-textarea
              v-model="formData.notes"
              :label="$t('StudyDesignPopulationForm.notes')"
              data-cy="sdp-notes"
              rows="3"
              :rules="[atLeastOneFieldRule]"
              clearable
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import study from '@/api/study'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  sdp: {
    type: Object,
    default: null,
  },
})
// 'saved' carries the saved population record so the caller can chain the
// separate criteria-assignment step (population creation/update and
// criteria assignment are two independent API calls).
const emit = defineEmits(['close', 'saved'])

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const studiesGeneralStore = useStudiesGeneralStore()
const form = ref()
const observer = ref()
const formData = ref({})

const title = computed(() =>
  props.sdp
    ? t('StudyDesignPopulationForm.edit_title')
    : t('StudyDesignPopulationForm.add_title')
)

function atLeastOneFieldRule() {
  const { group_id, name, definition, notes } = formData.value
  return (
    !!(group_id || name || definition || notes) ||
    t('StudyDesignPopulationForm.at_least_one_required')
  )
}

watch(
  () => props.open,
  (isOpen) => {
    if (!isOpen) return
    formData.value = props.sdp ? { ...props.sdp } : {}
  },
  { immediate: true }
)

function close() {
  emit('close')
  notificationHub.clearErrors()
  formData.value = {}
  observer.value?.reset()
}

async function submit() {
  notificationHub.clearErrors()
  const data = { ...formData.value }
  const studyUid = studiesGeneralStore.selectedStudy.uid

  try {
    let savedUid
    if (props.sdp) {
      await study.updateStudyDesignPopulation(studyUid, props.sdp.uid, data)
      savedUid = props.sdp.uid
      notificationHub.add({
        msg: t('StudyDesignPopulationForm.update_success'),
      })
    } else {
      const resp = await study.createStudyDesignPopulation(studyUid, data)
      savedUid = resp.data.uid
      notificationHub.add({ msg: t('StudyDesignPopulationForm.add_success') })
    }
    form.value.working = false
    emit('saved', { uid: savedUid, ...data })
    close()
  } catch {
    form.value.working = false
  }
}
</script>
