import repository from './repository'

export default {
  getSettings() {
    return repository.get('/system/settings')
  },
}
