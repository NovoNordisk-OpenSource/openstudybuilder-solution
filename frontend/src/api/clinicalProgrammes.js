import repository from './repository'

const resource = 'clinical-programmes'

export default {
  get(options) {
    const params = {
      ...options,
    }
    return repository.get(resource, { params })
  },
  create(data) {
    const params = {
      ...data,
    }
    return repository.post(resource, params)
  },
  retrieve(programmeUid) {
    return repository.get(`${resource}/${programmeUid}`)
  },
  patch(programmeUid, data) {
    return repository.patch(`${resource}/${programmeUid}`, data)
  },
  delete(programmeUid) {
    return repository.delete(`${resource}/${programmeUid}`)
  },
}
