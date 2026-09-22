<template>
  <v-alert :type="props.notification.type" rounded="0" border="start">
    <template #text>
      <p
        class="font-weight-bold text-white"
        :class="{ 'mb-4': props.notification?.error?.correlation_id }"
        v-html="props.notification.msg"
      ></p>
      <p
        v-if="props.notification?.error?.correlation_id"
        class="text-body-medium"
      >
        <span class="font-weight-bold">{{ $t('_global.correlation_id') }}</span>
        <br />
        {{ props.notification?.error?.correlation_id }}
      </p>
    </template>

    <template #close>
      <v-tooltip
        v-if="props.notification?.error"
        location="top left"
        style="z-index: 99999 !important"
      >
        <template #activator="{ props: tooltipProps }">
          <v-btn
            v-bind="tooltipProps"
            color="white"
            variant="text"
            size="small"
            elevation="0"
            density="compact"
            icon
            :readonly="isCopying"
            @click.stop="
              () => {
                tooltipProps.onMouseleave()
                copyError()
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
          <div v-html="t('NotificationPanel.copy_error')"></div>
        </template>
      </v-tooltip>

      <v-tooltip
        location="top left"
        :text="t('NotificationPanel.remove_notification')"
        style="z-index: 99999 !important"
      >
        <template #activator="{ props: tooltipProps }">
          <v-progress-circular
            v-if="props.notification.timeout > 0"
            v-bind="tooltipProps"
            :model-value="progress"
            width="3"
          >
            <v-btn
              color="white"
              size="small"
              density="compact"
              icon="mdi-close"
              @click="notificationHub.remove(props.notification)"
            />
          </v-progress-circular>
          <v-btn
            v-else
            v-bind="tooltipProps"
            color="white"
            size="small"
            density="compact"
            icon="mdi-close"
            @click.stop="notificationHub.remove(props.notification)"
          />
        </template>
      </v-tooltip>
    </template>
  </v-alert>
</template>

<script setup>
import { inject, onMounted, ref, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const notificationHub = inject('notificationHub')

const props = defineProps({
  notification: {
    type: Object,
    required: true,
  },
})

const progress = ref(0)
const isCopying = ref(false)

let intervalId = null

async function copyError() {
  isCopying.value = true
  try {
    navigator.clipboard.writeText(
      JSON.stringify(props.notification?.error, null, 2)
    )
  } catch (e) {
    console.error('Failed to copy error details:', e)
  } finally {
    setTimeout(() => {
      isCopying.value = false
    }, 1500)
  }
}

onMounted(() => {
  if (props.notification.timeout > 0) {
    intervalId = setInterval(() => {
      const elapsed = Date.now() - props.notification.time
      progress.value = Math.min(
        (elapsed / props.notification.timeout) * 100,
        100
      )
    }, 100)
  }
})

onBeforeUnmount(() => {
  if (intervalId) clearInterval(intervalId)
})
</script>
