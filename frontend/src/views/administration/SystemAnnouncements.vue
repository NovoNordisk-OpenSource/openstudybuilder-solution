<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('SystemAnnouncementsView.title') }}
    </div>
    <v-form ref="formRef">
      <v-card>
        <v-card-text class="text-body-medium">
          <v-row>
            <v-col md="6" sm="12">
              <v-sheet
                color="nnSeaBlue100"
                rounded="lg"
                class="pa-4"
                border="xs"
              >
                <div class="d-flex align-start justify-start">
                  <div class="mr-6">
                    <v-switch v-model="form.published" hide-details />
                  </div>
                  <div class="text-nnTrueBlue pt-2">
                    <div class="font-weight-bold mb-2 title">
                      {{ $t('SystemAnnouncementsView.show_title') }}
                    </div>
                    <span style="font-size: 14px">{{
                      $t('SystemAnnouncementsView.show_help')
                    }}</span>
                  </div>
                </div>
              </v-sheet>
            </v-col>
          </v-row>
          <v-row class="border-t-thin mt-4 pt-2" no-gutters>
            <v-col md="6" sm="12">
              <div class="page-subtitle">
                {{ $t('SystemAnnouncementsView.announcement_type') }}
              </div>
              <ChoiceField
                v-model="form.notification_type"
                :choices="announcementTypes"
                :inline="false"
              />
            </v-col>
            <v-col md="6" sm="12" class="border-s-thin px-4">
              <div class="page-subtitle">
                {{ $t('SystemAnnouncementsView.announcement_content') }}
              </div>
              <v-text-field
                v-model="form.title"
                :label="$t('SystemAnnouncementsView.announcement_title')"
                :rules="[formRules.required]"
                class="mb-3"
              />
              <v-textarea
                v-model="form.description"
                :label="$t('SystemAnnouncementsView.announcement_description')"
                :rules="[formRules.required]"
              />
              <div class="page-subtitle">
                {{ $t('SystemAnnouncementsView.announcement_schedule') }}
              </div>
              <v-text-field
                v-model="form.started_at"
                :label="$t('SystemAnnouncementsView.start_at')"
                type="datetime-local"
              />
              <v-text-field
                v-model="form.ended_at"
                :label="$t('SystemAnnouncementsView.end_at')"
                type="datetime-local"
              />
            </v-col>
          </v-row>
          <div class="text-headline-small font-weight-bold text-nnTrueBlue">
            {{ $t('SystemAnnouncementsView.preview') }}
          </div>
          <SystemAnnouncement :announcement="form" />
        </v-card-text>
      </v-card>
      <v-app-bar location="bottom" flat class="border-t-thin pa-2">
        <v-spacer />
        <v-btn
          color="secondary"
          rounded
          variant="outlined"
          class="mr-4"
          :loading="loading"
          @click="clearAll()"
        >
          {{ $t('_global.clear_all') }}
        </v-btn>
        <v-btn
          color="secondary"
          variant="flat"
          rounded
          :loading="loading"
          @click="submit"
        >
          {{ $t('_global.save_changes') }}
        </v-btn>
      </v-app-bar>
    </v-form>
  </div>
</template>

<script setup>
import { inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { DateTime } from 'luxon'
import ChoiceField from '@/components/ui/ChoiceField.vue'
import SystemAnnouncement from '@/components/tools/SystemAnnouncement.vue'
import constants from '@/constants/notifications'
import notificationsApi from '@/api/notifications'

const notificationHub = inject('notificationHub')
const formRules = inject('formRules')
const { t } = useI18n()

const form = ref(getInitialFormContent())
const formRef = ref()
const loading = ref(false)

let currentNotification = null

const announcementTypes = [
  {
    value: constants.NOTIF_TYPE_INFO,
    title: t('SystemAnnouncementsView.type_informative'),
    help: t('SystemAnnouncementsView.help_informative'),
  },
  {
    value: constants.NOTIF_TYPE_WARNING,
    title: t('SystemAnnouncementsView.type_warning'),
    help: t('SystemAnnouncementsView.help_warning'),
  },
  {
    value: constants.NOTIF_TYPE_ERROR,
    title: t('SystemAnnouncementsView.type_error'),
    help: t('SystemAnnouncementsView.help_error'),
  },
]

function getInitialFormContent() {
  return {
    notification_type: constants.NOTIF_TYPE_INFO,
    published: true,
  }
}

function clearAll() {
  form.value = getInitialFormContent()
  formRef.value.resetValidation()
}

async function submit() {
  const { valid } = await formRef.value.validate()
  if (!valid) {
    return
  }
  loading.value = true
  const data = { ...form.value }
  if (data.started_at) {
    const startedAtUTC = new Date(data.started_at).toISOString()
    data.started_at = startedAtUTC
  } else if (data.started_at === '') {
    data.started_at = null
  }
  if (data.ended_at) {
    const endedAtUTC = new Date(data.ended_at).toISOString()
    data.ended_at = endedAtUTC
  } else if (data.ended_at === '') {
    data.ended_at = null
  }
  let notification
  try {
    if (currentNotification) {
      await notificationsApi.update(currentNotification.sn, data)
      notification = 'SystemAnnouncementsView.update_success'
    } else {
      await notificationsApi.create(data)
      notification = 'SystemAnnouncementsView.add_success'
    }
  } finally {
    loading.value = false
  }
  notificationHub.add({ msg: t(notification), type: 'success' })
}

notificationsApi.get().then((resp) => {
  if (resp.data.length) {
    currentNotification = resp.data[0]
    form.value = { ...resp.data[0] }
    if (form.value.published_at) {
      form.value.published = true
    }
    if (resp.data[0].started_at) {
      const startedAt = DateTime.fromISO(resp.data[0].started_at)
      form.value.started_at = startedAt.toFormat('yyyy-MM-dd HH:mm')
    }
    if (resp.data[0].ended_at) {
      const endedAt = DateTime.fromISO(resp.data[0].ended_at)
      form.value.ended_at = endedAt.toFormat('yyyy-MM-dd HH:mm')
    }
  }
})
</script>

<style scoped>
.title {
  font-size: 18px;
}
</style>
