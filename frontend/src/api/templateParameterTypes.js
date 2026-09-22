import repository from './repository'

const resource = 'template-parameters'

export default {
  getTypes() {
    return repository.get(`/${resource}`)
  },
  getTerms(templateParameterName) {
    return repository.get(`${resource}/${templateParameterName}/terms`)
  },
}
