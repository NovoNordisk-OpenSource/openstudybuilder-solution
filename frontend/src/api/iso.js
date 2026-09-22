import repository from './repository'

const resource = 'iso'

export default {
  get(source, params) {
    return repository.get(`${resource}/${source}`, params)
  },
}
