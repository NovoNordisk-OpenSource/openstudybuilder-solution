import baseCollection from './baseCollection'
import repository from './repository'

const resource = 'activity-instance-classes'
const api = baseCollection(resource)

export default {
  ...api,

  getActivityItemClasses(activityInstanceClassUid, params) {
    return repository.get(
      `${resource}/${activityInstanceClassUid}/activity-item-classes`,
      { params }
    )
  },
  getModelMappingDatasets(params) {
    return repository.get(`${resource}/model-mappings/datasets`, { params })
  },
  getParentClassOverview(activityInstanceClassUid, version) {
    const url = version
      ? `${resource}/${activityInstanceClassUid}/parent-class-overview?version=${version}`
      : `${resource}/${activityInstanceClassUid}/parent-class-overview`
    return repository.get(url)
  },
  getOverview(activityInstanceClassUid, version) {
    const url = version
      ? `${resource}/${activityInstanceClassUid}/overview?version=${version}`
      : `${resource}/${activityInstanceClassUid}/overview`
    return repository.get(url)
  },
  getChildClasses(activityInstanceClassUid, params) {
    return repository.get(
      `${resource}/${activityInstanceClassUid}/child-classes`,
      { params }
    )
  },
  getItemClasses(activityInstanceClassUid, params) {
    return repository.get(
      `${resource}/${activityInstanceClassUid}/item-classes`,
      { params }
    )
  },
  getActivityInstanceClassVersions(uid) {
    return repository.get(`${resource}/${uid}/versions`)
  },
}
