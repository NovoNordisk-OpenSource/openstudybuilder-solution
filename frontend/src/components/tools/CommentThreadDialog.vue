<template>
  <v-card bg-color="dfltBackground" rounded="xl" class="pt-2 pb-8 px-4">
    <v-card-title
      class="d-flex flex-column align-start"
      style="white-space: normal"
    >
      <div class="d-flex align-center" style="width: 100%">
        <span class="dialog-title">{{
          $t('Comments.dialog_title', { item: props.title })
        }}</span>
        <v-spacer />
        <v-btn icon elevation="0" size="small" @click="close">
          <v-icon>mdi-close</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ $t('_global.close') }}
          </v-tooltip>
        </v-btn>
      </div>
      <span class="dialog-info-sub-title">{{
        $t('Comments.dialog_info', { type: props.itemType })
      }}</span>
    </v-card-title>
    <CommentThreadList
      :topic-path="props.topicPath"
      :is-transparent="false"
      :show-divider="false"
      dialog
    />
  </v-card>
</template>

<script setup>
import CommentThreadList from '@/components/tools/CommentThreadList.vue'

const emit = defineEmits(['close'])

const props = defineProps({
  title: {
    type: String,
    default: '',
  },
  topicPath: {
    type: String,
    default: '',
  },
  itemType: {
    type: String,
    default: '',
  },
})

function close() {
  emit('close')
}
</script>
