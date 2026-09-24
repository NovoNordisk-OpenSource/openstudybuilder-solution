import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router/index.js'

// Plugins
import appInsights from '@/plugins/appInsights'
import auth from '@/plugins/auth'
import eventBus from '@/plugins/eventBus'
import notificationHub from '@/plugins/notificationHub'
import formRules from '@/plugins/formRules'
import i18n from '@/plugins/i18n'
import vuetify from '@/plugins/vuetify'
import draggable from '@/plugins/draggable'
import pendo from '@/plugins/pendo'

// QuillEditor enhancements
import '@/plugins/quillTableBetter'

// Filters
import filters from '@/filters'

let globalConfig

// NOTE: keep this as an inline import.meta.env check rather than importing
// DEMO_MODE from @/demo/isDemoMode — Vite/Rolldown only constant-folds (and
// DCE-prunes) the `import('@openapi-spec')` branch below when the boolean is a
// literal in this module's scope. Importing the constant defeats that, and the
// branch survives into the production bundle. The build still succeeds (the
// vite.config.mjs plugin resolves @openapi-spec to an empty stub outside demo
// mode), so nothing tells you — you just ship a dead dynamic import.
// See also the same guard in api/repository.js, where the cost is far larger.
const DEMO_MODE = import.meta.env.VITE_ENABLE_DEMO_BACKEND === 'true'

const DEMO_CONFIG = {
  APP_ENV: 'demo',
  API_BASE_URL: '',
  EXTENSIONS_API_BASE_URL: '',
  DOC_BASE_URL: '',
  NEODASH_BASE_URL: '',
  NEED_HELP_URL: '',
  ENABLE_SCREEN_RECORDER: '0',
  APPINSIGHTS_CONNSTRING: '',
  APPINSIGHTS_DISABLE: '1',
  OAUTH_API_APP_ID: 'demo',
  OAUTH_ENABLED: '1',
  OAUTH_RBAC_ENABLED: '1',
  OAUTH_METADATA_URL: 'https://demo.invalid/.well-known/openid-configuration',
  OAUTH_UI_APP_ID: 'demo',
  PENDO_ENABLED: '0',
  BUILD_NUMBER: 'demo',
  BUILD_BRANCH: 'demo',
}

/*
 * Convert some string values to more appropriate ones
 */
function prepareConfig(config) {
  const trueValues = ['1', 't', 'true', 'on', 'y', 'yes']
  for (const field of [
    'OAUTH_ENABLED',
    'OAUTH_RBAC_ENABLED',
    'APPINSIGHTS_DISABLE',
    'ENABLE_SCREEN_RECORDER',
    'PENDO_ENABLED',
  ]) {
    if (field in config && typeof config[field] === 'string') {
      const currentValue = config[field].trim().toLowerCase()
      config[field] = trueValues.includes(currentValue)
    }
  }
}

const configPromise = DEMO_MODE
  ? import('@openapi-spec').then(({ default: spec }) => ({
      ...DEMO_CONFIG,
      FRONTEND_BUILD_NUMBER:
        typeof __DEMO_GIT_COMMIT__ === 'string' && __DEMO_GIT_COMMIT__
          ? `demo (${__DEMO_GIT_COMMIT__})`
          : 'demo',
      DOCUMENTATION_PORTAL_BUILD_NUMBER: 'demo',
      DATA_IMPORT_BUILD_NUMBER: 'mocked — no database',
      STANDARDS_IMPORT_BUILD_NUMBER: 'mocked — no database',
      NEO4J_MDR_BUILD_NUMBER: 'mocked — no database',
      STUDYBUILDER_EXPORT_BUILD_NUMBER: 'mocked — no database',
      API_BUILD_NUMBER: spec?.info?.version
        ? `mock backend based on OpenAPI specification ${spec.info.version}`
        : 'mock backend',
    }))
  : fetch('/config.json').then((resp) => resp.json())

const demoReady = DEMO_MODE
  ? import('@/api/repository').then(({ demoBackendReady }) => demoBackendReady)
  : Promise.resolve()

Promise.all([configPromise, demoReady]).then(([config]) => {
  const app = createApp(App)
  prepareConfig(config)
  globalConfig = config
  app.config.globalProperties.$config = config
  app.config.globalProperties.$filters = filters
  app.config.globalProperties.$globals = {
    historyDialogMaxWidth: '1600px',
    historyDialogFullscreen: true,
  }
  app.provide('$config', config)
  app.use(createPinia())
  app.use(router)
  app.use(auth, { config })
  if (!DEMO_MODE) {
    app.use(appInsights, {
      config,
      router,
      trackAppErrors: true,
      cloudRole: 'frontend',
      cloudRoleInstance: 'vue-app',
    })
  }
  app.use(eventBus)
  app.use(notificationHub)
  app.use(formRules)
  app.use(i18n).provide('$i18n', i18n)
  app.use(vuetify)
  app.use(draggable)
  if (!DEMO_MODE) {
    app.use(pendo, { config })
  }
  app.mount('#app')
})

export const useGlobalConfig = () => globalConfig
