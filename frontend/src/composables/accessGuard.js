import { inject } from 'vue'
import { useAuthStore } from '@/stores/auth'

export function useAccessGuard() {
  const authStore = useAuthStore()
  const $config = inject('$config')

  function checkPermission(permission) {
    if ($config.OAUTH_ENABLED && $config.OAUTH_RBAC_ENABLED) {
      // userInfo is normally populated by authStore.initialize() in the
      // router guard before any route renders; guard the access anyway
      // so a transient null (mid-navigation, expired token about to
      // redirect) fails closed instead of throwing.
      return authStore.userInfo?.roles?.includes(permission) ?? false
    }
    return true
  }

  return {
    userInfo: authStore.userInfo,
    checkPermission,
  }
}
