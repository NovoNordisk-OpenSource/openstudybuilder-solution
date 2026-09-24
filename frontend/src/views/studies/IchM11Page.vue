<template>
  <div class="px-4 h-100">
    <div class="page-title d-flex align-center">
      {{ $t('IchM11Page.title') }}
    </div>
    <v-card class="pa-6 h-100">
      <v-row>
        <v-col class="d-flex justify-center" cols="12">
          <v-progress-circular
            v-if="loading"
            class="ml-6 mt-12"
            size="128"
            color="primary"
            indeterminate
          />
        </v-col>
      </v-row>
      <iframe v-show="!loading" :title="$t('IchM11Page.title')" />
    </v-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import study from '@/api/study'

const studiesGeneralStore = useStudiesGeneralStore()

const loading = ref(false)

onMounted(() => {
  loading.value = true
  study.getDdfIchM11(studiesGeneralStore.selectedStudy.uid).then((resp) => {
    var iframe = document.createElement('iframe')
    iframe.classList.add('frame')
    document.querySelector('iframe').replaceWith(iframe)
    var iframeDoc = iframe.contentDocument
    iframeDoc.write(resp.data)
    iframeDoc.close()
    loading.value = false
  })
})
</script>

<style>
.frame {
  width: 100%;
  height: 100%;
}
</style>
