<template>
  <v-alert
    :color="getAlertColorFromAnnouncement()"
    :icon="getAlertIconFromAnnouncement()"
    :title="announcement.title"
    :text="announcement.description"
    class="text-nnTrueBlue mx-4 my-2"
    style="z-index: 20"
    closable
    @click:close="appStore.setSystemAnnouncement(null)"
  />
</template>

<script setup>
import { useAppStore } from '@/stores/app'
import constants from '@/constants/notifications'

const props = defineProps({
  announcement: {
    type: Object,
    default: () => {},
  },
})

const appStore = useAppStore()

function getAlertColorFromAnnouncement() {
  switch (props.announcement.notification_type) {
    case constants.NOTIF_TYPE_WARNING:
      return '#FAEECC'
    case constants.NOTIF_TYPE_ERROR:
      return '#FADDD8'
    default:
      return 'nnLightBlue200'
  }
}

function getAlertIconFromAnnouncement() {
  switch (props.announcement.notification_type) {
    case constants.NOTIF_TYPE_WARNING:
      return '$warning'
    case constants.NOTIF_TYPE_ERROR:
      return '$error'
    default:
      return '$info'
  }
}
</script>
