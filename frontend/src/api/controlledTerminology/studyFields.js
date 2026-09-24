import repository from '../repository'

const resource = '/meta-study-fields'

export default {
  get() {
    return repository.get(resource)
  },
}
