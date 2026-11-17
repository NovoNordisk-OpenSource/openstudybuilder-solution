import axios from 'axios'
import { requestInterceptors, responseInterceptors } from '@/api/repository'
import { useGlobalConfig } from '@/main'

const globalConfig = useGlobalConfig()

// This api client should behave in the same way as the client for the main API,
// except that it uses the Standards Import API base url
const requestInterceptorForStandardsImportApiOnFulfilled = async function (
  config
) {
  let interceptor = await requestInterceptors.onFulfilled(config)
  interceptor.baseURL = globalConfig.STANDARDS_IMPORT_API_BASE_URL
  return interceptor
}

const _axios = axios.create()

_axios.interceptors.request.use(
  requestInterceptorForStandardsImportApiOnFulfilled,
  requestInterceptors.onRejected
)

_axios.interceptors.response.use(
  responseInterceptors.onFulfilled,
  responseInterceptors.onRejected
)

export default _axios
