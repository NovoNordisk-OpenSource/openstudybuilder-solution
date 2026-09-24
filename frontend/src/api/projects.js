import repository from './repository'

const resource = 'projects'

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
  retrieve(projectUid) {
    return repository.get(`${resource}/${projectUid}`)
  },
  patch(projectUid, data) {
    return repository.patch(`${resource}/${projectUid}`, data)
  },
  delete(projectUid) {
    return repository.delete(`${resource}/${projectUid}`)
  },
}
