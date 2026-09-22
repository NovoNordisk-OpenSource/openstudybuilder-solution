import repository from './repository'

export default {
  getHeaderData(options, resource) {
    const params = {
      ...options,
    }
    if (params.filters?.['*']) {
      // GET /headers?lite=true endpoints do not support wildcard filtering
      params.lite = false
    } else {
      params.lite = true
    }
    return repository.get(`${resource}/headers`, { params })
  },
}
