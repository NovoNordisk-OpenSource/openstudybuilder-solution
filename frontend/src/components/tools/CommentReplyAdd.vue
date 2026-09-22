<template>
  <div class="comment-reply-form mt-4" :class="isTransparent ? 'mx-5' : 'mx-0'">
    <v-textarea
      v-model="text"
      auto-grow
      bg-color="white"
      rows="1"
      class="mt-n4"
      :class="isTransparent ? 'mx-0' : 'mx-5'"
      :label="$t('Comments.reply_add_placeholder')"
    />
    <div
      v-show="!loading"
      v-if="text.length > 0"
      class="mt-n2 pb-5"
      :class="isTransparent ? 'mx-0' : 'mx-5'"
    >
      <v-btn color="white" rounded="xl" @click="cancelCreate">
        {{ $t('_global.cancel') }}
      </v-btn>
      <v-btn
        v-if="threadStatus != statuses.COMMENT_STATUS_ACTIVE"
        class="ml-4"
        rounded="xl"
        color="white"
        @click="createReply(statuses.COMMENT_STATUS_ACTIVE)"
      >
        {{ $t('Comments.reply_and_reactivate_button') }}
      </v-btn>
      <v-btn
        v-if="threadStatus == statuses.COMMENT_STATUS_ACTIVE"
        class="ml-4"
        rounded="xl"
        color="white"
        @click="createReply(statuses.COMMENT_STATUS_RESOLVED)"
      >
        {{ $t('Comments.reply_and_resolve_button') }}
      </v-btn>
      <v-btn
        class="ml-4"
        rounded="xl"
        color="secondary"
        @click="createReply(null)"
      >
        {{ $t('Comments.reply_add_button') }}
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
import statuses from '@/constants/statuses'

const props = defineProps({
  threadId: {
    type: String,
    required: true,
  },
  threadStatus: {
    type: String,
    required: true,
  },
  isTransparent: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['commentReplyAdded'])

const text = ref('')
const loading = ref(false)

function createReply(newThreadStatus) {
  loading.value = true
  comments.createReply(props.threadId, text.value, newThreadStatus).then(
    () => {
      text.value = ''
      loading.value = false
      emit('commentReplyAdded')
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

<style scoped>
.comment-reply-form {
  margin-bottom: -1rem;
  margin-left: 40px;
}
</style>
