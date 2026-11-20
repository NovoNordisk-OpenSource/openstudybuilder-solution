import repository from '../repositoryStandardsImport'

const resource = 'effective-dates'

export default {
  run(effectiveDate) {
    return repository.post(`${resource}/${effectiveDate}/analysis`)
  },
}
