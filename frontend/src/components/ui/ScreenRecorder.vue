<template>
  <v-btn
    v-if="!isRecording"
    color="red"
    density="compact"
    icon="mdi-video-outline"
    @click="toggleRecording"
  />
</template>
<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { DateTime } from 'luxon'

const isRecording = ref(false)

let recorder = null

async function toggleRecording() {
  try {
    if (isRecording.value) {
      recorder.stop()
      isRecording.value = false
      return
    }
    const stream = await navigator.mediaDevices.getDisplayMedia({
      video: { mediaSource: 'screen' },
      audio: true,
    })
    isRecording.value = true

    recorder = new MediaRecorder(stream)
    const chunks = []

    recorder.ondataavailable = (e) => chunks.push(e.data)
    recorder.onstop = () => {
      const completeBlob = new Blob(chunks, { type: 'video/webm' })
      const url = URL.createObjectURL(completeBlob)
      const a = document.createElement('a')
      document.body.appendChild(a)
      a.style = 'display: none'
      a.href = url
      a.download = `osb - screen recording - ${DateTime.utc().toFormat("yyyy-MM-dd'T'HH_mm_ss")}.webm`
      a.click()
      URL.revokeObjectURL(url)
      isRecording.value = false
    }
    recorder.start()
  } catch (e) {
    console.error('Error during screen recording:', e)
  }
}

onMounted(() => {
  window.addEventListener('beforeunload', handleBeforeUnload)
})

onUnmounted(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
})

function handleBeforeUnload(e) {
  if (isRecording.value) {
    e.preventDefault()
  }
}
</script>
