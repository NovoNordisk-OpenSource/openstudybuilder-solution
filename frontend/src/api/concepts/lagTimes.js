import repository from '../repository'

const resource = 'concepts/lag-times'

export default {
  create(data) {
    const params = {
      ...data,
    }
    return repository.post(resource, params)
  },
}
