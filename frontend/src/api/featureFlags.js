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
  getVersions(uid, config) {
    return repository.get(`${resource}/${uid}/versions`, config)
  },
  getAllVersions(params) {
    return repository.get(`${resource}/audit-trail`, { params })
  },
  inactivate(uid) {
    return repository.delete(`${resource}/${uid}/activations`)
  },
  reactivate(uid) {
    return repository.post(`${resource}/${uid}/activations`)
  },
}
