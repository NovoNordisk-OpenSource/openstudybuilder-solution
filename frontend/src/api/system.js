import repository from './repository'

const basePath = '/system'

export default {
  getInformation() {
    return repository.get(`${basePath}/information`)
  },
}
