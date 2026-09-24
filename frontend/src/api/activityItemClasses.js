import baseCollection from './baseCollection'
import repository from './repository'

const resource = 'activity-item-classes'
const api = baseCollection(resource)

export default {
  ...api,

  getDatasetCodelists(activityItemClassUid, datasetUid, params) {
    return repository.get(
      `${resource}/${activityItemClassUid}/datasets/${datasetUid}/codelists`,
      {
        params,
      }
    )
  },
  getOverview(activityItemClassUid, version) {
    const url = version
      ? `${resource}/${activityItemClassUid}/overview?version=${version}`
      : `${resource}/${activityItemClassUid}/overview`
    return repository.get(url)
  },
  getActivityInstanceClasses(activityItemClassUid, params) {
    return repository.get(
      `${resource}/${activityItemClassUid}/activity-instance-classes`,
      { params }
    )
  },
  getActivityItemClassVersions(uid) {
    return repository.get(`${resource}/${uid}/versions`)
  },
}
