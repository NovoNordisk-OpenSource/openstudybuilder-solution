import repository from '../repositoryStandardsImport'

const resource = 'packages/files'

export default {
  getAll(params) {
    return repository.get(`${resource}`, { params })
  },
  uploadFile(fileContent) {
    return repository.post(`${resource}`, fileContent, {
      headers: { 'Content-Type': 'application/json' },
    })
  },
  discoverNewReleases(apiKey) {
    return repository.post('packages/discover', { api_key: apiKey })
  },
}
