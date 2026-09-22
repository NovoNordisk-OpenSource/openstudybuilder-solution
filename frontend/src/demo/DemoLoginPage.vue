<template>
  <div class="demo-login-overlay">
    <div class="demo-login-card">
      <div class="demo-login-header">
        <div class="demo-login-title">Demo sign-in</div>
        <div class="demo-login-subtitle">
          This is an OpenStudyBuilder demo running entirely in your browser — no
          real authentication or backend. Pick a display name and the access
          groups you want to simulate, and you'll be signed in for this session.
        </div>
      </div>

      <div class="demo-login-body">
        <label class="demo-login-label" for="demo-displayName">
          Display name
        </label>
        <input
          id="demo-displayName"
          v-model="displayName"
          type="text"
          class="demo-login-input"
          autocomplete="off"
        />

        <div class="demo-login-section-label">Presets</div>
        <div class="demo-login-presets">
          <button
            v-for="preset in presets"
            :key="preset.label"
            type="button"
            class="demo-login-preset"
            @click="applyPreset(preset.roles)"
          >
            {{ preset.label }}
          </button>
        </div>

        <div class="demo-login-section-label">Access groups</div>
        <div class="demo-login-roles">
          <label v-for="role in allRoles" :key="role" class="demo-login-role">
            <input v-model="selectedRoles" type="checkbox" :value="role" />
            <span>{{ role }}</span>
          </label>
        </div>

        <div class="demo-login-hint">
          Stored locally — no real authentication happens.
        </div>
      </div>

      <div class="demo-login-actions">
        <button
          type="button"
          class="demo-login-submit"
          :disabled="!displayName.trim()"
          @click="signIn"
        >
          Sign in
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { eventBusEmit } from '@/plugins/eventBus'
import roles from '@/constants/roles'
import { saveDemoUser } from '@/demo/demoAuth'

const router = useRouter()
const authStore = useAuthStore()

const allRoles = [
  roles.LIBRARY_READ,
  roles.LIBRARY_WRITE,
  roles.STUDY_READ,
  roles.STUDY_WRITE,
  roles.ADMIN_READ,
  roles.ADMIN_WRITE,
]

const presets = [
  {
    label: 'Read-only',
    roles: [roles.LIBRARY_READ, roles.STUDY_READ, roles.ADMIN_READ],
  },
  {
    label: 'Library editor',
    roles: [
      roles.LIBRARY_READ,
      roles.LIBRARY_WRITE,
      roles.STUDY_READ,
      roles.ADMIN_READ,
    ],
  },
  {
    label: 'Study editor',
    roles: [
      roles.STUDY_READ,
      roles.STUDY_WRITE,
      roles.LIBRARY_READ,
      roles.LIBRARY_WRITE,
      roles.ADMIN_READ,
    ],
  },
  { label: 'Full access', roles: [...allRoles] },
]

const displayName = ref('Demo User')
const selectedRoles = ref([...allRoles])

function applyPreset(rolesList) {
  selectedRoles.value = [...rolesList]
}

async function signIn() {
  saveDemoUser({
    name: displayName.value.trim(),
    roles: [...selectedRoles.value],
  })
  await authStore.initialize()
  eventBusEmit('userSignedIn')

  const next = sessionStorage.getItem('next')
  if (next) {
    const params = JSON.parse(sessionStorage.getItem('nextParams') ?? '{}')
    sessionStorage.removeItem('next')
    sessionStorage.removeItem('nextParams')
    router.push({ name: next, params })
  } else {
    router.push('/')
  }
}
</script>

<style scoped>
.demo-login-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  background: #f3f2f1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  font-family:
    'Segoe UI',
    system-ui,
    -apple-system,
    sans-serif;
  color: #1f1f1f;
}

.demo-login-card {
  width: 100%;
  max-width: 440px;
  background: #ffffff;
  box-shadow:
    0 2px 6px rgba(0, 0, 0, 0.13),
    0 0.5px 1.8px rgba(0, 0, 0, 0.1);
  padding: 44px 44px 32px;
}

.demo-login-header {
  margin-bottom: 24px;
}

.demo-login-title {
  font-size: 24px;
  font-weight: 600;
  line-height: 1.2;
}

.demo-login-subtitle {
  font-size: 15px;
  color: #605e5c;
  margin-top: 6px;
}

.demo-login-body {
  display: flex;
  flex-direction: column;
}

.demo-login-label {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 6px;
}

.demo-login-input {
  height: 32px;
  padding: 0 8px;
  border: 1px solid #605e5c;
  border-radius: 0;
  font-size: 14px;
  outline: none;
  background: #ffffff;
}
.demo-login-input:focus {
  border-color: #0067b8;
  box-shadow: inset 0 0 0 1px #0067b8;
}

.demo-login-section-label {
  font-size: 13px;
  font-weight: 600;
  color: #323130;
  margin-top: 18px;
  margin-bottom: 8px;
}

.demo-login-presets {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.demo-login-preset {
  background: #f3f2f1;
  border: 1px solid #d2d0ce;
  padding: 5px 12px;
  font-size: 13px;
  cursor: pointer;
  color: #1f1f1f;
}
.demo-login-preset:hover {
  background: #edebe9;
}

.demo-login-roles {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 12px;
}

.demo-login-role {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  cursor: pointer;
}
.demo-login-role input {
  margin: 0;
}

.demo-login-hint {
  font-size: 12px;
  color: #605e5c;
  margin-top: 18px;
}

.demo-login-actions {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}

.demo-login-submit {
  background: #0067b8;
  color: #ffffff;
  border: none;
  padding: 8px 28px;
  font-size: 14px;
  cursor: pointer;
  min-width: 108px;
}
.demo-login-submit:hover:not(:disabled) {
  background: #005ba1;
}
.demo-login-submit:disabled {
  background: #c8c6c4;
  cursor: not-allowed;
}
</style>
