<template>
  <v-card data-cy="form-body" color="white">
    <v-card-title>
      <span class="dialog-title">{{ $t('StudyQuickSelectForm.title') }}</span>
    </v-card-title>
    <v-card-text>
      <v-form ref="observer">
        <StudySelectorField v-model="selectedStudy" class="mt-4" />
      </v-form>
    </v-card-text>

    <v-card-actions class="pb-4">
      <v-spacer />
      <v-btn class="secondary-btn" color="white" elevation="1" @click="close">
        {{ $t('_global.cancel') }}
      </v-btn>
      <v-btn
        color="secondary"
        variant="flat"
        elevation="1"
        :loading="loading"
        @click="select"
      >
        {{ $t('_global.ok') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { nextTick, onMounted, ref } from 'vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import StudySelectorField from './StudySelectorField.vue'
import studyApi from '@/api/study'

const emit = defineEmits(['close', 'selected'])

const studiesGeneralStore = useStudiesGeneralStore()

const loading = ref(false)

const selectedStudy = ref(null)
const observer = ref()
const isInitializing = ref(true)

onMounted(async () => {
  if (studiesGeneralStore.selectedStudy) {
    const currentStudy = studiesGeneralStore.selectedStudy

    selectedStudy.value = {
      uid: currentStudy.study_parent_part?.uid || currentStudy.uid,
      id: currentStudy.current_metadata
        ? currentStudy.current_metadata.identification_metadata.study_id
        : currentStudy.id,
      acronym: currentStudy.current_metadata
        ? currentStudy.current_metadata.identification_metadata.study_acronym
        : currentStudy.acronym,
    }
  }

  await nextTick()
  isInitializing.value = false
})

function close() {
  emit('close')
}
async function select() {
  loading.value = true
  const { valid } = await observer.value.validate()
  if (!valid) {
    return
  }
  studiesGeneralStore.selectedStudyVersion = null
  studyApi
    .getStudy(selectedStudy.value.uid)
    .then((study) => {
      selectedStudy.value = study.data
      studiesGeneralStore.selectStudy(selectedStudy.value).then(() => {
        loading.value = false
        emit('selected')
        close()
      })
    })
    .catch((error) => {
      loading.value = false
      console.error('Error fetching study:', error)
    })
}
</script>
