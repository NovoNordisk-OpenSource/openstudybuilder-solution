<template>
  <v-card>
    <v-card-title class="text-headline-small mx-2">
      {{ $t('UserPreferencesView.title') }}
    </v-card-title>
    <v-card-text class="pb-4">
      <v-alert
        color="nnLightBlue200"
        icon="mdi-information-outline"
        class="text-nnTrueBlue mx-2 mb-4"
      >
        {{ $t('UserPreferencesView.help') }}
      </v-alert>

      <div class="mx-2">
        <v-form v-model="formValid" @submit.prevent="savePreferences">
          <div
            v-for="(meta, key) in metadata"
            :key="key"
            class="mb-4 d-flex align-center"
          >
            <div style="flex: 1">
              <PreferenceField
                :preference-key="key"
                :value="preferences[key]"
                :metadata="meta"
                @update:value="(val) => updatePreference(key, val)"
              />
            </div>
            <div class="ml-4 d-flex align-center">
              <v-chip
                v-if="key in overrides"
                color="secondary"
                size="small"
                class="mr-2"
              >
                {{ $t('_global.default') }}:
                {{ formatPreferenceValue(overrides[key], meta) }}
              </v-chip>
              <v-btn
                v-if="key in overrides"
                size="small"
                color="red"
                rounded
                @click="resetPreference(key)"
              >
                {{ $t('UserPreferencesView.reset_to_default') }}
              </v-btn>
            </div>
          </div>

          <v-divider />
          <div class="d-flex mt-4">
            <v-btn variant="outlined" rounded @click="emit('close')">
              {{ $t('_global.cancel') }}
            </v-btn>
            <v-spacer />
            <v-btn
              color="secondary"
              :disabled="!formValid || saving"
              :loading="saving"
              type="submit"
              rounded
            >
              {{ $t('_global.save') }}
            </v-btn>
          </div>
        </v-form>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, inject, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import preferencesApi from '@/api/preferences'
import PreferenceField from '@/components/preferences/PreferenceField.vue'
import { useAppStore } from '@/stores/app'
import { APP_THEMES } from '@/plugins/vuetify'

const notificationHub = inject('notificationHub')
const { t } = useI18n()
const appStore = useAppStore()

const emit = defineEmits(['close'])

const preferences = ref({})
const metadata = ref({})
const overrides = ref({})
const changedKeys = ref(new Set())
const formValid = ref(true)
const saving = ref(false)

function formatPreferenceValue(value, meta) {
  if (meta.type === 'boolean') {
    return value ? t('_global.yes') : t('_global.no')
  }

  return APP_THEMES[value]?.title ?? value
}

function updatePreference(key, val) {
  preferences.value[key] = val
  changedKeys.value.add(key)
}

async function loadPreferences() {
  try {
    const resp = await preferencesApi.getUserPreferences()
    preferences.value = { ...resp.data.preferences }
    metadata.value = { ...resp.data.metadata }
    overrides.value = { ...resp.data.overrides }
    changedKeys.value = new Set()
  } catch (error) {
    console.error('Failed to load user preferences:', error)
    notificationHub.add({
      msg: t('UserPreferencesView.load_error'),
      type: 'error',
    })
  }
}

async function savePreferences() {
  saving.value = true
  try {
    const payload = {}
    for (const key of changedKeys.value) {
      payload[key] = preferences.value[key]
    }
    await preferencesApi.updateUserPreferences(payload)
    await loadPreferences() // Reload to refresh override status
    appStore.applyPreferences(preferences.value)
    notificationHub.add({
      msg: t('UserPreferencesView.update_success'),
      type: 'success',
    })
    emit('close')
  } catch (error) {
    console.error('Failed to save user preferences:', error)
    notificationHub.add({
      msg: t('UserPreferencesView.save_error'),
      type: 'error',
    })
  } finally {
    saving.value = false
  }
}

async function resetPreference(key) {
  try {
    await preferencesApi.resetUserPreferenceKey(key)
    await loadPreferences() // Reload to get default value
    appStore.applyPreferences(preferences.value)
    notificationHub.add({
      msg: t('UserPreferencesView.reset_success'),
      type: 'success',
    })
  } catch (error) {
    console.error(`Failed to reset preference ${key}:`, error)
    notificationHub.add({
      msg: t('UserPreferencesView.reset_error'),
      type: 'error',
    })
  }
}

onMounted(() => {
  loadPreferences()
})
</script>

<style scoped>
.v-form {
  width: auto !important;
}
</style>
