import repository from './repository'

const resource = 'feature-flags'

export default {
  get(params) {
    return repository.get(`${resource}`, { params })
  },
  create(payload) {
    return repository.post(`${resource}`, payload)
  },
  update(featureFlagId, payload) {
    return repository.patch(`${resource}/${featureFlagId}`, payload)
  },
  getVersions(uid) {
    return repository.get(`${resource}/${uid}/versions`)
  },
  inactivate(uid) {
    return repository.delete(`${resource}/${uid}/activations`)
  },
  reactivate(uid) {
    return repository.post(`${resource}/${uid}/activations`)
  },
}
