import repository from './repository'

export default (resource) => ({
  getAll(params) {
    return repository.get(resource, { params })
  },
  get(uid) {
    return repository.get(`${resource}/${uid}`)
  },
  getHeaders(params) {
    return repository.get(`${resource}/headers`, { params })
  },
  getVersions(params) {
    return repository.get(`${resource}/versions`, { params })
  },
  create(data) {
    return repository.post(`${resource}`, data)
  },
  update(uid, data) {
    return repository.patch(`${resource}/${uid}`, data)
  },
  delete(uid) {
    return repository.delete(`${resource}/${uid}`)
  },
  approve(uid) {
    return repository.post(`${resource}/${uid}/approvals`)
  },
  inactivate(uid) {
    return repository.delete(`${resource}/${uid}/activations`)
  },
  reactivate(uid) {
    return repository.post(`${resource}/${uid}/activations`)
  },
  newVersion(uid) {
    return repository.post(`${resource}/${uid}/versions`)
  },
})
