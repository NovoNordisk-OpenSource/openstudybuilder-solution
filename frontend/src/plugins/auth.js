import { eventBusEmit } from './eventBus'
import { UserManager } from 'oidc-client-ts'
import roles from '@/constants/roles'
import { Buffer } from 'buffer'
import { demoAuthInterface } from '@/demo/demoAuth'
import { DEMO_MODE } from '@/demo/isDemoMode'

let manager = null

const authInterface = {
  validateAccess: function (to) {
    manager.getUser().then((user) => {
      if (!user || user.expired) {
        if (to.name !== 'Login') {
          sessionStorage.setItem('next', to.name)
          sessionStorage.setItem('nextParams', JSON.stringify(to.params))
        }
        manager.signinRedirect()
      }
    })
  },
  oauthLoginCallback: function () {
    return manager.signinRedirectCallback().then(() => {
      eventBusEmit('userSignedIn')
    })
  },
  clear: function () {
    manager.clearStaleState()
  },
  getAccessToken: function () {
    return manager.getUser().then((user) => {
      if (!user) {
        return null
      }
      return user.access_token
    })
  },
  getUserInfo: function () {
    return manager.getUser().then((user) => {
      if (!user || user.expired) {
        return null
      }
      return JSON.parse(
        Buffer.from(user.access_token.split('.')[1], 'base64').toString()
      )
    })
  },
  oauthLogout: async function () {
    return manager.signoutRedirect()
  },
}

const activeInterface = DEMO_MODE ? demoAuthInterface : authInterface

export default {
  install: (app, options) => {
    if (!DEMO_MODE) {
      manager = new UserManager({
        metadataUrl: options.config.OAUTH_METADATA_URL,
        authority: 'studybuilder-frontend',
        client_id: options.config.OAUTH_UI_APP_ID,
        redirect_uri: location.origin + '/oauth-callback',
        response_type: 'code',
        response_mode: 'fragment',
        post_logout_redirect_uri: location.origin,
        scope: `openid profile email offline_access api://${options.config.OAUTH_API_APP_ID}/API.call`,
      })
    }
    app.config.globalProperties.$auth = activeInterface
    app.config.globalProperties.$roles = roles
    app.provide('roles', roles)
  },
}

export const auth = activeInterface
