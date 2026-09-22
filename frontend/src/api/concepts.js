import repository from './repository'

const resource = 'concepts'

export default {
  create(data, source) {
    const params = {
      ...data,
    }
    return repository.post(`${resource}/${source}`, params)
  },
}
