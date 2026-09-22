import repository from './repository'

const resource = 'data-suppliers'

export default {
  get(params) {
    return repository.get(`${resource}`, params)
  },
  getDataSupplier(uid) {
    return repository.get(`${resource}/${uid}`)
  },
  create(data) {
    return repository.post(`${resource}`, data)
  },
  reactivate(uid) {
    return repository.post(`${resource}/${uid}/activations`)
  },
  inactivate(uid) {
    return repository.delete(`${resource}/${uid}/activations`)
  },
  update(data, uid) {
    return repository.patch(`${resource}/${uid}`, data)
  },
  getAuditTrail(uid) {
    return repository.get(`${resource}/${uid}/versions`)
  },
}
