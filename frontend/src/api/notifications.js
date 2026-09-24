import repository from './repository'

const resource = 'notifications'

export default {
  get(params) {
    return repository.get(`${resource}`, { params })
  },
  getActive() {
    return repository.get(`${resource}/actives`)
  },
  getObject(sn) {
    return repository.get(`${resource}/${sn}`)
  },
  create(data) {
    return repository.post(`${resource}`, data)
  },
  update(sn, data) {
    return repository.patch(`${resource}/${sn}`, data)
  },
}
