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
      <v-btn class="secondary-btn" color="white" elevation="3" @click="close">
        {{ $t('_global.cancel') }}
      </v-btn>
      <v-btn color="secondary" variant="flat" elevation="3" @click="select">
        {{ $t('_global.ok') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { ref } from 'vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import StudySelectorField from './StudySelectorField.vue'

const emit = defineEmits(['close', 'selected'])

const studiesGeneralStore = useStudiesGeneralStore()

const selectedStudy = ref(null)
const observer = ref()

function close() {
  emit('close')
}
async function select() {
  const { valid } = await observer.value.validate()
  if (!valid) {
    return
  }
  studiesGeneralStore.selectStudy(selectedStudy.value)
  emit('selected')
  close()
}
</script>
