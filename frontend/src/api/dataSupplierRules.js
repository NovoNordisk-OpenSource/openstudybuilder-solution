import repository from './repository'

const resource = 'data-suppliers/rules'

export default {
  get(params) {
    return repository.get(`${resource}`, { params })
  },
  getDataSupplierRule(uid) {
    return repository.get(`${resource}/${uid}`)
  },
  create(data) {
    return repository.post(`${resource}`, data)
  },
  update(uid, data) {
    return repository.patch(`${resource}/${uid}`, data)
  },
  reactivate(uid) {
    return repository.post(`${resource}/${uid}/activations`)
  },
  inactivate(uid) {
    return repository.delete(`${resource}/${uid}/activations`)
  },
  getAuditTrail(uid) {
    return repository.get(`${resource}/${uid}/versions`)
  },
}
