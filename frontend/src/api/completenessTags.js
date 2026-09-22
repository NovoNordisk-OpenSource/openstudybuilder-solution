import repository from './repository'

const resource = 'data-completeness-tags'

export default {
  get() {
    return repository.get(`${resource}`)
  },
  add(data) {
    return repository.post(`${resource}`, data)
  },
}
