import Vue from 'vue'
import { config } from '@vue/test-utils'
import Vuetify from 'vuetify'
import registerRequireContextHook from 'babel-plugin-require-context-hook/register'
import fetchMock from 'jest-fetch-mock'

config.mocks.$t = (key) => key
Vue.use(Vuetify)
Vue.config.productionTip = false
registerRequireContextHook()

process.env.BASE_URL = 'http://localhost:8080/'
fetchMock.mockResponse(
  JSON.stringify({
    API_BASE_URL: 'http://127.0.0.1:8000',
    DOC_BASE_URL: 'http://127.0.0.1:8081',
    STUDYBUILDER_VERSION: 'v0.1',
    FRONTEND_BUILD_NUMBER: 'dev',
    API_BUILD_NUMBER: 'dev',
    DOCUMENTATION_PORTAL_BUILD_NUMBER: 'dev',
    OAUTH_ENABLED: 'false',
    OAUTH_RBAC_ENABLED: 'false',
    OIDC_METADATA_URL: 'http://test.test/.well-known/openid-configuration',
    OAUTH_API_APP_ID: 'test-api-app-id',
    OAUTH_UI_APP_ID: 'test-ui-app-id',
  })
)
fetchMock.enableMocks()
