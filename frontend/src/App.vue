<template>
  <v-app full-height>
    <div
      class="position-absolute d-flex flex-column ga-2"
      style="z-index: 9999; top: 5px; right: 5px"
    >
      <ScreenRecorder v-if="ENABLE_SCREEN_RECORDER === true" />
      <NotificationPanel />
    </div>

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
  </v-app>
</template>
<script setup>
import { computed, inject, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import SideBar from '@/components/layout/SideBar.vue'
import TopBar from '@/components/layout/TopBar.vue'
import SystemAnnouncement from '@/components/tools/SystemAnnouncement.vue'
import { eventBus } from '@/plugins/eventBus'
import notifications from '@/api/notifications'
import NotificationPanel from './components/ui/notification/NotificationPanel.vue'
import ScreenRecorder from './components/ui/ScreenRecorder.vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const appStore = useAppStore()
const authStore = useAuthStore()
const notificationHub = inject('notificationHub')
const $config = inject('$config')
const { ENABLE_SCREEN_RECORDER } = $config

const breadcrumbs = computed(() => appStore.breadcrumbs)
const userInfo = computed(() => authStore.userInfo)
const displayWelcomeMsg = computed(() => authStore.displayWelcomeMsg)
const systemAnnouncement = computed(() => appStore.systemAnnouncement)

const layoutTemplate = computed(() => {
  return route.meta.layoutTemplate || '2cols'
})

watch(userInfo, (newValue) => {
  if (newValue?.preferred_username && window.pendo) {
    window.pendo.identify({
      visitor: { id: newValue.preferred_username },
    })
  }
  if (displayWelcomeMsg.value) {
    notificationHub.add({
      msg: t('_global.auth_success', { username: newValue.name }),
    })
    authStore.setWelcomeMsgFlag(false)
  }
})

watch(
  () => eventBus.value.get('userSignedIn'),
  () => {
    authStore.initialize()
    authStore.setWelcomeMsgFlag(true)
  }
)
onMounted(async () => {
  await appStore.initialize()
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
</script>

<style lang="scss" scoped>
.v-breadcrumbs {
  margin-top: 0;
  padding-top: 5px;
  padding-bottom: 5px;
  padding-left: 12px;
}
.v-container {
  position: relative;
  height: 100%;
}
</style>
