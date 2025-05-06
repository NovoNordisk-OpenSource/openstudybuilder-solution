import baseCollection from './baseCollection'
import repository from './repository'

const resource = 'activity-item-classes'
const api = baseCollection(resource)

export default {
  ...api,

  getTerms(activityItemClassUid, params) {
    return repository.get(`${resource}/${activityItemClassUid}/terms`, {
      params,
    })
  },
}
