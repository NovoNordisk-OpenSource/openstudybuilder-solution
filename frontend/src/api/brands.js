import repository from './repository'

const resource = 'brands'

export default {
  getAll() {
    return repository.get(resource)
  },
}
