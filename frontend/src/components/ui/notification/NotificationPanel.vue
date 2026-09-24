<template>
  <v-expand-both-transition>
    <v-btn
      v-if="
        notificationHub.queue.value.length > 0 && !isNotificationPanelExpanded
      "
      color="white"
      density="compact"
      :title="t('NotificationPanel.show_panel')"
      icon
      @click="toggleNotificationPanel"
    >
      <v-badge
        :content="notificationHub.queue.value.length"
        location="top left"
        color="secondary"
      >
        <v-icon icon="mdi-bell"></v-icon>
      </v-badge>
    </v-btn>
    <v-card
      v-if="notificationHub.queue.value.length > 0"
      class="position-fixed d-flex flex-column rounded-t-0"
      style="z-index: 9999; top: 70px"
      location="top right"
      width="550"
      max-height="300"
      elevation="1"
    >
      <v-card-title class="d-flex align-center pa-1 px-4">
        <v-badge
          :content="notificationHub.queue.value.length"
          location="top right"
          offset-y="2"
          offset-x="-15"
          color="black"
        >
          <span class="font-weight-bold">{{
            t('NotificationPanel.title')
          }}</span>
        </v-badge>

        <v-spacer />

        <v-tooltip
          v-if="notificationHub.queue.value.some((n) => n.error)"
          location="start"
          style="z-index: 99999 !important"
        >
          <template #activator="{ props: tooltipProps }">
            <v-btn
              v-bind="tooltipProps"
              variant="text"
              size="small"
              elevation="0"
              density="compact"
              icon
              :readonly="isScreenshotting"
              @click.stop="
                () => {
                  copyScreenshot()
                  tooltipProps.onMouseleave()
                }
              "
            >
              <v-fab-transition>
                <v-icon v-if="!isScreenshotting"
                  >mdi-fit-to-screen-outline</v-icon
                >
                <v-icon v-else>mdi-check</v-icon>
              </v-fab-transition>
            </v-btn>
          </template>

          <template #default>
            <div v-html="t('NotificationPanel.copy_screenshot')"></div>
          </template>
        </v-tooltip>

        <v-tooltip
          v-if="notificationHub.queue.value.filter((n) => n.error).length > 1"
          location="start"
          style="z-index: 99999 !important"
        >
          <template #activator="{ props: tooltipProps }">
            <v-btn
              v-bind="tooltipProps"
              variant="text"
              size="small"
              elevation="0"
              density="compact"
              icon
              :readonly="isCopying"
              @click.stop="
                () => {
                  copyErrors()
                  tooltipProps.onMouseleave()
                }
              "
            >
              <v-fab-transition>
                <v-icon v-if="!isCopying">mdi-content-copy</v-icon>
                <v-icon v-else>mdi-check</v-icon>
              </v-fab-transition>
            </v-btn>
          </template>

          <template #default>
            <div v-html="t('NotificationPanel.copy_all_error')"></div>
          </template>
        </v-tooltip>

        <v-tooltip
          location="start"
          :text="t('NotificationPanel.hide_panel')"
          style="z-index: 99999 !important"
        >
          <template #activator="{ props: tooltipProps }">
            <v-btn
              v-bind="tooltipProps"
              size="small"
              density="comfortable"
              icon="mdi-chevron-up"
              elevation="0"
              @click="toggleNotificationPanel"
            />
          </template>
        </v-tooltip>
      </v-card-title>

      <v-card-text class="pa-0" style="overflow-y: auto">
        <v-slide-x-reverse-transition group>
          <NotificationAlert
            v-for="[idx, notification] in notificationHub.queue.value.entries()"
            :key="`${notification.time}-${notification.msg}`"
            :notification="notification"
            :class="{ 'mb-2': idx != notificationHub.queue.value.length - 1 }"
          />
        </v-slide-x-reverse-transition>
      </v-card-text>

      <v-card-actions class="d-flex justify-center pa-0" style="min-height: 0">
        <v-btn
          class="font-weight-bold"
          elevation="0"
          :title="t('_global.clear_all')"
          rounded="0"
          block
          :text="t('_global.clear_all')"
          @click="notificationHub.clear"
        />
      </v-card-actions>
    </v-card>
  </v-expand-both-transition>
</template>

<script setup>
import { ref, inject, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import html2canvas from 'html2canvas'
import NotificationAlert from '@/components/ui/notification/NotificationAlert.vue'

const { t } = useI18n()

const notificationHub = inject('notificationHub')

const isNotificationPanelExpanded = ref(true)
const isCopying = ref(false)
const isScreenshotting = ref(false)

watch(notificationHub.queue, (queue) => {
  if (queue.length > 0) {
    isNotificationPanelExpanded.value = true
  } else {
    isNotificationPanelExpanded.value = false
  }
})

function toggleNotificationPanel() {
  isNotificationPanelExpanded.value = !isNotificationPanelExpanded.value
}

async function copyErrors() {
  isCopying.value = true
  try {
    const errors = new Set()
    for (const n of notificationHub.queue.value) {
      if (
        n.error &&
        !Array.from(errors).some(
          (e) => JSON.stringify(e) === JSON.stringify(n.error)
        )
      ) {
        errors.add(n.error)
      }
    }

    navigator.clipboard.writeText(JSON.stringify(Array.from(errors), null, 2))
  } catch (e) {
    console.error('Failed to copy all error details:', e)
  } finally {
    setTimeout(() => {
      isCopying.value = false
    }, 1500)
  }
}

async function copyScreenshot() {
  isScreenshotting.value = true
  try {
    const canvas = await html2canvas(document.body)
    canvas.toBlob(async (blob) => {
      if (blob) {
        await navigator.clipboard.write([
          new ClipboardItem({ 'image/png': blob }),
        ])
      }
    }, 'image/png')
  } catch (e) {
    console.error('Failed to take a screenshot:', e)
  } finally {
    setTimeout(() => {
      isScreenshotting.value = false
    }, 1500)
  }
}
</script>
