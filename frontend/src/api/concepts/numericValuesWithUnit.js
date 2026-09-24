import repository from '../repository'

const resource = 'concepts/numeric-values-with-unit'

export default {
  getAll(params) {
    return repository.get(resource, { params })
  },
  create(data) {
    const params = {
      ...data,
    }
    return repository.post(resource, params)
  },
}
