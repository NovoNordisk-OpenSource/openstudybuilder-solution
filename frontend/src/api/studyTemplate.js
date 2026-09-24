import repository from './repository'

const resource = 'studies'

export default {
  getStudyTemplate() {
    return repository.get(`${resource}/template`)
  },
  setStudyTemplate(data) {
    return repository.post(`${resource}/template`, data)
  },
  updateStudyTemplate(data) {
    return repository.patch(`${resource}/template`, data)
  },
}
