import repository from '../repository'

const resource = 'ct/paired-codelists'

export default {
  create(data) {
    return repository.post(resource, data)
  },
  getCodelistTerms(codelistUid, params) {
    return repository.get(`${resource}/${codelistUid}/terms`, { params })
  },
}
