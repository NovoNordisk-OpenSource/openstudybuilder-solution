<template>
  <div
    class="comments-wrapper mt-4 mb-4"
    :class="{ transparent: isTransparent }"
  >
    <v-divider
      v-if="!dialog"
      class="mb-8"
      :class="isTransparent ? 'mt-12' : 'mt-8'"
    />
    <v-sheet class="py-0 title elevation-0" rounded>
      <v-card-title v-if="!dialog" class="dialog-title mt-n8">
        {{ $t('Comments.comments_headline') }}
      </v-card-title>

      <v-btn-toggle
        v-model="filterThreadsBy"
        mandatory
        density="compact"
        color="nnBaseBlue"
        divided
        variant="outlined"
        class="ml-4 mt-2 mb-6"
      >
        <v-btn
          v-for="(item, index) in filteringOptions"
          :key="index"
          :value="item.value"
          class="no-uppercase"
          @click="filterThreads(item.value)"
        >
          {{ $t(`Comments.filter_by_${item.value}`) }} ({{
            getThreadCountByFilter(item.value)
          }})
        </v-btn>
      </v-btn-toggle>

      <div v-show="loading" class="px-6 mb-4">
        <v-progress-linear indeterminate color="primary" />
      </div>
      <v-list class="my-0 py-0">
        <v-list-item
          v-for="thread in commentTreadsFiltered"
          :key="thread.uid"
          class="comment-thread mb-2"
        >
          <v-card
            class="pt-2 pb-4 thread-card"
            rounded="lg"
            elevation="0"
            color="nnBaseLight"
          >
            <div
              @mouseover="thread._hovered = true"
              @mouseout="thread._hovered = false"
            >
              <v-row class="mx-5 mt-3 mb-n4">
                <v-col class="py-1 px-0 d-flex align-center">
                  <v-avatar
                    size="32"
                    :style="{
                      backgroundColor: getAvatarColor(
                        thread.author_display_name
                      ),
                    }"
                    class="mr-2 author-avatar"
                  >
                    <span class="avatar-text text-nnTrueBlue font-weight-bold">
                      {{ getInitials(thread.author_display_name) }}
                    </span>
                  </v-avatar>
                  <span class="author-name text-nnTrueBlue">
                    {{ thread.author_display_name }}
                  </span>
                  <span class="timestamp text-body-large">
                    {{ $filters.date(thread.created_at) }}
                    {{ isModified(thread.modified_at) }}
                  </span>
                </v-col>

                <v-col cols="auto" class="px-0 py-1 text-right comment-actions">
                  <div class="d-inline-block">
                    <div v-show="thread._hovered && isAuthor(thread)">
                      <v-btn
                        variant="outlined"
                        color="nnBaseBlue"
                        icon
                        size="x-small"
                        :title="$t('Comments.comment_edit')"
                        @click.stop="thread._editMode = true"
                      >
                        <v-icon icon="mdi-pencil-outline" />
                      </v-btn>
                      <v-btn
                        variant="outlined"
                        color="nnBaseBlue"
                        icon
                        size="x-small"
                        class="ml-3"
                        :title="$t('Comments.comment_delete')"
                        @click="deleteThread(thread.uid)"
                      >
                        <v-icon icon="mdi-delete-outline" />
                      </v-btn>
                    </div>
                  </div>
                  <div class="d-inline-block ml-4">
                    <v-menu location="bottom" offset-y>
                      <template #activator="{ props }">
                        <v-btn
                          :color="
                            actions.find(
                              (action) => action.newStatus === thread.status
                            )?.color
                          "
                          class="mt-1 no-uppercase"
                          size="small"
                          elevation="0"
                          v-bind="props"
                        >
                          {{ $t(`Comments.comment_status_${thread.status}`) }}
                          <v-icon
                            location="right"
                            icon="mdi-chevron-down"
                            class="pl-4"
                            size="large"
                          />
                        </v-btn>
                      </template>
                      <v-list>
                        <v-list-item
                          v-for="(item, index) in actions"
                          :key="index"
                          :value="index"
                          @click="setThreadStatus(thread, item.newStatus)"
                        >
                          <v-list-item-title>
                            <v-icon
                              v-if="item.newStatus === thread.status"
                              location="right"
                              icon="mdi-check"
                            />
                            <v-icon v-else />
                            {{
                              $t(`Comments.comment_status_${item.newStatus}`)
                            }}</v-list-item-title
                          >
                        </v-list-item>
                      </v-list>
                    </v-menu>
                  </div>
                </v-col>
              </v-row>

              <v-card-text
                v-show="!thread._editMode"
                class="pt-0 pb-3 pr-5 text-nnTrueBlue comment-text"
              >
                {{ thread.text }}
              </v-card-text>

              <div v-show="thread._editMode" class="comment-text mt-8">
                <v-textarea
                  v-model="thread._newText"
                  auto-grow
                  class="mr-5"
                  bg-color="white"
                  :label="$t('Comments.comment_edit')"
                />
                <div v-show="!loading" class="mt-n4 pb-4">
                  <v-btn
                    rounded="xl"
                    color="white"
                    @click="cancelThreadEdition(thread)"
                  >
                    {{ $t('_global.cancel') }}
                  </v-btn>
                  <v-btn
                    class="mx-4"
                    rounded="xl"
                    color="secondary"
                    :disabled="thread.text === thread._newText"
                    @click="editThread(thread.uid, thread._newText)"
                  >
                    {{ $t('Comments.comment_edit') }}
                  </v-btn>
                </div>
                <div v-show="loading" class="px-6 mb-4">
                  <v-progress-linear indeterminate color="primary" />
                </div>
              </div>
            </div>

            <!-- Replies -->
            <v-list class="mr-0 py-0" bg-color="transparent">
              <v-list-item
                v-for="reply in thread.replies"
                :key="reply.uid"
                class="comment-thread-reply mt-n1"
                @mouseover="reply._hovered = true"
                @mouseout="reply._hovered = false"
              >
                <v-row class="mx-5">
                  <v-col class="py-1 px-0 d-flex align-center">
                    <v-avatar
                      size="28"
                      :style="{
                        backgroundColor: getAvatarColor(
                          reply.author_display_name
                        ),
                      }"
                      class="mr-2 author-avatar"
                    >
                      <span
                        class="avatar-text text-nnTrueBlue font-weight-bold"
                      >
                        {{ getInitials(reply.author_display_name) }}
                      </span>
                    </v-avatar>
                    <span class="author-name text-nnTrueBlue">
                      {{ reply.author_display_name }}
                    </span>
                    <span class="timestamp text-body-large">
                      {{ $filters.date(reply.created_at) }}
                      {{ isModified(reply.modified_at) }}
                    </span>
                  </v-col>
                  <v-col cols="auto" class="pa-0 text-right">
                    <div v-show="reply._hovered && isAuthor(reply)">
                      <v-btn
                        variant="outlined"
                        color="nnBaseBlue"
                        icon
                        size="x-small"
                        :title="$t('Comments.reply_edit')"
                        @click.stop="reply._editMode = true"
                      >
                        <v-icon icon="mdi-pencil-outline" />
                      </v-btn>
                      <v-btn
                        variant="outlined"
                        color="nnBaseBlue"
                        icon
                        size="x-small"
                        class="ml-4"
                        :title="$t('Comments.reply_delete')"
                        @click.stop="deleteReply(thread.uid, reply.uid)"
                      >
                        <v-icon icon="mdi-delete-outline" />
                      </v-btn>
                    </div>
                  </v-col>
                </v-row>

                <v-card-text
                  v-show="!reply._editMode"
                  class="pt-0 pr-5 mt-n4 text-nnTrueBlue comment-text reply-text"
                >
                  {{ reply.text }}
                </v-card-text>

                <div v-show="reply._editMode" class="reply-text mt-4">
                  <v-textarea
                    v-model="reply._newText"
                    auto-grow
                    class="mr-5"
                    bg-color="white"
                    :label="$t('Comments.reply_edit')"
                  />
                  <div v-show="!loading" class="mt-n4 pb-4">
                    <v-btn
                      rounded="xl"
                      color="white"
                      @click="cancelReplyEdition(reply)"
                    >
                      {{ $t('_global.cancel') }}
                    </v-btn>
                    <v-btn
                      class="mx-4"
                      rounded="xl"
                      color="secondary"
                      :disabled="reply.text === reply._newText"
                      @click="editReply(thread.uid, reply.uid, reply._newText)"
                    >
                      {{ $t('Comments.reply_edit') }}
                    </v-btn>
                  </div>
                  <div v-show="loading" class="px-6 mb-4">
                    <v-progress-linear indeterminate color="primary" />
                  </div>
                </div>
              </v-list-item>
            </v-list>
            <!-- /Replies -->

            <CommentReplyAdd
              :thread-id="thread.uid"
              :thread-status="thread.status"
              :is-transparent="isTransparent"
              @comment-reply-added="getThreads"
            />
          </v-card>
        </v-list-item>
      </v-list>
      <CommentAdd
        :topic-path="topicPath"
        :is-transparent="isTransparent"
        @comment-thread-added="getThreads"
      />
    </v-sheet>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import comments from '@/api/comments'
import CommentAdd from './CommentAdd.vue'
import CommentReplyAdd from './CommentReplyAdd.vue'
import ConfirmDialog from './ConfirmDialog.vue'
import statuses from '@/constants/statuses'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const authStore = useAuthStore()

const props = defineProps({
  topicPath: {
    type: String,
    required: true,
  },
  isTransparent: {
    type: Boolean,
    default: false,
  },
  dialog: {
    type: Boolean,
    default: false,
  },
})

const userInfo = computed(() => {
  return authStore.userInfo
})

const actions = [
  { newStatus: statuses.COMMENT_STATUS_ACTIVE, color: 'nnSeaBlue300' },
  { newStatus: statuses.COMMENT_STATUS_RESOLVED, color: 'lightSuccess' },
]
const filteringOptions = [
  { value: 'ALL' },
  { value: 'MINE' },
  { value: statuses.COMMENT_STATUS_ACTIVE },
  { value: statuses.COMMENT_STATUS_RESOLVED },
]
const commentTreads = ref([])
const commentTreadsFiltered = ref([])
const filterThreadsBy = ref('ALL')
const loading = ref(false)
const confirm = ref()

watch(
  () => props.topicPath,
  () => {
    getThreads()
  }
)

onMounted(() => {
  getThreads()
})

function getInitials(name) {
  if (!name) return '?'
  const parts = name.trim().split(/\s+/)
  if (parts.length === 1) return parts[0][0].toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

// Generates a deterministic pastel HSL color from a username
function getAvatarColor(name) {
  if (!name) return '#B0BEC5'
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  const h = Math.abs(hash) % 360
  return `hsl(${h}, 45%, 72%)`
}

function isModified(modifiedAt) {
  if (modifiedAt) {
    return ' (edited) '
  }
}

function isAuthor(obj) {
  if (!userInfo.value?.preferred_username) return false
  return userInfo.value.oid === obj.author_id
}

function filterThreads(filter) {
  filterThreadsBy.value = filter
  switch (filter) {
    case statuses.COMMENT_STATUS_RESOLVED:
      commentTreadsFiltered.value = commentTreads.value.filter(
        (thread) => thread.status === statuses.COMMENT_STATUS_RESOLVED
      )
      break
    case statuses.COMMENT_STATUS_ACTIVE:
      commentTreadsFiltered.value = commentTreads.value.filter(
        (thread) => thread.status === statuses.COMMENT_STATUS_ACTIVE
      )
      break
    case 'MINE':
      commentTreadsFiltered.value = commentTreads.value.filter(
        (thread) =>
          thread.author_id === userInfo.value?.oid ||
          thread.replies.some((r) => r.author_id === userInfo.value?.oid)
      )
      break
    default:
      commentTreadsFiltered.value = commentTreads.value
  }
}

function getThreadCountByFilter(filter) {
  switch (filter) {
    case statuses.COMMENT_STATUS_RESOLVED:
      return commentTreads.value.filter(
        (thread) => thread.status === statuses.COMMENT_STATUS_RESOLVED
      ).length
    case statuses.COMMENT_STATUS_ACTIVE:
      return commentTreads.value.filter(
        (thread) => thread.status === statuses.COMMENT_STATUS_ACTIVE
      ).length
    case 'MINE':
      return commentTreads.value.filter(
        (thread) =>
          thread.author_id === userInfo.value?.oid ||
          thread.replies.some((r) => r.author_id === userInfo.value?.oid)
      ).length
    default:
      return commentTreads.value.length
  }
}

function getThreads() {
  if (!props.topicPath) {
    return
  }
  loading.value = true
  comments.getThreads(props.topicPath).then(
    (items) => {
      /*
      _hovered: true indicates that the edit/delete buttons are visible
      _editMode: true indicates that the thread/reply edit form is visible
      _newText: model for the new text of the thread/reply in case of edit
      */
      commentTreads.value = items.map((thread) => {
        thread._newText = thread.text
        thread._hovered = false
        thread._editMode = false
        for (const reply of thread.replies) {
          reply._newText = reply.text
          reply._hovered = false
          reply._editMode = false
        }
        return thread
      })
      filterThreads(filterThreadsBy.value)
      loading.value = false
    },
    () => {
      loading.value = false
    }
  )
}

function editThread(threadId, newText) {
  loading.value = true
  comments.editThread(threadId, { text: newText }).then(
    () => {
      getThreads()
    },
    () => {
      loading.value = false
    }
  )
}

function setThreadStatus(thread, newStatus) {
  if (thread.status === newStatus) {
    return
  }
  loading.value = true
  comments.editThread(thread.uid, { status: newStatus }).then(
    () => {
      getThreads()
    },
    () => {
      loading.value = false
    }
  )
}

function editReply(threadId, replyId, newText) {
  loading.value = true
  comments.editReply(threadId, replyId, { text: newText }).then(
    () => {
      getThreads()
    },
    () => {
      loading.value = false
    }
  )
}

async function deleteThread(threadId) {
  const options = {
    type: 'warning',
    cancelLabel: t('_global.cancel'),
    agreeLabel: t('Comments.comment_delete'),
  }
  if (await confirm.value.open(t('Comments.comment_delete_approve'), options)) {
    loading.value = true
    comments.deleteThread(threadId).then(
      () => {
        getThreads()
      },
      () => {
        loading.value = false
      }
    )
  }
}

async function deleteReply(threadId, replyId) {
  const options = {
    type: 'warning',
    cancelLabel: t('_global.cancel'),
    agreeLabel: t('Comments.reply_delete'),
  }
  if (await confirm.value.open(t('Comments.reply_delete_approve'), options)) {
    loading.value = true
    comments.deleteReply(threadId, replyId).then(
      () => {
        getThreads()
      },
      () => {
        loading.value = false
      }
    )
  }
}

function cancelReplyEdition(reply) {
  reply._editMode = false
  reply._newText = reply.text
}

function cancelThreadEdition(thread) {
  thread._editMode = false
  thread._newText = thread.text
}
</script>

<style scoped>
.comments-wrapper {
  .comment-thread,
  .comment-thread-reply {
    width: 100%;
    display: block;
    margin-left: 2px;
    margin-right: 2px;
    max-width: calc(100% - 4px);
  }

  .comment-thread-reply.v-list-item {
    padding-left: 0px !important;
    padding-right: 0px !important;
    background-color: transparent !important;
  }

  .timestamp {
    font-size: 0.8rem;
    font-weight: 100;
    padding-left: 10px;
  }

  .author-avatar {
    flex-shrink: 0;
  }

  .thread-card {
    border: 1px solid #9e9e9e !important;
  }

  .author-name {
    font-weight: 600;
    font-size: 1rem;
  }

  .comment-text {
    padding-left: 60px;
  }

  .reply-text {
    padding-left: 56px;
  }
}

.avatar-text {
  font-size: 0.8rem;
}

.comments-wrapper.transparent {
  .v-sheet,
  .v-list,
  .v-list-item {
    background-color: transparent;
    padding-left: 0px !important;
    padding-right: 0px !important;
  }
  .v-list-item {
    background-color: white;
  }
}

.no-uppercase {
  text-transform: unset !important;
}
</style>
