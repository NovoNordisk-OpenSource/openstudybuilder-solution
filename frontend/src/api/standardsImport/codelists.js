import repository from '../repositoryStandardsImport'

const resource = 'effective-dates'

export default {
  getDashboard(effectiveDate) {
    return repository.get(`${resource}/${effectiveDate}/dashboard`)
  },
  getCodelists(effectiveDate, params) {
    return repository.get(`${resource}/${effectiveDate}/codelists`, { params })
  },
  getCodelist(effectiveDate, codelistId, params) {
    return repository.get(
      `${resource}/${effectiveDate}/codelists/${codelistId}`,
      { params }
    )
  },
  markReviewed(effectiveDate, codelistId) {
    return repository.post(
      `${resource}/${effectiveDate}/codelists/${codelistId}/review`
    )
  },
  getTerms(effectiveDate, params) {
    return repository.get(`${resource}/${effectiveDate}/terms`, { params })
  },
  getTerm(effectiveDate, conceptId) {
    return repository.get(`${resource}/${effectiveDate}/terms/${conceptId}`)
  },
}
