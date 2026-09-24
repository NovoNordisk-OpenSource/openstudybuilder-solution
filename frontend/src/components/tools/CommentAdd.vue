<template>
  <div>
    <v-textarea
      v-model="text"
      auto-grow
      rows="1"
      class="mt-2"
      :class="isTransparent ? 'mx-0' : 'mx-5'"
      :label="$t('Comments.comment_add_placeholder')"
    />
    <div
      v-show="!loading"
      v-if="text.length > 0"
      class="mt-n2 pb-4"
      :class="isTransparent ? 'mx-0' : 'mx-5'"
    >
      <v-btn rounded="xl" color="white" @click="cancelCreate">
        {{ $t('_global.cancel') }}
      </v-btn>
      <v-btn
        class="primary-btn mx-4"
        rounded="xl"
        color="secondary"
        @click="createThread"
      >
        {{ $t('Comments.comment_add_button') }}
      </v-btn>
    </div>
    <div v-show="loading" class="px-6 mb-4">
      <v-progress-linear indeterminate color="primary" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import comments from '@/api/comments'

const props = defineProps({
  topicPath: {
    type: String,
    required: true,
  },
  isTransparent: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['commentThreadAdded'])

const text = ref('')
const loading = ref(false)

function createThread() {
  const data = {
    topic_path: props.topicPath,
    text: text.value,
  }
  loading.value = true
  comments.createThread(data).then(
    () => {
      text.value = ''
      loading.value = false
      emit('commentThreadAdded')
    },
    () => {
      loading.value = false
    }
  )
}

function cancelCreate() {
  text.value = ''
}
</script>
