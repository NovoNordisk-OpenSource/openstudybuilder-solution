import repository from '../repositoryStandardsImport'

const resource = 'effective-dates'

export default {
  getAll(params) {
    return repository.get(`${resource}`, { params })
  },
  get(effectiveDate) {
    return repository.get(`${resource}/${effectiveDate}`)
  },
}
