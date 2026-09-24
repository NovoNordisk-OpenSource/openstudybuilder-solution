<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('GlobalPreferencesView.title') }}
    </div>
    <v-card>
      <v-card-text>
        <v-alert
          color="nnLightBlue200"
          icon="mdi-information-outline"
          class="text-nnTrueBlue mx-4 my-2"
        >
          {{ $t('GlobalPreferencesView.help') }}
        </v-alert>

        <div class="mx-4 my-6">
          <v-form v-model="formValid" @submit.prevent="savePreferences">
            <div v-for="(meta, key) in metadata" :key="key" class="mb-4">
              <PreferenceField
                :preference-key="key"
                :value="preferences[key]"
                :metadata="meta"
                @update:value="(val) => updatePreference(key, val)"
              />
            </div>

            <v-btn
              color="primary"
              :disabled="!formValid || saving"
              :loading="saving"
              type="submit"
              class="mt-4"
            >
              {{ $t('_global.save') }}
            </v-btn>
          </v-form>
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { ref, inject, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import preferencesApi from '@/api/preferences'
import PreferenceField from '@/components/preferences/PreferenceField.vue'
import { useAppStore } from '@/stores/app'

const notificationHub = inject('notificationHub')
const appStore = useAppStore()
const { t } = useI18n()

const preferences = ref({})
const metadata = ref({})
const changedKeys = ref(new Set())
const formValid = ref(true)
const saving = ref(false)

function updatePreference(key, val) {
  preferences.value[key] = val
  changedKeys.value.add(key)
}

async function loadPreferences() {
  try {
    const resp = await preferencesApi.getGlobalPreferences()
    preferences.value = { ...resp.data.preferences }
    metadata.value = { ...resp.data.metadata }
    changedKeys.value = new Set()
  } catch (error) {
    console.error('Failed to load global preferences:', error)
    notificationHub.add({
      msg: t('GlobalPreferencesView.load_error'),
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
    await preferencesApi.updateGlobalPreferences(payload)
    appStore.applyPreferences(preferences.value)
    changedKeys.value = new Set()
    notificationHub.add({
      msg: t('GlobalPreferencesView.update_success'),
      type: 'success',
    })
  } catch (error) {
    console.error('Failed to save global preferences:', error)
    notificationHub.add({
      msg: t('GlobalPreferencesView.save_error'),
      type: 'error',
    })
  } finally {
    saving.value = false
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
