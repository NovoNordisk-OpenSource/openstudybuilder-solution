/**
 * In-browser auth stub for demo mode.
 *
 * Mirrors the shape of the real interface in `src/plugins/auth.js` so the rest
 * of the app (router guards, accessGuard composable, TopBar, authStore) doesn't
 * know it's looking at fake credentials. State persists in localStorage so the
 * demo session survives reloads.
 *
 * Auto-login: set VITE_DEMO_AUTH_ROLES (comma-separated, or `*` for all) and
 * optionally VITE_DEMO_AUTH_NAME to skip the picker. Useful for E2E tests and
 * for developers who want a fixed identity every reload.
 */

import roles from '@/constants/roles'
import { DEMO_MODE } from '@/demo/isDemoMode'

const STORAGE_KEY = 'studybuilder.demo.auth.v1'

const ALL_ROLES = [
  roles.LIBRARY_READ,
  roles.LIBRARY_WRITE,
  roles.STUDY_READ,
  roles.STUDY_WRITE,
  roles.ADMIN_READ,
  roles.ADMIN_WRITE,
]

function applyAutoLoginFromEnv() {
  if (!DEMO_MODE) return
  const rolesEnv = import.meta.env.VITE_DEMO_AUTH_ROLES
  if (typeof rolesEnv !== 'string' || rolesEnv.trim() === '') return
  const name = import.meta.env.VITE_DEMO_AUTH_NAME?.trim() || 'Demo User'
  const trimmed = rolesEnv.trim()
  const userRoles =
    trimmed === '*' || trimmed.toLowerCase() === 'all'
      ? [...ALL_ROLES]
      : trimmed
          .split(',')
          .map((r) => r.trim())
          .filter(Boolean)
  if (userRoles.length === 0) return
  saveDemoUser({ name, roles: userRoles })
}

export function loadDemoUser() {
  try {
    const raw = globalThis.localStorage?.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (!parsed || typeof parsed !== 'object') return null
    return parsed
  } catch {
    return null
  }
}

export function saveDemoUser(user) {
  try {
    globalThis.localStorage?.setItem(STORAGE_KEY, JSON.stringify(user))
  } catch {
    /* quota — ignore */
  }
}

export function clearDemoUser() {
  try {
    globalThis.localStorage?.removeItem(STORAGE_KEY)
  } catch {
    /* ignore */
  }
}

export const demoAuthInterface = {
  validateAccess(to) {
    // Match the shape of the real auth interface in src/plugins/auth.js:
    // it ignores `next` and triggers an external redirect via
    // manager.signinRedirect(). The router guard at src/router/index.js:1283
    // calls validateAccess and then unconditionally falls through to its own
    // next() at line 1300 — calling next() from here too would invoke it
    // twice and abort navigation. location.assign() does the equivalent of
    // a full-page reload to /login, which is what the real OAuth flow does
    // to the authorization server anyway.
    if (loadDemoUser()) return
    if (to.name === 'Login') return
    if (to.name) {
      sessionStorage.setItem('next', to.name)
      sessionStorage.setItem('nextParams', JSON.stringify(to.params ?? {}))
    }
    globalThis.location?.assign('/login')
  },
  oauthLoginCallback() {
    return Promise.resolve()
  },
  clear() {
    /* no stale state to clear in demo mode */
  },
  getAccessToken() {
    return Promise.resolve(loadDemoUser() ? 'demo-token' : null)
  },
  getUserInfo() {
    return Promise.resolve(loadDemoUser())
  },
  oauthLogout() {
    clearDemoUser()
    globalThis.location?.assign('/')
    return Promise.resolve()
  },
}

applyAutoLoginFromEnv()
