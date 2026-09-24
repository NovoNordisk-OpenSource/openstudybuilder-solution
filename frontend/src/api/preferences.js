import repository from './repository'

export default {
  getGlobalPreferences() {
    return repository.get('admin/global-preferences')
  },
  updateGlobalPreferences(payload) {
    return repository.patch('admin/global-preferences', payload)
  },
  getUserPreferences() {
    return repository.get('user-preferences')
  },
  updateUserPreferences(payload) {
    return repository.patch('user-preferences', payload)
  },
  resetUserPreferenceKey(key) {
    return repository.delete(`user-preferences/${key}`)
  },
}
