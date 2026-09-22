import repository from './repository'

const resource = 'admin'

export default {
  getComplexityActivityBurdens(params) {
    return repository.get(`${resource}/complexity-scores/activity-burdens`, {
      params,
    })
  },
  getComplexityBurdens(params) {
    return repository.get(`${resource}/complexity-scores/burdens`, { params })
  },
}
