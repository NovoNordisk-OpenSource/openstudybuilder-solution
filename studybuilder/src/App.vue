<template>
  <v-app full-height>
    <TopBar
      :hide-app-bar-nav-icon="layoutTemplate === 'empty'"
      @back-to-root="navigateToRoot"
    />

    <template v-if="layoutTemplate === 'empty'">
      <v-main class="bg-primary white-text">
        <SystemAnnouncement
          v-if="systemAnnouncement"
          :announcement="systemAnnouncement"
        />
        <router-view />
      </v-main>
    </template>

    <template v-else-if="layoutTemplate === 'error'">
      <v-main class="">
        <router-view />
      </v-main>
    </template>

    <template v-else>
      <SideBar />

      <v-main class="bg-dfltBackground">
        <v-container class="" fluid>
          <SystemAnnouncement
            v-if="systemAnnouncement"
            :announcement="systemAnnouncement"
          />
          <v-breadcrumbs :items="breadcrumbs" class="mb-2" />
          <router-view />
        </v-container>
      </v-main>
    </template>

    <v-snackbar
      v-model="snackbar"
      :color="notificationColor"
      :timeout="notificationTimeout"
      :min-width="550"
      location="top"
    >
      <v-row>
        <v-col cols="1">
          <v-icon
            color="white"
            class="mr-2"
            size="large"
            :icon="notificationIcon"
          />
        </v-col>
        <v-col cols="10">
          <div class="text-body-1 text-white mt-1">
            <div v-if="notificationTitle" class="font-weight-bold mb-4">
              {{ notificationTitle }}
            </div>
            <div
              v-for="(line, index) in notification"
              :key="`notif-line-${index}`"
              class="mb-2"
            >
              {{ line }}
            </div>
            <template v-if="correlationId">
              <p />
              <p class="text-body-2">
                <span class="font-weight-bold">{{
                  $t('_global.correlation_id')
                }}</span
                ><br />
                {{ correlationId }}
              </p>
            </template>
          </div>
        </v-col>
        <v-col cols="1">
          <v-btn
            color="white"
            size="small"
            icon="mdi-close"
            variant="text"
            @click="snackbar = false"
          />
        </v-col>
      </v-row>
    </v-snackbar>
  </v-app>
</template>
<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useTheme } from 'vuetify'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import SideBar from '@/components/layout/SideBar.vue'
import TopBar from '@/components/layout/TopBar.vue'
import SystemAnnouncement from '@/components/tools/SystemAnnouncement.vue'
import { eventBus } from '@/plugins/eventBus'
import notifications from '@/api/notifications'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const theme = useTheme()

const appStore = useAppStore()
const authStore = useAuthStore()

const breadcrumbs = computed(() => appStore.breadcrumbs)
const userData = computed(() => appStore.userData)
const userInfo = computed(() => authStore.userInfo)
const displayWelcomeMsg = computed(() => authStore.displayWelcomeMsg)
const systemAnnouncement = computed(() => appStore.systemAnnouncement)

const snackbar = ref(false)
const correlationId = ref(null)
const notification = ref([])
const notificationTitle = ref(null)
const notificationColor = ref(null)
const notificationTimeout = ref(-1)

const defaultNotificationTimeout = 3000

const layoutTemplate = computed(() => {
  return route.meta.layoutTemplate || '2cols'
})

const notificationIcon = computed(() => {
  if (
    notificationColor.value === 'green' ||
    notificationColor.value === 'success'
  ) {
    return 'mdi-check-circle-outline'
  }
  if (notificationColor.value === 'info') {
    return 'mdi-information-outline'
  }
  if (notificationColor.value === 'warning') {
    return 'mdi-alert-outline'
  }
  if (
    notificationColor.value === 'error' ||
    notificationColor.value === '#E6553F'
  ) {
    return 'mdi-alert-octagon-outline'
  }
  return ''
})

watch(userInfo, (newValue) => {
  if (displayWelcomeMsg.value) {
    showNotification({
      msg: t('_global.auth_success', { username: newValue.name }),
    })
    authStore.setWelcomeMsgFlag(false)
  }
})

watch(
  () => eventBus.value.get('notification'),
  (args) => showNotification(...args)
)
watch(
  () => eventBus.value.get('userSignedIn'),
  () => {
    authStore.initialize()
    authStore.setWelcomeMsgFlag(true)
  }
)
watch(
  () => eventBus.value.get('backToRoot'),
  () => {
    appStore.resetBreadcrumbs()
    appStore.setSection('')
    router.push('/')
  }
)

onMounted(async () => {
  appStore.initialize()
  theme.global.name.value = userData.value.darkTheme
    ? 'dark'
    : 'NNCustomLightTheme'
  authStore.initialize()
  const resp = await notifications.getActive()
  if (resp.data.length) {
    appStore.setSystemAnnouncement(resp.data[0])
  }
})

function navigateToRoot() {
  appStore.resetBreadcrumbs()
  appStore.setSection('')
  router.push('/')
}
function showNotification(options) {
  notification.value = options.msg
  if (typeof notification.value === 'string') {
    notification.value = [notification.value]
  }
  notificationTitle.value = options.title
  if (options.type) {
    notificationColor.value =
      options.type === 'error' ? '#E6553F' : options.type
  } else {
    notificationColor.value = 'green'
  }
  notificationTimeout.value = options.timeout
    ? options.timeout
    : defaultNotificationTimeout
  correlationId.value = options.correlationId
  snackbar.value = true
  if (options.type === 'error') {
    console.log(options.msg)
    if (options.correlationId) {
      console.log(`Correlation ID: ${options.correlationId}`)
    }
  }
}
</script>

<style lang="scss" scoped>
.v-breadcrumbs {
  padding-top: 5px;
  padding-bottom: 5px;
  padding-left: 12px;
}
.v-container {
  position: relative;
  height: 100%;
}
</style>
