import repository from './repository'

const resource = 'concepts/unit-definitions'

export default {
  get(params) {
    return repository.get(`${resource}`, params)
  },
  getObject(uid) {
    return repository.get(`${resource}/${uid}`)
  },
  getByDimension(dimension) {
    const params = { dimension: dimension, page_size: 0 }
    return repository.get(`${resource}`, { params })
  },
  getBySubset(subset) {
    const params = {
      subset: subset,
      sort_by: { conversion_factor_to_master: true },
      page_size: 0,
    }
    return repository.get(`${resource}`, { params })
  },
  create(data) {
    return repository.post(`${resource}`, data)
  },
  edit(uid, data) {
    return repository.patch(`${resource}/${uid}`, data)
  },
  delete(uid) {
    return repository.delete(`${resource}/${uid}`)
  },
  newVersion(uid) {
    return repository.post(`${resource}/${uid}/versions`)
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
  getUnitHistory(uid) {
    return repository.get(`${resource}/${uid}/versions`)
  },
}
