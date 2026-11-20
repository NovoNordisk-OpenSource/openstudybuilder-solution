import repository from '../repositoryStandardsImport'

const resource = 'inconsistencies'

export default {
  getResolutionStrategies() {
    return repository.get('resolution-strategies')
  },
  getAll(params) {
    return repository.get(`${resource}`, { params })
  },
  resolve(uid, data) {
    return repository.post(`${resource}/${uid}/resolution`, data)
  },
  deleteResolution(uid) {
    return repository.delete(`${resource}/${uid}/resolution`)
  },
}
